#!/usr/bin/env python3
"""
Analyze trader by individual strategies

A trader may use multiple strategies:
- Different strategy per symbol (BTC vs SOL)
- Different strategy per market condition (trend vs range)
- Different strategy per time of day

This script separates and analyzes each strategy independently.
"""

import pandas as pd
import json
from pathlib import Path
import sys

def analyze_strategies(trader_address, min_trades_per_strategy=20):
    """Analyze and separate different strategies used by a trader"""

    print("=" * 70)
    print("🔬 MULTI-STRATEGY ANALYSIS")
    print("=" * 70)

    vault_id = trader_address[:10]
    reports_dir = Path(f"reports/reverse_engineering/{vault_id}")

    # Load positions with features
    positions_path = reports_dir / "positions_with_features_complete.parquet"

    if not positions_path.exists():
        # Try alternative
        positions_path = reports_dir / "positions_with_features.parquet"

    if not positions_path.exists():
        print(f"\n❌ No analysis found for {vault_id}")
        print("   Run full analysis first:")
        print(f"   python3 reverse_engineer_vault_complete.py --vault {trader_address}")
        return

    print(f"\n📂 Loading analysis for {vault_id}...")
    df = pd.read_parquet(positions_path)
    print(f"✅ Loaded {len(df)} positions")

    # STRATEGY DETECTION
    print("\n" + "=" * 70)
    print("🔍 DETECTING DIFFERENT STRATEGIES")
    print("=" * 70)

    strategies = []

    # 1. BY SYMBOL
    print("\n📊 Strategy separation by SYMBOL:")
    print("-" * 70)

    if 'symbol' in df.columns:
        by_symbol = df.groupby('symbol').size().sort_values(ascending=False)

        for symbol, count in by_symbol.items():
            if count >= min_trades_per_strategy:
                symbol_df = df[df['symbol'] == symbol]
                win_rate = (symbol_df['is_winner'].sum() / len(symbol_df)) * 100
                avg_holding = symbol_df['holding_time_mins'].mean()
                avg_pnl = symbol_df['pnl'].mean()

                strategies.append({
                    'type': 'symbol',
                    'name': f'{symbol}_strategy',
                    'symbol': symbol,
                    'trades': count,
                    'win_rate': win_rate,
                    'avg_holding_mins': avg_holding,
                    'avg_pnl': avg_pnl,
                    'df': symbol_df
                })

                print(f"\n  {symbol}:")
                print(f"    Trades: {count}")
                print(f"    Win Rate: {win_rate:.1f}%")
                print(f"    Avg Holding: {avg_holding:.0f} mins")
                print(f"    Avg PnL: ${avg_pnl:.2f}")

    # 2. BY HOLDING TIME (different time horizons)
    print("\n⏱️  Strategy separation by HOLDING TIME:")
    print("-" * 70)

    if 'holding_time_mins' in df.columns:
        # Define time horizons
        df['time_horizon'] = pd.cut(
            df['holding_time_mins'],
            bins=[0, 15, 60, 240, 10000],
            labels=['scalp', 'short_term', 'medium_term', 'long_term']
        )

        by_horizon = df.groupby('time_horizon').size()

        for horizon, count in by_horizon.items():
            if count >= min_trades_per_strategy:
                horizon_df = df[df['time_horizon'] == horizon]
                win_rate = (horizon_df['is_winner'].sum() / len(horizon_df)) * 100
                avg_pnl = horizon_df['pnl'].mean()

                strategies.append({
                    'type': 'time_horizon',
                    'name': f'{horizon}_strategy',
                    'horizon': str(horizon),
                    'trades': count,
                    'win_rate': win_rate,
                    'avg_pnl': avg_pnl,
                    'df': horizon_df
                })

                print(f"\n  {horizon}:")
                print(f"    Trades: {count}")
                print(f"    Win Rate: {win_rate:.1f}%")
                print(f"    Avg PnL: ${avg_pnl:.2f}")

    # 3. BY DIRECTION (long vs short bias)
    print("\n📈📉 Strategy separation by DIRECTION:")
    print("-" * 70)

    if 'side' in df.columns:
        by_side = df.groupby('side').size()

        for side, count in by_side.items():
            if count >= min_trades_per_strategy:
                side_df = df[df['side'] == side]
                win_rate = (side_df['is_winner'].sum() / len(side_df)) * 100
                avg_pnl = side_df['pnl'].mean()

                strategies.append({
                    'type': 'direction',
                    'name': f'{side}_strategy',
                    'side': side,
                    'trades': count,
                    'win_rate': win_rate,
                    'avg_pnl': avg_pnl,
                    'df': side_df
                })

                print(f"\n  {side.upper()}:")
                print(f"    Trades: {count}")
                print(f"    Win Rate: {win_rate:.1f}%")
                print(f"    Avg PnL: ${avg_pnl:.2f}")

    # 4. BY MARKET REGIME (if available)
    print("\n🌊 Strategy separation by MARKET REGIME:")
    print("-" * 70)

    if 'trend_regime' in df.columns:
        by_regime = df.groupby('trend_regime').size()

        for regime, count in by_regime.items():
            if count >= min_trades_per_strategy:
                regime_df = df[df['trend_regime'] == regime]
                win_rate = (regime_df['is_winner'].sum() / len(regime_df)) * 100
                avg_pnl = regime_df['pnl'].mean()

                print(f"\n  {regime}:")
                print(f"    Trades: {count}")
                print(f"    Win Rate: {win_rate:.1f}%")
                print(f"    Avg PnL: ${avg_pnl:.2f}")

    # SUMMARY
    print("\n" + "=" * 70)
    print("📋 STRATEGY SUMMARY")
    print("=" * 70)

    print(f"\nTotal distinct strategies detected: {len(strategies)}")

    # Rank strategies by performance
    strategies_sorted = sorted(strategies, key=lambda x: x['win_rate'] * x['trades'], reverse=True)

    print("\n🏆 TOP STRATEGIES (by Win Rate × Volume):")
    print("-" * 70)

    for i, strat in enumerate(strategies_sorted[:5], 1):
        print(f"\n{i}. {strat['name']}")
        print(f"   Type: {strat['type']}")
        print(f"   Trades: {strat['trades']}")
        print(f"   Win Rate: {strat['win_rate']:.1f}%")
        print(f"   Avg PnL: ${strat['avg_pnl']:.2f}")
        print(f"   Score: {strat['win_rate'] * strat['trades']:.0f}")

    # RECOMMENDATION
    print("\n" + "=" * 70)
    print("💡 RECOMMENDATIONS")
    print("=" * 70)

    print("\n1️⃣  FOCUS ON BEST STRATEGY:")
    if strategies_sorted:
        best = strategies_sorted[0]
        print(f"   → {best['name']}")
        print(f"   Re-run analysis filtering by {best['type']}:")

        if best['type'] == 'symbol':
            print(f"\n   python3 reverse_engineer_vault_complete.py \\")
            print(f"     --vault {trader_address} \\")
            print(f"     --symbol {best['symbol']} \\")
            print(f"     --timeframe 5m")

    print("\n2️⃣  ANALYZE EACH STRATEGY SEPARATELY:")
    print("   Extract rules for each strategy independently")
    print("   This gives you multiple strategies to backtest")

    print("\n3️⃣  COMBINE STRATEGIES:")
    print("   Use different strategies for different market conditions")
    print("   Example: Trend-following in uptrend, mean-reversion in range")

    print("\n" + "=" * 70)

    # Save summary
    summary = {
        'trader': trader_address,
        'total_strategies': len(strategies),
        'strategies': [
            {k: v for k, v in s.items() if k != 'df'}
            for s in strategies_sorted
        ]
    }

    summary_path = reports_dir / "strategy_breakdown.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2, default=str)

    print(f"\n💾 Summary saved to: {summary_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 analyze_by_strategy.py <trader_address>")
        print("\nExample:")
        print("  python3 analyze_by_strategy.py 0x8bae3527e5a33fa0cf184f37bc112d071463ab6d")
        sys.exit(1)

    trader = sys.argv[1]
    analyze_strategies(trader)
