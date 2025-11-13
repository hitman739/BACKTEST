#!/usr/bin/env python3
"""
Test VRR Optimized Strategy on SOLUSDT 1m - Last 60 Days
Testing version with fixes for common issues
"""

from datetime import datetime, timedelta
from engine.backtester import Backtester
from strategies.vrr_optimized import VRROptimized
from engine.metrics import format_metrics_table
from engine.reporter import generate_report
import pandas as pd

print("=" * 70)
print("🚀 VRR OPTIMIZED BACKTEST - SOLUSDT 1m - Últimos 60 días")
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

# Crear estrategia VRR OPTIMIZADA
strategy = VRROptimized()
print(f"Estrategia: {strategy.name}")
print("\n🔧 Optimizaciones aplicadas:")
print("  ✓ VWAP cross exit DESACTIVADO (estaba cerrando 63.6% de trades)")
print("  ✓ TP1: 1.5R (antes 1.8R) - más fácil de alcanzar")
print("  ✓ TP2: 2.5R (antes 3.0R) - más realista")
print("  ✓ Trailing activation: 1.2R (antes 2.0R) - se activa más rápido")
print("  ✓ Max wait: 8 bars (antes 5) - más paciencia")
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
print("\n⏳ Ejecutando backtest optimizado (puede tomar unos segundos)...")
print("-" * 70)

try:
    results = backtester.run()

    print("-" * 70)

    # Generar reporte
    report_name = f"vrr_optimized_sol_1m_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
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

        # Comparación con versión anterior
        print("\n" + "=" * 70)
        print("🔄 COMPARACIÓN CON VERSIÓN ANTERIOR")
        print("=" * 70)
        print("Versión Adjusted (30 días):")
        print("  • Win Rate: 45.45%")
        print("  • Profit Factor: 0.42")
        print("  • Avg Win/Loss: $34 / $-67")
        print("  • VWAP exits: 63.6%")
        print(f"\nVersión Optimized (60 días):")
        win_rate = (trades_df['net_pnl'] > 0).sum() / len(trades_df) * 100
        print(f"  • Win Rate: {win_rate:.2f}%")
        print(f"  • Profit Factor: {results['metrics'].get('profit_factor', 0):.2f}")
        avg_win = trades_df[trades_df['net_pnl'] > 0]['net_pnl'].mean() if (trades_df['net_pnl'] > 0).any() else 0
        avg_loss = trades_df[trades_df['net_pnl'] <= 0]['net_pnl'].mean() if (trades_df['net_pnl'] <= 0).any() else 0
        print(f"  • Avg Win/Loss: ${avg_win:.2f} / ${avg_loss:.2f}")
        vwap_exits = exit_counts.get('vwap_cross', 0) if 'exit_reason' in trades_df.columns else 0
        vwap_pct = (vwap_exits / len(trades_df) * 100) if len(trades_df) > 0 else 0
        print(f"  • VWAP exits: {vwap_pct:.1f}% (debería ser 0%)")

    else:
        print("\n⚠️  NO SE GENERARON TRADES")
        print("\n💡 Soluciones:")
        print("  1. Ejecuta: python3 debug_vrr.py")
        print("  2. Regenera datos: python3 generate_sol_data.py")
        print("  3. Ajusta parámetros en strategies/vrr_optimized.py")

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
