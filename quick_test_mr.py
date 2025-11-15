#!/usr/bin/env python3
"""
Quick test - SimpleMeanRevert on BTCUSDT
"""

from engine.backtester import Backtester
from strategies.simple_mean_revert import SimpleMeanRevertStrategy
from datetime import datetime, timedelta

print("=" * 70)
print("QUICK TEST: SimpleMeanRevert on BTCUSDT 1m")
print("=" * 70)

strategy = SimpleMeanRevertStrategy()

# Use last 7 days for quick test
end_date = datetime.now()
start_date = end_date - timedelta(days=7)

print(f"\nPeriod: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
print(f"Timeframe: 1m")
print(f"Leverage: 5x")
print(f"Initial Balance: $10,000")
print()

print("Strategy Config:")
print(f"  Mean: MIDRANGE (60 candles = 1 hour)")
print(f"  Long entry: -2.0%, -4.0% from mean")
print(f"  Short entry: +2.0%, +4.0% from mean")
print(f"  Exit: Within 0.8% of mean OR +1.5% PnL")
print(f"  Hard stop: 8% from mean")
print(f"  Filters: RELAXED (0.5-5.0 for ATR/vol)")
print()

print("Running backtest...")
print("-" * 70)

try:
    backtester = Backtester(
        strategy=strategy,
        symbol='BTCUSDT',
        timeframe='1m',
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d'),
        initial_balance=10000,
        leverage=5.0,
        taker_fee=0.0006,
        slippage_bps=3.0,
        data_dir='./data/binance',
        use_cache=True
    )

    results = backtester.run()

    # Extract metrics
    metrics = results['metrics']

    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)

    print(f"Total Return: {metrics['total_return_pct']:.2f}%")
    print(f"Total Trades: {metrics['total_trades']}")

    if metrics['total_trades'] > 0:
        print(f"Winning Trades: {metrics['winning_trades']}")
        print(f"Win Rate: {metrics['winning_trades']/metrics['total_trades']*100:.1f}%")
        print(f"Profit Factor: {metrics['profit_factor']:.2f}")
        print(f"Max Drawdown: {metrics['max_drawdown_pct']:.2f}%")
        print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")

        # Calculate weekly
        days_traded = 7
        weekly_ret = (metrics['total_return_pct'] / days_traded) * 7
        print(f"Weekly Return: {weekly_ret:.2f}%")

        print("\n✓ SUCCESS - Strategy is generating trades!")
        print()
        print("Next steps:")
        print("  1. Try on more pairs: python3 compare_mean_reversion.py")
        print("  2. Or test original strategies (Shallow, Session, Deep Panic)")

    else:
        print("\n⚠️ STILL 0 TRADES")
        print()
        print("Debug steps:")
        print("  1. Run: python3 debug_mean_reversion.py")
        print("  2. Check if distance ever crosses -2% or +2%")
        print("  3. Check data quality (enough candles?)")

except Exception as e:
    print(f"\n✗ ERROR: {e}")
    print()
    print("Possible issues:")
    print("  - No data downloaded (run: python3 download_1m_data.py)")
    print("  - No internet access (must run on Mac, not Docker)")
    import traceback
    traceback.print_exc()

print("=" * 70)
