#!/usr/bin/env python3
"""
Test Momentum Strategies - 30-60 días para ver retornos MENSUALES

Las estrategias momentum con 10x leverage que funcionaban:
- Scalper Pro
- Momentum Hunter
- Hybrid Alpha
"""

from engine.backtester import Backtester
from strategies.scalper_pro import ScalperProStrategy
from strategies.momentum_hunter import MomentumHunterStrategy
from strategies.hybrid_alpha import HybridAlphaStrategy
from datetime import datetime, timedelta

STRATEGIES = {
    'Scalper Pro': {
        'class': ScalperProStrategy,
        'timeframe': '5m',
        'leverage': 10.0,
        'desc': 'RSI scalping (5m)',
        'taker_fee': 0.0006,
        'slippage': 5.0,
    },
    'Momentum Hunter': {
        'class': MomentumHunterStrategy,
        'timeframe': '15m',
        'leverage': 10.0,
        'desc': 'Volume breakouts (15m)',
        'taker_fee': 0.0006,
        'slippage': 3.0,
    },
    'Hybrid Alpha': {
        'class': HybridAlphaStrategy,
        'timeframe': '15m',
        'leverage': 10.0,
        'desc': 'Hybrid strategy (15m)',
        'taker_fee': 0.0006,
        'slippage': 3.0,
    },
}

# Test periods
PERIODS = {
    '30 días': 30,
    '60 días': 60,
}

PAIRS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
INITIAL_BALANCE = 10000

print("=" * 100)
print("TEST MOMENTUM STRATEGIES - Retornos Mensuales (10x leverage)")
print("=" * 100)
print()

for period_name, days_back in PERIODS.items():
    print(f"\n{'=' * 100}")
    print(f"PERIODO: {period_name}")
    print(f"{'=' * 100}")

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    print(f"Desde {start_date.strftime('%Y-%m-%d')} hasta {end_date.strftime('%Y-%m-%d')}")
    print()

    all_results = {}

    for strategy_name, strategy_config in STRATEGIES.items():
        print(f"\n{strategy_name} - {strategy_config['desc']} | {strategy_config['leverage']}x leverage")
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
                    taker_fee=strategy_config['taker_fee'],
                    slippage_bps=strategy_config['slippage'],
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

                # Calculate weekly and monthly
                weekly_ret = (total_ret / days_back) * 7
                monthly_ret = (total_ret / days_back) * 30

                strategy_results.append({
                    'symbol': symbol,
                    'return': total_ret,
                    'weekly': weekly_ret,
                    'monthly': monthly_ret,
                    'trades': trades,
                    'wr': wr,
                    'pf': pf,
                    'dd': dd
                })

                status = "✓" if total_ret > 0 else "✗"
                print(f"{status} {total_ret:+7.2f}% | Monthly {monthly_ret:+7.2f}% | {trades:3d} trades | WR {wr:5.1f}%")

            except Exception as e:
                print(f"ERROR: {str(e)[:60]}")
                strategy_results.append({
                    'symbol': symbol,
                    'return': 0,
                    'weekly': 0,
                    'monthly': 0,
                    'trades': 0,
                    'wr': 0,
                    'pf': 0,
                    'dd': 0
                })

        all_results[strategy_name] = strategy_results

        # Strategy summary
        valid = [r for r in strategy_results if r['trades'] > 0]
        if valid:
            avg_ret = sum(r['return'] for r in valid) / len(valid)
            avg_monthly = sum(r['monthly'] for r in valid) / len(valid)
            avg_weekly = sum(r['weekly'] for r in valid) / len(valid)
            total_trades = sum(r['trades'] for r in valid)
            avg_wr = sum(r['wr'] for r in valid) / len(valid)

            print(f"\n  PROMEDIO: {avg_ret:+.2f}% total | {avg_monthly:+.2f}% mensual | {avg_weekly:+.2f}% semanal")
            print(f"  {total_trades} trades | {avg_wr:.1f}% WR")

    # Period summary
    print(f"\n{'=' * 100}")
    print(f"RESUMEN {period_name.upper()}")
    print(f"{'=' * 100}")
    print(f"{'Strategy':<20} {'Avg Return%':<12} {'Monthly%':<12} {'Weekly%':<12} {'Trades':<8} {'WR%':<8} {'PF':<8}")
    print("-" * 100)

    period_summary = []

    for strategy_name, results in all_results.items():
        valid = [r for r in results if r['trades'] > 0]

        if valid:
            avg_ret = sum(r['return'] for r in valid) / len(valid)
            avg_monthly = sum(r['monthly'] for r in valid) / len(valid)
            avg_weekly = sum(r['weekly'] for r in valid) / len(valid)
            total_trades = sum(r['trades'] for r in valid)
            avg_wr = sum(r['wr'] for r in valid) / len(valid)
            avg_pf = sum(r['pf'] for r in valid) / len(valid)

            period_summary.append({
                'name': strategy_name,
                'return': avg_ret,
                'monthly': avg_monthly,
                'weekly': avg_weekly,
                'trades': total_trades,
                'wr': avg_wr,
                'pf': avg_pf
            })

            print(
                f"{strategy_name:<20} "
                f"{avg_ret:+10.2f}% "
                f"{avg_monthly:+10.2f}% "
                f"{avg_weekly:+10.2f}% "
                f"{total_trades:<8} "
                f"{avg_wr:<8.1f} "
                f"{avg_pf:<8.2f}"
            )

    if period_summary:
        print("\n🏆 MEJOR ESTRATEGIA:")
        best = max(period_summary, key=lambda x: x['monthly'])
        print(f"   {best['name']}")
        print(f"   Return mensual: {best['monthly']:+.2f}%")
        print(f"   Return semanal: {best['weekly']:+.2f}%")
        print(f"   Trades: {best['trades']}")
        print(f"   Win Rate: {best['wr']:.1f}%")
        print(f"   Profit Factor: {best['pf']:.2f}")

        if best['monthly'] >= 12:  # 12% mensual = 3% semanal
            print(f"\n   ✓✓✓ CUMPLE objetivo de 3%+ semanal!")
        elif best['monthly'] >= 8:
            print(f"\n   ✓✓ Cerca del objetivo (2%+ semanal)")
        elif best['monthly'] >= 4:
            print(f"\n   ✓ Rentable pero bajo objetivo (1%+ semanal)")
        else:
            print(f"\n   ⚠️ Por debajo del objetivo (<1% semanal)")

print("\n" + "=" * 100)
print("CONCLUSIÓN")
print("=" * 100)
print()
print("Compara los resultados de 30 días vs 60 días.")
print("La estrategia que funciona consistentemente en ambos periodos")
print("es la que debes usar para producción.")
print()
