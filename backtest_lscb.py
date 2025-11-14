#!/usr/bin/env python3
"""
Backtest LSCB Strategy

Tests the Liquidity Sweep Compression Breakout strategy on historical data.
"""

import sys
from datetime import datetime, timedelta
from engine.backtester import Backtester
from strategies.lscb_strategy import LSCBStrategy
from engine.reporter import generate_report
from engine.metrics import format_metrics_table

def main():
    """Run LSCB backtest"""

    # Parse arguments
    symbol = sys.argv[1] if len(sys.argv) > 1 else 'BTCUSDT'
    timeframe = sys.argv[2] if len(sys.argv) > 2 else '5m'
    days_back = int(sys.argv[3]) if len(sys.argv) > 3 else 90

    # Calculate dates
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')

    print("=" * 70)
    print("🎯 LSCB STRATEGY BACKTEST")
    print("=" * 70)
    print(f"\nSymbol: {symbol}")
    print(f"Timeframe: {timeframe}")
    print(f"Period: {start_str} to {end_str} ({days_back} days)")
    print(f"Initial Balance: $10,000")
    print(f"Risk per trade: 1%")
    print(f"Leverage: 1x")
    print("\nStrategy Parameters:")
    print("  - Swing lookback: 50 candles")
    print("  - Min swing touches: 3")
    print("  - Sweep wick: ≥50%")
    print("  - Sweep volume: ≥2x MA20")
    print("  - Compression: 2 candles, <0.6 ATR")
    print("  - TP1: 2R (33%)")
    print("  - TP2: 3.5R (33%)")
    print("  - Trailing: 1.5 ATR (33%)")
    print("\n" + "=" * 70)
    print("Loading data and initializing...")
    print("=" * 70)

    # Create strategy
    strategy = LSCBStrategy()

    # Create backtester
    backtester = Backtester(
        strategy=strategy,
        symbol=symbol,
        timeframe=timeframe,
        start_date=start_str,
        end_date=end_str,
        initial_balance=10000,
        leverage=1.0,
        maker_fee=0.0002,
        taker_fee=0.0004,
        slippage_bps=2.0,
        funding_rate=0.0001,
        data_dir="./data/binance"
    )

    # Run backtest
    results = backtester.run()

    # Print results
    print("\n" + "=" * 70)
    print("📊 BACKTEST RESULTS")
    print("=" * 70)
    print(format_metrics_table(results['metrics']))
    print("=" * 70)

    # Generate detailed report
    report_name = f"lscb_{symbol}_{timeframe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    generate_report(
        run_id=report_name,
        metrics=results['metrics'],
        config=results['config'],
        trades_df=results['trades'],
        equity_curve_df=results['equity_curve'],
        report_dir="./reports"
    )

    print(f"\n✅ Detailed report saved to: reports/{report_name}/")
    print(f"   - report.html (open in browser)")
    print(f"   - trades.csv (all trades)")
    print(f"   - equity_curve.csv (equity history)")

    # Show trade breakdown
    trades_df = results['trades']
    if len(trades_df) > 0:
        print(f"\n📈 Trade Breakdown:")
        print(f"   Total trades: {len(trades_df)}")

        if 'setup' in trades_df.columns:
            long_trades = trades_df[trades_df['setup'] == 'LSCB_LONG']
            short_trades = trades_df[trades_df['setup'] == 'LSCB_SHORT']
            print(f"   LONG trades: {len(long_trades)}")
            print(f"   SHORT trades: {len(short_trades)}")

        if 'exit_reason' in trades_df.columns:
            exit_reasons = trades_df['exit_reason'].value_counts()
            print(f"\n   Exit Reasons:")
            for reason, count in exit_reasons.items():
                pct = (count / len(trades_df)) * 100
                print(f"     {reason}: {count} ({pct:.1f}%)")

    print("\n" + "=" * 70)
    print("✅ BACKTEST COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    main()
