#!/usr/bin/env python3
"""
Test Ultra Simple MR - Thresholds ±0.5% (muy pequeños)
"""

from engine.backtester import Backtester
from strategies.ultra_simple_mr import UltraSimpleMRStrategy
from datetime import datetime, timedelta

print("=" * 70)
print("TEST: UltraSimpleMR (thresholds ±0.5%)")
print("=" * 70)

strategy = UltraSimpleMRStrategy()

# Use last 7 days
end_date = datetime.now()
start_date = end_date - timedelta(days=7)

print(f"\nConfig:")
print(f"  Mean lookback: {strategy.mean_lookback} candles (30 min)")
print(f"  Long entry: {strategy.long_thresholds}")
print(f"  Short entry: {strategy.short_thresholds}")
print(f"  Exit band: ±{strategy.mean_reentry_band}%")
print(f"  Target PnL: {strategy.target_pnl_pct}%")
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
    metrics = results['metrics']

    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)

    print(f"Total Return: {metrics['total_return_pct']:.2f}%")
    print(f"Total Trades: {metrics['total_trades']}")

    if metrics['total_trades'] > 0:
        print(f"Winning Trades: {metrics['winning_trades']}")
        print(f"Win Rate: {metrics['winning_trades']/metrics['total_trades']*100:.1f}%")
        print(f"Profit Factor: {metrics.get('profit_factor', 0):.2f}")
        print(f"Max Drawdown: {metrics.get('max_drawdown_pct', 0):.2f}%")
        print(f"Sharpe Ratio: {metrics.get('sharpe_ratio', 0):.2f}")

        weekly_ret = (metrics['total_return_pct'] / 7) * 7
        print(f"Weekly Return: {weekly_ret:.2f}%")

        print("\n✓✓✓ SUCCESS - Strategy is trading!")
        print()
        print("Con thresholds más pequeños (±0.5%) SÍ genera trades.")
        print("BTC no se mueve mucho en rangos de 1-2 horas.")
        print()
        print("Opciones:")
        print("  1. Usar thresholds más pequeños (±0.5%, ±1%)")
        print("  2. Usar lookback más largo (2-4 horas)")
        print("  3. Probar en pares más volátiles (altcoins)")

    else:
        print("\n⚠️ STILL 0 TRADES")
        print("\nEsto significa que BTC NO se desvía ni ±0.5% de la media de 30min")
        print("en los últimos 7 días. Mercado extremadamente estable.")
        print()
        print("Posibles soluciones:")
        print("  - Bajar threshold a ±0.3%")
        print("  - Probar en periodo más volátil")
        print("  - Usar datos de altcoins (AVAX, SOL, etc)")

except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("=" * 70)
