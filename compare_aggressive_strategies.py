#!/usr/bin/env python3
"""
Compare Aggressive Strategies - REALISTIC FEES & SLIPPAGE + 10X LEVERAGE

Tests 3 aggressive strategies with REAL market conditions:
- 🔥 10X LEVERAGE (multiplies returns AND losses)
- Binance taker fees: 0.06% per trade
- Realistic slippage: 0.03-0.05%
- Volatile altcoin pairs
- Multiple timeframes

Strategies:
1. Scalper Pro (5m) - Mean reversion scalping, target 2-4% weekly
2. Momentum Hunter (15m) - Breakout trading, target 3-6% weekly
3. Hybrid Alpha (15m) - Balanced hybrid, target 3-5% weekly

Target: 3-5% weekly returns for bot sales (WITH 10X LEVERAGE)
"""

import sys
from datetime import datetime, timedelta
from tabulate import tabulate

from engine.backtester import Backtester
from strategies.scalper_pro import ScalperProStrategy
from strategies.momentum_hunter import MomentumHunterStrategy
from strategies.hybrid_alpha import HybridAlphaStrategy


# ============================================================================
# CONFIGURATION
# ============================================================================

# Pairs - Volatile altcoins with good liquidity
PAIRS = {
    # Best performers from previous tests
    'AVAXUSDT': {'volatility': 'high', 'liquidity': 'excellent'},
    'DOTUSDT': {'volatility': 'medium', 'liquidity': 'excellent'},

    # Additional volatile pairs
    'NEARUSDT': {'volatility': 'high', 'liquidity': 'good'},
    'RNDRUSDT': {'volatility': 'very_high', 'liquidity': 'medium'},
    'PENDLEUSDT': {'volatility': 'very_high', 'liquidity': 'medium'},
}

# Strategy configurations
STRATEGIES = {
    'Scalper Pro': {
        'class': ScalperProStrategy,
        'timeframe': '5m',
        'taker_fee': 0.0006,  # 0.06% - Binance without BNB discount
        'slippage_bps': 5.0,  # 0.05% - 5m has more slippage
        'description': 'RSI mean reversion, 50-80 trades/week, 65-70% WR target'
    },
    'Momentum Hunter': {
        'class': MomentumHunterStrategy,
        'timeframe': '15m',
        'taker_fee': 0.0006,  # 0.06%
        'slippage_bps': 3.0,  # 0.03% - 15m has less slippage
        'description': 'Volume breakouts, 30-40 trades/week, 45-50% WR target'
    },
    'Hybrid Alpha': {
        'class': HybridAlphaStrategy,
        'timeframe': '15m',
        'taker_fee': 0.0006,  # 0.06%
        'slippage_bps': 3.0,  # 0.03%
        'description': 'Mean reversion + momentum, 40-50 trades/week, 55-60% WR target'
    },
}

DAYS_BACK = 60
INITIAL_BALANCE = 10000


# ============================================================================
# BACKTESTING FUNCTIONS
# ============================================================================

def test_strategy(strategy_name, strategy_config, symbol, pair_info):
    """Run backtest on a single strategy/pair combination"""
    try:
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=DAYS_BACK)
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')

        # Initialize strategy
        strategy = strategy_config['class']()
        timeframe = strategy_config['timeframe']

        # Run backtest with REALISTIC fees + LEVERAGE
        backtester = Backtester(
            strategy=strategy,
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_str,
            end_date=end_str,
            initial_balance=INITIAL_BALANCE,
            leverage=10.0,  # 🔥 10X LEVERAGE - multiplies returns AND losses
            maker_fee=0.0004,  # Won't use this (we're takers)
            taker_fee=strategy_config['taker_fee'],  # 0.06% - REALISTIC
            slippage_bps=strategy_config['slippage_bps'],  # REALISTIC slippage
            data_dir='./data/binance',
            use_cache=True
        )

        results = backtester.run()
        metrics = results['metrics']

        # Calculate weekly return
        days = DAYS_BACK
        weeks = days / 7
        total_return = metrics['total_return_pct']
        weekly_return = total_return / weeks if weeks > 0 else 0

        # Calculate costs
        total_trades = metrics['total_trades']
        avg_fee_per_trade = strategy_config['taker_fee'] * 2  # Entry + exit
        avg_slippage_per_trade = strategy_config['slippage_bps'] / 10000 * 2  # Entry + exit
        total_cost_pct = (avg_fee_per_trade + avg_slippage_per_trade) * total_trades

        return {
            'success': True,
            'return': total_return,
            'weekly_return': weekly_return,
            'trades': total_trades,
            'win_rate': metrics['win_rate_pct'],
            'profit_factor': metrics.get('profit_factor', 0),
            'sharpe': metrics.get('sharpe_ratio', 0),
            'max_dd': metrics.get('max_drawdown_pct', 0),
            'total_cost_pct': total_cost_pct,
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def main():
    print("=" * 100)
    print("⚡ AGGRESSIVE STRATEGIES COMPARISON - 10X LEVERAGE + REALISTIC FEES")
    print("=" * 100)
    print()
    print("🎯 Target: 3-5% WEEKLY returns (WITH 10X LEVERAGE)")
    print()
    print("🔥 LEVERAGE: 10X (multiplies both gains AND losses)")
    print()
    print("💰 Real Costs:")
    print("   - Binance Taker Fee: 0.06% per trade (no BNB discount)")
    print("   - Slippage: 0.03-0.05% depending on timeframe")
    print("   - Total cost per round-trip: ~0.18-0.22%")
    print()
    print(f"📊 Testing Period: Last {DAYS_BACK} days ({DAYS_BACK/7:.1f} weeks)")
    print(f"💵 Initial Balance: ${INITIAL_BALANCE:,.0f}")
    print(f"💰 Effective Buying Power: ${INITIAL_BALANCE * 10:,.0f} (with 10x leverage)")
    print()
    print("🪙 Pairs:")
    for symbol, info in PAIRS.items():
        print(f"   - {symbol:12s} (volatility: {info['volatility']}, liquidity: {info['liquidity']})")
    print()
    print("⚙️  Strategies:")
    for name, config in STRATEGIES.items():
        print(f"   - {name:18s} ({config['timeframe']}) - {config['description']}")
    print()
    print("=" * 100)
    print()

    all_results = {}

    # Test each strategy on each pair
    for strategy_name, strategy_config in STRATEGIES.items():
        print("=" * 100)
        print(f"🔥 TESTING: {strategy_name}")
        print("=" * 100)
        print(f"   Timeframe: {strategy_config['timeframe']}")
        print(f"   Fees: {strategy_config['taker_fee']*100:.2f}% taker")
        print(f"   Slippage: {strategy_config['slippage_bps']/100:.2f}%")
        print()

        all_results[strategy_name] = {}

        for symbol, pair_info in PAIRS.items():
            print(f"   Testing {symbol}... ", end='', flush=True)

            result = test_strategy(strategy_name, strategy_config, symbol, pair_info)

            if result['success']:
                all_results[strategy_name][symbol] = result

                # Visual indicator
                weekly = result['weekly_return']
                if weekly >= 3:
                    indicator = "🟢 TARGET HIT"
                elif weekly >= 1:
                    indicator = "🟡 DECENT"
                elif weekly >= 0:
                    indicator = "🟠 MARGINAL"
                else:
                    indicator = "🔴 LOSING"

                print(f"{indicator}")
                print(f"      Return: {result['return']:+.2f}% total, {result['weekly_return']:+.2f}% weekly")
                print(f"      Trades: {result['trades']}, WR: {result['win_rate']:.1f}%, PF: {result['profit_factor']:.2f}")
                print(f"      Costs: {result['total_cost_pct']:.2f}% total fees+slippage")
            else:
                print(f"❌ ERROR: {result['error']}")

            print()

        print()

    # ========================================================================
    # SUMMARY TABLES
    # ========================================================================

    print("=" * 100)
    print("📊 COMPREHENSIVE RESULTS - ALL STRATEGIES & PAIRS")
    print("=" * 100)
    print()

    # Table 1: Returns by strategy and pair
    print("💵 TOTAL RETURNS (%)")
    print("-" * 100)

    table_returns = []
    for symbol in PAIRS.keys():
        row = [symbol]
        for strategy_name in STRATEGIES.keys():
            if symbol in all_results.get(strategy_name, {}):
                ret = all_results[strategy_name][symbol]['return']
                row.append(f"{ret:+.2f}%")
            else:
                row.append("N/A")
        table_returns.append(row)

    # Add averages
    avg_row = ["AVERAGE"]
    for strategy_name in STRATEGIES.keys():
        returns = [all_results[strategy_name][sym]['return']
                  for sym in PAIRS.keys()
                  if sym in all_results.get(strategy_name, {})]
        if returns:
            avg_row.append(f"{sum(returns)/len(returns):+.2f}%")
        else:
            avg_row.append("N/A")
    table_returns.append(avg_row)

    headers = ["Pair"] + list(STRATEGIES.keys())
    print(tabulate(table_returns, headers=headers, tablefmt='simple'))
    print()

    # Table 2: Weekly returns
    print("📅 WEEKLY RETURNS (%) - THIS IS THE KEY METRIC")
    print("-" * 100)

    table_weekly = []
    for symbol in PAIRS.keys():
        row = [symbol]
        for strategy_name in STRATEGIES.keys():
            if symbol in all_results.get(strategy_name, {}):
                weekly = all_results[strategy_name][symbol]['weekly_return']
                if weekly >= 3:
                    row.append(f"🟢 {weekly:+.2f}%")
                elif weekly >= 1:
                    row.append(f"🟡 {weekly:+.2f}%")
                elif weekly >= 0:
                    row.append(f"🟠 {weekly:+.2f}%")
                else:
                    row.append(f"🔴 {weekly:+.2f}%")
            else:
                row.append("N/A")
        table_weekly.append(row)

    # Add averages
    avg_row = ["AVERAGE"]
    for strategy_name in STRATEGIES.keys():
        weeklies = [all_results[strategy_name][sym]['weekly_return']
                   for sym in PAIRS.keys()
                   if sym in all_results.get(strategy_name, {})]
        if weeklies:
            avg_weekly = sum(weeklies) / len(weeklies)
            if avg_weekly >= 3:
                avg_row.append(f"🟢 {avg_weekly:+.2f}%")
            elif avg_weekly >= 1:
                avg_row.append(f"🟡 {avg_weekly:+.2f}%")
            else:
                avg_row.append(f"🔴 {avg_weekly:+.2f}%")
        else:
            avg_row.append("N/A")
    table_weekly.append(avg_row)

    print(tabulate(table_weekly, headers=headers, tablefmt='simple'))
    print()

    # Table 3: Win rates
    print("🎯 WIN RATES (%)")
    print("-" * 100)

    table_wr = []
    for symbol in PAIRS.keys():
        row = [symbol]
        for strategy_name in STRATEGIES.keys():
            if symbol in all_results.get(strategy_name, {}):
                wr = all_results[strategy_name][symbol]['win_rate']
                row.append(f"{wr:.1f}%")
            else:
                row.append("N/A")
        table_wr.append(row)

    # Add averages
    avg_row = ["AVERAGE"]
    for strategy_name in STRATEGIES.keys():
        wrs = [all_results[strategy_name][sym]['win_rate']
              for sym in PAIRS.keys()
              if sym in all_results.get(strategy_name, {})]
        if wrs:
            avg_row.append(f"{sum(wrs)/len(wrs):.1f}%")
        else:
            avg_row.append("N/A")
    table_wr.append(avg_row)

    print(tabulate(table_wr, headers=headers, tablefmt='simple'))
    print()

    # Table 4: Profit factors
    print("💰 PROFIT FACTORS")
    print("-" * 100)

    table_pf = []
    for symbol in PAIRS.keys():
        row = [symbol]
        for strategy_name in STRATEGIES.keys():
            if symbol in all_results.get(strategy_name, {}):
                pf = all_results[strategy_name][symbol]['profit_factor']
                row.append(f"{pf:.2f}")
            else:
                row.append("N/A")
        table_pf.append(row)

    print(tabulate(table_pf, headers=headers, tablefmt='simple'))
    print()

    # ========================================================================
    # FINAL VERDICT
    # ========================================================================

    print("=" * 100)
    print("🏆 FINAL VERDICT - WHICH STRATEGY FOR BOT SALES?")
    print("=" * 100)
    print()

    # Calculate average metrics for each strategy
    strategy_stats = {}
    for strategy_name in STRATEGIES.keys():
        results_list = [all_results[strategy_name][sym]
                       for sym in PAIRS.keys()
                       if sym in all_results.get(strategy_name, {})]

        if results_list:
            strategy_stats[strategy_name] = {
                'avg_weekly': sum(r['weekly_return'] for r in results_list) / len(results_list),
                'avg_return': sum(r['return'] for r in results_list) / len(results_list),
                'avg_wr': sum(r['win_rate'] for r in results_list) / len(results_list),
                'avg_pf': sum(r['profit_factor'] for r in results_list) / len(results_list),
                'profitable_pairs': sum(1 for r in results_list if r['return'] > 0),
                'target_pairs': sum(1 for r in results_list if r['weekly_return'] >= 3),
                'total_pairs': len(results_list),
            }

    # Rank strategies
    ranked = sorted(strategy_stats.items(),
                   key=lambda x: x[1]['avg_weekly'],
                   reverse=True)

    for rank, (strategy_name, stats) in enumerate(ranked, 1):
        print(f"{rank}. {strategy_name}")
        print(f"   Average Weekly Return: {stats['avg_weekly']:+.2f}%")
        print(f"   Average Total Return: {stats['avg_return']:+.2f}%")
        print(f"   Average Win Rate: {stats['avg_wr']:.1f}%")
        print(f"   Average Profit Factor: {stats['avg_pf']:.2f}")
        print(f"   Profitable Pairs: {stats['profitable_pairs']}/{stats['total_pairs']}")
        print(f"   Hitting 3%+ weekly: {stats['target_pairs']}/{stats['total_pairs']} pairs")
        print()

        # Verdict
        if stats['avg_weekly'] >= 3:
            print(f"   ✅ EXCELLENT - Hits 3%+ weekly target!")
        elif stats['avg_weekly'] >= 1.5:
            print(f"   🟡 DECENT - Close to target, may work in better market conditions")
        elif stats['avg_weekly'] >= 0:
            print(f"   🟠 MARGINAL - Profitable but below target")
        else:
            print(f"   🔴 NOT VIABLE - Losing money")

        print()

    # Best pairs for each strategy
    print("🎯 BEST PAIRS FOR EACH STRATEGY:")
    print()
    for strategy_name in STRATEGIES.keys():
        if strategy_name in all_results:
            pairs_sorted = sorted(all_results[strategy_name].items(),
                                 key=lambda x: x[1]['weekly_return'],
                                 reverse=True)
            print(f"{strategy_name}:")
            for symbol, result in pairs_sorted[:3]:
                print(f"   {symbol:12s}: {result['weekly_return']:+.2f}% weekly (WR: {result['win_rate']:.1f}%, PF: {result['profit_factor']:.2f})")
            print()

    print("=" * 100)
    print("💡 RECOMMENDATIONS FOR BOT SALES:")
    print("=" * 100)
    print()

    best_strategy = ranked[0][0]
    best_stats = ranked[0][1]

    if best_stats['avg_weekly'] >= 3:
        print(f"✅ Use '{best_strategy}' for your bot!")
        print(f"   - Achieves {best_stats['avg_weekly']:+.2f}% weekly average")
        print(f"   - {best_stats['avg_wr']:.1f}% win rate (looks good to buyers)")
        print(f"   - Profitable on {best_stats['profitable_pairs']}/{best_stats['total_pairs']} pairs")
        print()
        print("📢 Marketing angle:")
        print(f"   'Proven {best_stats['avg_weekly']:.1f}% weekly returns with {best_stats['avg_wr']:.0f}% win rate'")
    else:
        print(f"⚠️  None of the strategies consistently hit 3%+ weekly in this period")
        print(f"   Best: '{best_strategy}' at {best_stats['avg_weekly']:+.2f}% weekly")
        print()
        print("Options:")
        print("   1. Test on longer period (90 days) to find better market conditions")
        print("   2. Optimize parameters for specific pairs")
        print("   3. Use different timeframes")
        print("   4. Add leverage (RISKY - but increases returns)")
        print("   5. Cherry-pick best performing pair/strategy combos for marketing")

    print()


if __name__ == '__main__':
    main()
