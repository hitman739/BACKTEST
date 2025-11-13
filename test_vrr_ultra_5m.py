#!/usr/bin/env python3
"""
Test VRR Ultra Strategy on SOLUSDT 5m - Last 60 Days
Ultra clean exits in 5-minute timeframe
Less noise, cleaner signals, better R/R
"""

from datetime import datetime, timedelta
from engine.backtester import Backtester
from strategies.vrr_ultra import VRRUltra
from engine.metrics import format_metrics_table
from engine.reporter import generate_report
import pandas as pd

print("=" * 70)
print("🚀 VRR ULTRA BACKTEST - SOLUSDT 5m - Últimos 60 días")
print("=" * 70)

# Calcular fechas (últimos 60 días)
end_date = datetime(2025, 11, 13)
start_date = end_date - timedelta(days=60)

print(f"\nPeríodo: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}")
print("Symbol: SOLUSDT")
print("Timeframe: 5 minutos")
print("Equity inicial: $10,000")
print("Leverage: 10x")
print()

# Crear estrategia VRR ULTRA
strategy = VRRUltra()
print(f"Estrategia: {strategy.name}")
print("\n🎯 VRR Ultra en 5m - VENTAJAS:")
print("  ✅ Menos ruido vs 1m")
print("  ✅ ATR más amplio → stops más holgados")
print("  ✅ Trailing stop tiene más espacio")
print("  ✅ Trades duran 10-20 minutos (vs 1-3 min)")
print("  ✅ TPs más alcanzables (precio tiene tiempo)")
print("\n🔧 CLEAN EXITS:")
print("  ✅ Stop Loss, TP1 (1.5R), TP2 (2.5R)")
print("  ✅ Trailing: activa a 1.2R")
print("  ❌ Sin VWAP, Volume exhaustion, Counter candle")
print()

# Configurar backtester
backtester = Backtester(
    strategy=strategy,
    symbol='SOLUSDT',
    timeframe='5m',
    start_date=start_date.strftime('%Y-%m-%d'),
    end_date=end_date.strftime('%Y-%m-%d'),
    initial_balance=10000,
    leverage=10,
    maker_fee=0.0002,
    taker_fee=0.0004,
    slippage_bps=3.0
)

# Ejecutar backtest
print("\n⏳ Ejecutando backtest ultra 5m (puede tomar unos segundos)...")
print("-" * 70)

try:
    results = backtester.run()

    print("-" * 70)

    # Generar reporte
    report_name = f"vrr_ultra_sol_5m_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
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
            duration_mins = trades_df['duration_bars'].mean() * 5  # 5m bars
            print(f"\n⏱️  Duración promedio: {duration_mins:.1f} minutos ({trades_df['duration_bars'].mean():.1f} bars)")
            print(f"   Duración mínima: {trades_df['duration_bars'].min() * 5:.0f} minutos")
            print(f"   Duración máxima: {trades_df['duration_bars'].max() * 5:.0f} minutos")

        # Comparación
        print("\n" + "=" * 70)
        print("🔄 COMPARACIÓN 1m vs 5m")
        print("=" * 70)
        print("\n1m Ultra (esperado):")
        print("  • Trades: ~35-40")
        print("  • Duración: 2-5 min")
        print("  • Win Rate: ~50%")

        win_rate = (trades_df['net_pnl'] > 0).sum() / len(trades_df) * 100
        print(f"\n5m Ultra (actual):")
        total_pnl = results['metrics'].get('total_pnl', 0)
        pf = results['metrics'].get('profit_factor', 0)
        print(f"  • Trades: {len(trades_df)}")
        print(f"  • Duración: {duration_mins:.1f} min")
        print(f"  • Win Rate: {win_rate:.2f}%")
        print(f"  • PnL: ${total_pnl:.2f}")
        print(f"  • Profit Factor: {pf:.2f}")

        # Expectativas
        if pf > 1.0:
            print("\n🎉 ✅ PROFITABLE! Profit Factor > 1.0")
        else:
            print(f"\n⚠️  Profit Factor {pf:.2f} < 1.0 - Necesita más optimización")

    else:
        print("\n⚠️  NO SE GENERARON TRADES")
        print("\n💡 Posibles razones:")
        print("  • 5m tiene menos barras → menos setups")
        print("  • Necesitas regenerar datos para 5m: python3 generate_sol_data_5m.py")

    print("\n" + "=" * 70)
    print(f"📁 Reportes guardados en: reports/{report_name}/")
    print("=" * 70)

    print("\n✅ Backtest completado exitosamente!")

except Exception as e:
    print(f"\n❌ Error durante el backtest: {e}")
    import traceback
    traceback.print_exc()
    print("\n💡 Asegúrate de generar datos primero:")
    print("   python3 generate_sol_data_5m.py")
