#!/usr/bin/env python3
"""
Test VRR Strategy on SOLUSDT 1m - Last 30 Days
Simple script to run VRR backtest
"""

from datetime import datetime, timedelta
from engine.backtester import Backtester
from strategies.vrr_adjusted import VRRAdjusted
from engine.metrics import format_metrics_table
from engine.reporter import generate_report
import pandas as pd

print("=" * 70)
print("🚀 VRR BACKTEST - SOLUSDT 1m - Últimos 60 días")
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

# Crear estrategia VRR
strategy = VRRAdjusted()
print(f"Estrategia: {strategy.name}")

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
print("\n⏳ Ejecutando backtest (puede tomar unos segundos)...")
print("-" * 70)

try:
    results = backtester.run()

    print("-" * 70)

    # Generar reporte
    report_name = f"vrr_sol_1m_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
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

        # Por calidad de setup
        if 'setup_quality' in trades_df.columns:
            print("\n⭐ Performance por Calidad de Setup:")
            for quality in ['extreme', 'high', 'moderate']:
                q_trades = trades_df[trades_df['setup_quality'] == quality]
                if len(q_trades) > 0:
                    wins = (q_trades['net_pnl'] > 0).sum()
                    win_rate = (wins / len(q_trades)) * 100
                    avg_pnl = q_trades['net_pnl'].mean()
                    total_pnl = q_trades['net_pnl'].sum()
                    print(f"  • {quality:10s}: {len(q_trades):3d} trades | "
                          f"WR: {win_rate:5.1f}% | "
                          f"Avg: ${avg_pnl:7.2f} | "
                          f"Total: ${total_pnl:7.2f}")

        # Top trades
        print("\n💎 Top 5 Mejores Trades:")
        top_cols = ['entry_time', 'side', 'entry_price', 'exit_price', 'net_pnl', 'exit_reason']
        available_cols = [col for col in top_cols if col in trades_df.columns]
        top_trades = trades_df.nlargest(5, 'net_pnl')[available_cols]
        print(top_trades.to_string(index=False))

        print("\n📉 Top 5 Peores Trades:")
        worst_trades = trades_df.nsmallest(5, 'net_pnl')[available_cols]
        print(worst_trades.to_string(index=False))

        # Estadísticas de duración
        if 'duration_bars' in trades_df.columns:
            print(f"\n⏱️  Duración promedio: {trades_df['duration_bars'].mean():.1f} minutos")
            print(f"   Duración mínima: {trades_df['duration_bars'].min():.0f} minutos")
            print(f"   Duración máxima: {trades_df['duration_bars'].max():.0f} minutos")

    else:
        print("\n⚠️  NO SE GENERARON TRADES")
        print("\n¿Por qué?")
        print("  • Los filtros pueden ser muy estrictos")
        print("  • El mercado no tuvo suficiente volatilidad")
        print("  • Los datos sintéticos no tienen las características necesarias")
        print("\n💡 Soluciones:")
        print("  1. Ejecuta: python3 debug_vrr.py")
        print("  2. Usa datos reales de Binance (modifica use_cache=False)")
        print("  3. Ajusta parámetros en strategies/vrr_adjusted.py")

    print("\n" + "=" * 70)
    print(f"📁 Reportes guardados en: reports/{report_name}/")
    print("=" * 70)

    print("\n✅ Backtest completado exitosamente!")

except Exception as e:
    print(f"\n❌ Error durante el backtest: {e}")
    import traceback
    traceback.print_exc()
    print("\n💡 Tip: Asegúrate de haber generado datos primero:")
    print("   python3 generate_sol_data.py")
