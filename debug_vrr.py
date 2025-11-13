"""
Debug VRR Strategy - Analyze why no trades are generated
"""

import pandas as pd
from engine.data_loader import load_data
from strategies.vrr_strategy import VRRStrategy
from engine.strategy import StrategyContext, StrategyState


def main():
    print("=" * 70)
    print("VRR STRATEGY DEBUG ANALYSIS")
    print("=" * 70)
    print()

    # Load data
    print("Loading SOLUSDT 1m data...")
    df = load_data('SOLUSDT', '1m', '2024-10-01', '2024-11-13')
    print(f"Loaded {len(df)} candles")
    print()

    # Initialize strategy
    strategy = VRRStrategy()

    # Create context
    context = StrategyContext(
        symbol='SOLUSDT',
        timeframe='1m',
        leverage=10.0,
        account_equity=10000.0,
        position_size=0.0,
        data=df
    )

    # Initialize indicators
    print("Computing indicators...")
    df = strategy.initialize(context)
    context.data = df
    print("Done")
    print()

    # Analyze conditions over the dataset
    print("Analyzing entry conditions...")
    print("-" * 70)

    checks = {
        'total_bars': 0,
        'sufficient_data': 0,
        'valid_indicators': 0,
        'volatility_filter_pass': 0,
        'trend_filter_pass': 0,
        'time_filter_pass': 0,
        'directional_move_pass': 0,
        'rsi_extreme': 0,
        'volume_spike': 0,
        'volume_ratio': 0,
        'reversal_candle': 0,
        'volume_divergence': 0,
        'structure_valid': 0,
    }

    state = StrategyState()

    # Check conditions bar by bar
    lookback = max(strategy.lookback, strategy.atr_period_long, 50)

    for idx in range(lookback, min(lookback + 10000, len(df))):  # Check first 10k bars
        bar = df.iloc[idx]
        checks['total_bars'] += 1

        # 1. Sufficient data
        if idx >= lookback:
            checks['sufficient_data'] += 1
        else:
            continue

        # 2. Valid indicators
        if not (pd.isna(bar['atr']) or pd.isna(bar['rsi']) or pd.isna(bar['volume_ma'])):
            checks['valid_indicators'] += 1
        else:
            continue

        # 3. Volatility filter
        if bar['atr'] >= (strategy.atr_vol_mult * bar['atr_long']):
            checks['volatility_filter_pass'] += 1
        else:
            continue

        # 4. Trend filter
        if not pd.isna(bar['ema_20']) and not pd.isna(bar['ema_50']):
            ema_diff_pct = abs(bar['ema_20'] - bar['ema_50']) / bar['close']
            if ema_diff_pct >= 0.005:
                checks['trend_filter_pass'] += 1
            else:
                continue
        else:
            continue

        # 5. Time filter
        if strategy._check_trading_hours(bar):
            checks['time_filter_pass'] += 1
        else:
            continue

        # 6. Directional move
        recent_bars = df.iloc[idx - strategy.lookback + 1:idx + 1]
        directional_move = strategy._calculate_directional_move(recent_bars)
        if directional_move >= (strategy.directional_atr_mult * bar['atr']):
            checks['directional_move_pass'] += 1
        else:
            continue

        # 7. RSI extreme
        is_overbought = bar['rsi'] > strategy.rsi_ob
        is_oversold = bar['rsi'] < strategy.rsi_os
        if is_overbought or is_oversold:
            checks['rsi_extreme'] += 1
        else:
            continue

        # 8. Volume spike
        if bar['volume'] >= (strategy.vol_spike * bar['volume_ma']):
            checks['volume_spike'] += 1
        else:
            continue

        # 9. Volume ratio
        if bar['volume_ratio'] >= strategy.vol_ratio_min:
            checks['volume_ratio'] += 1
        else:
            continue

        # 10. Reversal candle
        wick_quality = strategy._check_reversal_candle(bar, is_overbought)
        if wick_quality['is_reversal']:
            checks['reversal_candle'] += 1
        else:
            continue

        # 11. Volume divergence
        if strategy._check_volume_divergence(recent_bars):
            checks['volume_divergence'] += 1
        else:
            continue

        # 12. Structure
        prev_bar = df.iloc[idx - 1]
        if strategy._validate_structure(bar, prev_bar):
            checks['structure_valid'] += 1
            print(f"\n✓ FULL SETUP DETECTED at bar {idx} ({bar['timestamp']})")
            print(f"  Price: ${bar['close']:.2f}")
            print(f"  RSI: {bar['rsi']:.1f}")
            print(f"  ATR: ${bar['atr']:.4f}")
            print(f"  Volume Ratio: {bar['volume_ratio']:.2f}x")
            print(f"  Wick %: {wick_quality['wick_percentage']*100:.1f}%")
            print(f"  Direction: {'SHORT' if is_overbought else 'LONG'}")

    # Print summary
    print()
    print("=" * 70)
    print("FILTER FUNNEL ANALYSIS")
    print("=" * 70)

    prev_count = checks['total_bars']
    for key, count in checks.items():
        if prev_count > 0:
            pass_rate = (count / prev_count) * 100
            print(f"{key:30s}: {count:6d} ({pass_rate:5.2f}% pass rate)")
        else:
            print(f"{key:30s}: {count:6d}")
        prev_count = count

    print("=" * 70)
    print()

    # Show example bars that almost passed
    print("SAMPLE BARS WITH HIGH ATR (potential setups):")
    print("-" * 70)
    high_atr_bars = df.nlargest(10, 'atr')[['timestamp', 'close', 'atr', 'rsi', 'volume_ratio', 'candle_range']]
    print(high_atr_bars.to_string())
    print()

    print("SAMPLE BARS WITH EXTREME RSI:")
    print("-" * 70)
    extreme_rsi = df[(df['rsi'] > 74) | (df['rsi'] < 26)].head(10)[['timestamp', 'close', 'rsi', 'volume_ratio', 'atr']]
    print(extreme_rsi.to_string())
    print()


if __name__ == '__main__':
    main()
