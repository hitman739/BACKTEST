"""
Generate synthetic SOLUSDT 1m data with high volatility spikes

This creates realistic data with:
- Periodic volatility spikes
- Volume surges
- Reversal patterns
- Trending and ranging periods
"""

import pandas as pd
import numpy as np
from pathlib import Path


def generate_sol_data_with_spikes(
    start_date: str,
    periods: int,
    base_price: float = 150.0,
    daily_volatility: float = 0.05
) -> pd.DataFrame:
    """
    Generate SOLUSDT 1m data with realistic volatility spikes

    Args:
        start_date: Start date
        periods: Number of 1-minute bars
        base_price: Starting price
        daily_volatility: Base daily volatility (5%)

    Returns:
        DataFrame with OHLCV data
    """
    np.random.seed(42)

    timestamps = pd.date_range(start=start_date, periods=periods, freq='1min')

    # Calculate per-minute volatility
    periods_per_day = 1440  # 1-minute bars in a day
    period_volatility = daily_volatility / np.sqrt(periods_per_day)

    # Generate base price series with trending behavior
    trend = np.linspace(0, 0.15, periods)  # 15% trend over period
    base_returns = np.random.normal(0, period_volatility, periods)
    base_returns += trend / periods

    # Add volatility spikes (every ~500-1000 bars)
    spike_probability = 0.015  # ~1.5% chance per bar
    spike_magnitude = 3.0  # 3x normal volatility

    for i in range(periods):
        if np.random.random() < spike_probability:
            # Create a spike cluster (3-8 bars)
            spike_duration = np.random.randint(3, 9)
            for j in range(spike_duration):
                if i + j < periods:
                    base_returns[i + j] += np.random.normal(0, period_volatility * spike_magnitude)

    # Calculate prices
    prices = base_price * np.exp(np.cumsum(base_returns))

    # Generate OHLC with realistic patterns
    data = []
    for i, close in enumerate(prices):
        # Determine bar characteristics
        is_volatile = abs(base_returns[i]) > (period_volatility * 2)

        if is_volatile:
            # Larger range for volatile bars
            bar_range_pct = abs(np.random.normal(0, 0.008))  # ~0.8% range
        else:
            # Normal range
            bar_range_pct = abs(np.random.normal(0, 0.003))  # ~0.3% range

        # Generate OHLC
        high = close * (1 + bar_range_pct * np.random.random())
        low = close * (1 - bar_range_pct * np.random.random())
        open_price = low + (high - low) * np.random.random()

        # Ensure close is within high/low
        close = max(min(close, high), low)

        # Ensure OHLC relationships
        high = max(high, open_price, close)
        low = min(low, open_price, close)

        # Generate volume with spikes
        base_volume = 2000 + np.random.randint(0, 3000)

        # Volume spikes on volatile bars
        if is_volatile:
            volume_mult = 2.0 + np.random.random() * 3.0  # 2-5x volume
            volume = base_volume * volume_mult
        else:
            # Normal volume variation
            volume = base_volume * (0.8 + np.random.random() * 0.4)

        # Create reversal patterns occasionally
        if i > 0 and is_volatile:
            prev_close = data[-1]['close']
            move_direction = close - prev_close

            # 30% chance of creating a reversal wick
            if np.random.random() < 0.3:
                if move_direction > 0:
                    # Bullish move, create upper wick (bearish reversal signal)
                    wick_size = (high - close) * 2.0
                    high = close + wick_size
                else:
                    # Bearish move, create lower wick (bullish reversal signal)
                    wick_size = (close - low) * 2.0
                    low = close - wick_size

        data.append({
            'timestamp': timestamps[i],
            'open': round(open_price, 4),
            'high': round(high, 4),
            'low': round(low, 4),
            'close': round(close, 4),
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
    # Generate 60 days of 1-minute data
    # 60 days * 24 hours * 60 minutes = 86,400 candles
    periods = 60 * 24 * 60

    print("Generating synthetic SOLUSDT 1m data with volatility spikes...")
    df = generate_sol_data_with_spikes(
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

    # Analyze volatility characteristics
    df['returns'] = df['close'].pct_change()
    df['range_pct'] = (df['high'] - df['low']) / df['close']

    print(f"\nVolatility characteristics:")
    print(f"  Avg return: {df['returns'].mean()*100:.4f}%")
    print(f"  Std return: {df['returns'].std()*100:.4f}%")
    print(f"  Avg range:  {df['range_pct'].mean()*100:.4f}%")
    print(f"  Max range:  {df['range_pct'].max()*100:.4f}%")

    # Count potential VRR setups (large moves)
    large_moves = (df['range_pct'] > 0.01).sum()  # >1% moves
    print(f"\nLarge moves (>1% range): {large_moves} ({large_moves/len(df)*100:.2f}%)")

    # Save to cache
    save_test_data('SOLUSDT', '1m', df)

    print("\nTest data ready!")
    print("\nSample data (first 10 bars):")
    print(df.head(10)[['timestamp', 'open', 'high', 'low', 'close', 'volume']].to_string())

    print("\nSample data (bars with large range):")
    large_range_samples = df.nlargest(5, 'range_pct')[['timestamp', 'open', 'high', 'low', 'close', 'range_pct']]
    print(large_range_samples.to_string())
