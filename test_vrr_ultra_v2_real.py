#!/usr/bin/env python3
"""
Test VRR Ultra v2 Strategy on REAL SOLUSDT 1m data - Last 60 Days

Improvements in v2:
- Wider stops (1.2× setup range) to reduce stop outs
- Closer TPs (1.3R/2.0R instead of 1.5R/2.5R) - more achievable
- Earlier trailing (1.0R vs 1.2R) - protect profits sooner
- More patience (10 bars vs 8)

Using REAL Binance data (not synthetic)
"""

from datetime import datetime, timedelta
from engine.backtester import Backtester
from strategies.vrr_ultra_v2 import VRRUltraV2
from engine.metrics import format_metrics_table
from engine.reporter import generate_report
import pandas as pd

print("=" * 70)
print("🚀 VRR ULTRA V2 BACKTEST - REAL SOLUSDT 1m - 60 días")
print("=" * 70)

# Calcular fechas (últimos 60 días)
end_date = datetime(2025, 11, 13)
start_date = end_date - timedelta(days=60)

print(f"\nPeríodo: {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}")
print("Symbol: SOLUSDT")
print("Timeframe: 1 minuto")
print("Data Source: 🌐 REAL BINANCE DATA")
print("Equity inicial: $10,000")
print("Leverage: 10x")
print()

# Crear estrategia VRR ULTRA V2
strategy = VRRUltraV2()
print(f"Estrategia: {strategy.name}")
print("\n✨ IMPROVEMENTS IN V2:")
print("  🎯 Closer TPs: TP1 1.3R, TP2 2.0R (more achievable, was 1.5R/2.5R)")
print("  🛡️  Earlier trailing: 1.0R activation (protect profits sooner, was 1.2R)")
print("  🔒 Tighter trailing: 0.4R distance (lock profits, was 0.5R)")
print("  ⏱️  More patience: 10 bars timeout (was 8)")
print("\n🎯 TARGET METRICS:")
print("  • Win Rate: >55%")
print("  • Profit Factor: >1.0 (PROFITABLE)")
print("  • Stop Losses: <30% (was 34.2%)")
print("  • TPs achieved: >30% (was 21.1%)")
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
print("\n⏳ Ejecutando backtest con DATOS REALES...")
print("   (Si es la primera vez, descargará de Binance API)")
print("-" * 70)

try:
    results = backtester.run()

    print("-" * 70)

    # Generar reporte
    report_name = f"vrr_ultra_v2_real_1m_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
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
        winners = (trades_df['net_pnl'] > 0).sum()
        losers = (trades_df['net_pnl'] <= 0).sum()
        print(f"💰 Ganadores: {winners}")
        print(f"❌ Perdedores: {losers}")

        # Exit reasons
        if 'exit_reason' in trades_df.columns:
            print("\n📊 Razones de Salida:")
            exit_counts = trades_df['exit_reason'].value_counts()
            for reason, count in exit_counts.items():
                pct = (count / len(trades_df)) * 100
                emoji = "✅" if reason in ['take_profit_2', 'trailing_stop'] else "⚠️" if reason in ['timeout', 'new_impulse'] else "❌"
                print(f"  {emoji} {reason:20s}: {count:3d} trades ({pct:5.1f}%)")

            # Compare with v1
            sl_pct = exit_counts.get('stop_loss', 0) / len(trades_df) * 100 if len(trades_df) > 0 else 0
            tp_pct = exit_counts.get('take_profit_2', 0) / len(trades_df) * 100 if len(trades_df) > 0 else 0
            print(f"\n  📉 Stop Losses: {sl_pct:.1f}% (target <30%, was 34.2% in v1)")
            print(f"  📈 TP2 achieved: {tp_pct:.1f}% (target >30%, was 21.1% in v1)")

        # Top trades
        print("\n💎 Top 5 Mejores Trades:")
        top_cols = ['entry_time', 'side', 'entry_price', 'exit_price', 'net_pnl', 'exit_reason']
        available_cols = [col for col in top_cols if col in trades_df.columns]
        top_trades = trades_df.nlargest(5, 'net_pnl')[available_cols]
        print(top_trades.to_string(index=False))

        print("\n📉 Top 5 Peores Trades:")
        worst_trades = trades_df.nsmallest(5, 'net_pnl')[available_cols]
        print(worst_trades.to_string(index=False))

        # R/R Analysis
        avg_win = trades_df[trades_df['net_pnl'] > 0]['net_pnl'].mean() if winners > 0 else 0
        avg_loss = trades_df[trades_df['net_pnl'] <= 0]['net_pnl'].mean() if losers > 0 else 0
        rr_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0

        print(f"\n💰 Risk/Reward Analysis:")
        print(f"   Avg Win: ${avg_win:.2f}")
        print(f"   Avg Loss: ${avg_loss:.2f}")
        print(f"   R/R Ratio: {rr_ratio:.2f} (target >1.0, was 0.71 in v1)")

        # Duración
        if 'duration_bars' in trades_df.columns:
            print(f"\n⏱️  Duración promedio: {trades_df['duration_bars'].mean():.1f} minutos")
            print(f"   Duración mínima: {trades_df['duration_bars'].min():.0f} minutos")
            print(f"   Duración máxima: {trades_df['duration_bars'].max():.0f} minutos")

        # Comparación con versiones anteriores
        print("\n" + "=" * 70)
        print("🔄 COMPARACIÓN CON VERSIONES ANTERIORES")
        print("=" * 70)
        print("\nAdjusted (synthetic data, VWAP exits):")
        print("  • PnL: -$777 | WR: 48.28% | PF: 0.51")
        print("\nOptimized (synthetic data, Vol exhaust):")
        print("  • PnL: -$898 | WR: 42.11% | PF: 0.64")
        print("\nUltra v1 (synthetic data, clean exits):")
        print("  • PnL: -$552 | WR: 55.26% | PF: 0.88")

        win_rate = winners / len(trades_df) * 100 if len(trades_df) > 0 else 0
        total_pnl = results['metrics'].get('total_pnl', 0)
        pf = results['metrics'].get('profit_factor', 0)

        print(f"\nUltra v2 (REAL data, improved params):")
        print(f"  • PnL: ${total_pnl:.2f} | WR: {win_rate:.2f}% | PF: {pf:.2f}")

        if pf >= 1.0:
            print("\n🎉 🎉 🎉 PROFITABLE! Profit Factor >= 1.0 🎉 🎉 🎉")
        elif pf >= 0.95:
            print("\n✨ Almost there! Very close to profitable")
        else:
            print(f"\n⚠️  Still needs optimization (PF {pf:.2f} < 1.0)")

    else:
        print("\n⚠️  NO SE GENERARON TRADES")
        print("\n💡 Asegúrate de haber descargado datos reales:")
        print("   python3 download_real_data.py")

    print("\n" + "=" * 70)
    print(f"📁 Reportes guardados en: reports/{report_name}/")
    print("=" * 70)

    print("\n✅ Backtest completado exitosamente!")

except Exception as e:
    print(f"\n❌ Error durante el backtest: {e}")
    import traceback
    traceback.print_exc()
    print("\n💡 Si hay error de datos, ejecuta primero:")
    print("   python3 download_real_data.py")
