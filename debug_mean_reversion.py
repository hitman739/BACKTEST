#!/usr/bin/env python3
"""
Debug script para ver por qué no hay trades
"""

import pandas as pd
from datetime import datetime, timedelta
from engine.data_loader import load_data
from strategies.shallow_revert import ShallowRevertStrategy
from engine.strategy import StrategyContext

# Load data
symbol = 'BTCUSDT'
timeframe = '1m'
end_date = datetime.now()
start_date = end_date - timedelta(days=30)

print(f"Loading {symbol} {timeframe} data...")
df = load_data(
    symbol=symbol,
    timeframe=timeframe,
    start_date=start_date.strftime('%Y-%m-%d'),
    end_date=end_date.strftime('%Y-%m-%d'),
    data_dir='./data/binance',
    use_cache=True
)

print(f"✓ Loaded {len(df)} candles\n")

# Initialize strategy
strategy = ShallowRevertStrategy()
context = StrategyContext(
    symbol=symbol,
    timeframe=timeframe,
    leverage=5.0,
    account_equity=10000,
    position_size=0,
    data=df
)

print("Initializing strategy...")
df = strategy.initialize(context)
print(f"✓ Indicators calculated\n")

# Check if data has required columns
print("Checking data columns:")
required = ['mean_price', 'distance_pct', 'atr_ratio', 'vol_ratio', 'daily_range_pct', 'hour']
for col in required:
    if col in df.columns:
        print(f"  ✓ {col}")
    else:
        print(f"  ✗ {col} MISSING!")

print()

# Sample the data to see values
print("Sample of calculated values (first 20 non-NaN rows):")
sample = df[['close', 'mean_price', 'distance_pct', 'atr_ratio', 'vol_ratio', 'hour']].dropna().head(20)
print(sample)
print()

# Check distance_pct range
print("Distance % statistics:")
distance = df['distance_pct'].dropna()
print(f"  Min: {distance.min():.2f}%")
print(f"  Max: {distance.max():.2f}%")
print(f"  Mean: {distance.mean():.2f}%")
print(f"  Std: {distance.std():.2f}%")
print()

# Check how many times distance crosses thresholds
long_thresh = [-1.5, -2.5]
short_thresh = [1.5, 2.5]

print("Threshold crossings:")
print(f"  Distance <= {long_thresh[0]}%: {(distance <= long_thresh[0]).sum()} times")
print(f"  Distance <= {long_thresh[1]}%: {(distance <= long_thresh[1]).sum()} times")
print(f"  Distance >= {short_thresh[0]}%: {(distance >= short_thresh[0]).sum()} times")
print(f"  Distance >= {short_thresh[1]}%: {(distance >= short_thresh[1]).sum()} times")
print()

# Check regime filters
print("Regime filter statistics:")
atr_ratio = df['atr_ratio'].dropna()
vol_ratio = df['vol_ratio'].dropna()
daily_range = df['daily_range_pct'].dropna()

print(f"  ATR ratio (need 0.8-2.0):")
print(f"    Min: {atr_ratio.min():.2f}, Max: {atr_ratio.max():.2f}")
print(f"    In range: {((atr_ratio >= 0.8) & (atr_ratio <= 2.0)).sum()} / {len(atr_ratio)}")

print(f"  Vol ratio (need 0.8-2.5):")
print(f"    Min: {vol_ratio.min():.2f}, Max: {vol_ratio.max():.2f}")
print(f"    In range: {((vol_ratio >= 0.8) & (vol_ratio <= 2.5)).sum()} / {len(vol_ratio)}")

print(f"  Daily range %:")
print(f"    Min: {daily_range.min():.2f}%, Max: {daily_range.max():.2f}%")
print()

# Check session filter (8-20 UTC)
hours = df['hour'].dropna()
print(f"Trading hours filter (8-20 UTC):")
print(f"  Bars in range: {((hours >= 8) & (hours < 20)).sum()} / {len(hours)}")
print()

# Find bars that pass ALL filters AND cross threshold
print("Looking for valid entry opportunities...")

valid_bars = df[
    (df['atr_ratio'] >= 0.8) &
    (df['atr_ratio'] <= 2.0) &
    (df['vol_ratio'] >= 0.8) &
    (df['vol_ratio'] <= 2.5) &
    (df['hour'] >= 8) &
    (df['hour'] < 20) &
    (
        (df['distance_pct'] <= -1.5) |
        (df['distance_pct'] >= 1.5)
    )
].dropna()

print(f"✓ Found {len(valid_bars)} bars that pass all filters and cross threshold")

if len(valid_bars) > 0:
    print("\nFirst 5 valid entry opportunities:")
    print(valid_bars[['timestamp', 'close', 'mean_price', 'distance_pct', 'atr_ratio', 'vol_ratio']].head())
else:
    print("\n⚠️ NO VALID ENTRY OPPORTUNITIES FOUND!")
    print("This means filters are too strict or thresholds never reached.")
