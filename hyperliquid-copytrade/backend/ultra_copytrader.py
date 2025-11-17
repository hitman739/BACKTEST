"""
Ultra-Low Latency Copy Trading Manager
Optimized for minimal evento → orden latency
"""
import asyncio
import logging
from typing import Dict, Optional
from hyperliquid.info import Info
from hyperliquid.utils import constants
from ultra_websocket import UltraLowLatencyWebSocket
from ultra_executor import UltraOrderExecutor
import time

logger = logging.getLogger(__name__)


class UltraCopyTrader:
    """
    Copy trading manager optimized for speed

    Architecture:
    1. WebSocket receives event from target trader
    2. Immediately calculate position size
    3. Execute order without blocking
    4. Continue processing

    Target: < 100ms from event to order submission
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        target_wallet: str,
        copy_ratio: float = 1.0,  # How much to copy (1.0 = 100%)
        testnet: bool = False
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.target_wallet = target_wallet.lower()
        self.copy_ratio = copy_ratio
        self.testnet = testnet

        # Initialize components
        self.websocket = UltraLowLatencyWebSocket(testnet=testnet)
        self.executor = UltraOrderExecutor(api_key, api_secret, testnet=testnet)

        # Info client for initial sync only
        base_url = constants.TESTNET_API_URL if testnet else constants.MAINNET_API_URL
        self.info = Info(base_url, skip_ws=True)

        # State (in-memory for speed)
        self.target_positions: Dict[str, Dict] = {}  # coin -> position data
        self.my_positions: Dict[str, Dict] = {}  # coin -> position data
        self.my_account_value: float = 0.0
        self.target_account_value: float = 0.0

        self.is_running = False
        self.initialized = False

        # Statistics
        self.trades_copied = 0
        self.total_latency_ms = 0.0
        self.min_latency_ms = float('inf')
        self.max_latency_ms = 0.0

        logger.info(f"⚡ UltraCopyTrader initialized")
        logger.info(f"   Target: {target_wallet}")
        logger.info(f"   Copy Ratio: {copy_ratio * 100}%")

    async def start(self):
        """Start copy trading"""
        self.is_running = True
        logger.info("🚀 Starting ultra-low latency copy trading...")

        # Step 1: Sync initial state (ONE-TIME REST calls)
        await self._initial_sync()

        # Step 2: Subscribe to WebSocket events
        await self.websocket.subscribe_user_fills(
            self.target_wallet,
            self._on_target_fill  # This is the critical path
        )

        logger.info("✅ Copy trading active - listening for events")

    async def _initial_sync(self):
        """
        Initial synchronization (REST calls)
        Only runs once at startup
        """
        logger.info("📊 Syncing initial state...")

        try:
            # Get target's positions
            target_state = self.info.user_state(self.target_wallet)

            if target_state:
                self.target_account_value = float(
                    target_state.get("marginSummary", {}).get("accountValue", 0)
                )

                if "assetPositions" in target_state:
                    for asset in target_state["assetPositions"]:
                        if "position" in asset:
                            pos = asset["position"]
                            coin = pos["coin"]
                            size = float(pos.get("szi", 0))

                            if size != 0:
                                self.target_positions[coin] = {
                                    "size": size,
                                    "entry_px": float(pos.get("entryPx", 0)),
                                    "margin_used": float(pos.get("marginUsed", 0))
                                }

            logger.info(f"   Target account value: ${self.target_account_value:,.2f}")
            logger.info(f"   Target positions: {len(self.target_positions)}")

            # Get my positions
            my_state = self.info.user_state(self.api_key)  # Uses API key to get own account

            if my_state:
                self.my_account_value = float(
                    my_state.get("marginSummary", {}).get("accountValue", 0)
                )

                if "assetPositions" in my_state:
                    for asset in my_state["assetPositions"]:
                        if "position" in asset:
                            pos = asset["position"]
                            coin = pos["coin"]
                            size = float(pos.get("szi", 0))

                            if size != 0:
                                self.my_positions[coin] = {
                                    "size": size,
                                    "entry_px": float(pos.get("entryPx", 0))
                                }

            logger.info(f"   My account value: ${self.my_account_value:,.2f}")
            logger.info(f"   My positions: {len(self.my_positions)}")

            self.initialized = True
            logger.info("✅ Initial sync complete")

        except Exception as e:
            logger.error(f"❌ Initial sync failed: {e}")
            raise

    async def _on_target_fill(self, event):
        """
        CRITICAL PATH: Event handler for target trader fills

        This function is called on EVERY fill from the target trader.
        Optimized for minimal latency.

        Target: < 100ms from event receipt to order submission
        """
        start_time = time.perf_counter()

        try:
            if not event or "data" not in event:
                return

            data = event["data"]

            # Extract fills
            fills = data.get("fills", [])

            if not fills:
                return

            # Process each fill
            for fill in fills:
                await self._process_fill_fast(fill, start_time)

        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"❌ Event processing error ({latency_ms:.1f}ms): {e}")

    async def _process_fill_fast(self, fill: Dict, event_start_time: float):
        """
        Process a single fill with minimal latency

        Steps:
        1. Extract fill data (< 5ms)
        2. Calculate my order size (< 10ms)
        3. Submit order (< 50ms)
        4. Update state (< 10ms)

        Total: < 75ms
        """
        try:
            # Extract data (minimal processing)
            coin = fill.get("coin")
            side = fill.get("side")  # "B" or "A" (Buy/Ask)
            size = abs(float(fill.get("sz", 0)))
            price = float(fill.get("px", 0))
            closed_pnl = fill.get("closedPnl")

            if not coin or size == 0:
                return

            is_buy = (side == "B")

            # Determine if this is opening or closing
            is_closing = (closed_pnl is not None)

            if is_closing:
                # Target closed a position
                await self._copy_close(coin, size, event_start_time)
            else:
                # Target opened/added to position
                await self._copy_open(coin, is_buy, size, price, event_start_time)

        except Exception as e:
            logger.error(f"❌ Fill processing error: {e}")

    async def _copy_open(
        self,
        coin: str,
        is_buy: bool,
        target_size: float,
        price: float,
        event_start_time: float
    ):
        """
        Copy open/add position

        Fast path: Calculate size and submit immediately
        """
        try:
            # Calculate my order size based on account ratio
            if self.target_account_value == 0:
                logger.warning(f"⚠️ Target account value is 0, skipping {coin}")
                return

            # My size = target size * (my account / target account) * copy ratio
            account_ratio = self.my_account_value / self.target_account_value
            my_size = target_size * account_ratio * self.copy_ratio

            # Minimum size check
            if my_size < 0.001:  # Hyperliquid minimum
                logger.debug(f"⚠️ Size too small: {my_size}")
                return

            # Submit order (async, non-blocking)
            result = await self.executor.execute_market_order(
                coin=coin,
                is_buy=is_buy,
                size=my_size,
                slippage=0.02  # 2% slippage tolerance
            )

            # Calculate total latency
            total_latency_ms = (time.perf_counter() - event_start_time) * 1000

            if result:
                # Update statistics
                self.trades_copied += 1
                self.total_latency_ms += total_latency_ms
                self.min_latency_ms = min(self.min_latency_ms, total_latency_ms)
                self.max_latency_ms = max(self.max_latency_ms, total_latency_ms)

                # Update my positions (in memory)
                if coin in self.my_positions:
                    # Add to existing
                    self.my_positions[coin]["size"] += my_size if is_buy else -my_size
                else:
                    # New position
                    self.my_positions[coin] = {
                        "size": my_size if is_buy else -my_size,
                        "entry_px": price
                    }

                avg_latency = self.total_latency_ms / self.trades_copied

                logger.info(
                    f"🚀 COPIED: {coin} {'BUY' if is_buy else 'SELL'} {my_size:.4f} "
                    f"| Latency: {total_latency_ms:.1f}ms (avg: {avg_latency:.1f}ms)"
                )

        except Exception as e:
            latency_ms = (time.perf_counter() - event_start_time) * 1000
            logger.error(f"❌ Copy open error ({latency_ms:.1f}ms): {e}")

    async def _copy_close(
        self,
        coin: str,
        target_size: float,
        event_start_time: float
    ):
        """
        Copy close position

        Fast path: Close immediately
        """
        try:
            # Check if I have this position
            if coin not in self.my_positions:
                logger.debug(f"⚠️ No position to close: {coin}")
                return

            my_position = self.my_positions[coin]
            my_size = my_position["size"]

            # Calculate how much to close
            if self.target_account_value == 0:
                return

            account_ratio = self.my_account_value / self.target_account_value
            close_size = target_size * account_ratio * self.copy_ratio

            # Don't close more than I have
            close_size = min(close_size, abs(my_size))

            if close_size < 0.001:
                return

            # Submit close order
            result = await self.executor.close_position(coin, my_size)

            total_latency_ms = (time.perf_counter() - event_start_time) * 1000

            if result:
                # Update statistics
                self.trades_copied += 1
                self.total_latency_ms += total_latency_ms
                self.min_latency_ms = min(self.min_latency_ms, total_latency_ms)
                self.max_latency_ms = max(self.max_latency_ms, total_latency_ms)

                # Update positions
                del self.my_positions[coin]

                avg_latency = self.total_latency_ms / self.trades_copied

                logger.info(
                    f"🛑 CLOSED: {coin} {close_size:.4f} "
                    f"| Latency: {total_latency_ms:.1f}ms (avg: {avg_latency:.1f}ms)"
                )

        except Exception as e:
            latency_ms = (time.perf_counter() - event_start_time) * 1000
            logger.error(f"❌ Copy close error ({latency_ms:.1f}ms): {e}")

    async def stop(self):
        """Stop copy trading"""
        self.is_running = False
        self.websocket.unsubscribe_all()

        if self.trades_copied > 0:
            avg_latency = self.total_latency_ms / self.trades_copied
            logger.info(f"📊 Copy Trading Stats:")
            logger.info(f"   Trades copied: {self.trades_copied}")
            logger.info(f"   Avg latency: {avg_latency:.1f}ms")
            logger.info(f"   Min latency: {self.min_latency_ms:.1f}ms")
            logger.info(f"   Max latency: {self.max_latency_ms:.1f}ms")

        logger.info("🛑 Copy trading stopped")

    def get_stats(self) -> Dict:
        """Get current statistics"""
        avg_latency = (
            self.total_latency_ms / self.trades_copied
            if self.trades_copied > 0
            else 0
        )

        return {
            "is_running": self.is_running,
            "trades_copied": self.trades_copied,
            "avg_latency_ms": avg_latency,
            "min_latency_ms": self.min_latency_ms if self.trades_copied > 0 else 0,
            "max_latency_ms": self.max_latency_ms,
            "target_positions": len(self.target_positions),
            "my_positions": len(self.my_positions),
            "my_account_value": self.my_account_value,
            "target_account_value": self.target_account_value
        }
