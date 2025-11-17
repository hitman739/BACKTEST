"""
Simulator Engine - Proportional Copy Trading Simulation

Simulates a 10,000 USDT account copying a Hyperliquid trader proportionally.
- Uses REAL data from Hyperliquid (fills, positions, prices)
- Only simulates trades AFTER start_time
- Copies same % of equity risk as the trader
- No fees or funding (for now)
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from hyperliquid.info import Info
from hyperliquid.utils import constants
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SimulatedPosition:
    """Represents a simulated position for one symbol"""
    symbol: str
    side: str  # "long" or "short"
    size_sim: float  # Simulated position size
    avg_entry_price_sim: float  # Average entry price for simulation
    # Note: Simulation always uses 1x leverage
    # Position sizing is based on trader's margin (considering their leverage)

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
                    "mark_price": mark_price,
                    "unrealized_pnl_pos": pos.get_unrealized_pnl(mark_price)
                })

        return {
            "wallet": self.wallet_address,
            "start_time": self.start_time,
            "equity_sim_actual": self.equity_sim_actual,
            "pnl_total_sim": self.pnl_total_sim,
            "pnl_pct_sim": self.pnl_pct_sim,
            "realized_pnl_sim": self.realized_pnl_sim,
            "unrealized_pnl_sim": self.unrealized_pnl_sim,
            "open_positions": open_positions,
            "trades_count_sim": self.trades_count_sim
        }


class SimulatorEngine:
    """Main simulator engine managing multiple wallet simulations"""

    def __init__(self, testnet: bool = False):
        self.testnet = testnet
        self.info = Info(constants.TESTNET_API_URL if testnet else constants.MAINNET_API_URL)
        self.simulations: Dict[str, WalletSimulation] = {}  # wallet -> simulation
        self.running = False
        self.update_task = None

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
            user_state = self.info.user_state(wallet_address)
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
            user_state = self.info.user_state(wallet_address)
            if not user_state or 'assetPositions' not in user_state:
                return 1.0  # Default to 1x if can't determine

            # Find position for this symbol
            for position in user_state['assetPositions']:
                if position['position']['coin'] == symbol:
                    leverage = float(position['position']['leverage']['value'])
                    logger.debug(f"Trader leverage for {symbol}: {leverage}x")
                    return leverage

            # If no position found, use default
            return 1.0

        except Exception as e:
            logger.error(f"Error getting trader leverage: {e}")
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
            symbol = fill['coin']
            size_trader = abs(float(fill['sz']))  # Positive size
            price_fill = float(fill['px'])
            side = fill['side']  # 'A' (ask/sell) or 'B' (bid/buy)

            # Get trader's current position to determine leverage
            current_pos = simulation.positions.get(symbol)

            # Calculate notional value of trader's fill
            notional_trader = size_trader * price_fill

            # Get trader's leverage for this symbol
            leverage_trader = self.get_trader_leverage(wallet_address, symbol)

            # Calculate MARGIN USED (not notional) considering leverage
            # margin_used = notional / leverage
            margin_used_trader = notional_trader / leverage_trader

            # Get trader's current equity
            trader_equity = simulation.last_trader_equity or 100000.0

            # Calculate risk fraction based on MARGIN, not notional
            risk_frac = margin_used_trader / trader_equity

            # Calculate simulated notional WITHOUT leverage
            # Simulation always uses 1x leverage, but sizing is based on trader's margin
            notional_sim = risk_frac * simulation.equity_sim_actual
            size_sim = notional_sim / price_fill

            logger.info(f"Processing fill: {symbol} {side} {size_trader} @ {price_fill}")
            logger.info(f"Trader leverage: {leverage_trader}x | Margin: ${margin_used_trader:.2f} | Risk: {risk_frac:.4%}")
            logger.info(f"Sim notional: ${notional_sim:.2f} | Sim size: {size_sim:.6f}")

            # Determine action based on side and current position
            if not current_pos or current_pos.size_sim == 0:
                # Opening new position
                position_side = "long" if side == 'B' else "short"
                simulation.positions[symbol] = SimulatedPosition(
                    symbol=symbol,
                    side=position_side,
                    size_sim=size_sim,
                    avg_entry_price_sim=price_fill
                )
                simulation.trades_count_sim += 1
                logger.info(f"Opened {position_side} position: {size_sim:.6f} {symbol} @ {price_fill}")

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
                    simulation.trades_count_sim += 1

                    logger.info(f"Increased position: {new_size:.6f} {symbol} @ {new_avg_price:.2f}")

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

                    logger.info(f"Closed {close_size:.6f} {symbol}, realized PnL: ${realized_pnl:.2f}")

                    # Update position size
                    new_size = old_size - close_size
                    if new_size <= 0.0001:  # Position fully closed
                        current_pos.size_sim = 0.0
                        logger.info(f"Position fully closed for {symbol}")
                    else:
                        current_pos.size_sim = new_size
                        logger.info(f"Position reduced to {new_size:.6f} {symbol}")

                    # If size_sim > old_size, we're reversing (close + open opposite)
                    if size_sim > old_size:
                        reverse_size = size_sim - old_size
                        new_side = "short" if current_pos.side == "long" else "long"
                        simulation.positions[symbol] = SimulatedPosition(
                            symbol=symbol,
                            side=new_side,
                            size_sim=reverse_size,
                            avg_entry_price_sim=price_fill
                        )
                        logger.info(f"Reversed to {new_side} {reverse_size:.6f} {symbol} @ {price_fill}")

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
            all_mids = self.info.all_mids()

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
                user_fills = self.info.user_fills(wallet_address)

                if not user_fills:
                    continue

                # Process each fill
                for fill in user_fills:
                    await self.process_fill(wallet_address, fill)

                # Update trader's equity
                user_state = self.info.user_state(wallet_address)
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
