#!/usr/bin/env python3
"""
Download data for Momentum Strategies (5m and 15m)

Momentum strategies need:
- Scalper Pro: 5m data
- Momentum Hunter: 15m data
- Hybrid Alpha: 15m data
"""

from engine.data_loader import load_data
from datetime import datetime, timedelta

PAIRS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
TIMEFRAMES = ['5m', '15m']
DAYS_BACK = 60  # 60 días para test mensual

end_date = datetime.now()
start_date = end_date - timedelta(days=DAYS_BACK)

start_str = start_date.strftime('%Y-%m-%d')
end_str = end_date.strftime('%Y-%m-%d')

print("=" * 70)
print("DESCARGA DE DATOS PARA ESTRATEGIAS MOMENTUM")
print("=" * 70)
print(f"Periodo: {start_str} to {end_str} ({DAYS_BACK} días)")
print(f"Pairs: {', '.join(PAIRS)}")
print(f"Timeframes: {', '.join(TIMEFRAMES)}")
print("=" * 70)
print()

total_success = 0
total_attempts = 0

for timeframe in TIMEFRAMES:
    print(f"\n{'=' * 70}")
    print(f"TIMEFRAME: {timeframe}")
    print(f"{'=' * 70}")

    for symbol in PAIRS:
        total_attempts += 1
        print(f"\n{symbol} {timeframe}...", end=' ')

        try:
            df = load_data(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_str,
                end_date=end_str,
                data_dir='./data/binance',
                use_cache=False  # Force fresh download
            )

            days = len(df) * {'5m': 5, '15m': 15, '1m': 1}[timeframe] / (60 * 24)
            print(f"✓ {len(df):,} candles ({days:.1f} días)")
            total_success += 1

        except Exception as e:
            print(f"✗ Error: {str(e)[:60]}")

print()
print("=" * 70)
print(f"Descarga completa: {total_success}/{total_attempts} exitosas")
print("=" * 70)

if total_success == total_attempts:
    print("\n✓✓✓ Todos los datos descargados correctamente!")
    print("\nAhora puedes correr:")
    print("  python3 test_momentum_monthly.py")
    print()
elif total_success > 0:
    print(f"\n⚠️ Solo {total_success} de {total_attempts} descargados")
    print("Algunas estrategias pueden no funcionar.")
    print()
else:
    print("\n✗✗✗ Ninguna descarga exitosa")
    print("Verifica tu conexión a internet.")
    print()
