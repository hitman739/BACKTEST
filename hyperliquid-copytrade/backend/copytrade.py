"""
Copy Trading Logic
Monitors target wallet and copies trades based on margin % used
"""
import asyncio
import logging
from typing import Callable, Optional
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants
import eth_account

logger = logging.getLogger(__name__)


class CopyTradeManager:
    """Manages copy trading from a target wallet"""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        target_wallet: str,
        testnet: bool = True,
        callback: Optional[Callable] = None
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.target_wallet = target_wallet
        self.testnet = testnet
        self.callback = callback

        # State
        self.is_running = False
        self.trades_copied = 0
        self.last_positions = {}

        # Initialize Hyperliquid clients
        base_url = constants.TESTNET_API_URL if testnet else constants.MAINNET_API_URL
        self.info = Info(base_url, skip_ws=True)

        # Initialize exchange for executing trades
        account = eth_account.Account.from_key(api_secret)
        self.exchange = Exchange(account, base_url)

        # Get my account address
        self.my_wallet = account.address

        logger.info(f"Initialized CopyTradeManager")
        logger.info(f"My wallet: {self.my_wallet}")
        logger.info(f"Target wallet: {target_wallet}")
        logger.info(f"Testnet: {testnet}")

    async def start(self):
        """Start monitoring and copying trades"""
        self.is_running = True
        logger.info("Starting copy trading...")

        await self._send_update({
            "type": "info",
            "message": "Copy trading started. Monitoring target wallet..."
        })

        try:
            while self.is_running:
                await self._check_and_copy()
                await asyncio.sleep(5)  # Check every 5 seconds

        except Exception as e:
            logger.error(f"Error in copy trading loop: {e}")
            await self._send_update({
                "type": "error",
                "message": f"Error: {str(e)}"
            })
            self.is_running = False

    async def stop(self):
        """Stop copy trading"""
        self.is_running = False
        logger.info("Stopping copy trading...")

    async def _check_and_copy(self):
        """Check target wallet positions and copy any changes"""
        try:
            # Get target wallet's current positions
            user_state = self.info.user_state(self.target_wallet)

            if not user_state:
                logger.warning("No user state returned from API")
                return

            current_positions = {}

            # Parse positions
            if "assetPositions" in user_state:
                for position in user_state["assetPositions"]:
                    if "position" in position:
                        pos = position["position"]
                        coin = pos["coin"]
                        size = float(pos["szi"])

                        if size != 0:  # Only track open positions
                            current_positions[coin] = {
                                "size": size,
                                "entry_px": float(pos.get("entryPx", 0)),
                                "leverage": float(pos.get("leverage", {}).get("value", 1)),
                                "margin_used": float(pos.get("marginUsed", 0)),
                            }

            # Detect changes
            await self._process_position_changes(current_positions, user_state)

            # Update last positions
            self.last_positions = current_positions

        except Exception as e:
            logger.error(f"Error checking positions: {e}")

    async def _process_position_changes(self, current_positions: dict, user_state: dict):
        """Process any position changes and copy them"""

        # Get my account value
        my_state = self.info.user_state(self.my_wallet)
        my_account_value = float(my_state.get("marginSummary", {}).get("accountValue", 0))

        if my_account_value == 0:
            logger.warning("My account value is 0, cannot copy trades")
            return

        # Get target account value
        target_account_value = float(user_state.get("marginSummary", {}).get("accountValue", 0))

        if target_account_value == 0:
            logger.warning("Target account value is 0, cannot calculate margin %")
            return

        # Check for new positions
        for coin, pos_data in current_positions.items():
            if coin not in self.last_positions:
                # New position opened
                await self._copy_position(
                    coin,
                    pos_data,
                    my_account_value,
                    target_account_value,
                    is_new=True
                )

        # Check for closed positions
        for coin in self.last_positions:
            if coin not in current_positions:
                # Position closed
                await self._close_position(coin)

        # Check for position size changes (could be adds/reduces)
        for coin, pos_data in current_positions.items():
            if coin in self.last_positions:
                old_size = self.last_positions[coin]["size"]
                new_size = pos_data["size"]

                if abs(new_size - old_size) > 0.0001:  # Size changed
                    await self._copy_position(
                        coin,
                        pos_data,
                        my_account_value,
                        target_account_value,
                        is_new=False
                    )

    async def _copy_position(
        self,
        coin: str,
        pos_data: dict,
        my_account_value: float,
        target_account_value: float,
        is_new: bool
    ):
        """Copy a position based on margin % used"""

        try:
            # Calculate margin % used by target
            margin_used = pos_data["margin_used"]
            margin_pct = (margin_used / target_account_value) * 100

            # Calculate my position size
            my_margin = (margin_pct / 100) * my_account_value
            leverage = pos_data["leverage"]
            entry_px = pos_data["entry_px"]

            if entry_px == 0:
                logger.warning(f"Entry price is 0 for {coin}, cannot copy")
                return

            # Calculate size: (margin * leverage) / price
            my_size = (my_margin * leverage) / entry_px

            # Determine side (long or short)
            is_buy = pos_data["size"] > 0

            logger.info(f"Copying {coin}: margin_pct={margin_pct:.2f}%, my_size={my_size:.4f}, is_buy={is_buy}")

            # Execute trade
            order_result = self.exchange.market_open(
                coin=coin,
                is_buy=is_buy,
                sz=abs(my_size),
                px=None,  # Market order
            )

            action = "Opened" if is_new else "Adjusted"
            self.trades_copied += 1

            await self._send_update({
                "type": "trade",
                "action": action.lower(),
                "coin": coin,
                "size": my_size,
                "margin_pct": margin_pct,
                "is_buy": is_buy,
                "order_result": str(order_result)
            })

            logger.info(f"{action} position: {coin}, size={my_size:.4f}, result={order_result}")

        except Exception as e:
            logger.error(f"Error copying position {coin}: {e}")
            await self._send_update({
                "type": "error",
                "message": f"Error copying {coin}: {str(e)}"
            })

    async def _close_position(self, coin: str):
        """Close a position"""
        try:
            # Get my current position
            my_state = self.info.user_state(self.my_wallet)

            my_position = None
            if "assetPositions" in my_state:
                for position in my_state["assetPositions"]:
                    if "position" in position:
                        pos = position["position"]
                        if pos["coin"] == coin:
                            my_position = pos
                            break

            if not my_position:
                logger.info(f"No position to close for {coin}")
                return

            size = float(my_position["szi"])

            if abs(size) < 0.0001:
                logger.info(f"Position size too small for {coin}, skipping close")
                return

            # Close position (reverse side)
            is_buy = size < 0  # If we're short, we buy to close

            order_result = self.exchange.market_close(
                coin=coin,
                sz=abs(size),
                px=None,
            )

            self.trades_copied += 1

            await self._send_update({
                "type": "trade",
                "action": "closed",
                "coin": coin,
                "size": size,
                "order_result": str(order_result)
            })

            logger.info(f"Closed position: {coin}, size={size}, result={order_result}")

        except Exception as e:
            logger.error(f"Error closing position {coin}: {e}")
            await self._send_update({
                "type": "error",
                "message": f"Error closing {coin}: {str(e)}"
            })

    async def _send_update(self, update: dict):
        """Send update via callback if available"""
        if self.callback:
            try:
                await self.callback(update)
            except Exception as e:
                logger.error(f"Error sending update: {e}")
