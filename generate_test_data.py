"""
Generate synthetic test data for backtesting demonstration
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta


def generate_realistic_crypto_data(
    start_date: str,
    periods: int,
    freq: str = '5min',
    base_price: float = 60000.0,
    daily_volatility: float = 0.03
) -> pd.DataFrame:
    """
    Generate realistic synthetic cryptocurrency OHLCV data

    Args:
        start_date: Start date
        periods: Number of periods
        freq: Frequency
        base_price: Starting price
        daily_volatility: Daily volatility (default 3%)

    Returns:
        DataFrame with OHLCV data
    """
    np.random.seed(42)  # For reproducibility

    # Generate timestamps
    timestamps = pd.date_range(start=start_date, periods=periods, freq=freq)

    # Calculate per-period volatility (for 5m bars from daily volatility)
    periods_per_day = 288  # 5-minute bars in a day
    period_volatility = daily_volatility / np.sqrt(periods_per_day)

    # Generate price series using geometric Brownian motion
    returns = np.random.normal(0, period_volatility, periods)
    # Add some trending behavior
    trend = np.linspace(0, 0.2, periods)  # 20% uptrend over the period
    returns += trend / periods

    # Calculate prices
    prices = base_price * np.exp(np.cumsum(returns))

    # Generate OHLC from close prices
    data = []
    for i, close in enumerate(prices):
        # Generate realistic intra-bar price movement
        bar_range_pct = abs(np.random.normal(0, 0.002))  # ~0.2% typical range

        # Random OHLC within the range
        high = close * (1 + bar_range_pct * np.random.random())
        low = close * (1 - bar_range_pct * np.random.random())

        # Open is somewhere between high and low
        open_price = low + (high - low) * np.random.random()

        # Ensure close is within high/low
        close = max(min(close, high), low)

        # Ensure OHLC relationships are maintained
        high = max(high, open_price, close)
        low = min(low, open_price, close)

        # Generate volume with some randomness
        base_volume = 500 + np.random.randint(0, 1000)
        # Higher volume on larger price moves
        price_move = abs(close - open_price) / open_price
        volume = base_volume * (1 + price_move * 10)

        data.append({
            'timestamp': timestamps[i],
            'open': round(open_price, 2),
            'high': round(high, 2),
            'low': round(low, 2),
            'close': round(close, 2),
            'volume': round(volume, 2)
        })

    df = pd.DataFrame(data)
    return df


def save_test_data(symbol: str, timeframe: str, df: pd.DataFrame, data_dir: str = './data/binance'):
    """Save test data to cache"""
    path = Path(data_dir) / symbol
    path.mkdir(parents=True, exist_ok=True)

    file_path = path / f"{timeframe}.parquet"
    df.to_parquet(file_path, index=False)
    print(f"Saved {len(df)} candles to {file_path}")


if __name__ == '__main__':
    # Generate 60 days of 5-minute data
    # 60 days * 24 hours * 12 (5-min intervals) = 17,280 candles
    periods = 60 * 24 * 12

    print("Generating realistic synthetic BTCUSDT 5m data...")
    df = generate_realistic_crypto_data(
        start_date='2024-08-01',
        periods=periods,
        freq='5min',
        base_price=60000.0,
        daily_volatility=0.03  # 3% daily volatility
    )

    print(f"Generated {len(df)} candles from {df['timestamp'].iloc[0]} to {df['timestamp'].iloc[-1]}")
    print(f"Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
    print(f"Start price: ${df['close'].iloc[0]:.2f}")
    print(f"End price: ${df['close'].iloc[-1]:.2f}")
    print(f"Total return: {((df['close'].iloc[-1] / df['close'].iloc[0]) - 1) * 100:.2f}%")

    # Save to cache
    save_test_data('BTCUSDT', '5m', df)

    print("\nTest data ready!")
    print("\nSample data (first 10 bars):")
    print(df.head(10).to_string())

    print("\nSample data (last 10 bars):")
    print(df.tail(10).to_string())
