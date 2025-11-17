"""
Simulator Engine - Proportional Copy Trading Simulation

Simulates a 10,000 USDT account copying a Hyperliquid trader proportionally.
- Uses REAL data from Hyperliquid (fills, positions, prices)
- Only simulates trades AFTER start_time (no historical backfill)
- Copies same % of equity risk as the trader with SAME LEVERAGE
- No fees or funding (for now)

LOGIC:
- trader_notional = trader_size * price
- trader_margin = trader_notional / trader_leverage
- risk_fraction = trader_margin / trader_equity
- my_notional = risk_fraction * my_equity * trader_leverage (SAME LEVERAGE AS TRADER)
- my_size = my_notional / price
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from hyperliquid.info import Info
from hyperliquid.utils import constants
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - [%(levelname)s] - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class SimulatedPosition:
    """Represents a simulated position for one symbol"""
    symbol: str
    side: str  # "long" or "short"
    size_sim: float  # Simulated position size
    avg_entry_price_sim: float  # Average entry price for simulation
    leverage: float = 1.0  # Leverage used (same as trader)

    def get_unrealized_pnl(self, mark_price: float) -> float:
        """Calculate unrealized PnL for this position"""
        if self.size_sim == 0:
            return 0.0

        if self.side == "long":
            return self.size_sim * (mark_price - self.avg_entry_price_sim)
        else:  # short
            return self.size_sim * (self.avg_entry_price_sim - mark_price)


@dataclass
class WalletSimulation:
    """Simulates copying a specific wallet with proportional sizing"""
    wallet_address: str
    start_time: float  # Unix timestamp when simulation started
    equity_sim_initial: float = 10000.0  # Always start with 10k
    realized_pnl_sim: float = 0.0  # PnL from closed positions
    positions: Dict[str, SimulatedPosition] = field(default_factory=dict)  # symbol -> position
    trades_count_sim: int = 0  # Number of simulated trades
    last_trader_equity: Optional[float] = None  # Cache trader's equity
    recent_fills: List[dict] = field(default_factory=list)  # Last 10 fills for debugging

    @property
    def unrealized_pnl_sim(self) -> float:
        """Calculate total unrealized PnL from all open positions"""
        # We'll need mark prices - this will be set externally
        return sum(pos.get_unrealized_pnl(pos.mark_price)
                   for pos in self.positions.values()
                   if hasattr(pos, 'mark_price'))

    @property
    def pnl_total_sim(self) -> float:
        """Total PnL = realized + unrealized"""
        return self.realized_pnl_sim + self.unrealized_pnl_sim

    @property
    def equity_sim_actual(self) -> float:
        """Current simulated equity"""
        return self.equity_sim_initial + self.pnl_total_sim

    @property
    def pnl_pct_sim(self) -> float:
        """PnL percentage based on initial equity"""
        return (self.pnl_total_sim / self.equity_sim_initial) * 100

    def get_snapshot(self) -> dict:
        """Get current snapshot of simulation state"""
        open_positions = []
        for symbol, pos in self.positions.items():
            if pos.size_sim != 0:
                mark_price = getattr(pos, 'mark_price', pos.avg_entry_price_sim)
                open_positions.append({
                    "symbol": symbol,
                    "side": pos.side,
                    "size_sim": pos.size_sim,
                    "avg_entry_price_sim": pos.avg_entry_price_sim,
                    "leverage": pos.leverage,
                    "mark_price": mark_price,
                    "unrealized_pnl_pos": pos.get_unrealized_pnl(mark_price)
                })

        return {
            "wallet": self.wallet_address,
            "start_time": self.start_time,
            "start_time_iso": datetime.fromtimestamp(self.start_time).isoformat(),
            "equity_sim_initial": self.equity_sim_initial,
            "equity_sim_actual": self.equity_sim_actual,
            "pnl_total_sim": self.pnl_total_sim,
            "pnl_pct_sim": self.pnl_pct_sim,
            "realized_pnl_sim": self.realized_pnl_sim,
            "unrealized_pnl_sim": self.unrealized_pnl_sim,
            "open_positions": open_positions,
            "num_open_positions": len(open_positions),
            "trades_count_sim": self.trades_count_sim,
            "roi_pct": self.pnl_pct_sim
        }

    def get_debug_info(self) -> dict:
        """Get detailed debug information including recent fills"""
        snapshot = self.get_snapshot()
        snapshot["recent_fills"] = self.recent_fills[-5:]  # Last 5 fills
        snapshot["last_trader_equity"] = self.last_trader_equity
        return snapshot


class SimulatorEngine:
    """Main simulator engine managing multiple wallet simulations"""

    def __init__(self, testnet: bool = False):
        self.testnet = testnet
        self.info = None  # Lazy initialization
        self.simulations: Dict[str, WalletSimulation] = {}  # wallet -> simulation
        self.running = False
        self.update_task = None

    def _get_info(self) -> Info:
        """Lazy initialization of Info object"""
        if self.info is None:
            try:
                self.info = Info(constants.TESTNET_API_URL if self.testnet else constants.MAINNET_API_URL)
            except Exception as e:
                logger.error(f"Failed to initialize Hyperliquid Info client: {e}")
                raise
        return self.info

    async def start_simulation(self, wallet_address: str) -> WalletSimulation:
        """Start simulating a wallet from NOW"""
        logger.info(f"Starting simulation for wallet: {wallet_address}")

        # Clean any previous simulation for this wallet
        if wallet_address in self.simulations:
            logger.info(f"Removing previous simulation for {wallet_address}")
            del self.simulations[wallet_address]

        # Create new simulation
        simulation = WalletSimulation(
            wallet_address=wallet_address,
            start_time=time.time(),
            equity_sim_initial=10000.0
        )

        # Get trader's current equity
        try:
            user_state = self._get_info().user_state(wallet_address)
            if user_state and 'marginSummary' in user_state:
                simulation.last_trader_equity = float(user_state['marginSummary']['accountValue'])
                logger.info(f"Trader equity: ${simulation.last_trader_equity:,.2f}")
        except Exception as e:
            logger.error(f"Error getting trader equity: {e}")
            simulation.last_trader_equity = 100000.0  # Default fallback

        self.simulations[wallet_address] = simulation

        # Start background update task if not running
        if not self.running:
            await self.start_background_updates()

        return simulation

    async def stop_simulation(self, wallet_address: str) -> bool:
        """Stop simulating a wallet"""
        if wallet_address in self.simulations:
            logger.info(f"Stopping simulation for wallet: {wallet_address}")
            del self.simulations[wallet_address]

            # Stop background task if no simulations left
            if len(self.simulations) == 0 and self.running:
                await self.stop_background_updates()

            return True
        return False

    def get_simulation(self, wallet_address: str) -> Optional[WalletSimulation]:
        """Get simulation for a wallet"""
        return self.simulations.get(wallet_address)

    def get_all_wallets(self) -> List[dict]:
        """Get summary of all active simulations"""
        return [
            {
                "wallet": wallet,
                "equity_sim_actual": sim.equity_sim_actual,
                "pnl_total_sim": sim.pnl_total_sim,
                "pnl_pct_sim": sim.pnl_pct_sim,
                "trades_count_sim": sim.trades_count_sim,
                "start_time": sim.start_time
            }
            for wallet, sim in self.simulations.items()
        ]

    def get_trader_leverage(self, wallet_address: str, symbol: str) -> float:
        """Get the leverage the trader is using for a specific symbol"""
        try:
            user_state = self._get_info().user_state(wallet_address)
            if not user_state:
                logger.warning(f"Could not get user_state for {wallet_address}")
                return 1.0

            # Check if assetPositions exists
            if 'assetPositions' not in user_state:
                logger.debug(f"No assetPositions in user_state for {wallet_address}")
                return 1.0

            # Find position for this symbol
            for pos_data in user_state['assetPositions']:
                try:
                    # Handle different possible structures
                    if 'position' in pos_data:
                        position = pos_data['position']
                        coin = position.get('coin', '')

                        if coin == symbol:
                            # Try to get leverage
                            if 'leverage' in position:
                                lev_data = position['leverage']
                                if isinstance(lev_data, dict) and 'value' in lev_data:
                                    leverage = float(lev_data['value'])
                                elif isinstance(lev_data, (int, float, str)):
                                    leverage = float(lev_data)
                                else:
                                    logger.warning(f"Unexpected leverage format: {lev_data}")
                                    leverage = 1.0

                                logger.info(f"Trader leverage for {symbol}: {leverage}x")
                                return leverage
                except (KeyError, ValueError, TypeError) as e:
                    logger.debug(f"Error parsing position data: {e}")
                    continue

            # If no position found, use default
            logger.debug(f"No position found for {symbol}, using 1x leverage")
            return 1.0

        except Exception as e:
            logger.error(f"Error getting trader leverage for {wallet_address}/{symbol}: {e}", exc_info=True)
            return 1.0  # Safe default

    async def process_fill(self, wallet_address: str, fill: dict):
        """Process a real fill from the trader and simulate it proportionally"""
        simulation = self.simulations.get(wallet_address)
        if not simulation:
            return

        # Only process fills after start_time
        fill_time = fill.get('time', 0) / 1000  # Convert ms to seconds
        if fill_time < simulation.start_time:
            logger.debug(f"Ignoring fill before start_time: {fill_time} < {simulation.start_time}")
            return

        try:
            # Validate fill data
            if not fill or not isinstance(fill, dict):
                logger.error(f"Invalid fill data: {fill}")
                return

            symbol = fill.get('coin')
            if not symbol:
                logger.error(f"Missing 'coin' in fill: {fill}")
                return

            size_str = fill.get('sz')
            price_str = fill.get('px')
            side = fill.get('side')

            if not all([size_str, price_str, side]):
                logger.error(f"Missing required fields in fill: {fill}")
                return

            try:
                size_trader = abs(float(size_str))  # Positive size
                price_fill = float(price_str)
            except (ValueError, TypeError) as e:
                logger.error(f"Invalid numeric values in fill: {fill}, error: {e}")
                return

            if size_trader <= 0 or price_fill <= 0:
                logger.error(f"Invalid size or price in fill: size={size_trader}, price={price_fill}")
                return

            # Get trader's current position to determine leverage
            current_pos = simulation.positions.get(symbol)

            # ========================================
            # PROPORTIONAL SIZING WITH SAME LEVERAGE
            # ========================================

            # 1. Calculate trader's notional
            notional_trader = size_trader * price_fill

            # 2. Get trader's leverage for this symbol
            leverage_trader = self.get_trader_leverage(wallet_address, symbol)

            # 3. Calculate trader's MARGIN used
            margin_trader = notional_trader / leverage_trader

            # 4. Get trader's current equity
            trader_equity = simulation.last_trader_equity or 100000.0

            # 5. Calculate risk fraction
            risk_frac = margin_trader / trader_equity

            # 6. Calculate MY notional WITH SAME LEVERAGE
            # This is the KEY change: we use the same leverage as the trader
            my_notional = risk_frac * simulation.equity_sim_actual * leverage_trader
            size_sim = my_notional / price_fill

            # ========================================
            # DETAILED LOGGING
            # ========================================
            logger.info("=" * 80)
            logger.info(f"🔄 NEW FILL from trader {wallet_address[:10]}...")
            logger.info(f"   Coin: {symbol} | Side: {side} | Trader Size: {size_trader:.6f} | Price: ${price_fill:.2f}")
            logger.info(f"   Trader Notional: ${notional_trader:.2f}")
            logger.info(f"   Trader Leverage: {leverage_trader:.1f}x")
            logger.info(f"   Trader Margin: ${margin_trader:.2f}")
            logger.info(f"   Trader Equity: ${trader_equity:.2f}")
            logger.info(f"   Risk Fraction: {risk_frac:.4%}")
            logger.info(f"")
            logger.info(f"📊 SIMULATED FILL:")
            logger.info(f"   My Equity: ${simulation.equity_sim_actual:.2f}")
            logger.info(f"   My Leverage: {leverage_trader:.1f}x (same as trader)")
            logger.info(f"   My Notional: ${my_notional:.2f}")
            logger.info(f"   My Size: {size_sim:.6f} {symbol}")
            logger.info(f"   Entry Price: ${price_fill:.2f}")

            # Save fill for debugging (keep last 10)
            fill_debug = {
                "time": fill_time,
                "coin": symbol,
                "side": side,
                "trader_size": size_trader,
                "my_size": size_sim,
                "price": price_fill,
                "leverage": leverage_trader,
                "trader_notional": notional_trader,
                "my_notional": my_notional
            }
            simulation.recent_fills.append(fill_debug)
            if len(simulation.recent_fills) > 10:
                simulation.recent_fills.pop(0)

            # Determine action based on side and current position
            if not current_pos or current_pos.size_sim == 0:
                # Opening new position
                position_side = "long" if side == 'B' else "short"
                simulation.positions[symbol] = SimulatedPosition(
                    symbol=symbol,
                    side=position_side,
                    size_sim=size_sim,
                    avg_entry_price_sim=price_fill,
                    leverage=leverage_trader
                )
                simulation.trades_count_sim += 1
                logger.info(f"")
                logger.info(f"✅ OPENED {position_side.upper()} position: {size_sim:.6f} {symbol} @ ${price_fill:.2f}")
                logger.info(f"   Leverage: {leverage_trader:.1f}x")
                logger.info(f"   Current PnL: ${simulation.pnl_total_sim:.2f} | Equity: ${simulation.equity_sim_actual:.2f}")
                logger.info("=" * 80)

            else:
                # There's an existing position
                # Check if this fill is in the same direction or opposite
                is_buy = (side == 'B')
                is_long_pos = (current_pos.side == "long")

                if (is_buy and is_long_pos) or (not is_buy and not is_long_pos):
                    # Adding to position
                    old_size = current_pos.size_sim
                    old_price = current_pos.avg_entry_price_sim
                    new_size = old_size + size_sim

                    # Weighted average entry price
                    new_avg_price = ((old_size * old_price) + (size_sim * price_fill)) / new_size

                    current_pos.size_sim = new_size
                    current_pos.avg_entry_price_sim = new_avg_price
                    current_pos.leverage = leverage_trader
                    simulation.trades_count_sim += 1

                    logger.info(f"")
                    logger.info(f"📈 INCREASED position: {old_size:.6f} → {new_size:.6f} {symbol}")
                    logger.info(f"   New Avg Entry: ${new_avg_price:.2f}")
                    logger.info(f"   Leverage: {leverage_trader:.1f}x")
                    logger.info(f"   Current PnL: ${simulation.pnl_total_sim:.2f} | Equity: ${simulation.equity_sim_actual:.2f}")
                    logger.info("=" * 80)

                else:
                    # Closing or reducing position (opposite direction)
                    old_size = current_pos.size_sim
                    close_size = min(size_sim, old_size)

                    # Calculate realized PnL on closed portion
                    if current_pos.side == "long":
                        realized_pnl = close_size * (price_fill - current_pos.avg_entry_price_sim)
                    else:  # short
                        realized_pnl = close_size * (current_pos.avg_entry_price_sim - price_fill)

                    simulation.realized_pnl_sim += realized_pnl
                    simulation.trades_count_sim += 1

                    logger.info(f"")
                    logger.info(f"💰 CLOSED/REDUCED {current_pos.side.upper()} position: {old_size:.6f} → {max(0, old_size - close_size):.6f} {symbol}")
                    logger.info(f"   Closed Size: {close_size:.6f}")
                    logger.info(f"   Exit Price: ${price_fill:.2f}")
                    logger.info(f"   Entry Price: ${current_pos.avg_entry_price_sim:.2f}")
                    logger.info(f"   Realized PnL: ${realized_pnl:+.2f}")
                    logger.info(f"   Total Realized PnL: ${simulation.realized_pnl_sim:.2f}")

                    # Update position size
                    new_size = old_size - close_size
                    if new_size <= 0.0001:  # Position fully closed
                        current_pos.size_sim = 0.0
                        logger.info(f"   ✅ Position FULLY CLOSED for {symbol}")
                    else:
                        current_pos.size_sim = new_size
                        logger.info(f"   📉 Position REDUCED to {new_size:.6f} {symbol}")

                    logger.info(f"   Current Total PnL: ${simulation.pnl_total_sim:.2f} | Equity: ${simulation.equity_sim_actual:.2f}")

                    # If size_sim > old_size, we're reversing (close + open opposite)
                    if size_sim > old_size:
                        reverse_size = size_sim - old_size
                        new_side = "short" if current_pos.side == "long" else "long"
                        simulation.positions[symbol] = SimulatedPosition(
                            symbol=symbol,
                            side=new_side,
                            size_sim=reverse_size,
                            avg_entry_price_sim=price_fill,
                            leverage=leverage_trader
                        )
                        logger.info(f"   🔄 REVERSED to {new_side.upper()}: {reverse_size:.6f} {symbol} @ ${price_fill:.2f}")

                    logger.info("=" * 80)

        except Exception as e:
            logger.error(f"Error processing fill: {e}", exc_info=True)

    async def update_mark_prices(self):
        """Update mark prices for all symbols with open positions"""
        try:
            # Get all unique symbols across all simulations
            symbols = set()
            for sim in self.simulations.values():
                symbols.update(sim.positions.keys())

            if not symbols:
                return

            # Get all mids (mark prices)
            all_mids = self._get_info().all_mids()

            # Update mark price for each position
            for sim in self.simulations.values():
                for symbol, pos in sim.positions.items():
                    if pos.size_sim != 0:
                        mark_price = all_mids.get(symbol, pos.avg_entry_price_sim)
                        pos.mark_price = mark_price

        except Exception as e:
            logger.error(f"Error updating mark prices: {e}")

    async def check_for_new_fills(self):
        """Check for new fills for all simulated wallets"""
        for wallet_address, sim in list(self.simulations.items()):
            try:
                # Get user fills
                user_fills = self._get_info().user_fills(wallet_address)

                if not user_fills:
                    continue

                # Process each fill
                for fill in user_fills:
                    await self.process_fill(wallet_address, fill)

                # Update trader's equity
                user_state = self._get_info().user_state(wallet_address)
                if user_state and 'marginSummary' in user_state:
                    sim.last_trader_equity = float(user_state['marginSummary']['accountValue'])

            except Exception as e:
                logger.error(f"Error checking fills for {wallet_address}: {e}")

    async def background_update_loop(self):
        """Background task to update simulations periodically"""
        logger.info("Starting background update loop")

        while self.running:
            try:
                # Update mark prices
                await self.update_mark_prices()

                # Check for new fills (less frequently to avoid rate limits)
                await self.check_for_new_fills()

                # Wait before next update
                await asyncio.sleep(5)  # Update every 5 seconds

            except Exception as e:
                logger.error(f"Error in background update loop: {e}")
                await asyncio.sleep(5)

        logger.info("Background update loop stopped")

    async def start_background_updates(self):
        """Start the background update task"""
        if not self.running:
            self.running = True
            self.update_task = asyncio.create_task(self.background_update_loop())
            logger.info("Background updates started")

    async def stop_background_updates(self):
        """Stop the background update task"""
        if self.running:
            self.running = False
            if self.update_task:
                self.update_task.cancel()
                try:
                    await self.update_task
                except asyncio.CancelledError:
                    pass
            logger.info("Background updates stopped")


# Global simulator instance
simulator_engine = SimulatorEngine(testnet=False)
