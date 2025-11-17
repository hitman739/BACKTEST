"""
Metrics Calculator
Calculates PnL, fees, fee factor, and other metrics from database
"""
import logging
from typing import Dict, Optional
from database import Database
from hyperliquid.info import Info
from hyperliquid.utils import constants

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """Calculate wallet metrics from database"""

    # Hyperliquid fee structure
    MAKER_FEE = 0.00015  # 0.015% (assuming mid-tier)
    TAKER_FEE = 0.00045  # 0.045%

    def __init__(self, database: Database, testnet: bool = False):
        self.database = database
        self.testnet = testnet
        self.info = None  # Lazy initialization

    def _get_info(self) -> Info:
        """Lazy initialization of Info object"""
        if self.info is None:
            try:
                self.info = Info(
                    constants.TESTNET_API_URL if self.testnet else constants.MAINNET_API_URL,
                    skip_ws=True
                )
                logger.info("Hyperliquid Info client initialized for metrics")
            except Exception as e:
                logger.error(f"Failed to initialize Hyperliquid Info client: {e}")
                raise
        return self.info

    def calculate_metrics(self, wallet_address: str) -> Dict:
        """
        Calculate comprehensive metrics for a wallet

        Returns:
        {
            "equity": current account value,
            "total_volume": total volume traded,
            "total_fees": total fees paid,
            "realized_pnl": PnL from closed positions,
            "unrealized_pnl": PnL from open positions,
            "total_pnl": realized + unrealized,
            "num_trades": number of trades,
            "num_open_positions": number of open positions,
            "fee_factor_mixed": (profit_after_fees / profit_before_fees) with mixed fees,
            "fee_factor_taker": (profit_after_fees / profit_before_fees) with 100% taker,
            "roi": return on investment %
        }
        """
        wallet_address = wallet_address.lower()

        # Get wallet info
        wallet_cursor = self.database.conn.cursor()
        wallet_cursor.execute("SELECT initial_balance FROM wallets WHERE address = ?",
                             (wallet_address,))
        wallet_row = wallet_cursor.fetchone()

        if not wallet_row:
            logger.warning(f"Wallet {wallet_address} not found")
            return {}

        initial_balance = wallet_row["initial_balance"]

        # Get all fills
        fills = self.database.get_fills(wallet_address, limit=10000)

        # Calculate total volume and realized PnL from fills
        total_volume = 0.0
        realized_pnl = 0.0
        total_fees_paid = 0.0

        for fill in fills:
            volume = abs(fill["size"]) * fill["price"]
            total_volume += volume

            # Realized PnL (only on closing trades)
            if fill["closed_pnl"] is not None:
                realized_pnl += fill["closed_pnl"]

            # Fees
            if fill["fee"] is not None:
                total_fees_paid += abs(fill["fee"])

        # Get open positions
        positions = self.database.get_positions(wallet_address)

        # Calculate unrealized PnL from open positions
        unrealized_pnl = 0.0
        all_mids = None

        if positions:
            try:
                all_mids = self._get_info().all_mids()
            except Exception as e:
                logger.warning(f"Could not fetch prices: {e}")
                all_mids = {}

        for position in positions:
            coin = position["coin"]
            size = position["size"]
            entry_px = position["entry_px"]

            # Get current price
            current_px = float(all_mids.get(coin, entry_px)) if all_mids else entry_px

            # Calculate unrealized PnL
            if size > 0:  # Long
                pnl = size * (current_px - entry_px)
            else:  # Short
                pnl = abs(size) * (entry_px - current_px)

            unrealized_pnl += pnl

        # Total PnL
        total_pnl = realized_pnl + unrealized_pnl

        # Current equity
        equity = initial_balance + total_pnl

        # ROI
        roi = ((equity - initial_balance) / initial_balance) * 100 if initial_balance > 0 else 0

        # Number of trades
        num_trades = len(fills)
        num_open_positions = len(positions)

        # Fee Factor Calculation
        fee_factor_mixed = self._calculate_fee_factor(total_volume, total_pnl, mixed=True)
        fee_factor_taker = self._calculate_fee_factor(total_volume, total_pnl, mixed=False)

        metrics = {
            "equity": equity,
            "total_volume": total_volume,
            "total_fees": total_fees_paid,
            "realized_pnl": realized_pnl,
            "unrealized_pnl": unrealized_pnl,
            "total_pnl": total_pnl,
            "num_trades": num_trades,
            "num_open_positions": num_open_positions,
            "fee_factor_mixed": fee_factor_mixed,
            "fee_factor_taker": fee_factor_taker,
            "roi": roi
        }

        return metrics

    def _calculate_fee_factor(self, total_volume: float, total_pnl: float, mixed: bool = True) -> Optional[float]:
        """
        Calculate fee factor ratio

        fee_factor = (profit_after_fees) / (profit_before_fees)
        fee_factor = (total_pnl - estimated_fees) / total_pnl

        Args:
            total_volume: Total volume traded
            total_pnl: Total PnL before fees
            mixed: If True, use 75% maker + 25% taker. If False, use 100% taker

        Returns:
            Fee factor ratio (0-1), or None if can't calculate
        """
        if total_pnl <= 0:
            return None  # Can't calculate fee factor if not profitable

        # Estimate fees based on volume
        if mixed:
            # 75% maker, 25% taker (realistic scenario)
            fee_rate = 0.75 * self.MAKER_FEE + 0.25 * self.TAKER_FEE
        else:
            # 100% taker (worst case)
            fee_rate = self.TAKER_FEE

        estimated_fees = total_volume * fee_rate

        # Fee factor
        profit_after_fees = total_pnl - estimated_fees
        fee_factor = profit_after_fees / total_pnl

        return max(0, min(1, fee_factor))  # Clamp between 0 and 1

    async def update_all_metrics(self):
        """Update metrics for all active wallets"""
        wallets = self.database.get_active_wallets()

        logger.info(f"Updating metrics for {len(wallets)} wallets...")

        for wallet in wallets:
            try:
                metrics = self.calculate_metrics(wallet)

                if metrics:
                    self.database.save_metrics(wallet, metrics)
                    logger.info(f"✅ Updated metrics for {wallet}: PnL=${metrics['total_pnl']:.2f}, "
                               f"FFr={metrics['fee_factor_mixed']:.3f}")
            except Exception as e:
                logger.error(f"Error updating metrics for {wallet}: {e}")

    async def start_periodic_updates(self, interval_seconds: int = 60):
        """Start periodic metrics updates"""
        logger.info(f"Starting periodic metrics updates (every {interval_seconds}s)")

        while True:
            try:
                await self.update_all_metrics()
            except Exception as e:
                logger.error(f"Error in periodic update: {e}")

            await asyncio.sleep(interval_seconds)


# Import asyncio at the top if not already there
import asyncio
