#!/usr/bin/env python3
"""
Generate synthetic SOLUSDT 5-minute data for backtesting
Creates 60 days of 5m OHLCV data with realistic volatility spikes
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta


def generate_sol_data_5m(start_date: str, periods: int, base_price: float = 150.0, daily_volatility: float = 0.05):
    """
    Generate synthetic SOL/USDT 5-minute data with volatility spikes

    Args:
        start_date: Starting date (YYYY-MM-DD)
        periods: Number of 5-minute candles to generate
        base_price: Starting price
        daily_volatility: Daily volatility (default 5% for SOL)

    Returns:
        DataFrame with OHLCV data
    """

    # Convert daily volatility to 5-minute volatility
    # Daily = 288 5-minute candles (24h * 60min / 5min)
    candles_per_day = 288
    period_volatility = daily_volatility / np.sqrt(candles_per_day)

    # Generate timestamps (5-minute intervals)
    start = pd.to_datetime(start_date)
    timestamps = [start + timedelta(minutes=5*i) for i in range(periods)]

    # Generate price movement
    np.random.seed(42)  # For reproducibility

    # Base random walk with drift
    returns = np.random.normal(0.00002, period_volatility, periods)  # Slight upward drift

    # Add volatility spikes every ~500-1000 candles
    spike_intervals = np.random.randint(500, 1000, periods // 750)
    spike_positions = np.cumsum(spike_intervals)
    spike_positions = spike_positions[spike_positions < periods]

    for pos in spike_positions:
        # Create volatility expansion (3-8 candles)
        spike_length = np.random.randint(3, 8)
        spike_direction = np.random.choice([-1, 1])  # Bullish or bearish

        for i in range(spike_length):
            if pos + i < periods:
                # Larger moves during spike
                returns[pos + i] = spike_direction * np.random.uniform(0.015, 0.035)  # 1.5-3.5% per 5m

    # Calculate close prices
    price_multipliers = np.exp(returns)
    closes = base_price * np.cumprod(price_multipliers)

    # Generate realistic OHLC from close
    data = []
    for i, close in enumerate(closes):
        # Random candle range (0.1% to 0.5% for normal candles)
        candle_range_pct = np.random.uniform(0.001, 0.005)

        # Larger ranges during spikes
        if i in spike_positions or (i > 0 and abs(returns[i]) > 0.01):
            candle_range_pct = np.random.uniform(0.01, 0.03)

        candle_range = close * candle_range_pct

        # Determine if candle is bullish or bearish
        is_bullish = returns[i] >= 0

        if is_bullish:
            open_price = close - abs(returns[i] * close * np.random.uniform(0.3, 0.7))
            high = close + candle_range * np.random.uniform(0.1, 0.3)
            low = open_price - candle_range * np.random.uniform(0.1, 0.3)

            # Reversal candles have long wicks
            if i in spike_positions:
                # Long upper wick for bearish reversal
                if returns[i] < -0.015:
                    high = close + candle_range * 2.0
                # Long lower wick for bullish reversal
                elif returns[i] > 0.015:
                    low = open_price - candle_range * 2.0
        else:
            open_price = close - abs(returns[i] * close * np.random.uniform(0.3, 0.7))
            high = open_price + candle_range * np.random.uniform(0.1, 0.3)
            low = close - candle_range * np.random.uniform(0.1, 0.3)

            # Reversal candles
            if i in spike_positions:
                if returns[i] < -0.015:
                    high = open_price + candle_range * 2.0
                elif returns[i] > 0.015:
                    low = close - candle_range * 2.0

        # Ensure OHLC relationships are valid
        high = max(high, open_price, close)
        low = min(low, open_price, close)

        # Generate volume (higher during large moves)
        base_volume = np.random.uniform(100000, 500000)
        if abs(returns[i]) > 0.01:
            base_volume *= np.random.uniform(3, 8)  # Volume spike

        data.append({
            'timestamp': timestamps[i],
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': base_volume
        })

    df = pd.DataFrame(data)

    return df


def save_to_cache(df: pd.DataFrame, symbol: str = 'SOLUSDT', timeframe: str = '5m'):
    """Save generated data to cache directory"""
    cache_dir = Path('./data/binance')
    cache_dir.mkdir(parents=True, exist_ok=True)

    start = df['timestamp'].iloc[0].strftime('%Y-%m-%d')
    end = df['timestamp'].iloc[-1].strftime('%Y-%m-%d')

    file_path = cache_dir / f"{symbol}_{timeframe}_{start}_{end}.parquet"
    df.to_parquet(file_path, index=False)
    print(f"Saved {len(df)} candles to {file_path}")


if __name__ == '__main__':
    # Generate 60 days of 5-minute data
    # 60 days * 24 hours * 12 candles/hour = 17,280 candles
    periods = 60 * 24 * 12

    print("Generating synthetic SOLUSDT 5m data with volatility spikes...")
    df = generate_sol_data_5m(
        start_date='2025-09-14',
        periods=periods,
        base_price=150.0,
        daily_volatility=0.05  # 5% daily volatility (SOL is volatile)
    )

    print(f"\nGenerated {len(df)} candles from {df['timestamp'].iloc[0]} to {df['timestamp'].iloc[-1]}")
    print(f"Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
    print(f"Start price: ${df['close'].iloc[0]:.2f}")
    print(f"End price: ${df['close'].iloc[-1]:.2f}")
    print(f"Total return: {((df['close'].iloc[-1] / df['close'].iloc[0]) - 1) * 100:.2f}%")

    # Calculate some stats
    df['returns'] = df['close'].pct_change()
    df['candle_range'] = ((df['high'] - df['low']) / df['close'] * 100)

    large_moves = df[df['candle_range'] > 1.0]
    print(f"\nLarge moves (>1% range): {len(large_moves)} candles ({len(large_moves)/len(df)*100:.1f}%)")

    vol_spikes = df[df['volume'] > df['volume'].quantile(0.95)]
    print(f"Volume spikes (>95th percentile): {len(vol_spikes)} candles")

    # Save to cache
    save_to_cache(df, symbol='SOLUSDT', timeframe='5m')

    print("\n✅ Data generation complete!")
    print("\n💡 Now you can run:")
    print("   python3 test_vrr_ultra_5m.py")
