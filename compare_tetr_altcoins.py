#!/usr/bin/env python3
"""
Compare TETR Original vs Ultra on volatile altcoins

Tests both versions on high-volatility altcoins to see if
TETR Ultra's ADX filter works better in explosive markets.
"""

import sys
from datetime import datetime, timedelta
from tabulate import tabulate

from engine.backtester import Backtester
from strategies.tetr_strategy import TETRStrategy
from strategies.tetr_ultra import TETRUltraStrategy


# Configuration
VOLATILE_ALTCOINS = [
    'AVAXUSDT',   # Avalanche - high volatility
    'LINKUSDT',   # Chainlink - strong trends
    'DOTUSDT',    # Polkadot - good volume
    'ADAUSDT',    # Cardano - large cap alt
    'ATOMUSDT',   # Cosmos - volatile
]

TIMEFRAME = '15m'
DAYS_BACK = 60
INITIAL_BALANCE = 10000


def test_strategy(strategy, strategy_name, symbol):
    """Run backtest on a single symbol"""
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=DAYS_BACK)

        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')

        # Run backtest
        backtester = Backtester(
            strategy=strategy,
            symbol=symbol,
            timeframe=TIMEFRAME,
            start_date=start_str,
            end_date=end_str,
            initial_balance=INITIAL_BALANCE,
            data_dir='./data/binance',
            use_cache=True
        )

        results = backtester.run()
        metrics = results['metrics']

        return {
            'success': True,
            'return': metrics['total_return_pct'],
            'trades': metrics['total_trades'],
            'win_rate': metrics['win_rate_pct'],
            'profit_factor': metrics.get('profit_factor', 0),
            'sharpe': metrics.get('sharpe_ratio', 0),
            'max_dd': metrics.get('max_drawdown_pct', 0),
        }

    except Exception as e:
        print(f"❌ Error testing {strategy_name} on {symbol}: {e}")
        return {'success': False, 'error': str(e)}


def main():
    print("=" * 80)
    print("⚔️  TETR ORIGINAL vs ULTRA - VOLATILE ALTCOINS TEST")
    print("=" * 80)
    print()
    print(f"Testing on high-volatility altcoins:")
    print(f"  Pairs: {', '.join(VOLATILE_ALTCOINS)}")
    print(f"  Timeframe: {TIMEFRAME}")
    print(f"  Period: Last {DAYS_BACK} days")
    print()
    print("Why altcoins?")
    print("  ✅ SOL improved +5.56% with Ultra (more volatile)")
    print("  ✅ ADX filter works better in strong trends")
    print("  ✅ Altcoins have more explosive moves than BTC/ETH")
    print("=" * 80)
    print()

    all_results = []

    for symbol in VOLATILE_ALTCOINS:
        print("=" * 80)
        print(f"📊 Testing {symbol}")
        print("=" * 80)
        print()

        # Test original
        print(f"🔵 TETR Original on {symbol}...")
        orig_strategy = TETRStrategy()
        orig_result = test_strategy(orig_strategy, "TETR Original", symbol)

        # Test ultra
        print(f"🟢 TETR Ultra on {symbol}...")
        ultra_strategy = TETRUltraStrategy()
        ultra_result = test_strategy(ultra_strategy, "TETR Ultra", symbol)

        if orig_result['success'] and ultra_result['success']:
            improvement = ultra_result['return'] - orig_result['return']

            all_results.append({
                'pair': symbol,
                'orig_return': orig_result['return'],
                'ultra_return': ultra_result['return'],
                'improvement': improvement,
                'orig_trades': orig_result['trades'],
                'ultra_trades': ultra_result['trades'],
                'orig_wr': orig_result['win_rate'],
                'ultra_wr': ultra_result['win_rate'],
                'orig_pf': orig_result['profit_factor'],
                'ultra_pf': ultra_result['profit_factor'],
            })

            print(f"\n✅ {symbol} Results:")
            print(f"   Original: {orig_result['return']:+.2f}% ({orig_result['trades']} trades, {orig_result['win_rate']:.1f}% WR, PF {orig_result['profit_factor']:.2f})")
            print(f"   Ultra:    {ultra_result['return']:+.2f}% ({ultra_result['trades']} trades, {ultra_result['win_rate']:.1f}% WR, PF {ultra_result['profit_factor']:.2f})")
            print(f"   Δ:        {improvement:+.2f}%")

        print()

    # Summary
    print("=" * 80)
    print("📊 COMPREHENSIVE COMPARISON - VOLATILE ALTCOINS")
    print("=" * 80)
    print()

    if not all_results:
        print("❌ No successful backtests")
        return

    # Table
    table_data = []
    for r in all_results:
        table_data.append([
            r['pair'],
            f"{r['orig_return']:+.2f}%",
            f"{r['ultra_return']:+.2f}%",
            f"{r['improvement']:+.2f}%",
            r['orig_trades'],
            r['ultra_trades'],
            f"{r['orig_wr']:.1f}%",
            f"{r['ultra_wr']:.1f}%",
            f"{r['orig_pf']:.2f}",
            f"{r['ultra_pf']:.2f}",
        ])

    headers = [
        "Pair", "Orig Return", "Ultra Return", "Δ Return",
        "Orig Trades", "Ultra Trades", "Orig WR", "Ultra WR",
        "Orig PF", "Ultra PF"
    ]

    print(tabulate(table_data, headers=headers, tablefmt='simple'))
    print()

    # Statistics
    print("=" * 80)
    print("📈 SUMMARY")
    print("=" * 80)
    print()

    avg_orig_return = sum(r['orig_return'] for r in all_results) / len(all_results)
    avg_ultra_return = sum(r['ultra_return'] for r in all_results) / len(all_results)
    avg_improvement = avg_ultra_return - avg_orig_return

    avg_orig_wr = sum(r['orig_wr'] for r in all_results) / len(all_results)
    avg_ultra_wr = sum(r['ultra_wr'] for r in all_results) / len(all_results)
    wr_improvement = avg_ultra_wr - avg_orig_wr

    avg_orig_pf = sum(r['orig_pf'] for r in all_results) / len(all_results)
    avg_ultra_pf = sum(r['ultra_pf'] for r in all_results) / len(all_results)
    pf_improvement = avg_ultra_pf - avg_orig_pf

    pairs_better = sum(1 for r in all_results if r['improvement'] > 0)

    print(f"Average Return:")
    print(f"  TETR Original: {avg_orig_return:+.2f}%")
    print(f"  TETR Ultra:    {avg_ultra_return:+.2f}%")
    print(f"  Improvement:   {avg_improvement:+.2f}%")
    print()

    print(f"Average Win Rate:")
    print(f"  TETR Original: {avg_orig_wr:.1f}%")
    print(f"  TETR Ultra:    {avg_ultra_wr:.1f}%")
    print(f"  Improvement:   {wr_improvement:+.1f}%")
    print()

    print(f"Average Profit Factor:")
    print(f"  TETR Original: {avg_orig_pf:.2f}")
    print(f"  TETR Ultra:    {avg_ultra_pf:.2f}")
    print(f"  Improvement:   {pf_improvement:+.2f}")
    print()

    print(f"Pairs with better performance: {pairs_better}/{len(all_results)}")
    print()

    # Verdict
    print("=" * 80)
    print("💡 VERDICT")
    print("=" * 80)
    print()

    if avg_improvement > 1.0 and pairs_better >= len(all_results) * 0.6:
        print(f"✅ TETR Ultra is {avg_improvement:+.2f}% better on volatile altcoins!")
        print(f"   Ultra wins on {pairs_better}/{len(all_results)} pairs.")
        print(f"   ADX filter works well in explosive markets.")
        print()
        print("💡 Recommendation:")
        print("   - Use TETR Ultra for volatile altcoins")
        print("   - Use TETR Original for BTC/ETH (lower volatility)")
    elif avg_improvement > 0:
        print(f"⚠️  TETR Ultra slightly better ({avg_improvement:+.2f}%)")
        print(f"   But only {pairs_better}/{len(all_results)} pairs improved.")
        print(f"   Results are mixed.")
        print()
        print("💡 Recommendation:")
        print("   - Test on longer period (90 days)")
        print("   - Try adjusting ADX threshold")
    else:
        print(f"⚠️  TETR Ultra is {avg_improvement:+.2f}% worse on altcoins")
        print(f"   Only {pairs_better}/{len(all_results)} pairs improved.")
        print()
        print("💡 Recommendation:")
        print("   - Try different timeframe (1h)")
        print("   - Lower ADX threshold (20 instead of 25)")
        print("   - Period may have been too lateral")

    print()

    # Best performers
    best_improvements = sorted(all_results, key=lambda x: x['improvement'], reverse=True)[:3]
    print("🏆 Top 3 Improvements:")
    for i, r in enumerate(best_improvements, 1):
        print(f"   {i}. {r['pair']}: {r['improvement']:+.2f}% ({r['orig_return']:+.2f}% → {r['ultra_return']:+.2f}%)")
    print()

    worst_improvements = sorted(all_results, key=lambda x: x['improvement'])[:3]
    print("⚠️  Top 3 Declines:")
    for i, r in enumerate(worst_improvements, 1):
        print(f"   {i}. {r['pair']}: {r['improvement']:+.2f}% ({r['orig_return']:+.2f}% → {r['ultra_return']:+.2f}%)")
    print()


if __name__ == '__main__':
    main()
