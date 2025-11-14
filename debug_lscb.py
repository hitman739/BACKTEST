#!/usr/bin/env python3
"""
Debug LSCB Strategy - Check what conditions are being met
"""

import pandas as pd
from strategies.lscb_strategy import LSCBStrategy
from engine.data_loader import load_data
from engine.strategy import StrategyContext

# Load data
print("Loading BTC data...")
df = load_data(
    symbol='BTCUSDT',
    timeframe='5m',
    start_date='2024-08-01',
    end_date='2024-09-29',
    data_dir='./data/binance',
    use_cache=True
)

print(f"Loaded {len(df)} candles")

# Initialize strategy
strategy = LSCBStrategy()
context = StrategyContext(
    symbol='BTCUSDT',
    timeframe='5m',
    leverage=1.0,
    account_equity=10000,
    position_size=0,
    data=df
)

df = strategy.initialize(context)
print("Indicators computed")

# Check conditions across the dataset
swing_lookback = strategy.swing_lookback

long_conditions = {
    'ema_rising': 0,
    'swing_low_found': 0,
    'sweep_found': 0,
    'rejection_ok': 0,
    'compression_ok': 0,
    'rsi_ok': 0,
    'confirmation_ok': 0,
    'all_conditions_met': 0
}

short_conditions = {
    'ema_falling': 0,
    'swing_high_found': 0,
    'sweep_found': 0,
    'rejection_ok': 0,
    'compression_ok': 0,
    'rsi_ok': 0,
    'confirmation_ok': 0,
    'all_conditions_met': 0
}

print(f"\nChecking conditions bar by bar (starting at bar {swing_lookback + 20})...")

for idx in range(swing_lookback + 20, len(df)):
    data = df.iloc[:idx+1]

    # LONG checks
    if data['ema_50_slope'].iloc[idx] > 0:
        long_conditions['ema_rising'] += 1

        swing_low = strategy._find_swing_low(data, idx)
        if swing_low is not None:
            long_conditions['swing_low_found'] += 1

            sweep_idx = strategy._find_sweep_candle(data, idx, swing_low, 'long')
            if sweep_idx is not None:
                long_conditions['sweep_found'] += 1

                if strategy._check_rejection(data, sweep_idx, 'long'):
                    long_conditions['rejection_ok'] += 1

                    if strategy._check_compression(data, sweep_idx):
                        long_conditions['compression_ok'] += 1

                        if strategy._check_rsi_long(data, idx):
                            long_conditions['rsi_ok'] += 1

                            if strategy._check_confirmation_long(data, idx, sweep_idx):
                                long_conditions['confirmation_ok'] += 1
                                long_conditions['all_conditions_met'] += 1

    # SHORT checks
    if data['ema_50_slope'].iloc[idx] < 0:
        short_conditions['ema_falling'] += 1

        swing_high = strategy._find_swing_high(data, idx)
        if swing_high is not None:
            short_conditions['swing_high_found'] += 1

            sweep_idx = strategy._find_sweep_candle(data, idx, swing_high, 'short')
            if sweep_idx is not None:
                short_conditions['sweep_found'] += 1

                if strategy._check_rejection(data, sweep_idx, 'short'):
                    short_conditions['rejection_ok'] += 1

                    if strategy._check_compression(data, sweep_idx):
                        short_conditions['compression_ok'] += 1

                        if strategy._check_rsi_short(data, idx):
                            short_conditions['rsi_ok'] += 1

                            if strategy._check_confirmation_short(data, idx, sweep_idx):
                                short_conditions['confirmation_ok'] += 1
                                short_conditions['all_conditions_met'] += 1

print("\n" + "=" * 70)
print("📊 LONG SETUP CONDITIONS ANALYSIS")
print("=" * 70)
total_bars = len(df) - (swing_lookback + 20)
for condition, count in long_conditions.items():
    pct = (count / total_bars) * 100
    print(f"{condition:25} {count:6} bars ({pct:5.2f}%)")

print("\n" + "=" * 70)
print("📊 SHORT SETUP CONDITIONS ANALYSIS")
print("=" * 70)
for condition, count in short_conditions.items():
    pct = (count / total_bars) * 100
    print(f"{condition:25} {count:6} bars ({pct:5.2f}%)")

print("\n" + "=" * 70)
print("💡 INTERPRETATION")
print("=" * 70)
print(f"\nTotal bars analyzed: {total_bars}")
print(f"\nLONG setups found: {long_conditions['all_conditions_met']}")
print(f"SHORT setups found: {short_conditions['all_conditions_met']}")

if long_conditions['all_conditions_met'] == 0 and short_conditions['all_conditions_met'] == 0:
    print("\n⚠️  No complete setups found!")
    print("\nMost restrictive conditions:")

    # Find bottleneck for LONG
    print("\nLONG bottleneck:")
    for cond, count in sorted(long_conditions.items(), key=lambda x: x[1]):
        if cond != 'all_conditions_met':
            print(f"  - {cond}: {count} ({(count/total_bars)*100:.2f}%)")
            if count < 10:
                break

    # Find bottleneck for SHORT
    print("\nSHORT bottleneck:")
    for cond, count in sorted(short_conditions.items(), key=lambda x: x[1]):
        if cond != 'all_conditions_met':
            print(f"  - {cond}: {count} ({(count/total_bars)*100:.2f}%)")
            if count < 10:
                break

print("\n" + "=" * 70)
