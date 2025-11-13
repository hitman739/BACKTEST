#!/usr/bin/env python3
"""
Test VRR Ultra Strategy on SOLUSDT 1m - Last 60 Days
Ultra clean exits - NO aggressive exits, only TPs/Trailing/SL
"""

from datetime import datetime, timedelta
from engine.backtester import Backtester
from strategies.vrr_ultra import VRRUltra
from engine.metrics import format_metrics_table
from engine.reporter import generate_report
import pandas as pd

print("=" * 70)
print("🚀 VRR ULTRA BACKTEST - SOLUSDT 1m - Últimos 60 días")
print("=" * 70)

# Calcular fechas (últimos 60 días)
end_date = datetime(2025, 11, 13)
start_date = end_date - timedelta(days=60)

print(f"\nPeríodo: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}")
print("Symbol: SOLUSDT")
print("Timeframe: 1 minuto")
print("Equity inicial: $10,000")
print("Leverage: 10x")
print()

# Crear estrategia VRR ULTRA
strategy = VRRUltra()
print(f"Estrategia: {strategy.name}")
print("\n🔧 VRR Ultra - CLEAN EXITS:")
print("  ✅ Stop Loss (protección)")
print("  ✅ TP1: 1.5R (50% profit)")
print("  ✅ TP2: 2.5R (resto)")
print("  ✅ Trailing: activa a 1.2R, distancia 0.5R")
print("  ✅ New Impulse (setup invalidado)")
print("  ✅ Timeout: 8 bars máximo")
print("\n  ❌ VWAP cross: DESACTIVADO")
print("  ❌ Volume exhaustion: DESACTIVADO")
print("  ❌ Counter candle: DESACTIVADO")
print()

# Configurar backtester
backtester = Backtester(
    strategy=strategy,
    symbol='SOLUSDT',
    timeframe='1m',
    start_date=start_date.strftime('%Y-%m-%d'),
    end_date=end_date.strftime('%Y-%m-%d'),
    initial_balance=10000,
    leverage=10,
    maker_fee=0.0002,
    taker_fee=0.0004,
    slippage_bps=3.0
)

# Ejecutar backtest
print("\n⏳ Ejecutando backtest ultra (puede tomar unos segundos)...")
print("-" * 70)

try:
    results = backtester.run()

    print("-" * 70)

    # Generar reporte
    report_name = f"vrr_ultra_sol_1m_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    generate_report(
        run_id=report_name,
        metrics=results['metrics'],
        config=results['config'],
        trades_df=results['trades'],
        equity_curve_df=results['equity_curve']
    )

    # Mostrar resultados principales
    print("\n" + "=" * 70)
    print("📊 RESULTADOS PRINCIPALES")
    print("=" * 70)
    print(format_metrics_table(results['metrics']))

    # Análisis detallado de trades
    if len(results['trades']) > 0:
        trades_df = results['trades']

        print("\n" + "=" * 70)
        print("📈 ANÁLISIS DETALLADO")
        print("=" * 70)

        print(f"\n✅ Total de Trades: {len(trades_df)}")
        print(f"💰 Ganadores: {(trades_df['net_pnl'] > 0).sum()}")
        print(f"❌ Perdedores: {(trades_df['net_pnl'] <= 0).sum()}")

        # Exit reasons
        if 'exit_reason' in trades_df.columns:
            print("\n📊 Razones de Salida:")
            exit_counts = trades_df['exit_reason'].value_counts()
            for reason, count in exit_counts.items():
                pct = (count / len(trades_df)) * 100
                print(f"  • {reason:20s}: {count:3d} trades ({pct:5.1f}%)")

        # Top trades
        print("\n💎 Top 5 Mejores Trades:")
        top_cols = ['entry_time', 'side', 'entry_price', 'exit_price', 'net_pnl', 'exit_reason']
        available_cols = [col for col in top_cols if col in trades_df.columns]
        top_trades = trades_df.nlargest(5, 'net_pnl')[available_cols]
        print(top_trades.to_string(index=False))

        print("\n📉 Top 5 Peores Trades:")
        worst_trades = trades_df.nsmallest(5, 'net_pnl')[available_cols]
        print(worst_trades.to_string(index=False))

        # Duración
        if 'duration_bars' in trades_df.columns:
            print(f"\n⏱️  Duración promedio: {trades_df['duration_bars'].mean():.1f} minutos")
            print(f"   Duración mínima: {trades_df['duration_bars'].min():.0f} minutos")
            print(f"   Duración máxima: {trades_df['duration_bars'].max():.0f} minutos")

        # Comparación
        print("\n" + "=" * 70)
        print("🔄 COMPARACIÓN CON VERSIONES ANTERIORES (60 días)")
        print("=" * 70)
        print("\nAdjusted (VWAP exits 62%):")
        print("  • PnL: -$777.60 | WR: 48.28% | PF: 0.51")
        print("\nOptimized (Volume exhaust 68%):")
        print("  • PnL: -$898.00 | WR: 42.11% | PF: 0.64")

        win_rate = (trades_df['net_pnl'] > 0).sum() / len(trades_df) * 100
        print(f"\nUltra (Clean exits):")
        total_pnl = results['metrics'].get('total_pnl', 0)
        pf = results['metrics'].get('profit_factor', 0)
        print(f"  • PnL: ${total_pnl:.2f} | WR: {win_rate:.2f}% | PF: {pf:.2f}")

    else:
        print("\n⚠️  NO SE GENERARON TRADES")

    print("\n" + "=" * 70)
    print(f"📁 Reportes guardados en: reports/{report_name}/")
    print("=" * 70)

    print("\n✅ Backtest completado exitosamente!")

except Exception as e:
    print(f"\n❌ Error durante el backtest: {e}")
    import traceback
    traceback.print_exc()
