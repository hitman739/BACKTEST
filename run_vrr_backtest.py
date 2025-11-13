#!/usr/bin/env python3
"""
Run VRR Strategy Backtest on SOLUSDT 1m

This script runs the Volatility Rejection Reversal strategy
on Solana futures with 1-minute candles.
"""

import sys
from datetime import datetime
from engine.backtester import Backtester
from strategies.vrr_strategy import VRRStrategy
from engine.metrics import format_metrics_table
from engine.reporter import generate_report


def main():
    print("=" * 70)
    print("VOLATILITY REJECTION REVERSAL (VRR) - BACKTEST")
    print("=" * 70)
    print()

    # Configuration
    config = {
        'symbol': 'SOLUSDT',
        'timeframe': '1m',
        'start_date': '2024-10-01',
        'end_date': '2024-11-13',
        'initial_balance': 10000.0,
        'leverage': 10.0,  # SOL can handle higher leverage
        'maker_fee': 0.0002,
        'taker_fee': 0.0004,
        'slippage_bps': 3.0,  # Slightly higher for 1m
    }

    print("Configuration:")
    print(f"  Symbol:       {config['symbol']}")
    print(f"  Timeframe:    {config['timeframe']}")
    print(f"  Period:       {config['start_date']} to {config['end_date']}")
    print(f"  Equity:       ${config['initial_balance']:,.2f}")
    print(f"  Leverage:     {config['leverage']}x")
    print(f"  Maker Fee:    {config['maker_fee']*100:.3f}%")
    print(f"  Taker Fee:    {config['taker_fee']*100:.3f}%")
    print(f"  Slippage:     {config['slippage_bps']} bps")
    print()

    # Create strategy instance
    print("Initializing VRR Strategy...")
    strategy = VRRStrategy()
    print(f"  Strategy: {strategy.name}")
    print()

    # Create backtester
    print("Creating backtester...")
    backtester = Backtester(
        strategy=strategy,
        symbol=config['symbol'],
        timeframe=config['timeframe'],
        start_date=config['start_date'],
        end_date=config['end_date'],
        initial_balance=config['initial_balance'],
        leverage=config['leverage'],
        maker_fee=config['maker_fee'],
        taker_fee=config['taker_fee'],
        slippage_bps=config['slippage_bps'],
        data_dir='./data/binance'
    )

    # Run backtest
    print("Running backtest...")
    print("-" * 70)
    try:
        results = backtester.run()
        print("-" * 70)
        print()

        # Generate report
        report_name = f"vrr_{config['symbol']}_{config['timeframe']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        generate_report(
            run_id=report_name,
            metrics=results['metrics'],
            config=results['config'],
            trades_df=results['trades'],
            equity_curve_df=results['equity_curve'],
            report_dir='./reports'
        )

        # Display results
        print()
        print("=" * 70)
        print("BACKTEST RESULTS")
        print("=" * 70)
        print(format_metrics_table(results['metrics']))
        print("=" * 70)
        print()

        # Additional VRR-specific analysis
        if len(results['trades']) > 0:
            print("=" * 70)
            print("VRR-SPECIFIC ANALYSIS")
            print("=" * 70)

            trades_df = results['trades']

            # Group by exit reason
            if 'exit_reason' in trades_df.columns:
                print("\nExit Reasons Distribution:")
                exit_counts = trades_df['exit_reason'].value_counts()
                for reason, count in exit_counts.items():
                    pct = (count / len(trades_df)) * 100
                    print(f"  {reason:20s}: {count:3d} trades ({pct:5.1f}%)")

            # Performance by setup quality
            if 'setup_quality' in trades_df.columns:
                print("\nPerformance by Setup Quality:")
                for quality in ['extreme', 'high', 'moderate']:
                    quality_trades = trades_df[trades_df['setup_quality'] == quality]
                    if len(quality_trades) > 0:
                        avg_pnl = quality_trades['net_pnl'].mean()
                        win_rate = (quality_trades['net_pnl'] > 0).sum() / len(quality_trades) * 100
                        avg_r = quality_trades['r_multiple'].mean() if 'r_multiple' in quality_trades else 0
                        print(f"  {quality:10s}: {len(quality_trades):3d} trades, "
                              f"Win Rate: {win_rate:5.1f}%, "
                              f"Avg PnL: ${avg_pnl:7.2f}, "
                              f"Avg R: {avg_r:5.2f}")

            # Time analysis
            if 'entry_time' in trades_df.columns:
                print("\nPerformance by Hour (UTC):")
                trades_df['hour'] = pd.to_datetime(trades_df['entry_time']).dt.hour
                hourly_perf = trades_df.groupby('hour')['net_pnl'].agg(['count', 'mean'])
                hourly_perf = hourly_perf[hourly_perf['count'] > 0].sort_values('mean', ascending=False)
                print(hourly_perf.head(10).to_string())

            print("=" * 70)

        print()
        print(f"✓ Reports saved to: reports/{report_name}/")
        print()

        return 0

    except Exception as e:
        print()
        print(f"✗ Backtest failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    import pandas as pd  # Import here for time analysis
    sys.exit(main())
