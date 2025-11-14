"""
Technical Indicators Library

Provides all indicators needed for strategy development:
- Moving averages (SMA, EMA, WMA)
- Momentum indicators (RSI, MACD)
- Volatility indicators (ATR, Bollinger Bands)
- Trend indicators (ADX)
- Volume indicators (VWAP, Volume MA, OBV)
- Price action (Swing High/Low, True Range)
- Fibonacci levels
"""

import numpy as np
import pandas as pd
from typing import Tuple, Optional


class Indicators:
    """Technical indicator calculation library"""

    @staticmethod
    def sma(series: pd.Series, period: int) -> pd.Series:
        """Simple Moving Average"""
        return series.rolling(window=period).mean()

    @staticmethod
    def ema(series: pd.Series, period: int) -> pd.Series:
        """Exponential Moving Average"""
        return series.ewm(span=period, adjust=False).mean()

    @staticmethod
    def wma(series: pd.Series, period: int) -> pd.Series:
        """Weighted Moving Average"""
        weights = np.arange(1, period + 1)

        def weighted_mean(x):
            if len(x) < period:
                return np.nan
            return np.dot(x[-period:], weights) / weights.sum()

        return series.rolling(window=period).apply(weighted_mean, raw=True)

    @staticmethod
    def rsi(series: pd.Series, period: int = 14) -> pd.Series:
        """Relative Strength Index"""
        delta = series.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def true_range(high: pd.Series, low: pd.Series, close: pd.Series) -> pd.Series:
        """True Range"""
        hl = high - low
        hc = abs(high - close.shift(1))
        lc = abs(low - close.shift(1))

        tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
        return tr

    @staticmethod
    def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Average True Range"""
        tr = Indicators.true_range(high, low, close)
        atr = tr.rolling(window=period).mean()
        return atr

    @staticmethod
    def vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
        """Volume Weighted Average Price (resets daily)"""
        typical_price = (high + low + close) / 3
        cumulative_tpv = (typical_price * volume).cumsum()
        cumulative_volume = volume.cumsum()

        vwap = cumulative_tpv / cumulative_volume
        return vwap

    @staticmethod
    def bollinger_bands(
        series: pd.Series,
        period: int = 20,
        std_dev: float = 2.0
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Bollinger Bands

        Returns:
            (middle, upper, lower)
        """
        middle = series.rolling(window=period).mean()
        std = series.rolling(window=period).std()

        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)

        return middle, upper, lower

    @staticmethod
    def macd(
        series: pd.Series,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        MACD (Moving Average Convergence Divergence)

        Returns:
            (macd_line, signal_line, histogram)
        """
        ema_fast = series.ewm(span=fast, adjust=False).mean()
        ema_slow = series.ewm(span=slow, adjust=False).mean()

        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal, adjust=False).mean()
        histogram = macd_line - signal_line

        return macd_line, signal_line, histogram

    @staticmethod
    def stochastic(
        high: pd.Series,
        low: pd.Series,
        close: pd.Series,
        period: int = 14,
        smooth_k: int = 3,
        smooth_d: int = 3
    ) -> Tuple[pd.Series, pd.Series]:
        """
        Stochastic Oscillator

        Returns:
            (%K, %D)
        """
        lowest_low = low.rolling(window=period).min()
        highest_high = high.rolling(window=period).max()

        k_raw = 100 * (close - lowest_low) / (highest_high - lowest_low)
        k = k_raw.rolling(window=smooth_k).mean()
        d = k.rolling(window=smooth_d).mean()

        return k, d

    @staticmethod
    def swing_high(high: pd.Series, left_bars: int = 5, right_bars: int = 5) -> pd.Series:
        """
        Detect swing highs

        Returns:
            Series with swing high prices (NaN where no swing high)
        """
        swing_highs = pd.Series(index=high.index, dtype=float)

        for i in range(left_bars, len(high) - right_bars):
            center_high = high.iloc[i]
            is_swing_high = True

            # Check left bars
            for j in range(i - left_bars, i):
                if high.iloc[j] >= center_high:
                    is_swing_high = False
                    break

            # Check right bars
            if is_swing_high:
                for j in range(i + 1, i + right_bars + 1):
                    if high.iloc[j] >= center_high:
                        is_swing_high = False
                        break

            if is_swing_high:
                swing_highs.iloc[i] = center_high

        return swing_highs

    @staticmethod
    def swing_low(low: pd.Series, left_bars: int = 5, right_bars: int = 5) -> pd.Series:
        """
        Detect swing lows

        Returns:
            Series with swing low prices (NaN where no swing low)
        """
        swing_lows = pd.Series(index=low.index, dtype=float)

        for i in range(left_bars, len(low) - right_bars):
            center_low = low.iloc[i]
            is_swing_low = True

            # Check left bars
            for j in range(i - left_bars, i):
                if low.iloc[j] <= center_low:
                    is_swing_low = False
                    break

            # Check right bars
            if is_swing_low:
                for j in range(i + 1, i + right_bars + 1):
                    if low.iloc[j] <= center_low:
                        is_swing_low = False
                        break

            if is_swing_low:
                swing_lows.iloc[i] = center_low

        return swing_lows

    @staticmethod
    def fibonacci_retracement(
        high_price: float,
        low_price: float,
        is_uptrend: bool = True
    ) -> dict:
        """
        Calculate Fibonacci retracement levels

        Args:
            high_price: Swing high price
            low_price: Swing low price
            is_uptrend: True for uptrend (retracing from high), False for downtrend

        Returns:
            Dictionary with Fibonacci levels
        """
        diff = high_price - low_price

        if is_uptrend:
            levels = {
                "0.0": high_price,
                "0.236": high_price - (0.236 * diff),
                "0.382": high_price - (0.382 * diff),
                "0.500": high_price - (0.500 * diff),
                "0.618": high_price - (0.618 * diff),
                "0.786": high_price - (0.786 * diff),
                "1.0": low_price,
            }
        else:
            levels = {
                "0.0": low_price,
                "0.236": low_price + (0.236 * diff),
                "0.382": low_price + (0.382 * diff),
                "0.500": low_price + (0.500 * diff),
                "0.618": low_price + (0.618 * diff),
                "0.786": low_price + (0.786 * diff),
                "1.0": high_price,
            }

        return levels

    @staticmethod
    def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """
        Average Directional Index (ADX)

        Measures trend strength (0-100):
        - 0-25: Weak/absent trend
        - 25-50: Strong trend
        - 50-75: Very strong trend
        - 75-100: Extremely strong trend

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: Lookback period (default 14)

        Returns:
            ADX values (0-100)
        """
        # Calculate True Range
        tr = Indicators.true_range(high, low, close)

        # Calculate directional movement
        high_diff = high.diff()
        low_diff = -low.diff()

        # Positive and negative directional movement
        plus_dm = pd.Series(0.0, index=high.index)
        minus_dm = pd.Series(0.0, index=low.index)

        plus_dm[(high_diff > low_diff) & (high_diff > 0)] = high_diff
        minus_dm[(low_diff > high_diff) & (low_diff > 0)] = low_diff

        # Smooth the values using Wilder's smoothing (similar to EMA)
        atr = tr.ewm(alpha=1/period, adjust=False).mean()
        plus_di = 100 * (plus_dm.ewm(alpha=1/period, adjust=False).mean() / atr)
        minus_di = 100 * (minus_dm.ewm(alpha=1/period, adjust=False).mean() / atr)

        # Calculate DX (Directional Index)
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        dx = dx.fillna(0)

        # ADX is the smoothed DX
        adx = dx.ewm(alpha=1/period, adjust=False).mean()

        return adx

    @staticmethod
    def volume_ma(volume: pd.Series, period: int = 20) -> pd.Series:
        """Volume Moving Average"""
        return volume.rolling(window=period).mean()

    @staticmethod
    def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
        """On-Balance Volume"""
        direction = np.sign(close.diff())
        direction[0] = 0
        obv = (direction * volume).cumsum()
        return obv

    @staticmethod
    def add_all_indicators(
        df: pd.DataFrame,
        config: Optional[dict] = None
    ) -> pd.DataFrame:
        """
        Add commonly used indicators to a DataFrame

        Args:
            df: DataFrame with OHLCV data
            config: Optional configuration for indicator periods

        Returns:
            DataFrame with additional indicator columns
        """
        if config is None:
            config = {}

        df = df.copy()

        # Moving averages
        for period in config.get('sma_periods', [20, 50, 200]):
            df[f'sma_{period}'] = Indicators.sma(df['close'], period)

        for period in config.get('ema_periods', [9, 21, 55]):
            df[f'ema_{period}'] = Indicators.ema(df['close'], period)

        # RSI
        for period in config.get('rsi_periods', [14]):
            df[f'rsi_{period}'] = Indicators.rsi(df['close'], period)

        # ATR
        for period in config.get('atr_periods', [14]):
            df[f'atr_{period}'] = Indicators.atr(df['high'], df['low'], df['close'], period)

        # Volume indicators
        for period in config.get('volume_ma_periods', [20]):
            df[f'volume_ma_{period}'] = Indicators.volume_ma(df['volume'], period)

        # MACD
        if config.get('add_macd', True):
            macd, signal, hist = Indicators.macd(df['close'])
            df['macd'] = macd
            df['macd_signal'] = signal
            df['macd_hist'] = hist

        # Bollinger Bands
        if config.get('add_bbands', True):
            bb_middle, bb_upper, bb_lower = Indicators.bollinger_bands(df['close'])
            df['bb_middle'] = bb_middle
            df['bb_upper'] = bb_upper
            df['bb_lower'] = bb_lower

        return df


def add_indicators(df: pd.DataFrame, indicator_specs: dict) -> pd.DataFrame:
    """
    Add specific indicators to DataFrame based on specification

    Args:
        df: OHLCV DataFrame
        indicator_specs: Dictionary specifying which indicators to add
            Example:
            {
                'ema_20': {'type': 'ema', 'period': 20, 'source': 'close'},
                'rsi': {'type': 'rsi', 'period': 14},
                'atr': {'type': 'atr', 'period': 14}
            }

    Returns:
        DataFrame with added indicator columns
    """
    df = df.copy()

    for name, spec in indicator_specs.items():
        ind_type = spec['type'].lower()
        source = spec.get('source', 'close')

        if ind_type == 'sma':
            df[name] = Indicators.sma(df[source], spec['period'])

        elif ind_type == 'ema':
            df[name] = Indicators.ema(df[source], spec['period'])

        elif ind_type == 'wma':
            df[name] = Indicators.wma(df[source], spec['period'])

        elif ind_type == 'rsi':
            df[name] = Indicators.rsi(df[source], spec['period'])

        elif ind_type == 'atr':
            df[name] = Indicators.atr(df['high'], df['low'], df['close'], spec['period'])

        elif ind_type == 'vwap':
            df[name] = Indicators.vwap(df['high'], df['low'], df['close'], df['volume'])

        elif ind_type == 'volume_ma':
            df[name] = Indicators.volume_ma(df['volume'], spec['period'])

        elif ind_type == 'bbands':
            middle, upper, lower = Indicators.bollinger_bands(
                df[source], spec.get('period', 20), spec.get('std_dev', 2.0)
            )
            df[f'{name}_middle'] = middle
            df[f'{name}_upper'] = upper
            df[f'{name}_lower'] = lower

        elif ind_type == 'macd':
            macd, signal, hist = Indicators.macd(
                df[source],
                spec.get('fast', 12),
                spec.get('slow', 26),
                spec.get('signal', 9)
            )
            df[f'{name}'] = macd
            df[f'{name}_signal'] = signal
            df[f'{name}_hist'] = hist

    return df
