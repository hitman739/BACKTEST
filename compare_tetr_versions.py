#!/usr/bin/env python3
"""
Compare TETR Original vs TETR Ultra

Tests both versions on the same data to see improvement
"""

from engine.backtester import Backtester
from strategies.tetr_strategy import TETRStrategy
from strategies.tetr_ultra import TETRUltraStrategy
from engine.metrics import format_metrics_table
import pandas as pd
from datetime import datetime, timedelta

# Configuration
PAIRS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
TIMEFRAME = '15m'
DAYS_BACK = 60

# Calculate dates
end_date = datetime.now()
start_date = end_date - timedelta(days=DAYS_BACK)
start_str = start_date.strftime('%Y-%m-%d')
end_str = end_date.strftime('%Y-%m-%d')

print("="*80)
print("⚔️  TETR ORIGINAL vs TETR ULTRA")
print("="*80)
print(f"\nTesting both versions on:")
print(f"  Pairs: {', '.join(PAIRS)}")
print(f"  Timeframe: {TIMEFRAME}")
print(f"  Period: {start_str} to {end_str}")
print("\nTETR Ultra improvements:")
print("  ✅ ADX filter (ADX > 25) - only strong trends")
print("  ✅ Wider stops (0.8 ATR vs 0.5 ATR) - less whipsaws")
print("  ✅ Faster breakeven (0.75R vs 1R) - protect capital sooner")
print("  ✅ Tighter EMAs (8/21/55 vs 9/21/55)")
print("  ✅ More lenient pullback (0.5% vs 0.3%)")
print("="*80)

def test_strategy(strategy, name, symbol):
    """Test a strategy on a pair"""

    try:
        backtester = Backtester(
            strategy=strategy,
            symbol=symbol,
            timeframe=TIMEFRAME,
            start_date=start_str,
            end_date=end_str,
            initial_balance=10000,
            data_dir='./data/binance',
            use_cache=True
        )

        results = backtester.run()

        return {
            'success': True,
            'name': name,
            'symbol': symbol,
            'metrics': results['metrics'],
            'trades': results['trades']
        }

    except Exception as e:
        print(f"❌ Error testing {name} on {symbol}: {e}")
        return {
            'success': False,
            'name': name,
            'symbol': symbol,
            'error': str(e)
        }

def main():
    all_results = []

    for symbol in PAIRS:
        print(f"\n{'='*80}")
        print(f"📊 Testing {symbol}")
        print(f"{'='*80}")

        # Test TETR Original
        print(f"\n🔵 TETR Original on {symbol}...")
        original = test_strategy(TETRStrategy(), "TETR Original", symbol)
        all_results.append(original)

        # Test TETR Ultra
        print(f"🟢 TETR Ultra on {symbol}...")
        ultra = test_strategy(TETRUltraStrategy(), "TETR Ultra", symbol)
        all_results.append(ultra)

        if original['success'] and ultra['success']:
            # Quick comparison
            orig_return = original['metrics']['total_return_pct']
            ultra_return = ultra['metrics']['total_return_pct']
            improvement = ultra_return - orig_return

            print(f"\n📊 {symbol} Comparison:")
            print(f"   Original: {orig_return:+.2f}%")
            print(f"   Ultra:    {ultra_return:+.2f}%")
            print(f"   Improvement: {improvement:+.2f}%")

    # Generate comprehensive comparison
    print(f"\n{'='*80}")
    print("📊 COMPREHENSIVE COMPARISON")
    print(f"{'='*80}")

    successful = [r for r in all_results if r['success']]

    if not successful:
        print("\n❌ No successful backtests")
        return

    # Group by version
    original_results = [r for r in successful if 'Original' in r['name']]
    ultra_results = [r for r in successful if 'Ultra' in r['name']]

    # Create comparison table
    comparison_data = []
    for symbol in PAIRS:
        orig = next((r for r in original_results if r['symbol'] == symbol), None)
        ultra = next((r for r in ultra_results if r['symbol'] == symbol), None)

        if orig and ultra:
            orig_m = orig['metrics']
            ultra_m = ultra['metrics']

            comparison_data.append({
                'Pair': symbol,
                'Orig Return': f"{orig_m['total_return_pct']:.2f}%",
                'Ultra Return': f"{ultra_m['total_return_pct']:.2f}%",
                'Δ Return': f"{ultra_m['total_return_pct'] - orig_m['total_return_pct']:+.2f}%",
                'Orig Trades': orig_m['total_trades'],
                'Ultra Trades': ultra_m['total_trades'],
                'Orig WR': f"{orig_m['win_rate_pct']:.1f}%",
                'Ultra WR': f"{ultra_m['win_rate_pct']:.1f}%",
                'Orig PF': f"{orig_m['profit_factor']:.2f}",
                'Ultra PF': f"{ultra_m['profit_factor']:.2f}",
            })

    df = pd.DataFrame(comparison_data)
    print("\n" + df.to_string(index=False))

    # Summary statistics
    print(f"\n{'='*80}")
    print("📈 SUMMARY")
    print(f"{'='*80}")

    if original_results and ultra_results:
        # Average improvements
        orig_avg_return = sum([r['metrics']['total_return_pct'] for r in original_results]) / len(original_results)
        ultra_avg_return = sum([r['metrics']['total_return_pct'] for r in ultra_results]) / len(ultra_results)
        avg_improvement = ultra_avg_return - orig_avg_return

        orig_avg_wr = sum([r['metrics']['win_rate_pct'] for r in original_results]) / len(original_results)
        ultra_avg_wr = sum([r['metrics']['win_rate_pct'] for r in ultra_results]) / len(ultra_results)
        wr_improvement = ultra_avg_wr - orig_avg_wr

        orig_avg_pf = sum([r['metrics']['profit_factor'] for r in original_results]) / len(original_results)
        ultra_avg_pf = sum([r['metrics']['profit_factor'] for r in ultra_results]) / len(ultra_results)
        pf_improvement = ultra_avg_pf - orig_avg_pf

        print(f"\nAverage Return:")
        print(f"  TETR Original: {orig_avg_return:+.2f}%")
        print(f"  TETR Ultra:    {ultra_avg_return:+.2f}%")
        print(f"  Improvement:   {avg_improvement:+.2f}%")

        print(f"\nAverage Win Rate:")
        print(f"  TETR Original: {orig_avg_wr:.1f}%")
        print(f"  TETR Ultra:    {ultra_avg_wr:.1f}%")
        print(f"  Improvement:   {wr_improvement:+.1f}%")

        print(f"\nAverage Profit Factor:")
        print(f"  TETR Original: {orig_avg_pf:.2f}")
        print(f"  TETR Ultra:    {ultra_avg_pf:.2f}")
        print(f"  Improvement:   {pf_improvement:+.2f}")

        # Count improvements
        better_pairs = 0
        for symbol in PAIRS:
            orig = next((r for r in original_results if r['symbol'] == symbol), None)
            ultra = next((r for r in ultra_results if r['symbol'] == symbol), None)
            if orig and ultra:
                if ultra['metrics']['total_return_pct'] > orig['metrics']['total_return_pct']:
                    better_pairs += 1

        print(f"\nPairs with better performance: {better_pairs}/{len(PAIRS)}")

    print(f"\n{'='*80}")
    print("💡 VERDICT")
    print(f"{'='*80}")

    if avg_improvement > 0:
        print(f"\n✅ TETR Ultra is {avg_improvement:.2f}% better on average!")
        print(f"   ADX filter and wider stops are working.")
    else:
        print(f"\n⚠️  TETR Ultra is {avg_improvement:.2f}% worse")
        print(f"   Optimizations may not suit this market period.")
        print(f"   Try:")
        print(f"     - Different timeframe (1h)")
        print(f"     - Different ADX threshold")
        print(f"     - Different period (market may be lateral)")

    print(f"\n{'='*80}")

if __name__ == "__main__":
    main()
