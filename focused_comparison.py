#!/usr/bin/env python3
"""
FOCUSED COMPARISON - What Works Best for Autonomous Bot?

Tests:
1. Scalper Pro (5m momentum) on BTCUSDT - 59 days
2. Mean Reversion strategies (1m) on SOLUSDT - 44 days

Goal: Find which strategy delivers 3-5% weekly consistently
"""

from engine.backtester import Backtester
from strategies.scalper_pro import ScalperProStrategy
from strategies.ultra_simple_mr import UltraSimpleMRStrategy
from strategies.improved_simple_mr import ImprovedSimpleMRStrategy
from strategies.shallow_revert import ShallowRevertStrategy
from datetime import datetime

INITIAL_BALANCE = 10000

# Test 1: Momentum strategy on BTCUSDT 5m
print("=" * 100)
print("TEST 1: SCALPER PRO (Momentum)")
print("=" * 100)
print("Symbol: BTCUSDT | Timeframe: 5m | Leverage: 10x")
print("Period: 2024-08-01 to 2024-09-29 (59 días)")
print("-" * 100)

try:
    strategy = ScalperProStrategy()

    backtester = Backtester(
        strategy=strategy,
        symbol='BTCUSDT',
        timeframe='5m',
        start_date='2024-08-01',
        end_date='2024-09-29',
        initial_balance=INITIAL_BALANCE,
        leverage=10.0,
        maker_fee=0.0002,
        taker_fee=0.0006,
        slippage_bps=5.0,
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
    days = 59
    weekly_ret = (total_ret / days) * 7
    monthly_ret = (total_ret / days) * 30

    print(f"\nRESULTADOS:")
    print(f"  Total Return: {total_ret:+.2f}%")
    print(f"  Weekly Return: {weekly_ret:+.2f}%")
    print(f"  Monthly Return: {monthly_ret:+.2f}%")
    print(f"  Total Trades: {trades}")
    print(f"  Win Rate: {wr:.1f}%")
    print(f"  Profit Factor: {pf:.2f}")
    print(f"  Max Drawdown: {dd:.2f}%")
    print(f"  Sharpe Ratio: {sharpe:.2f}")

    scalper_results = {
        'name': 'Scalper Pro',
        'return': total_ret,
        'weekly': weekly_ret,
        'monthly': monthly_ret,
        'trades': trades,
        'wr': wr,
        'pf': pf,
        'dd': dd,
        'sharpe': sharpe
    }

    if weekly_ret >= 3.0:
        print(f"\n  ✓✓✓ CUMPLE OBJETIVO de 3%+ semanal!")
    elif weekly_ret >= 2.0:
        print(f"\n  ✓✓ Cerca del objetivo (2%+ semanal)")
    elif weekly_ret >= 1.0:
        print(f"\n  ✓ Rentable pero bajo objetivo (1%+ semanal)")
    else:
        print(f"\n  ✗ No alcanza objetivo (<1% semanal)")

except Exception as e:
    print(f"\n✗ ERROR: {str(e)}")
    scalper_results = None

# Test 2: Mean Reversion strategies on SOLUSDT 1m
print("\n" + "=" * 100)
print("TEST 2: MEAN REVERSION STRATEGIES")
print("=" * 100)
print("Symbol: SOLUSDT | Timeframe: 1m | Leverage: 5x")
print("Period: 2024-10-01 to 2024-11-14 (44 días)")
print("=" * 100)

MR_STRATEGIES = {
    'UltraSimple MR': {
        'class': UltraSimpleMRStrategy,
        'desc': 'Thresholds ±0.5%, very tight'
    },
    'ImprovedSimple MR': {
        'class': ImprovedSimpleMRStrategy,
        'desc': 'Thresholds ±0.8%, optimized'
    },
    'Shallow Revert': {
        'class': ShallowRevertStrategy,
        'desc': 'Thresholds ±1.5%, conservative'
    },
}

mr_results = []

for strategy_name, strategy_config in MR_STRATEGIES.items():
    print(f"\n{strategy_name} - {strategy_config['desc']}")
    print("-" * 100)

    try:
        strategy = strategy_config['class']()

        backtester = Backtester(
            strategy=strategy,
            symbol='SOLUSDT',
            timeframe='1m',
            start_date='2024-10-01',
            end_date='2024-11-14',
            initial_balance=INITIAL_BALANCE,
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

        print(f"\nRESULTADOS:")
        print(f"  Total Return: {total_ret:+.2f}%")
        print(f"  Weekly Return: {weekly_ret:+.2f}%")
        print(f"  Monthly Return: {monthly_ret:+.2f}%")
        print(f"  Total Trades: {trades}")
        print(f"  Win Rate: {wr:.1f}%")
        print(f"  Profit Factor: {pf:.2f}")
        print(f"  Max Drawdown: {dd:.2f}%")
        print(f"  Sharpe Ratio: {sharpe:.2f}")

        mr_results.append({
            'name': strategy_name,
            'return': total_ret,
            'weekly': weekly_ret,
            'monthly': monthly_ret,
            'trades': trades,
            'wr': wr,
            'pf': pf,
            'dd': dd,
            'sharpe': sharpe
        })

        if weekly_ret >= 3.0:
            print(f"\n  ✓✓✓ CUMPLE OBJETIVO de 3%+ semanal!")
        elif weekly_ret >= 2.0:
            print(f"\n  ✓✓ Cerca del objetivo (2%+ semanal)")
        elif weekly_ret >= 1.0:
            print(f"\n  ✓ Rentable pero bajo objetivo (1%+ semanal)")
        else:
            print(f"\n  ✗ No alcanza objetivo (<1% semanal)")

    except Exception as e:
        print(f"\n✗ ERROR: {str(e)[:80]}")

# Final comparison
print("\n" + "=" * 100)
print("COMPARACIÓN FINAL - ¿QUÉ USAR PARA EL BOT AUTÓNOMO?")
print("=" * 100)

all_results = []
if scalper_results:
    all_results.append(scalper_results)
all_results.extend(mr_results)

if all_results:
    # Sort by weekly return
    sorted_by_weekly = sorted(all_results, key=lambda x: x['weekly'], reverse=True)

    print(f"\n{'Strategy':<20} {'Weekly%':<12} {'Monthly%':<12} {'Trades':<10} {'WR%':<8} {'PF':<8} {'DD%':<8} {'Sharpe':<8}")
    print("-" * 100)

    for r in sorted_by_weekly:
        print(
            f"{r['name']:<20} "
            f"{r['weekly']:+10.2f}% "
            f"{r['monthly']:+10.2f}% "
            f"{r['trades']:<10} "
            f"{r['wr']:<8.1f} "
            f"{r['pf']:<8.2f} "
            f"{r['dd']:<8.2f} "
            f"{r['sharpe']:<8.2f}"
        )

    # Winner
    print("\n" + "=" * 100)
    print("🏆 GANADOR ABSOLUTO")
    print("=" * 100)

    winner = sorted_by_weekly[0]

    print(f"\n{winner['name']}:")
    print(f"  Return Total: {winner['return']:+.2f}%")
    print(f"  Return Semanal: {winner['weekly']:+.2f}%")
    print(f"  Return Mensual: {winner['monthly']:+.2f}%")
    print(f"  Trades: {winner['trades']}")
    print(f"  Win Rate: {winner['wr']:.1f}%")
    print(f"  Profit Factor: {winner['pf']:.2f}")
    print(f"  Max Drawdown: {winner['dd']:.2f}%")
    print(f"  Sharpe Ratio: {winner['sharpe']:.2f}")

    print("\n" + "=" * 100)
    print("ANÁLISIS Y RECOMENDACIÓN")
    print("=" * 100)

    if winner['weekly'] >= 3.0:
        print(f"\n✓✓✓ {winner['name']} CUMPLE el objetivo de 3-5% semanal")
        print(f"\nPROYECCIÓN ANUAL: {winner['weekly'] * 52:.1f}%")
        print(f"\nRECOMENDACIÓN:")
        print(f"  1. Usar {winner['name']} como estrategia principal del bot")
        print(f"  2. Testear en más pares para diversificar")
        print(f"  3. Optimizar parámetros para mejorar Sharpe y DD")
        print(f"  4. Implementar gestión de riesgo adicional")
    elif winner['weekly'] >= 2.0:
        print(f"\n✓ {winner['name']} está cerca del objetivo (2%+ semanal)")
        print(f"\nPROYECCIÓN ANUAL: {winner['weekly'] * 52:.1f}%")
        print(f"\nRECOMENDACIÓN:")
        print(f"  1. Optimizar parámetros de {winner['name']} para alcanzar 3%")
        print(f"  2. Considerar aumentar leverage ligeramente")
        print(f"  3. Testear en más pares volátiles")
    elif winner['weekly'] >= 1.0:
        print(f"\n⚠️ {winner['name']} es rentable pero bajo objetivo")
        print(f"\nPROYECCIÓN ANUAL: {winner['weekly'] * 52:.1f}%")
        print(f"\nRECOMENDACIÓN:")
        print(f"  1. Optimizar parámetros agresivamente")
        print(f"  2. Considerar aumentar leverage a 15-20x")
        print(f"  3. Buscar pares más volátiles")
        print(f"  4. Combinar con otras estrategias")
    else:
        print(f"\n✗ Ninguna estrategia alcanza 1% semanal")
        print(f"\nRECOMENDACIÓN:")
        print(f"  1. Descargar datos de periodos más volátiles")
        print(f"  2. Testear en más altcoins (NEAR, AVAX, etc)")
        print(f"  3. Optimizar parámetros más agresivamente")
        print(f"  4. Considerar estrategias híbridas")

    # Best by category
    best_pf = max(all_results, key=lambda x: x['pf'])
    best_wr = max(all_results, key=lambda x: x['wr'])
    best_dd = min(all_results, key=lambda x: x['dd'])

    print("\n" + "=" * 100)
    print("MEJORES POR CATEGORÍA")
    print("=" * 100)
    print(f"  Mejor Return: {winner['name']} ({winner['weekly']:+.2f}% semanal)")
    print(f"  Mejor Profit Factor: {best_pf['name']} ({best_pf['pf']:.2f})")
    print(f"  Mejor Win Rate: {best_wr['name']} ({best_wr['wr']:.1f}%)")
    print(f"  Menor Drawdown: {best_dd['name']} ({best_dd['dd']:.2f}%)")

else:
    print("\n⚠️ No hay resultados para comparar")

print("\n" + "=" * 100)
