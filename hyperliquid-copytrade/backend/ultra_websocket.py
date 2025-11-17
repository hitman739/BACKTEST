"""
Ultra-Low Latency WebSocket Manager for Hyperliquid
Handles real-time events with minimal overhead
"""
import asyncio
import logging
from typing import Callable, Dict, Optional
from hyperliquid.info import Info
from hyperliquid.utils import constants

logger = logging.getLogger(__name__)


class UltraLowLatencyWebSocket:
    """
    WebSocket manager optimized for minimal latency

    Key optimizations:
    - Event processing happens immediately (no queuing)
    - Callbacks are async (non-blocking)
    - Minimal logging in critical path
    - Direct event → action pipeline
    """

    def __init__(self, testnet: bool = False):
        self.testnet = testnet
        base_url = constants.TESTNET_API_URL if testnet else constants.MAINNET_API_URL
        self.info = Info(base_url, skip_ws=False)  # Enable WebSocket

        self.subscriptions: Dict[str, Callable] = {}
        self.is_connected = False

        logger.info(f"🔌 WebSocket Manager initialized (testnet={testnet})")

    async def subscribe_user_events(self, wallet: str, callback: Callable):
        """
        Subscribe to user events (fills, orders, positions)

        Args:
            wallet: Target wallet address
            callback: Async function to call on events (callback(event))
        """
        subscription = {
            "type": "userEvents",
            "user": wallet.lower()
        }

        # Subscribe with optimized callback
        self.info.subscribe(subscription, self._create_fast_callback(callback))

        self.subscriptions[wallet.lower()] = callback
        self.is_connected = True

        logger.info(f"✅ Subscribed to userEvents for {wallet}")

    def _create_fast_callback(self, user_callback: Callable):
        """
        Create optimized callback wrapper
        Minimizes overhead between event and user callback
        """
        def fast_callback(event):
            # Immediately schedule the async callback
            # Don't wait, don't block, just fire and continue
            if asyncio.iscoroutinefunction(user_callback):
                asyncio.create_task(user_callback(event))
            else:
                user_callback(event)

        return fast_callback

    async def subscribe_user_fills(self, wallet: str, callback: Callable):
        """Subscribe to user fills only (faster, more specific)"""
        subscription = {
            "type": "userFills",
            "user": wallet.lower()
        }

        self.info.subscribe(subscription, self._create_fast_callback(callback))
        logger.info(f"✅ Subscribed to userFills for {wallet}")

    def unsubscribe_all(self):
        """Unsubscribe from all events"""
        self.subscriptions.clear()
        self.is_connected = False
        logger.info("🔌 Unsubscribed from all events")
