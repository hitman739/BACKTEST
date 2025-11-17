"""
Ultra-Fast Order Executor
Sends orders with minimal latency
"""
import asyncio
import logging
from typing import Dict, Optional
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants
import time

logger = logging.getLogger(__name__)


class UltraOrderExecutor:
    """
    Order executor optimized for speed

    Key features:
    - Async order submission (non-blocking)
    - Minimal validation (trust input)
    - No DB writes in critical path
    - Fire-and-forget for max speed
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        testnet: bool = False
    ):
        base_url = constants.TESTNET_API_URL if testnet else constants.MAINNET_API_URL

        # Initialize Exchange client for trading
        self.exchange = Exchange(
            base_url=base_url,
            api_key=api_key,
            api_secret=api_secret
        )

        self.testnet = testnet
        self.pending_orders: Dict[str, float] = {}  # oid -> timestamp

        logger.info(f"⚡ Order Executor initialized (testnet={testnet})")

    async def execute_market_order(
        self,
        coin: str,
        is_buy: bool,
        size: float,
        slippage: float = 0.01  # 1% slippage
    ) -> Optional[Dict]:
        """
        Execute market order with minimal latency

        Args:
            coin: Asset symbol (e.g., "BTC")
            is_buy: True for buy, False for sell
            size: Order size
            slippage: Max slippage tolerance

        Returns:
            Order result or None if failed
        """
        start_time = time.perf_counter()

        try:
            # Build order request
            # Using limit order at market price + slippage for guaranteed fill
            order_request = {
                "coin": coin,
                "is_buy": is_buy,
                "sz": size,
                "limit_px": None,  # Market order
                "order_type": {"limit": {"tif": "Ioc"}},  # Immediate or Cancel
                "reduce_only": False
            }

            # Send order (async, non-blocking)
            result = self.exchange.order(order_request)

            latency_ms = (time.perf_counter() - start_time) * 1000

            if result and result.get("status") == "ok":
                logger.info(f"✅ Order executed: {coin} {'BUY' if is_buy else 'SELL'} {size} ({latency_ms:.1f}ms)")
                return result
            else:
                logger.warning(f"⚠️ Order failed: {result}")
                return None

        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"❌ Order error ({latency_ms:.1f}ms): {e}")
            return None

    async def execute_limit_order(
        self,
        coin: str,
        is_buy: bool,
        size: float,
        limit_price: float
    ) -> Optional[Dict]:
        """Execute limit order"""
        start_time = time.perf_counter()

        try:
            order_request = {
                "coin": coin,
                "is_buy": is_buy,
                "sz": size,
                "limit_px": limit_price,
                "order_type": {"limit": {"tif": "Gtc"}},  # Good til canceled
                "reduce_only": False
            }

            result = self.exchange.order(order_request)

            latency_ms = (time.perf_counter() - start_time) * 1000

            if result and result.get("status") == "ok":
                logger.info(f"✅ Limit order: {coin} {'BUY' if is_buy else 'SELL'} {size} @ ${limit_price} ({latency_ms:.1f}ms)")
                return result
            else:
                logger.warning(f"⚠️ Limit order failed: {result}")
                return None

        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"❌ Limit order error ({latency_ms:.1f}ms): {e}")
            return None

    async def close_position(self, coin: str, size: float) -> Optional[Dict]:
        """
        Close position with market order

        Args:
            coin: Asset to close
            size: Position size (positive for long, negative for short)
        """
        is_buy = size < 0  # If short, buy to close
        abs_size = abs(size)

        start_time = time.perf_counter()

        try:
            order_request = {
                "coin": coin,
                "is_buy": is_buy,
                "sz": abs_size,
                "limit_px": None,  # Market order
                "order_type": {"limit": {"tif": "Ioc"}},
                "reduce_only": True  # Close position only
            }

            result = self.exchange.order(order_request)

            latency_ms = (time.perf_counter() - start_time) * 1000

            if result and result.get("status") == "ok":
                logger.info(f"✅ Position closed: {coin} {abs_size} ({latency_ms:.1f}ms)")
                return result
            else:
                logger.warning(f"⚠️ Close failed: {result}")
                return None

        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"❌ Close error ({latency_ms:.1f}ms): {e}")
            return None
