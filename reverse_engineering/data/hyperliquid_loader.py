"""
Hyperliquid Data Loader
Fetches OHLCV candle data from Hyperliquid API
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


class HyperliquidDataLoader:
    """Loads OHLCV data from Hyperliquid API"""

    def __init__(self, data_dir: str = "./data/hyperliquid"):
        self.api_url = "https://api.hyperliquid.xyz/info"
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def get_data(
        self,
        symbol: str,
        timeframe: str = '5m',
        start_date: str = None,
        end_date: str = None,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data from Hyperliquid

        Args:
            symbol: Trading symbol (e.g., 'HYPE')
            timeframe: Candle timeframe ('1m', '5m', '15m', '1h', '4h', '1d')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            use_cache: Whether to use cached data

        Returns:
            DataFrame with OHLCV data
        """
        # Check cache
        if use_cache:
            cached = self._load_from_cache(symbol, timeframe, start_date, end_date)
            if cached is not None and not cached.empty:
                return cached

        # Fetch from API
        df = self._fetch_candles(symbol, timeframe, start_date, end_date)

        # Save to cache
        if not df.empty:
            self._save_to_cache(df, symbol, timeframe, start_date, end_date)

        return df

    def _fetch_candles(
        self,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """Fetch candles from Hyperliquid API"""

        # Convert timeframe to Hyperliquid format
        interval_map = {
            '1m': '1m',
            '5m': '5m',
            '15m': '15m',
            '1h': '1h',
            '4h': '4h',
            '1d': '1d'
        }

        if timeframe not in interval_map:
            print(f"⚠️  Unsupported timeframe: {timeframe}, defaulting to 5m")
            timeframe = '5m'

        interval = interval_map[timeframe]

        # Convert dates to timestamps (milliseconds)
        if start_date:
            start_ts = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp() * 1000)
        else:
            start_ts = int((datetime.now() - timedelta(days=60)).timestamp() * 1000)

        if end_date:
            end_ts = int(datetime.strptime(end_date, '%Y-%m-%d').timestamp() * 1000)
        else:
            end_ts = int(datetime.now().timestamp() * 1000)

        # Request payload
        payload = {
            "type": "candleSnapshot",
            "req": {
                "coin": symbol,
                "interval": interval,
                "startTime": start_ts,
                "endTime": end_ts
            }
        }

        try:
            response = requests.post(self.api_url, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()

            if not data or not isinstance(data, list):
                print(f"❌ No candle data returned for {symbol}")
                return pd.DataFrame()

            # Parse candles
            candles = []
            for candle in data:
                # Hyperliquid candle format: [timestamp, open, high, low, close, volume]
                if isinstance(candle, dict):
                    # Handle dict format
                    candles.append({
                        'timestamp': pd.to_datetime(candle['t'], unit='ms'),
                        'open': float(candle['o']),
                        'high': float(candle['h']),
                        'low': float(candle['l']),
                        'close': float(candle['c']),
                        'volume': float(candle['v'])
                    })
                elif isinstance(candle, list) and len(candle) >= 6:
                    # Handle array format: [time, open, high, low, close, volume]
                    candles.append({
                        'timestamp': pd.to_datetime(candle[0], unit='ms'),
                        'open': float(candle[1]),
                        'high': float(candle[2]),
                        'low': float(candle[3]),
                        'close': float(candle[4]),
                        'volume': float(candle[5])
                    })

            if not candles:
                return pd.DataFrame()

            df = pd.DataFrame(candles)
            df = df.sort_values('timestamp').reset_index(drop=True)

            print(f"✅ Fetched {len(df)} candles for {symbol} from Hyperliquid")
            return df

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 403:
                print(f"❌ Hyperliquid API blocked (403). Try from different IP or use VPN")
            else:
                print(f"❌ HTTP Error fetching {symbol}: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"❌ Error fetching {symbol} from Hyperliquid: {e}")
            return pd.DataFrame()

    def _load_from_cache(
        self,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str
    ) -> Optional[pd.DataFrame]:
        """Load data from cache"""
        filename = f"{symbol}_{timeframe}_{start_date}_{end_date}.parquet"
        filepath = self.data_dir / filename

        if filepath.exists():
            try:
                df = pd.read_parquet(filepath)
                print(f"📂 Loaded {len(df)} candles from cache: {filename}")
                return df
            except Exception as e:
                print(f"⚠️  Error loading cache: {e}")
                return None
        return None

    def _save_to_cache(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str
    ):
        """Save data to cache"""
        filename = f"{symbol}_{timeframe}_{start_date}_{end_date}.parquet"
        filepath = self.data_dir / filename

        try:
            df.to_parquet(filepath, index=False)
            print(f"💾 Cached to: {filename}")
        except Exception as e:
            print(f"⚠️  Error saving cache: {e}")
