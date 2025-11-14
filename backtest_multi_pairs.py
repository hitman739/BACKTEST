#!/usr/bin/env python3
"""
Multi-Pair Backtest - TETR Strategy

Tests TETR on multiple pairs with real Binance data
Designed to run on Mac with proper error handling
"""

import sys
from datetime import datetime, timedelta
from engine.backtester import Backtester
from strategies.tetr_strategy import TETRStrategy
from engine.metrics import format_metrics_table
import pandas as pd

# Configuration
PAIRS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
TIMEFRAME = '15m'  # Better signals than 5m
DAYS_BACK = 60
INITIAL_BALANCE = 10000

# Calculate dates
end_date = datetime.now()
start_date = end_date - timedelta(days=DAYS_BACK)
start_str = start_date.strftime('%Y-%m-%d')
end_str = end_date.strftime('%Y-%m-%d')

print("="*80)
print("🚀 MULTI-PAIR BACKTEST - TETR STRATEGY")
print("="*80)
print(f"\nConfiguration:")
print(f"  Strategy:   Triple EMA Trend Rider (TETR)")
print(f"  Timeframe:  {TIMEFRAME}")
print(f"  Period:     {start_str} to {end_str} ({DAYS_BACK} days)")
print(f"  Pairs:      {', '.join(PAIRS)}")
print(f"  Balance:    ${INITIAL_BALANCE:,}")
print(f"\nNote: Using 15m timeframe for better signal quality")
print("="*80)

def test_pair(symbol):
    """Test TETR on a single pair"""

    print(f"\n{'='*80}")
    print(f"📊 Testing {symbol}")
    print(f"{'='*80}")

    try:
        # Create strategy instance
        strategy = TETRStrategy()

        # Create backtester
        backtester = Backtester(
            strategy=strategy,
            symbol=symbol,
            timeframe=TIMEFRAME,
            start_date=start_str,
            end_date=end_str,
            initial_balance=INITIAL_BALANCE,
            leverage=1.0,
            maker_fee=0.0002,
            taker_fee=0.0004,
            slippage_bps=2.0,
            data_dir='./data/binance',
            use_cache=True
        )

        # Run backtest
        print(f"\n⏳ Running backtest for {symbol}...")
        results = backtester.run()

        # Show results
        print(f"\n📊 Results for {symbol}:")
        print(format_metrics_table(results['metrics']))

        # Trade summary
        trades_df = results['trades']
        if len(trades_df) > 0:
            print(f"\n📈 Trade Summary:")
            print(f"  Total trades: {len(trades_df)}")
            print(f"  Winners: {len(trades_df[trades_df['pnl'] > 0])}")
            print(f"  Losers: {len(trades_df[trades_df['pnl'] <= 0])}")

            # Best/worst trades
            best = trades_df.nlargest(1, 'pnl').iloc[0]
            worst = trades_df.nsmallest(1, 'pnl').iloc[0]

            print(f"\n  Best trade:  ${best['pnl']:.2f} on {best['entry_time']}")
            print(f"  Worst trade: ${worst['pnl']:.2f} on {worst['entry_time']}")
        else:
            print(f"\n⚠️  No trades executed for {symbol}")

        return {
            'symbol': symbol,
            'success': True,
            'results': results,
            'metrics': results['metrics'],
            'trades': trades_df
        }

    except Exception as e:
        print(f"\n❌ Error testing {symbol}: {e}")
        import traceback
        traceback.print_exc()

        return {
            'symbol': symbol,
            'success': False,
            'error': str(e)
        }

def main():
    """Run backtest on all pairs"""

    all_results = []

    # Test each pair
    for symbol in PAIRS:
        result = test_pair(symbol)
        all_results.append(result)

        # Small pause between pairs
        import time
        time.sleep(1)

    # Generate comparison
    print(f"\n{'='*80}")
    print("📊 MULTI-PAIR COMPARISON")
    print(f"{'='*80}")

    successful_results = [r for r in all_results if r['success']]

    if not successful_results:
        print("\n❌ No successful backtests to compare")
        return

    # Create comparison table
    comparison_data = []
    for result in successful_results:
        metrics = result['metrics']
        trades = result['trades']

        comparison_data.append({
            'Pair': result['symbol'],
            'Return %': f"{metrics['total_return_pct']:.2f}%",
            'Trades': metrics['total_trades'],
            'Win Rate': f"{metrics['win_rate_pct']:.1f}%",
            'Profit Factor': f"{metrics['profit_factor']:.2f}",
            'Sharpe': f"{metrics['sharpe_ratio']:.2f}",
            'Max DD': f"{metrics['max_drawdown_pct']:.1f}%",
            'Avg R': f"{metrics['avg_r_multiple']:.2f}",
            'Final $': f"${metrics['final_equity']:.2f}",
        })

    # Create DataFrame
    df = pd.DataFrame(comparison_data)
    df['Return_numeric'] = df['Return %'].str.rstrip('%').astype(float)
    df = df.sort_values('Return_numeric', ascending=False)
    df = df.drop('Return_numeric', axis=1)

    print("\n" + df.to_string(index=False))

    # Summary statistics
    print(f"\n{'='*80}")
    print("📈 SUMMARY")
    print(f"{'='*80}")

    total_trades = sum([r['metrics']['total_trades'] for r in successful_results])
    profitable_pairs = len([r for r in successful_results if r['metrics']['total_return_pct'] > 0])

    print(f"\nPairs tested: {len(successful_results)}")
    print(f"Profitable pairs: {profitable_pairs}/{len(successful_results)}")
    print(f"Total trades executed: {total_trades}")

    # Best performing pair
    if comparison_data:
        best_pair = df.iloc[0]
        print(f"\n🏆 Best Performer: {best_pair['Pair']}")
        print(f"   Return: {best_pair['Return %']}")
        print(f"   Final Equity: {best_pair['Final $']}")
        print(f"   Sharpe: {best_pair['Sharpe']}")

    # Average metrics across all pairs
    avg_return = sum([r['metrics']['total_return_pct'] for r in successful_results]) / len(successful_results)
    avg_sharpe = sum([r['metrics']['sharpe_ratio'] for r in successful_results]) / len(successful_results)
    avg_wr = sum([r['metrics']['win_rate_pct'] for r in successful_results]) / len(successful_results)

    print(f"\n📊 Average Metrics Across All Pairs:")
    print(f"   Avg Return: {avg_return:.2f}%")
    print(f"   Avg Sharpe: {avg_sharpe:.2f}")
    print(f"   Avg Win Rate: {avg_wr:.1f}%")

    # Recommendations
    print(f"\n{'='*80}")
    print("💡 RECOMMENDATIONS")
    print(f"{'='*80}")

    if profitable_pairs == len(successful_results):
        print("\n✅ All pairs profitable! TETR is robust across different markets.")
    elif profitable_pairs > 0:
        print(f"\n⚠️  {profitable_pairs}/{len(successful_results)} pairs profitable.")
        print("   Consider focusing on profitable pairs or optimizing parameters.")
    else:
        print("\n❌ No pairs profitable in this period.")
        print("   Market conditions may not favor trend following.")
        print("   Consider:")
        print("     - Testing different time periods")
        print("     - Adding ADX filter (trend strength)")
        print("     - Adjusting parameters")

    print(f"\n{'='*80}")
    print("✅ BACKTEST COMPLETE")
    print(f"{'='*80}")
    print("\nData saved to:")
    for result in successful_results:
        print(f"  - reports/tetr_{result['symbol']}_{TIMEFRAME}_*/")

if __name__ == "__main__":
    main()
