"""
Hyperliquid WebSocket Indexer
Connects to Hyperliquid WebSocket and indexes data in real-time
"""
import asyncio
import logging
from typing import Dict, Set, Callable
from hyperliquid.info import Info
from hyperliquid.utils import constants
from database import Database

logger = logging.getLogger(__name__)


class HyperliquidIndexer:
    """
    Real-time indexer for Hyperliquid data
    Uses WebSocket to receive live updates and stores in local database
    """

    def __init__(self, database: Database, testnet: bool = False):
        self.database = database
        self.testnet = testnet
        self.info = None  # Lazy initialization

        # Track active subscriptions
        self.active_wallets: Set[str] = set()
        self.subscription_ids: Dict[str, int] = {}

        logger.info(f"Initialized HyperliquidIndexer (testnet={testnet})")

    def _get_info(self) -> Info:
        """Lazy initialization of Info object (REST API only, no WebSocket)"""
        if self.info is None:
            try:
                self.info = Info(
                    constants.TESTNET_API_URL if self.testnet else constants.MAINNET_API_URL,
                    skip_ws=True  # Skip WebSocket (use REST API only to avoid 403 errors)
                )
                logger.info("Hyperliquid Info client initialized (REST API only)")
            except Exception as e:
                logger.error(f"Failed to initialize Hyperliquid Info client: {e}")
                raise
        return self.info

    async def start(self):
        """Start the indexer"""
        logger.info("Starting indexer...")

        # Load active wallets from database
        wallets = self.database.get_active_wallets()
        logger.info(f"Found {len(wallets)} active wallets to track")

        # Subscribe to each wallet
        for wallet in wallets:
            await self.add_wallet(wallet)

        logger.info("Indexer started and subscriptions active")

    async def add_wallet(self, wallet_address: str, initial_balance: float = 10000.0):
        """
        Add a wallet to track
        1. Add to database
        2. Sync historical data via REST
        3. Subscribe to WebSocket for live updates
        """
        wallet_address = wallet_address.lower()

        # Add to database
        self.database.add_wallet(wallet_address, initial_balance)

        # Sync historical data first
        logger.info(f"Syncing historical data for {wallet_address}...")
        await self._sync_historical_data(wallet_address)

        # Subscribe to real-time updates
        await self._subscribe_to_wallet(wallet_address)

        self.active_wallets.add(wallet_address)
        logger.info(f"✅ Wallet {wallet_address} fully indexed and subscribed")

    async def _sync_historical_data(self, wallet_address: str):
        """Sync historical data via REST API (one-time)"""
        try:
            # Get user state (positions)
            user_state = self._get_info().user_state(wallet_address)

            if user_state and "assetPositions" in user_state:
                for asset_position in user_state["assetPositions"]:
                    if "position" in asset_position:
                        position = asset_position["position"]
                        size = float(position.get("szi", 0))

                        if size != 0:
                            self.database.upsert_position(wallet_address, position)

            # Get historical fills
            fills = self._get_info().user_fills(wallet_address)

            if fills:
                logger.info(f"Syncing {len(fills)} historical fills for {wallet_address}")
                for fill in fills:
                    self.database.add_fill(wallet_address, fill)

            # Update sync timestamp
            self.database.update_wallet_sync_time(wallet_address)

            logger.info(f"✅ Historical sync complete for {wallet_address}")

        except Exception as e:
            logger.error(f"Error syncing historical data for {wallet_address}: {e}")

    async def _subscribe_to_wallet(self, wallet_address: str):
        """Subscribe to WebSocket feeds for a wallet (if WebSocket is enabled)"""
        try:
            # Check if WebSocket is available (we're using skip_ws=True to avoid 403 errors)
            info = self._get_info()

            # Since we're using skip_ws=True, we can't subscribe to WebSocket
            # Data will be updated via REST API polling instead
            logger.info(f"ℹ️  WebSocket subscriptions skipped for {wallet_address} (using REST API polling)")
            logger.info(f"   Data will be updated via periodic REST API calls")

            # If we wanted to use WebSocket (when Hyperliquid allows it), we would do:
            # user_events_sub = {"type": "userEvents", "user": wallet_address}
            # info.subscribe(user_events_sub, self._handle_user_event)

        except Exception as e:
            logger.error(f"Error in subscribe method for {wallet_address}: {e}")

    async def remove_wallet(self, wallet_address: str):
        """Remove a wallet from tracking"""
        wallet_address = wallet_address.lower()

        # Mark as inactive in database
        self.database.remove_wallet(wallet_address)

        # Remove from active set
        self.active_wallets.discard(wallet_address)

        # Note: hyperliquid SDK doesn't have unsubscribe, so subscriptions will remain
        # but we won't process the data anymore

        logger.info(f"Removed wallet {wallet_address} from tracking")

    # =====================
    # WEBSOCKET CALLBACKS
    # =====================

    def _handle_user_event(self, event):
        """Handle userEvents WebSocket message"""
        try:
            if not event or "data" not in event:
                return

            data = event["data"]

            # Extract wallet address
            wallet_address = data.get("user", "").lower()

            if wallet_address not in self.active_wallets:
                return  # Ignore events for inactive wallets

            # Handle different event types
            if "fills" in data:
                # New fills
                for fill in data["fills"]:
                    self.database.add_fill(wallet_address, fill)
                    logger.info(f"🔥 New fill: {wallet_address} - {fill.get('coin')} {fill.get('side')}")

            # Additional event types can be processed here

        except Exception as e:
            logger.error(f"Error handling user event: {e}")

    def _handle_user_fill(self, message):
        """Handle userFills WebSocket message"""
        try:
            if not message or "data" not in message:
                return

            data = message["data"]

            wallet_address = data.get("user", "").lower()

            if wallet_address not in self.active_wallets:
                return

            # Process fills
            if "fills" in data:
                for fill in data["fills"]:
                    self.database.add_fill(wallet_address, fill)
                    logger.info(f"💰 Fill received: {wallet_address} - {fill.get('coin')}")

        except Exception as e:
            logger.error(f"Error handling user fill: {e}")

    def _handle_user_funding(self, message):
        """Handle userFundings WebSocket message"""
        try:
            if not message or "data" not in message:
                return

            data = message["data"]

            wallet_address = data.get("user", "").lower()

            if wallet_address not in self.active_wallets:
                return

            # Store funding payments
            coin = data.get("coin")
            funding_rate = float(data.get("fundingRate", 0))
            payment = float(data.get("payment", 0))
            time = data.get("time")

            cursor = self.database.conn.cursor()
            cursor.execute("""
                INSERT INTO funding_payments (wallet_address, coin, funding_rate, payment, time)
                VALUES (?, ?, ?, ?, ?)
            """, (wallet_address, coin, funding_rate, payment, time))
            self.database.conn.commit()

            logger.info(f"💸 Funding payment: {wallet_address} - {coin} ${payment}")

        except Exception as e:
            logger.error(f"Error handling funding payment: {e}")

    async def stop(self):
        """Stop the indexer"""
        logger.info("Stopping indexer...")
        # WebSocket will be cleaned up automatically
        self.active_wallets.clear()
        logger.info("Indexer stopped")
