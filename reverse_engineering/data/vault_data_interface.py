"""
Vault Data Interface
Loads and standardizes Hyperliquid vault trades
"""

import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class VaultDataInterface:
    """Interface to fetch and standardize Hyperliquid vault data"""

    def __init__(self, vault_address: str, output_dir: str = "reports/reverse_engineering"):
        self.vault_address = vault_address
        self.output_dir = Path(output_dir) / vault_address[:10]
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.api_url = "https://api.hyperliquid.xyz/info"

    def fetch_trades(self, limit: int = 5000) -> List[Dict]:
        """Fetch raw trades from Hyperliquid API"""
        print(f"📥 Fetching trades from vault {self.vault_address[:10]}...")

        payload = {"type": "userFills", "user": self.vault_address}

        try:
            response = requests.post(self.api_url, json=payload, timeout=30)
            response.raise_for_status()
            trades = response.json()

            if isinstance(trades, list):
                trades = trades[:limit]
                print(f"✅ Fetched {len(trades)} trades")
                return trades
            else:
                print(f"❌ Unexpected response format")
                return []
        except Exception as e:
            print(f"❌ Error fetching trades: {e}")
            return []

    def standardize_trades(self, raw_trades: List[Dict]) -> pd.DataFrame:
        """Convert raw trades to standardized DataFrame"""
        print("🔄 Standardizing trades...")

        if not raw_trades:
            return pd.DataFrame()

        df = pd.DataFrame(raw_trades)

        # Standardize columns
        df['timestamp'] = pd.to_datetime(df['time'].astype(int), unit='ms')
        df['symbol'] = df['coin']
        df['side'] = df['side'].map({'B': 'long', 'A': 'short'})
        df['price'] = df['px'].astype(float)
        df['size'] = df['sz'].astype(float)
        df['closed_pnl'] = df.get('closedPnl', 0).astype(float)
        df['fee'] = df.get('fee', 0).astype(float)
        df['notional'] = df['price'] * df['size']

        # Sort by time
        df = df.sort_values('timestamp').reset_index(drop=True)

        print(f"✅ Standardized {len(df)} trades")
        print(f"   Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
        print(f"   Symbols: {df['symbol'].unique().tolist()}")

        return df

    def save_data(self, df: pd.DataFrame, filename: str = "vault_data.parquet"):
        """Save standardized data"""
        filepath = self.output_dir / filename
        df.to_parquet(filepath, index=False)
        print(f"💾 Saved to: {filepath}")
        return filepath

    def load_data(self, filename: str = "vault_data.parquet") -> pd.DataFrame:
        """Load previously saved data"""
        filepath = self.output_dir / filename
        if filepath.exists():
            df = pd.read_parquet(filepath)
            print(f"📂 Loaded {len(df)} trades from {filepath}")
            return df
        else:
            print(f"❌ File not found: {filepath}")
            return pd.DataFrame()

    def run(self, force_refresh: bool = False) -> pd.DataFrame:
        """Main method: fetch, standardize, and save"""

        # Try to load cached data first
        if not force_refresh:
            df = self.load_data()
            if not df.empty:
                return df

        # Fetch and process
        raw_trades = self.fetch_trades()
        df = self.standardize_trades(raw_trades)

        if not df.empty:
            self.save_data(df)

        return df
