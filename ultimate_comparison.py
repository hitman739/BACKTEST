#!/usr/bin/env python3
"""
COMPARACIÓN DEFINITIVA - Todas las estrategias

Momentum Strategies (10x leverage):
- Scalper Pro (5m)
- Momentum Hunter (15m)
- Hybrid Alpha (15m)

Mean Reversion Strategies (5x leverage):
- UltraSimple MR (±0.5%)
- ImprovedSimple MR (±0.8%)
- Shallow Revert (±1.5%)

Probadas en:
- BTCUSDT, ETHUSDT, SOLUSDT
"""

from engine.backtester import Backtester
from strategies.scalper_pro import ScalperProStrategy
from strategies.momentum_hunter import MomentumHunterStrategy
from strategies.hybrid_alpha import HybridAlphaStrategy
from strategies.ultra_simple_mr import UltraSimpleMRStrategy
from strategies.improved_simple_mr import ImprovedSimpleMRStrategy
from strategies.shallow_revert import ShallowRevertStrategy
from datetime import datetime, timedelta

# Test configuration
PAIRS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
DAYS_BACK = 7
INITIAL_BALANCE = 10000

# Momentum strategies (10x leverage, 15m data)
MOMENTUM_STRATEGIES = {
    'Scalper Pro': {
        'class': ScalperProStrategy,
        'timeframe': '5m',
        'leverage': 10.0,
        'desc': 'RSI mean reversion scalping'
    },
    'Momentum Hunter': {
        'class': MomentumHunterStrategy,
        'timeframe': '15m',
        'leverage': 10.0,
        'desc': 'Volume breakout + ADX trend'
    },
    'Hybrid Alpha': {
        'class': HybridAlphaStrategy,
        'timeframe': '15m',
        'leverage': 10.0,
        'desc': 'Hybrid momentum + mean reversion'
    },
}

# Mean reversion strategies (5x leverage, 1m data)
MEAN_REVERSION_STRATEGIES = {
    'UltraSimple MR': {
        'class': UltraSimpleMRStrategy,
        'timeframe': '1m',
        'leverage': 5.0,
        'desc': 'Thresholds ±0.5%, very tight'
    },
    'ImprovedSimple MR': {
        'class': ImprovedSimpleMRStrategy,
        'timeframe': '1m',
        'leverage': 5.0,
        'desc': 'Thresholds ±0.8%, optimized'
    },
    'Shallow Revert': {
        'class': ShallowRevertStrategy,
        'timeframe': '1m',
        'leverage': 5.0,
        'desc': 'Thresholds ±1.5%, conservative'
    },
}

ALL_STRATEGIES = {**MOMENTUM_STRATEGIES, **MEAN_REVERSION_STRATEGIES}

end_date = datetime.now()
start_date = end_date - timedelta(days=DAYS_BACK)

print("=" * 100)
print("COMPARACIÓN ULTIMATE - Todas las Estrategias")
print("=" * 100)
print(f"Periodo: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')} ({DAYS_BACK} días)")
print(f"Initial Balance: ${INITIAL_BALANCE:,}")
print(f"Fees: 0.06% taker | Slippage: 0.03%")
print("=" * 100)
print()

all_results = {}

for strategy_name, strategy_config in ALL_STRATEGIES.items():
    print(f"\n{strategy_name} - {strategy_config['desc']}")
    print(f"Timeframe: {strategy_config['timeframe']} | Leverage: {strategy_config['leverage']}x")
    print("-" * 100)

    strategy_results = []

    for symbol in PAIRS:
        print(f"  {symbol}...", end=' ')

        try:
            strategy = strategy_config['class']()

            backtester = Backtester(
                strategy=strategy,
                symbol=symbol,
                timeframe=strategy_config['timeframe'],
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                initial_balance=INITIAL_BALANCE,
                leverage=strategy_config['leverage'],
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

            # Calculate weekly return
            weekly_ret = (total_ret / DAYS_BACK) * 7

            strategy_results.append({
                'symbol': symbol,
                'return': total_ret,
                'weekly': weekly_ret,
                'trades': trades,
                'wr': wr,
                'pf': pf,
                'dd': dd,
                'sharpe': sharpe
            })

            status = "✓" if total_ret > 0 else "✗"
            print(f"{status} {total_ret:+6.2f}% | Weekly {weekly_ret:+6.2f}% | {trades:3d} trades | WR {wr:5.1f}% | PF {pf:4.2f}")

        except Exception as e:
            print(f"ERROR: {str(e)[:50]}")
            strategy_results.append({
                'symbol': symbol,
                'return': 0,
                'weekly': 0,
                'trades': 0,
                'wr': 0,
                'pf': 0,
                'dd': 0,
                'sharpe': 0
            })

    all_results[strategy_name] = strategy_results

# Summary table
print("\n" + "=" * 100)
print("TABLA RESUMEN - Todas las Estrategias")
print("=" * 100)
print(f"{'Strategy':<20} {'Avg Return%':<12} {'Avg Weekly%':<12} {'Total Trades':<12} {'Avg WR%':<10} {'Avg PF':<8} {'Max DD%':<8}")
print("-" * 100)

summary_data = []

for strategy_name, results in all_results.items():
    valid = [r for r in results if r['trades'] > 0]

    if valid:
        avg_return = sum(r['return'] for r in valid) / len(valid)
        avg_weekly = sum(r['weekly'] for r in valid) / len(valid)
        total_trades = sum(r['trades'] for r in valid)
        avg_wr = sum(r['wr'] for r in valid) / len(valid)
        avg_pf = sum(r['pf'] for r in valid) / len(valid)
        max_dd = max(r['dd'] for r in valid)
        avg_sharpe = sum(r['sharpe'] for r in valid) / len(valid)

        summary_data.append({
            'name': strategy_name,
            'return': avg_return,
            'weekly': avg_weekly,
            'trades': total_trades,
            'wr': avg_wr,
            'pf': avg_pf,
            'dd': max_dd,
            'sharpe': avg_sharpe
        })

        ret_str = f"{avg_return:+.2f}%"
        weekly_str = f"{avg_weekly:+.2f}%"

        print(
            f"{strategy_name:<20} "
            f"{ret_str:<12} "
            f"{weekly_str:<12} "
            f"{total_trades:<12} "
            f"{avg_wr:<10.1f} "
            f"{avg_pf:<8.2f} "
            f"{max_dd:<8.2f}"
        )
    else:
        print(f"{strategy_name:<20} {'N/A':<12} {'N/A':<12} {'0':<12}")

# Rankings
print("\n" + "=" * 100)
print("RANKINGS")
print("=" * 100)

if summary_data:
    # Sort by different metrics
    by_return = sorted(summary_data, key=lambda x: x['return'], reverse=True)
    by_weekly = sorted(summary_data, key=lambda x: x['weekly'], reverse=True)
    by_pf = sorted(summary_data, key=lambda x: x['pf'], reverse=True)
    by_dd = sorted(summary_data, key=lambda x: x['dd'])  # Lower is better
    by_sharpe = sorted(summary_data, key=lambda x: x['sharpe'], reverse=True)

    print("\n🏆 Top 3 por Return Total:")
    for i, s in enumerate(by_return[:3], 1):
        print(f"  {i}. {s['name']}: {s['return']:+.2f}%")

    print("\n📈 Top 3 por Return Semanal:")
    for i, s in enumerate(by_weekly[:3], 1):
        print(f"  {i}. {s['name']}: {s['weekly']:+.2f}%")

    print("\n💰 Top 3 por Profit Factor:")
    for i, s in enumerate(by_pf[:3], 1):
        print(f"  {i}. {s['name']}: {s['pf']:.2f}")

    print("\n🛡️  Top 3 por Menor Drawdown:")
    for i, s in enumerate(by_dd[:3], 1):
        print(f"  {i}. {s['name']}: {s['dd']:.2f}%")

    print("\n📊 Top 3 por Sharpe Ratio:")
    for i, s in enumerate(by_sharpe[:3], 1):
        print(f"  {i}. {s['name']}: {s['sharpe']:.2f}")

    # Overall winner
    print("\n" + "=" * 100)
    print("🌟 GANADOR ABSOLUTO (basado en return ajustado por riesgo):")
    print("=" * 100)

    # Calculate score: (return * pf) / (dd if dd > 0 else 1)
    for s in summary_data:
        risk_adj_return = (s['return'] * s['pf']) / (s['dd'] if s['dd'] > 0 else 1)
        s['score'] = risk_adj_return

    winner = max(summary_data, key=lambda x: x['score'])

    print(f"\n🏆 {winner['name']}")
    print(f"   Return: {winner['return']:+.2f}%")
    print(f"   Weekly: {winner['weekly']:+.2f}%")
    print(f"   Profit Factor: {winner['pf']:.2f}")
    print(f"   Max DD: {winner['dd']:.2f}%")
    print(f"   Sharpe: {winner['sharpe']:.2f}")
    print(f"   Total Trades: {winner['trades']}")
    print(f"   Win Rate: {winner['wr']:.1f}%")

    # Best by category
    print("\n📋 MEJOR POR CATEGORÍA:")
    print(f"   Mejor Return: {by_return[0]['name']} ({by_return[0]['return']:+.2f}%)")
    print(f"   Mejor Sharpe: {by_sharpe[0]['name']} ({by_sharpe[0]['sharpe']:.2f})")
    print(f"   Menor DD: {by_dd[0]['name']} ({by_dd[0]['dd']:.2f}%)")

    # Analysis
    print("\n" + "=" * 100)
    print("ANÁLISIS:")
    print("=" * 100)

    positive_strats = [s for s in summary_data if s['return'] > 0]
    negative_strats = [s for s in summary_data if s['return'] < 0]

    print(f"\nEstrategias rentables: {len(positive_strats)} de {len(summary_data)}")
    print(f"Estrategias con pérdidas: {len(negative_strats)} de {len(summary_data)}")

    if positive_strats:
        best_positive = max(positive_strats, key=lambda x: x['return'])
        print(f"\nMejor estrategia rentable: {best_positive['name']}")
        print(f"  Return: {best_positive['return']:+.2f}%")
        print(f"  Risk/Reward: PF {best_positive['pf']:.2f}, DD {best_positive['dd']:.2f}%")

        if best_positive['weekly'] >= 0.5:
            print(f"\n✓ {best_positive['name']} alcanza {best_positive['weekly']:+.2f}% semanal")
            print(f"  Esto proyecta a {best_positive['weekly'] * 52:.1f}% anual")
        else:
            print(f"\n⚠️ Return semanal bajo ({best_positive['weekly']:+.2f}%)")
            print(f"   Considera aumentar leverage o optimizar parámetros")

    if all(s['return'] < 0 for s in summary_data):
        print("\n⚠️ TODAS LAS ESTRATEGIAS CON PÉRDIDAS")
        print("   Posibles razones:")
        print("   - Periodo de test desfavorable (últimos 7 días)")
        print("   - Mercado en rango bajo (sin tendencias ni reversiones claras)")
        print("   - Fees muy altos vs retornos")
        print("\n   Recomendaciones:")
        print("   - Probar en periodo más largo (30-60 días)")
        print("   - Probar en datos históricos volátiles (Nov 2024, etc)")
        print("   - Optimizar thresholds/parámetros por par")

else:
    print("\n⚠️ Ninguna estrategia generó trades")
    print("   Descarga datos: python3 download_1m_data.py")

print("\n" + "=" * 100)
print("COMPARACIÓN COMPLETA")
print("=" * 100)
