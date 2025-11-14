#!/usr/bin/env python3
"""
Debug sweep candle criteria - see which conditions fail
"""

import pandas as pd
from strategies.lscb_strategy import LSCBStrategy
from engine.data_loader import load_data
from engine.strategy import StrategyContext

# Load data
df = load_data(
    symbol='BTCUSDT',
    timeframe='5m',
    start_date='2024-08-01',
    end_date='2024-09-29',
    data_dir='./data/binance',
    use_cache=True
)

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

# Check sweep criteria when we have a swing level
swing_lookback = strategy.swing_lookback

sweep_stats = {
    'total_swing_lows': 0,
    'candles_below_swing': 0,
    'failed_sweep_size': 0,
    'failed_wick_pct': 0,
    'failed_volume': 0,
    'passed_all': 0
}

print("\n🔍 ANALYZING SWEEP CANDLE CRITERIA\n")
print("=" * 70)

for idx in range(swing_lookback + 20, min(swing_lookback + 500, len(df))):  # Check first 500 bars
    data = df.iloc[:idx+1]

    # Find swing low
    swing_low = strategy._find_swing_low(data, idx)

    if swing_low is not None:
        sweep_stats['total_swing_lows'] += 1

        # Check last 5 candles for sweep
        for i in range(max(0, idx - 5), idx):
            candle = data.iloc[i]

            # Check if candle goes below swing
            if candle['low'] < swing_low:
                sweep_stats['candles_below_swing'] += 1
                sweep_size = swing_low - candle['low']

                # Check each criterion
                sweep_size_pct = (sweep_size / candle['close']) * 100

                if sweep_size_pct < strategy.min_sweep_size_pct:
                    sweep_stats['failed_sweep_size'] += 1
                    continue

                wick_pct = (candle['lower_wick'] / candle['candle_range']) * 100 if candle['candle_range'] > 0 else 0

                if wick_pct < strategy.min_wick_pct:
                    sweep_stats['failed_wick_pct'] += 1
                    continue

                vol_ratio = candle['volume'] / candle['volume_ma20'] if candle['volume_ma20'] > 0 else 0

                if vol_ratio < strategy.min_volume_multiple:
                    sweep_stats['failed_volume'] += 1
                    continue

                sweep_stats['passed_all'] += 1

# Print results
print("Sweep Candle Criteria Analysis (first 500 bars)")
print("=" * 70)
print(f"\nSwing lows detected: {sweep_stats['total_swing_lows']}")
print(f"Candles that go below swing: {sweep_stats['candles_below_swing']}")
print(f"\nFailures by criterion:")
print(f"  - Sweep size <0.5%: {sweep_stats['failed_sweep_size']}")
print(f"  - Wick <50%: {sweep_stats['failed_wick_pct']}")
print(f"  - Volume <2x MA20: {sweep_stats['failed_volume']}")
print(f"\n✅ Passed all criteria: {sweep_stats['passed_all']}")

print("\n" + "=" * 70)
print("💡 RECOMMENDATIONS")
print("=" * 70)

if sweep_stats['candles_below_swing'] > 0:
    failure_rate = lambda x: (x / sweep_stats['candles_below_swing']) * 100

    print(f"\nOf {sweep_stats['candles_below_swing']} candles that swept below swing:")
    print(f"  - {failure_rate(sweep_stats['failed_sweep_size']):.1f}% failed sweep size test")
    print(f"  - {failure_rate(sweep_stats['failed_wick_pct']):.1f}% failed wick percentage test")
    print(f"  - {failure_rate(sweep_stats['failed_volume']):.1f}% failed volume test")

    print("\n🔧 Suggested parameter adjustments:")
    print("  - Reduce min_sweep_size_pct from 0.5% to 0.2%")
    print("  - Reduce min_wick_pct from 50% to 35%")
    print("  - Reduce min_volume_multiple from 2.0x to 1.5x")
else:
    print("\n⚠️  No candles even go below swing levels!")
    print("  - Check if swing detection is too restrictive (min_touches)")
    print("  - Increase swing_tolerance_pct")

print("\n" + "=" * 70)

# Sample some sweep candidates
print("\n📊 SAMPLE SWEEP CANDIDATES (relaxed criteria)")
print("=" * 70)

found_samples = 0
for idx in range(swing_lookback + 20, len(df)):
    if found_samples >= 5:
        break

    data = df.iloc[:idx+1]
    swing_low = strategy._find_swing_low(data, idx)

    if swing_low is not None:
        for i in range(max(0, idx - 5), idx):
            candle = data.iloc[i]

            if candle['low'] < swing_low:
                sweep_size = swing_low - candle['low']
                sweep_size_pct = (sweep_size / candle['close']) * 100
                wick_pct = (candle['lower_wick'] / candle['candle_range']) * 100 if candle['candle_range'] > 0 else 0
                vol_ratio = candle['volume'] / candle['volume_ma20'] if candle['volume_ma20'] > 0 else 0

                print(f"\nCandle {i} @ {candle['timestamp']}")
                print(f"  Swing low: ${swing_low:.2f}")
                print(f"  Candle low: ${candle['low']:.2f}")
                print(f"  Sweep size: {sweep_size_pct:.3f}% ({'✅' if sweep_size_pct >= 0.5 else '❌'})")
                print(f"  Wick %: {wick_pct:.1f}% ({'✅' if wick_pct >= 50 else '❌'})")
                print(f"  Volume ratio: {vol_ratio:.2f}x ({'✅' if vol_ratio >= 2.0 else '❌'})")

                found_samples += 1
                if found_samples >= 5:
                    break
