#!/usr/bin/env python3
"""
Compare Mean Reversion Strategy Variants

Tests three mean reversion profiles:
1. Shallow Revert - Conservative, tight stops, high winrate
2. Session Revert - Intermediate, session VWAP targeting
3. Deep Panic Revert - Aggressive, extreme event trading

All with realistic fees, leverage, and regime filters.
"""

import pandas as pd
from datetime import datetime, timedelta
from engine.backtester import Backtester
from strategies.shallow_revert import ShallowRevertStrategy
from strategies.session_revert import SessionRevertStrategy
from strategies.deep_panic_revert import DeepPanicRevertStrategy

# Test configuration
PAIRS = {
    'BTCUSDT': {'volatility': 'medium', 'liquidity': 'excellent'},
    'ETHUSDT': {'volatility': 'medium', 'liquidity': 'excellent'},
    'SOLUSDT': {'volatility': 'high', 'liquidity': 'excellent'},
}

STRATEGIES = {
    'Shallow Revert': {
        'class': ShallowRevertStrategy,
        'description': 'Conservative, tight stops',
        'expected_winrate': 0.70,
        'expected_sharpe': 1.0,
    },
    'Session Revert': {
        'class': SessionRevertStrategy,
        'description': 'Intermediate, VWAP targeting',
        'expected_winrate': 0.65,
        'expected_sharpe': 0.75,
    },
    'Deep Panic Revert': {
        'class': DeepPanicRevertStrategy,
        'description': 'Aggressive, extreme events',
        'expected_winrate': 0.60,
        'expected_sharpe': 0.55,
    },
}

# Backtesting parameters
TIMEFRAME = '1m'  # Mean reversion works best on lower timeframes
DAYS_BACK = 30  # Last 30 days
INITIAL_BALANCE = 10000
LEVERAGE = 5.0  # Conservative leverage for mean reversion
TAKER_FEE = 0.0006  # 0.06% (Binance futures without BNB)
SLIPPAGE_BPS = 3.0  # 0.03% slippage

# Calculate date range
end_date = datetime.now()
start_date = end_date - timedelta(days=DAYS_BACK)
start_str = start_date.strftime('%Y-%m-%d')
end_str = end_date.strftime('%Y-%m-%d')


def format_pct(value, decimals=2):
    """Format percentage with color"""
    if value > 0:
        return f"+{value:.{decimals}f}%"
    return f"{value:.{decimals}f}%"


def format_number(value, decimals=2):
    """Format number with thousands separator"""
    return f"{value:,.{decimals}f}"


def run_backtest(strategy_class, symbol, timeframe, start_str, end_str):
    """Run a single backtest"""
    try:
        strategy = strategy_class()

        backtester = Backtester(
            strategy=strategy,
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_str,
            end_date=end_str,
            initial_balance=INITIAL_BALANCE,
            leverage=LEVERAGE,
            maker_fee=0.0002,
            taker_fee=TAKER_FEE,
            slippage_bps=SLIPPAGE_BPS,
            data_dir='./data/binance',
            use_cache=True
        )

        results = backtester.run()
        return results

    except Exception as e:
        print(f"   ✗ Error: {e}")
        return None


def print_header():
    """Print report header"""
    print("=" * 100)
    print("MEAN REVERSION STRATEGY COMPARISON")
    print("=" * 100)
    print(f"Period: {start_str} to {end_str} ({DAYS_BACK} days)")
    print(f"Initial Balance: ${INITIAL_BALANCE:,}")
    print(f"Leverage: {LEVERAGE}x")
    print(f"Timeframe: {TIMEFRAME}")
    print(f"Fees: {TAKER_FEE*100:.2f}% taker, Slippage: {SLIPPAGE_BPS/100:.2f}%")
    print("=" * 100)
    print()


def print_strategy_results(strategy_name, strategy_config, pair_results):
    """Print results for one strategy across all pairs"""
    print(f"\n{'=' * 100}")
    print(f"STRATEGY: {strategy_name}")
    print(f"{'=' * 100}")
    print(f"Description: {strategy_config['description']}")
    print(f"Expected WinRate: {strategy_config['expected_winrate']*100:.0f}%, Expected Sharpe: {strategy_config['expected_sharpe']:.2f}")
    print(f"{'-' * 100}")

    # Header
    print(f"{'Pair':<12} {'Total%':<10} {'Weekly%':<10} {'Trades':<8} {'WR%':<8} {'PF':<8} {'MaxDD%':<10} {'Sharpe':<8}")
    print(f"{'-' * 100}")

    total_returns = []
    total_trades = []
    total_wins = []

    for pair, results in pair_results.items():
        if results is None:
            print(f"{pair:<12} {'ERROR':<10}")
            continue

        # Extract metrics from results
        metrics = results.get('metrics', {})

        total_ret = metrics.get('total_return_pct', 0.0)
        total_returns.append(total_ret)

        num_trades = metrics.get('total_trades', 0)
        total_trades.append(num_trades)

        winning_trades = metrics.get('winning_trades', 0)
        total_wins.append(winning_trades)

        win_rate = (winning_trades / num_trades * 100) if num_trades > 0 else 0.0
        profit_factor = metrics.get('profit_factor', 0.0)
        max_dd = metrics.get('max_drawdown_pct', 0.0)
        sharpe = metrics.get('sharpe_ratio', 0.0)

        # Calculate weekly return
        days_traded = DAYS_BACK
        weekly_ret = (total_ret / days_traded) * 7 if days_traded > 0 else 0.0

        print(
            f"{pair:<12} "
            f"{format_pct(total_ret, 2):<10} "
            f"{format_pct(weekly_ret, 2):<10} "
            f"{num_trades:<8} "
            f"{win_rate:<8.1f} "
            f"{profit_factor:<8.2f} "
            f"{max_dd:<10.2f} "
            f"{sharpe:<8.2f}"
        )

    # Summary statistics
    print(f"{'-' * 100}")
    avg_return = sum(total_returns) / len(total_returns) if total_returns else 0.0
    avg_weekly = (avg_return / DAYS_BACK) * 7 if DAYS_BACK > 0 else 0.0
    sum_trades = sum(total_trades)
    sum_wins = sum(total_wins)
    avg_wr = (sum_wins / sum_trades * 100) if sum_trades > 0 else 0.0

    print(
        f"{'AVERAGE':<12} "
        f"{format_pct(avg_return, 2):<10} "
        f"{format_pct(avg_weekly, 2):<10} "
        f"{sum_trades:<8} "
        f"{avg_wr:<8.1f}"
    )


def print_comparison_table(all_results):
    """Print side-by-side comparison of all strategies"""
    print(f"\n{'=' * 100}")
    print("STRATEGY COMPARISON SUMMARY")
    print(f"{'=' * 100}")

    print(f"{'Strategy':<20} {'Avg Return%':<15} {'Avg Weekly%':<15} {'Total Trades':<15} {'Avg WR%':<10}")
    print(f"{'-' * 100}")

    strategy_stats = []

    for strategy_name, pair_results in all_results.items():
        total_returns = []
        total_trades = 0
        total_wins = 0

        for pair, results in pair_results.items():
            if results is None:
                continue
            metrics = results.get('metrics', {})
            total_returns.append(metrics.get('total_return_pct', 0.0))
            total_trades += metrics.get('total_trades', 0)
            total_wins += metrics.get('winning_trades', 0)

        avg_return = sum(total_returns) / len(total_returns) if total_returns else 0.0
        avg_weekly = (avg_return / DAYS_BACK) * 7
        avg_wr = (total_wins / total_trades * 100) if total_trades > 0 else 0.0

        strategy_stats.append({
            'name': strategy_name,
            'avg_return': avg_return,
            'avg_weekly': avg_weekly,
            'total_trades': total_trades,
            'avg_wr': avg_wr
        })

        print(
            f"{strategy_name:<20} "
            f"{format_pct(avg_return, 2):<15} "
            f"{format_pct(avg_weekly, 2):<15} "
            f"{total_trades:<15} "
            f"{avg_wr:<10.1f}"
        )

    print(f"{'=' * 100}")

    # Determine best strategy by different metrics
    print("\nBEST PERFORMERS:")
    if strategy_stats:
        best_return = max(strategy_stats, key=lambda x: x['avg_return'])
        best_wr = max(strategy_stats, key=lambda x: x['avg_wr'])

        print(f"  Highest Return: {best_return['name']} ({format_pct(best_return['avg_return'])})")
        print(f"  Highest WinRate: {best_wr['name']} ({best_wr['avg_wr']:.1f}%)")


def main():
    """Run comparison across all strategies and pairs"""
    print_header()

    all_results = {}

    for strategy_name, strategy_config in STRATEGIES.items():
        print(f"\nRunning {strategy_name}...")

        pair_results = {}

        for pair in PAIRS.keys():
            print(f"  Testing {pair}...", end=' ')

            results = run_backtest(
                strategy_config['class'],
                pair,
                TIMEFRAME,
                start_str,
                end_str
            )

            pair_results[pair] = results

            if results:
                metrics = results.get('metrics', {})
                total_ret = metrics.get('total_return_pct', 0.0)
                trades = metrics.get('total_trades', 0)
                print(f"✓ {format_pct(total_ret)} ({trades} trades)")
            else:
                print("✗ Failed")

        all_results[strategy_name] = pair_results

        # Print detailed results for this strategy
        print_strategy_results(strategy_name, strategy_config, pair_results)

    # Print final comparison
    print_comparison_table(all_results)

    print("\n" + "=" * 100)
    print("ANALYSIS COMPLETE")
    print("=" * 100)

    print("\nNOTES:")
    print("  • Mean reversion strategies perform best in ranging/choppy markets")
    print("  • High winrate but lower Sharpe is expected (tolerates drawdown)")
    print("  • Deep Panic Revert should have few trades but high R when it works")
    print("  • Shallow Revert should have more frequent trades with smaller wins")
    print("  • All strategies use regime filters to avoid bad market conditions")
    print()


if __name__ == '__main__':
    main()
