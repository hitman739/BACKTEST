#!/usr/bin/env python3
"""
CLI Entry Point for Crypto Backtesting Engine

Usage:
    python run_backtest.py --strategy strategies/examples/ema_cross.yaml \
                           --symbol BTCUSDT \
                           --timeframe 5m \
                           --from 2024-08-01 \
                           --to 2024-10-01 \
                           --equity 10000 \
                           --leverage 5 \
                           --report_name test_run_001
"""

import argparse
import sys
from pathlib import Path

from engine.backtester import run_backtest


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Run cryptocurrency futures backtests',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic backtest with default settings
  python run_backtest.py --strategy strategies/examples/ema_cross.yaml \\
                         --symbol BTCUSDT --timeframe 5m \\
                         --from 2024-08-01 --to 2024-10-01

  # Custom fees and leverage
  python run_backtest.py --strategy strategies/examples/ema_cross.yaml \\
                         --symbol ETHUSDT --timeframe 15m \\
                         --from 2024-07-01 --to 2024-09-01 \\
                         --equity 50000 --leverage 10 \\
                         --fees_maker 0.0001 --fees_taker 0.0003

  # With custom report name
  python run_backtest.py --strategy strategies/examples/ema_cross.yaml \\
                         --symbol BTCUSDT --timeframe 1h \\
                         --from 2024-01-01 --to 2024-06-01 \\
                         --report_name btc_hourly_h1_2024
        """
    )

    # Required arguments
    parser.add_argument(
        '--strategy',
        type=str,
        required=True,
        help='Path to strategy file (YAML/JSON or Python class)'
    )

    parser.add_argument(
        '--symbol',
        type=str,
        required=True,
        help='Trading symbol (e.g., BTCUSDT, ETHUSDT)'
    )

    parser.add_argument(
        '--timeframe',
        type=str,
        required=True,
        choices=['1m', '3m', '5m', '15m', '30m', '1h', '2h', '4h', '6h', '8h', '12h', '1d', '3d', '1w'],
        help='Candle timeframe'
    )

    parser.add_argument(
        '--from',
        dest='start_date',
        type=str,
        required=True,
        help='Start date (YYYY-MM-DD)'
    )

    parser.add_argument(
        '--to',
        dest='end_date',
        type=str,
        required=True,
        help='End date (YYYY-MM-DD)'
    )

    # Optional arguments with defaults
    parser.add_argument(
        '--equity',
        type=float,
        default=10000,
        help='Initial equity/balance (default: 10000)'
    )

    parser.add_argument(
        '--leverage',
        type=float,
        default=1.0,
        help='Leverage multiplier (default: 1.0)'
    )

    parser.add_argument(
        '--fees_maker',
        type=float,
        default=0.0002,
        help='Maker fee rate (default: 0.0002 = 0.02%%)'
    )

    parser.add_argument(
        '--fees_taker',
        type=float,
        default=0.0004,
        help='Taker fee rate (default: 0.0004 = 0.04%%)'
    )

    parser.add_argument(
        '--slippage',
        type=float,
        default=2.0,
        help='Slippage in basis points (default: 2.0)'
    )

    parser.add_argument(
        '--report_name',
        type=str,
        default=None,
        help='Custom report name (default: auto-generated timestamp)'
    )

    parser.add_argument(
        '--data_dir',
        type=str,
        default='./data/binance',
        help='Directory for cached data (default: ./data/binance)'
    )

    parser.add_argument(
        '--report_dir',
        type=str,
        default='./reports',
        help='Directory for reports (default: ./reports)'
    )

    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Force re-download of data (ignore cache)'
    )

    return parser.parse_args()


def validate_args(args):
    """Validate arguments"""
    errors = []

    # Check strategy file exists
    if not Path(args.strategy).exists():
        errors.append(f"Strategy file not found: {args.strategy}")

    # Validate date format (basic check)
    import re
    date_pattern = r'^\d{4}-\d{2}-\d{2}$'

    if not re.match(date_pattern, args.start_date):
        errors.append(f"Invalid start date format: {args.start_date} (expected YYYY-MM-DD)")

    if not re.match(date_pattern, args.end_date):
        errors.append(f"Invalid end date format: {args.end_date} (expected YYYY-MM-DD)")

    # Validate ranges
    if args.equity <= 0:
        errors.append(f"Equity must be positive: {args.equity}")

    if args.leverage <= 0:
        errors.append(f"Leverage must be positive: {args.leverage}")

    if args.fees_maker < 0 or args.fees_maker > 1:
        errors.append(f"Maker fees must be between 0 and 1: {args.fees_maker}")

    if args.fees_taker < 0 or args.fees_taker > 1:
        errors.append(f"Taker fees must be between 0 and 1: {args.fees_taker}")

    if errors:
        print("Validation errors:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)


def main():
    """Main entry point"""
    print("=" * 60)
    print("Crypto Futures Backtesting Engine")
    print("=" * 60)

    # Parse and validate arguments
    args = parse_args()
    validate_args(args)

    # Print configuration
    print("\nConfiguration:")
    print(f"  Strategy:     {args.strategy}")
    print(f"  Symbol:       {args.symbol}")
    print(f"  Timeframe:    {args.timeframe}")
    print(f"  Period:       {args.start_date} to {args.end_date}")
    print(f"  Equity:       ${args.equity:,.2f}")
    print(f"  Leverage:     {args.leverage}x")
    print(f"  Maker Fee:    {args.fees_maker * 100:.3f}%")
    print(f"  Taker Fee:    {args.fees_taker * 100:.3f}%")
    print(f"  Slippage:     {args.slippage} bps")
    print()

    try:
        # Run backtest
        results = run_backtest(
            strategy_path=args.strategy,
            symbol=args.symbol,
            timeframe=args.timeframe,
            start_date=args.start_date,
            end_date=args.end_date,
            initial_balance=args.equity,
            leverage=args.leverage,
            maker_fee=args.fees_maker,
            taker_fee=args.fees_taker,
            slippage_bps=args.slippage,
            report_name=args.report_name,
            data_dir=args.data_dir,
            report_dir=args.report_dir
        )

        print("\n✓ Backtest completed successfully")
        return 0

    except Exception as e:
        print(f"\n✗ Backtest failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
