#!/usr/bin/env python3
"""
Comparar UltraSimple vs ImprovedSimple en altcoins
"""

from engine.backtester import Backtester
from strategies.ultra_simple_mr import UltraSimpleMRStrategy
from strategies.improved_simple_mr import ImprovedSimpleMRStrategy
from datetime import datetime, timedelta

PAIRS = ['SOLUSDT', 'AVAXUSDT', 'ETHUSDT']
STRATEGIES = {
    'UltraSimple': {
        'class': UltraSimpleMRStrategy,
        'desc': 'Thresholds ±0.5%, exit 0.2%, target 0.8%'
    },
    'ImprovedSimple': {
        'class': ImprovedSimpleMRStrategy,
        'desc': 'Thresholds ±0.8%, exit 0.3%, target 1.2%'
    }
}

DAYS_BACK = 7
end_date = datetime.now()
start_date = end_date - timedelta(days=DAYS_BACK)

print("=" * 90)
print("COMPARACIÓN: UltraSimple vs ImprovedSimple en Altcoins")
print("=" * 90)
print(f"Periodo: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}")
print(f"Leverage: 5x | Fees: 0.06% | Slippage: 0.03%")
print("=" * 90)
print()

all_results = {}

for strategy_name, strategy_config in STRATEGIES.items():
    print(f"\n{strategy_name} ({strategy_config['desc']}):")
    print("-" * 90)

    strategy_results = []

    for symbol in PAIRS:
        print(f"  {symbol}...", end=' ')

        try:
            strategy = strategy_config['class']()

            backtester = Backtester(
                strategy=strategy,
                symbol=symbol,
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

            total_ret = metrics['total_return_pct']
            trades = metrics['total_trades']
            wr = (metrics['winning_trades'] / trades * 100) if trades > 0 else 0
            pf = metrics.get('profit_factor', 0)
            dd = metrics.get('max_drawdown_pct', 0)
            sharpe = metrics.get('sharpe_ratio', 0)

            strategy_results.append({
                'symbol': symbol,
                'return': total_ret,
                'trades': trades,
                'wr': wr,
                'pf': pf,
                'dd': dd,
                'sharpe': sharpe
            })

            status = "✓" if total_ret > 0 else "✗"
            print(f"{status} {total_ret:+6.2f}% | {trades:3d} trades | WR {wr:5.1f}% | DD {dd:5.1f}%")

        except Exception as e:
            print(f"ERROR: {e}")
            strategy_results.append({
                'symbol': symbol,
                'return': 0,
                'trades': 0,
                'wr': 0,
                'pf': 0,
                'dd': 0,
                'sharpe': 0
            })

    all_results[strategy_name] = strategy_results

# Comparison table
print("\n" + "=" * 90)
print("TABLA COMPARATIVA")
print("=" * 90)

for strategy_name in STRATEGIES.keys():
    print(f"\n{strategy_name}:")
    print(f"{'Pair':<12} {'Return%':<10} {'Trades':<8} {'WR%':<8} {'PF':<8} {'DD%':<8} {'Sharpe':<8}")
    print("-" * 90)

    results = all_results[strategy_name]
    valid = [r for r in results if r['trades'] > 0]

    for r in results:
        if r['trades'] > 0:
            print(
                f"{r['symbol']:<12} "
                f"{r['return']:+8.2f}% "
                f"{r['trades']:<8} "
                f"{r['wr']:<8.1f} "
                f"{r['pf']:<8.2f} "
                f"{r['dd']:<8.2f} "
                f"{r['sharpe']:<8.2f}"
            )
        else:
            print(f"{r['symbol']:<12} {'N/A':<10}")

    if valid:
        avg_ret = sum(r['return'] for r in valid) / len(valid)
        total_trades = sum(r['trades'] for r in valid)
        avg_wr = sum(r['wr'] for r in valid) / len(valid)
        avg_pf = sum(r['pf'] for r in valid) / len(valid)
        max_dd = max(r['dd'] for r in valid)
        avg_sharpe = sum(r['sharpe'] for r in valid) / len(valid)

        print("-" * 90)
        print(
            f"{'AVERAGE':<12} "
            f"{avg_ret:+8.2f}% "
            f"{total_trades:<8} "
            f"{avg_wr:<8.1f} "
            f"{avg_pf:<8.2f} "
            f"{max_dd:<8.2f} "
            f"{avg_sharpe:<8.2f}"
        )

# Winner
print("\n" + "=" * 90)
print("GANADOR:")
print("=" * 90)

winners = {}
for strategy_name, results in all_results.items():
    valid = [r for r in results if r['trades'] > 0]
    if valid:
        avg_ret = sum(r['return'] for r in valid) / len(valid)
        max_dd = max(r['dd'] for r in valid)
        avg_pf = sum(r['pf'] for r in valid) / len(valid)
        winners[strategy_name] = {
            'return': avg_ret,
            'dd': max_dd,
            'pf': avg_pf
        }

if winners:
    best_return = max(winners.items(), key=lambda x: x[1]['return'])
    best_pf = max(winners.items(), key=lambda x: x[1]['pf'])
    best_dd = min(winners.items(), key=lambda x: x[1]['dd'])

    print(f"Mejor Return: {best_return[0]} ({best_return[1]['return']:+.2f}%)")
    print(f"Mejor Profit Factor: {best_pf[0]} ({best_pf[1]['pf']:.2f})")
    print(f"Menor Drawdown: {best_dd[0]} ({best_dd[1]['dd']:.2f}%)")

    print("\nRECOMENDACIÓN:")
    if best_return[0] == best_pf[0] == best_dd[0]:
        print(f"  🏆 {best_return[0]} es claramente superior en todos los aspectos")
    elif best_return[0] == best_pf[0]:
        print(f"  ✓ {best_return[0]} tiene mejor return y PF")
    elif best_return[1]['return'] > 0:
        print(f"  ✓ {best_return[0]} tiene mejor return ({best_return[1]['return']:+.2f}%)")
        if best_return[1]['dd'] > 20:
            print(f"    Pero cuidado con DD de {best_return[1]['dd']:.1f}%")
    else:
        print(f"  ⚠️ Ambas estrategias tienen return negativo o muy bajo")
        print(f"     Considera:")
        print(f"     - Probar en periodo más volátil")
        print(f"     - Usar 5m o 15m timeframe")
        print(f"     - Ajustar thresholds basado en volatilidad real del par")

print("\n" + "=" * 90)
