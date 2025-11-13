"""
OHLCV Aligner
Aligns vault trades with OHLCV candles to compute indicators at entry/exit
"""

import pandas as pd
import asyncio
from engine.data_loader import BinanceDataLoader
from reverse_engineering.data.hyperliquid_loader import HyperliquidDataLoader
from pathlib import Path


class OHLCVAligner:
    """Aligns trades with OHLCV data and adds technical indicators"""

    def __init__(self, data_dir: str = "./data/binance"):
        self.binance_loader = BinanceDataLoader(data_dir)
        self.hyperliquid_loader = HyperliquidDataLoader("./data/hyperliquid")

    def align_positions(
        self,
        positions_df: pd.DataFrame,
        timeframe: str = '5m',
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Align positions with OHLCV data

        For each position, fetches OHLCV around entry/exit and adds:
        - Indicators at entry time
        - Indicators at exit time
        - Price context
        """
        print(f"🔄 Aligning positions with {timeframe} OHLCV...")

        if positions_df.empty:
            return positions_df

        # Get unique symbols and date range
        symbols = positions_df['symbol'].unique()
        min_date = positions_df['entry_time'].min()
        max_date = positions_df['exit_time'].max()

        # Add buffer
        start_date = (min_date - pd.Timedelta(days=1)).strftime('%Y-%m-%d')
        end_date = (max_date + pd.Timedelta(days=1)).strftime('%Y-%m-%d')

        aligned_positions = []

        for symbol in symbols:
            print(f"  Fetching {symbol} data...")

            # Try Binance first, then fallback to Hyperliquid
            ohlcv = pd.DataFrame()

            # Try Binance
            try:
                print(f"    Trying Binance...")
                ohlcv = asyncio.run(
                    self.binance_loader.get_data(
                        symbol=symbol,
                        timeframe=timeframe,
                        start_date=start_date,
                        end_date=end_date,
                        use_cache=use_cache
                    )
                )
            except Exception as e:
                print(f"    ⚠️  Binance failed: {e}")

            # Fallback to Hyperliquid if Binance failed
            if ohlcv.empty:
                try:
                    print(f"    Trying Hyperliquid...")
                    ohlcv = self.hyperliquid_loader.get_data(
                        symbol=symbol,
                        timeframe=timeframe,
                        start_date=start_date,
                        end_date=end_date,
                        use_cache=use_cache
                    )
                except Exception as e:
                    print(f"    ⚠️  Hyperliquid failed: {e}")

            if ohlcv.empty:
                print(f"    ❌ No data available for {symbol} from any source")
                continue

            try:
                # Add basic indicators
                ohlcv = self._add_indicators(ohlcv)

                # Align each position
                sym_positions = positions_df[positions_df['symbol'] == symbol].copy()

                for idx, pos in sym_positions.iterrows():
                    # Find nearest candles
                    entry_candle = self._find_nearest_candle(ohlcv, pos['entry_time'])
                    exit_candle = self._find_nearest_candle(ohlcv, pos['exit_time'])

                    if entry_candle is not None and exit_candle is not None:
                        # Add indicator values at entry
                        for col in ['close', 'ema_20', 'ema_50', 'rsi', 'atr', 'volume']:
                            if col in entry_candle:
                                pos[f'entry_{col}'] = entry_candle[col]

                        # Add indicator values at exit
                        for col in ['close', 'rsi', 'atr']:
                            if col in exit_candle:
                                pos[f'exit_{col}'] = exit_candle[col]

                    aligned_positions.append(pos)

            except Exception as e:
                print(f"    ❌ Error fetching {symbol}: {e}")
                continue

        df = pd.DataFrame(aligned_positions)

        if not df.empty:
            print(f"✅ Aligned {len(df)} positions with OHLCV")
        else:
            print("⚠️  No positions could be aligned")

        return df

    def _find_nearest_candle(self, ohlcv: pd.DataFrame, timestamp: pd.Timestamp) -> pd.Series:
        """Find candle closest to timestamp"""
        if ohlcv.empty:
            return None

        idx = ohlcv['timestamp'].searchsorted(timestamp)
        if idx >= len(ohlcv):
            idx = len(ohlcv) - 1

        return ohlcv.iloc[idx]

    def _add_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add basic technical indicators"""
        # EMAs
        df['ema_20'] = df['close'].ewm(span=20, adjust=False).mean()
        df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()

        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        # ATR
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = true_range.rolling(window=14).mean()

        return df
