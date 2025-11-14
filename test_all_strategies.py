#!/usr/bin/env python3
"""
Test All Custom Strategies

Tests all 5 custom strategies on the same dataset and compares results
"""

from datetime import datetime
from engine.backtester import Backtester
from engine.metrics import format_metrics_table
import pandas as pd

# Import all strategies
from strategies.vcb_strategy import VCBStrategy
from strategies.mre_strategy import MREStrategy
from strategies.tetr_strategy import TETRStrategy
from strategies.vsm_strategy import VSMStrategy
from strategies.srb_strategy import SRBStrategy

def test_strategy(strategy, name):
    """Test a single strategy and return results"""

    print(f"\n{'='*70}")
    print(f"Testing: {name}")
    print(f"{'='*70}")

    backtester = Backtester(
        strategy=strategy,
        symbol='BTCUSDT',
        timeframe='5m',
        start_date='2024-08-01',
        end_date='2024-09-29',
        initial_balance=10000,
        leverage=1.0,
        data_dir='./data/binance',
        use_cache=True
    )

    results = backtester.run()

    print(f"\n📊 Results:")
    print(format_metrics_table(results['metrics']))

    return {
        'name': name,
        'results': results,
        'metrics': results['metrics']
    }

def main():
    """Test all strategies and compare"""

    print("="*70)
    print("🎯 TESTING ALL CUSTOM STRATEGIES")
    print("="*70)
    print("\nDataset: BTCUSDT 5m (Aug 1 - Sep 29, 2024)")
    print("Initial Balance: $10,000")
    print("\nStrategies to test:")
    print("  1. VCB  - Volatility Compression Breakout")
    print("  2. MRE  - Mean Reversion Extreme")
    print("  3. TETR - Triple EMA Trend Rider")
    print("  4. VSM  - Volume Spike Momentum")
    print("  5. SRB  - Support Resistance Bounce")
    print("\nStarting tests...\n")

    # Test all strategies
    strategies = [
        (VCBStrategy(), "VCB - Volatility Compression Breakout"),
        (MREStrategy(), "MRE - Mean Reversion Extreme"),
        (TETRStrategy(), "TETR - Triple EMA Trend Rider"),
        (VSMStrategy(), "VSM - Volume Spike Momentum"),
        (SRBStrategy(), "SRB - Support Resistance Bounce"),
    ]

    all_results = []

    for strategy, name in strategies:
        try:
            result = test_strategy(strategy, name)
            all_results.append(result)
        except Exception as e:
            print(f"\n❌ Error testing {name}: {e}")
            import traceback
            traceback.print_exc()

    # Generate comparison table
    print("\n" + "="*70)
    print("📊 STRATEGY COMPARISON")
    print("="*70)

    comparison_data = []
    for result in all_results:
        metrics = result['metrics']
        trades_df = result['results']['trades']

        comparison_data.append({
            'Strategy': result['name'].split(' - ')[0],
            'Return %': f"{metrics['total_return_pct']:.2f}%",
            'Trades': metrics['total_trades'],
            'Win Rate': f"{metrics['win_rate_pct']:.1f}%",
            'Profit Factor': f"{metrics['profit_factor']:.2f}",
            'Sharpe': f"{metrics['sharpe_ratio']:.2f}",
            'Max DD': f"{metrics['max_drawdown_pct']:.1f}%",
            'Avg R': f"{metrics['avg_r_multiple']:.2f}",
            'Final $': f"${metrics['final_equity']:.2f}",
        })

    # Create DataFrame and sort by return
    df = pd.DataFrame(comparison_data)
    df['Return_numeric'] = df['Return %'].str.rstrip('%').astype(float)
    df = df.sort_values('Return_numeric', ascending=False)
    df = df.drop('Return_numeric', axis=1)

    print("\n" + df.to_string(index=False))

    # Find best strategy
    print("\n" + "="*70)
    print("🏆 RANKINGS")
    print("="*70)

    # Best by return
    best_return = df.iloc[0]
    print(f"\n🥇 Best Return: {best_return['Strategy']}")
    print(f"   Return: {best_return['Return %']}")
    print(f"   Final Equity: {best_return['Final $']}")

    # Best by win rate
    df_sorted_wr = df.copy()
    df_sorted_wr['WR_numeric'] = df_sorted_wr['Win Rate'].str.rstrip('%').astype(float)
    df_sorted_wr = df_sorted_wr.sort_values('WR_numeric', ascending=False)
    best_wr = df_sorted_wr.iloc[0]
    print(f"\n📈 Best Win Rate: {best_wr['Strategy']}")
    print(f"   Win Rate: {best_wr['Win Rate']}")
    print(f"   Return: {best_wr['Return %']}")

    # Best by Sharpe
    df_sorted_sharpe = df.copy()
    df_sorted_sharpe['Sharpe_numeric'] = df_sorted_sharpe['Sharpe'].astype(float)
    df_sorted_sharpe = df_sorted_sharpe.sort_values('Sharpe_numeric', ascending=False)
    best_sharpe = df_sorted_sharpe.iloc[0]
    print(f"\n⚡ Best Risk-Adjusted (Sharpe): {best_sharpe['Strategy']}")
    print(f"   Sharpe: {best_sharpe['Sharpe']}")
    print(f"   Return: {best_sharpe['Return %']}")

    # Lowest drawdown
    df_sorted_dd = df.copy()
    df_sorted_dd['DD_numeric'] = df_sorted_dd['Max DD'].str.rstrip('%').astype(float)
    df_sorted_dd = df_sorted_dd.sort_values('DD_numeric', ascending=True)
    best_dd = df_sorted_dd.iloc[0]
    print(f"\n🛡️  Lowest Drawdown: {best_dd['Strategy']}")
    print(f"   Max DD: {best_dd['Max DD']}")
    print(f"   Return: {best_dd['Return %']}")

    # Trade frequency
    df_sorted_trades = df.copy()
    df_sorted_trades['Trades_numeric'] = df_sorted_trades['Trades'].astype(int)
    df_sorted_trades = df_sorted_trades.sort_values('Trades_numeric', ascending=False)
    most_active = df_sorted_trades.iloc[0]
    print(f"\n🔥 Most Active: {most_active['Strategy']}")
    print(f"   Trades: {most_active['Trades']}")
    print(f"   Avg per day: {int(most_active['Trades'])/60:.1f}")

    # Summary
    print("\n" + "="*70)
    print("💡 SUMMARY")
    print("="*70)

    profitable = len([r for r in comparison_data if float(r['Return %'].rstrip('%')) > 0])
    print(f"\nProfitable strategies: {profitable}/{len(all_results)}")

    if profitable > 0:
        print(f"\n✅ Winner: {best_return['Strategy']}")
        print(f"   This strategy would turn $10,000 into {best_return['Final $']}")
    else:
        print("\n⚠️  All strategies lost money in this period")
        print("   Market conditions may not have been favorable")
        print("   Consider:")
        print("     - Testing on different time periods")
        print("     - Optimizing parameters")
        print("     - Adding market regime filters")

    print("\n" + "="*70)
    print("✅ TESTING COMPLETE")
    print("="*70)

if __name__ == "__main__":
    main()
