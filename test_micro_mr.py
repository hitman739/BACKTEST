#!/usr/bin/env python3
"""
Test Micro MR - Ultra tight risk control (0.8% stop)
"""

from engine.backtester import Backtester
from strategies.micro_mr import MicroMRStrategy

print("=" * 90)
print("MICRO MR - Ultra Tight Risk Control")
print("=" * 90)
print("Hard Stop: 0.8% (with 5x leverage = 4% account risk max)")
print("Position Size: 0.3% per layer")
print("Thresholds: ±1.0%, ±2.0%")
print("=" * 90)
print()

try:
    strategy = MicroMRStrategy()

    backtester = Backtester(
        strategy=strategy,
        symbol='SOLUSDT',
        timeframe='1m',
        start_date='2024-10-01',
        end_date='2024-11-14',
        initial_balance=10000,
        leverage=5.0,
        maker_fee=0.0002,
        taker_fee=0.0006,
        slippage_bps=3.0,
        data_dir='./data/binance',
        use_cache=True
    )

    results = backtester.run()
    metrics = results['metrics']

    total_ret = metrics['total_return_pct']
    trades = metrics['total_trades']
    wr = (metrics['winning_trades'] / trades * 100) if trades > 0 else 0
    pf = metrics.get('profit_factor', 0)
    dd = metrics.get('max_drawdown_pct', 0)
    sharpe = metrics.get('sharpe_ratio', 0)

    # Calculate weekly and monthly
    days = 44
    weekly_ret = (total_ret / days) * 7
    monthly_ret = (total_ret / days) * 30

    print("\nRESULTADOS:")
    print(f"  Total Return: {total_ret:+.2f}%")
    print(f"  Weekly Return: {weekly_ret:+.2f}%")
    print(f"  Monthly Return: {monthly_ret:+.2f}%")
    print(f"  Total Trades: {trades}")
    print(f"  Win Rate: {wr:.1f}%")
    print(f"  Profit Factor: {pf:.2f}")
    print(f"  Max Drawdown: {dd:.2f}%")
    print(f"  Sharpe Ratio: {sharpe:.2f}")
    print()

    if total_ret > -50:
        print("✓ Did NOT blow up the account!")
        if total_ret > 0:
            print(f"✓✓ PROFITABLE: {total_ret:+.2f}%")
            if weekly_ret >= 3.0:
                print(f"✓✓✓ MEETS GOAL: {weekly_ret:+.2f}% weekly!")
            elif weekly_ret >= 2.0:
                print(f"✓✓ Close to goal: {weekly_ret:+.2f}% weekly")
            elif weekly_ret >= 1.0:
                print(f"✓ Profitable but low: {weekly_ret:+.2f}% weekly")
        else:
            print(f"⚠️ Small loss: {total_ret:+.2f}% (but manageable)")
    else:
        print(f"✗ Still blowing up: {total_ret:+.2f}%")

    print("\n" + "=" * 90)
    print("ANÁLISIS:")
    print("=" * 90)

    if trades > 0:
        avg_win = metrics.get('avg_win', 0)
        avg_loss = metrics.get('avg_loss', 0)
        print(f"  Avg Win: +{avg_win:.2f}%")
        print(f"  Avg Loss: {avg_loss:.2f}%")
        print(f"  Risk/Reward Ratio: {abs(avg_win/avg_loss) if avg_loss != 0 else 0:.2f}")

        if dd < 15:
            print(f"\n  ✓ Drawdown bajo control ({dd:.1f}%)")
        else:
            print(f"\n  ⚠️ Drawdown todavía alto ({dd:.1f}%)")

        if pf > 1.0:
            print(f"  ✓ Profit Factor positivo ({pf:.2f})")
        else:
            print(f"  ✗ Profit Factor negativo ({pf:.2f}) - perdiendo más de lo que gana")

except Exception as e:
    print(f"\n✗ ERROR: {str(e)}")
    import traceback
    traceback.print_exc()
