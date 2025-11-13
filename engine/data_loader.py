"""
Data Loader Module - Downloads and caches Binance Futures OHLCV data
"""

import os
import asyncio
import aiohttp
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Tuple
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BinanceDataLoader:
    """
    Handles downloading and caching historical OHLCV data from Binance Futures
    """

    BASE_URL = "https://fapi.binance.com"

    TIMEFRAME_MAP = {
        "1m": "1m",
        "3m": "3m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "1h",
        "2h": "2h",
        "4h": "4h",
        "6h": "6h",
        "8h": "8h",
        "12h": "12h",
        "1d": "1d",
        "3d": "3d",
        "1w": "1w",
    }

    def __init__(self, data_dir: str = "./data/binance"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, symbol: str, timeframe: str) -> Path:
        """Get the cache file path for a symbol/timeframe combination"""
        symbol_dir = self.data_dir / symbol
        symbol_dir.mkdir(exist_ok=True)
        return symbol_dir / f"{timeframe}.parquet"

    async def _fetch_klines(
        self,
        session: aiohttp.ClientSession,
        symbol: str,
        interval: str,
        start_time: int,
        end_time: int,
        limit: int = 1500
    ) -> list:
        """Fetch klines from Binance API"""
        url = f"{self.BASE_URL}/fapi/v1/klines"
        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": start_time,
            "endTime": end_time,
            "limit": limit
        }

        try:
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"API error: {response.status}")
                    return []
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return []

    async def download_data(
        self,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        Download historical data from Binance Futures

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            timeframe: Candle interval (e.g., '5m', '1h')
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format

        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        if timeframe not in self.TIMEFRAME_MAP:
            raise ValueError(f"Invalid timeframe. Must be one of {list(self.TIMEFRAME_MAP.keys())}")

        interval = self.TIMEFRAME_MAP[timeframe]
        start_dt = pd.to_datetime(start_date)
        end_dt = pd.to_datetime(end_date)

        start_ms = int(start_dt.timestamp() * 1000)
        end_ms = int(end_dt.timestamp() * 1000)

        all_klines = []
        current_start = start_ms

        async with aiohttp.ClientSession() as session:
            while current_start < end_ms:
                logger.info(f"Fetching {symbol} {timeframe} from {pd.to_datetime(current_start, unit='ms')}")

                klines = await self._fetch_klines(
                    session, symbol, interval, current_start, end_ms, limit=1500
                )

                if not klines:
                    break

                all_klines.extend(klines)
                current_start = klines[-1][0] + 1

                # Rate limiting
                await asyncio.sleep(0.2)

        if not all_klines:
            raise ValueError(f"No data retrieved for {symbol} {timeframe}")

        # Convert to DataFrame
        df = pd.DataFrame(all_klines, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_volume', 'trades', 'taker_buy_base',
            'taker_buy_quote', 'ignore'
        ])

        # Keep only required columns and convert types
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype(float)

        # Remove duplicates and sort
        df = df.drop_duplicates(subset=['timestamp']).sort_values('timestamp').reset_index(drop=True)

        return df

    def save_to_cache(self, df: pd.DataFrame, symbol: str, timeframe: str):
        """Save DataFrame to cache"""
        cache_path = self._get_cache_path(symbol, timeframe)
        df.to_parquet(cache_path, index=False)
        logger.info(f"Saved {len(df)} candles to {cache_path}")

    def load_from_cache(
        self,
        symbol: str,
        timeframe: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
        """Load DataFrame from cache"""
        cache_path = self._get_cache_path(symbol, timeframe)

        if not cache_path.exists():
            return None

        df = pd.read_parquet(cache_path)

        # Filter by date range if specified
        if start_date:
            df = df[df['timestamp'] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df['timestamp'] <= pd.to_datetime(end_date)]

        if len(df) == 0:
            return None

        return df

    async def get_data(
        self,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Get historical data, using cache if available

        Args:
            symbol: Trading pair
            timeframe: Candle interval
            start_date: Start date 'YYYY-MM-DD'
            end_date: End date 'YYYY-MM-DD'
            use_cache: Whether to use cached data

        Returns:
            DataFrame with OHLCV data
        """
        if use_cache:
            cached_df = self.load_from_cache(symbol, timeframe, start_date, end_date)
            if cached_df is not None and len(cached_df) > 0:
                logger.info(f"Loaded {len(cached_df)} candles from cache")
                return cached_df

        # Download fresh data
        logger.info(f"Downloading {symbol} {timeframe} from {start_date} to {end_date}")
        df = await self.download_data(symbol, timeframe, start_date, end_date)

        # Save to cache
        self.save_to_cache(df, symbol, timeframe)

        return df


def load_data(
    symbol: str,
    timeframe: str,
    start_date: str,
    end_date: str,
    data_dir: str = "./data/binance",
    use_cache: bool = True
) -> pd.DataFrame:
    """
    Convenience function to load data synchronously

    Args:
        symbol: Trading pair (e.g., 'BTCUSDT')
        timeframe: Candle interval (e.g., '5m')
        start_date: Start date 'YYYY-MM-DD'
        end_date: End date 'YYYY-MM-DD'
        data_dir: Directory for caching data
        use_cache: Whether to use cached data

    Returns:
        DataFrame with columns: timestamp, open, high, low, close, volume
    """
    loader = BinanceDataLoader(data_dir)
    return asyncio.run(loader.get_data(symbol, timeframe, start_date, end_date, use_cache))
