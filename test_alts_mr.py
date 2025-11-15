#!/usr/bin/env python3
"""
Test UltraSimple MR en altcoins (más volátiles que BTC)
"""

from engine.backtester import Backtester
from strategies.ultra_simple_mr import UltraSimpleMRStrategy
from datetime import datetime, timedelta

PAIRS = ['SOLUSDT', 'AVAXUSDT', 'LINKUSDT', 'NEARUSDT', 'ETHUSDT']
TIMEFRAME = '1m'
DAYS_BACK = 7

end_date = datetime.now()
start_date = end_date - timedelta(days=DAYS_BACK)

print("=" * 80)
print("TEST: UltraSimpleMR en ALTCOINS (más volátiles)")
print("=" * 80)
print(f"Periodo: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}")
print(f"Thresholds: ±0.5%, ±1.0%")
print(f"Leverage: 5x")
print("=" * 80)
print()

results_summary = []

for symbol in PAIRS:
    print(f"Testing {symbol}...", end=' ')

    try:
        strategy = UltraSimpleMRStrategy()

        backtester = Backtester(
            strategy=strategy,
            symbol=symbol,
            timeframe=TIMEFRAME,
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

        total_ret = metrics['total_return_pct']
        trades = metrics['total_trades']
        wr = (metrics['winning_trades'] / trades * 100) if trades > 0 else 0
        pf = metrics.get('profit_factor', 0)
        dd = metrics.get('max_drawdown_pct', 0)

        results_summary.append({
            'symbol': symbol,
            'return': total_ret,
            'trades': trades,
            'wr': wr,
            'pf': pf,
            'dd': dd
        })

        status = "✓" if total_ret > 0 else "✗"
        print(f"{status} {total_ret:+.2f}% ({trades} trades, WR {wr:.0f}%)")

    except Exception as e:
        print(f"ERROR: {e}")
        results_summary.append({
            'symbol': symbol,
            'return': 0,
            'trades': 0,
            'wr': 0,
            'pf': 0,
            'dd': 0
        })

print()
print("=" * 80)
print("RESUMEN DE RESULTADOS")
print("=" * 80)
print(f"{'Pair':<12} {'Return%':<10} {'Trades':<8} {'WR%':<8} {'PF':<8} {'MaxDD%':<10}")
print("-" * 80)

for r in results_summary:
    ret_str = f"{r['return']:+.2f}%" if r['trades'] > 0 else "N/A"
    print(
        f"{r['symbol']:<12} "
        f"{ret_str:<10} "
        f"{r['trades']:<8} "
        f"{r['wr']:<8.1f} "
        f"{r['pf']:<8.2f} "
        f"{r['dd']:<10.2f}"
    )

print("-" * 80)

# Calculate averages
valid_results = [r for r in results_summary if r['trades'] > 0]
if valid_results:
    avg_return = sum(r['return'] for r in valid_results) / len(valid_results)
    total_trades = sum(r['trades'] for r in valid_results)
    avg_wr = sum(r['wr'] for r in valid_results) / len(valid_results)
    avg_pf = sum(r['pf'] for r in valid_results) / len(valid_results)
    max_dd = max(r['dd'] for r in valid_results)

    print(
        f"{'AVERAGE':<12} "
        f"{avg_return:+.2f}%{'':<4} "
        f"{total_trades:<8} "
        f"{avg_wr:<8.1f} "
        f"{avg_pf:<8.2f} "
        f"{max_dd:<10.2f}"
    )

    print()
    print("=" * 80)
    print("ANÁLISIS:")
    print("=" * 80)

    # Best performer
    best = max(valid_results, key=lambda x: x['return'])
    worst = min(valid_results, key=lambda x: x['return'])
    most_trades = max(valid_results, key=lambda x: x['trades'])

    print(f"Mejor return: {best['symbol']} ({best['return']:+.2f}%)")
    print(f"Peor return: {worst['symbol']} ({worst['return']:+.2f}%)")
    print(f"Más trades: {most_trades['symbol']} ({most_trades['trades']} trades)")
    print()

    if avg_return < 0:
        print("⚠️ Return promedio negativo")
        print("   Problemas posibles:")
        print("   - Thresholds demasiado pequeños (overtrade)")
        print("   - Fees comiendo profits")
        print("   - Mercado trending (no mean reversion)")
        print()
        print("   Sugerencias:")
        print("   - Aumentar thresholds a ±0.8%, ±1.5%")
        print("   - Aumentar exit band a ±0.3-0.5%")
        print("   - Aumentar target PnL a 1.2-1.5%")
    elif avg_return > 0 and avg_return < 1:
        print("✓ Return positivo pero bajo (<1%)")
        print("   Con 5x leverage, puedes ajustar para más agresividad")
    elif avg_return >= 1:
        print("✓✓ Return positivo y razonable (>1%)")
        print("   Estrategia viable para seguir optimizando")

    print()

    if max_dd > 20:
        print(f"⚠️ Max DD muy alto ({max_dd:.1f}%)")
        print("   - Reduce risk per trade")
        print("   - Usa hard stops más ajustados")
        print("   - Reduce número de layers")

else:
    print("\n⚠️ Ningún par generó trades")
    print("   Necesitas datos descargados: python3 download_1m_data.py")

print()
print("=" * 80)
