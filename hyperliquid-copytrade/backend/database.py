"""
Database schema and models for Hyperliquid indexer
Stores all wallet data locally for fast queries without hitting Hyperliquid API
"""
import sqlite3
from datetime import datetime
from typing import Optional, List, Dict
import logging
import json

logger = logging.getLogger(__name__)


class Database:
    """SQLite database for storing Hyperliquid data"""

    def __init__(self, db_path: str = "hyperliquid_data.db"):
        self.db_path = db_path
        self.conn = None
        self.init_database()

    def init_database(self):
        """Initialize database with schema"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Return rows as dicts

        cursor = self.conn.cursor()

        # Wallets being tracked
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wallets (
                address TEXT PRIMARY KEY,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                initial_balance REAL DEFAULT 10000.0,
                is_active BOOLEAN DEFAULT 1,
                last_sync TIMESTAMP
            )
        """)

        # Fills (trades executed)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS fills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wallet_address TEXT NOT NULL,
                coin TEXT NOT NULL,
                side TEXT NOT NULL,
                price REAL NOT NULL,
                size REAL NOT NULL,
                time TIMESTAMP NOT NULL,
                closed_pnl REAL,
                fee REAL,
                fee_token TEXT,
                is_maker BOOLEAN,
                order_id TEXT,
                start_position REAL,
                direction TEXT,
                hash TEXT UNIQUE,
                FOREIGN KEY (wallet_address) REFERENCES wallets(address)
            )
        """)

        # Positions (current open positions)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS positions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wallet_address TEXT NOT NULL,
                coin TEXT NOT NULL,
                side TEXT NOT NULL,
                size REAL NOT NULL,
                entry_px REAL NOT NULL,
                leverage REAL NOT NULL,
                margin_used REAL NOT NULL,
                unrealized_pnl REAL,
                liquidation_px REAL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(wallet_address, coin),
                FOREIGN KEY (wallet_address) REFERENCES wallets(address)
            )
        """)

        # Orders (open orders)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wallet_address TEXT NOT NULL,
                order_id TEXT UNIQUE NOT NULL,
                coin TEXT NOT NULL,
                side TEXT NOT NULL,
                limit_px REAL NOT NULL,
                size REAL NOT NULL,
                filled_size REAL DEFAULT 0,
                order_type TEXT,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (wallet_address) REFERENCES wallets(address)
            )
        """)

        # Funding payments
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS funding_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wallet_address TEXT NOT NULL,
                coin TEXT NOT NULL,
                funding_rate REAL NOT NULL,
                payment REAL NOT NULL,
                time TIMESTAMP NOT NULL,
                FOREIGN KEY (wallet_address) REFERENCES wallets(address)
            )
        """)

        # Wallet metrics (calculated periodically)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS wallet_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                wallet_address TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                equity REAL NOT NULL,
                total_volume REAL NOT NULL,
                total_fees REAL NOT NULL,
                realized_pnl REAL NOT NULL,
                unrealized_pnl REAL NOT NULL,
                total_pnl REAL NOT NULL,
                num_trades INTEGER NOT NULL,
                num_open_positions INTEGER NOT NULL,
                fee_factor_mixed REAL,
                fee_factor_taker REAL,
                roi REAL,
                FOREIGN KEY (wallet_address) REFERENCES wallets(address)
            )
        """)

        # Create indexes for fast queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fills_wallet ON fills(wallet_address)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_fills_time ON fills(time)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_positions_wallet ON positions(wallet_address)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_wallet ON orders(wallet_address)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_funding_wallet ON funding_payments(wallet_address)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_wallet ON wallet_metrics(wallet_address)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_metrics_time ON wallet_metrics(timestamp)")

        self.conn.commit()
        logger.info(f"Database initialized: {self.db_path}")

    # =====================
    # WALLET OPERATIONS
    # =====================

    def add_wallet(self, address: str, initial_balance: float = 10000.0):
        """Add a wallet to track"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO wallets (address, initial_balance, is_active)
            VALUES (?, ?, 1)
        """, (address.lower(), initial_balance))
        self.conn.commit()
        logger.info(f"Added wallet: {address}")

    def remove_wallet(self, address: str):
        """Mark wallet as inactive"""
        cursor = self.conn.cursor()
        cursor.execute("UPDATE wallets SET is_active = 0 WHERE address = ?", (address.lower(),))
        self.conn.commit()
        logger.info(f"Removed wallet: {address}")

    def get_active_wallets(self) -> List[str]:
        """Get all active wallets"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT address FROM wallets WHERE is_active = 1")
        return [row["address"] for row in cursor.fetchall()]

    def update_wallet_sync_time(self, address: str):
        """Update last sync timestamp"""
        cursor = self.conn.cursor()
        cursor.execute("UPDATE wallets SET last_sync = CURRENT_TIMESTAMP WHERE address = ?",
                      (address.lower(),))
        self.conn.commit()

    # =====================
    # FILL OPERATIONS
    # =====================

    def add_fill(self, wallet_address: str, fill_data: dict):
        """Add a fill (trade execution)"""
        cursor = self.conn.cursor()

        # Extract data
        coin = fill_data.get("coin")
        side = fill_data.get("side")
        px = float(fill_data.get("px", 0))
        sz = float(fill_data.get("sz", 0))
        time = fill_data.get("time")
        closed_pnl = float(fill_data.get("closedPnl", 0)) if "closedPnl" in fill_data else None
        fee = float(fill_data.get("fee", 0)) if "fee" in fill_data else None
        fee_token = fill_data.get("feeToken")
        is_maker = fill_data.get("crossed", True) == False  # crossed=False means maker
        order_id = fill_data.get("oid")
        start_position = float(fill_data.get("startPosition", 0)) if "startPosition" in fill_data else None
        direction = fill_data.get("dir")
        hash_val = fill_data.get("hash") or fill_data.get("tid")

        try:
            cursor.execute("""
                INSERT OR IGNORE INTO fills
                (wallet_address, coin, side, price, size, time, closed_pnl, fee,
                 fee_token, is_maker, order_id, start_position, direction, hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (wallet_address.lower(), coin, side, px, sz, time, closed_pnl, fee,
                  fee_token, is_maker, order_id, start_position, direction, hash_val))
            self.conn.commit()

            if cursor.rowcount > 0:
                logger.info(f"Added fill: {wallet_address} - {coin} {side} {sz} @ ${px}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error adding fill: {e}")
            return False

    def get_fills(self, wallet_address: str, limit: int = 100) -> List[Dict]:
        """Get fills for a wallet"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM fills
            WHERE wallet_address = ?
            ORDER BY time DESC
            LIMIT ?
        """, (wallet_address.lower(), limit))
        return [dict(row) for row in cursor.fetchall()]

    # =====================
    # POSITION OPERATIONS
    # =====================

    def upsert_position(self, wallet_address: str, position_data: dict):
        """Insert or update a position"""
        cursor = self.conn.cursor()

        coin = position_data.get("coin")
        size = float(position_data.get("szi", 0))
        entry_px = float(position_data.get("entryPx", 0))
        leverage = float(position_data.get("leverage", {}).get("value", 1))
        margin_used = float(position_data.get("marginUsed", 0))
        unrealized_pnl = float(position_data.get("unrealizedPnl", 0))
        liquidation_px = float(position_data.get("liquidationPx", 0))

        side = "long" if size > 0 else "short"

        cursor.execute("""
            INSERT INTO positions
            (wallet_address, coin, side, size, entry_px, leverage, margin_used,
             unrealized_pnl, liquidation_px, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(wallet_address, coin) DO UPDATE SET
                side = ?,
                size = ?,
                entry_px = ?,
                leverage = ?,
                margin_used = ?,
                unrealized_pnl = ?,
                liquidation_px = ?,
                updated_at = CURRENT_TIMESTAMP
        """, (wallet_address.lower(), coin, side, size, entry_px, leverage, margin_used,
              unrealized_pnl, liquidation_px, side, size, entry_px, leverage, margin_used,
              unrealized_pnl, liquidation_px))
        self.conn.commit()

    def delete_position(self, wallet_address: str, coin: str):
        """Delete a position (when closed)"""
        cursor = self.conn.cursor()
        cursor.execute("""
            DELETE FROM positions
            WHERE wallet_address = ? AND coin = ?
        """, (wallet_address.lower(), coin))
        self.conn.commit()
        logger.info(f"Deleted position: {wallet_address} - {coin}")

    def get_positions(self, wallet_address: str) -> List[Dict]:
        """Get open positions for a wallet"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM positions
            WHERE wallet_address = ?
            ORDER BY updated_at DESC
        """, (wallet_address.lower(),))
        return [dict(row) for row in cursor.fetchall()]

    # =====================
    # METRICS OPERATIONS
    # =====================

    def save_metrics(self, wallet_address: str, metrics: dict):
        """Save calculated metrics snapshot"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO wallet_metrics
            (wallet_address, equity, total_volume, total_fees, realized_pnl,
             unrealized_pnl, total_pnl, num_trades, num_open_positions,
             fee_factor_mixed, fee_factor_taker, roi)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (wallet_address.lower(), metrics.get("equity", 0), metrics.get("total_volume", 0),
              metrics.get("total_fees", 0), metrics.get("realized_pnl", 0),
              metrics.get("unrealized_pnl", 0), metrics.get("total_pnl", 0),
              metrics.get("num_trades", 0), metrics.get("num_open_positions", 0),
              metrics.get("fee_factor_mixed"), metrics.get("fee_factor_taker"),
              metrics.get("roi")))
        self.conn.commit()

    def get_latest_metrics(self, wallet_address: str) -> Optional[Dict]:
        """Get latest metrics for a wallet"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM wallet_metrics
            WHERE wallet_address = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (wallet_address.lower(),))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_metrics_history(self, wallet_address: str, limit: int = 100) -> List[Dict]:
        """Get metrics history"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM wallet_metrics
            WHERE wallet_address = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (wallet_address.lower(), limit))
        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
