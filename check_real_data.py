#!/usr/bin/env python3
"""
Revisar datos reales de BTCUSDT para ver rangos de movimiento
"""

from engine.data_loader import load_data
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

print("=" * 70)
print("ANÁLISIS DE DATOS REALES - BTCUSDT 1m")
print("=" * 70)

end_date = datetime.now()
start_date = end_date - timedelta(days=7)

print(f"\nCargando datos {start_date.strftime('%Y-%m-%d')} a {end_date.strftime('%Y-%m-%d')}...")

try:
    df = load_data(
        symbol='BTCUSDT',
        timeframe='1m',
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d'),
        data_dir='./data/binance',
        use_cache=True
    )

    print(f"✓ {len(df)} candles cargados\n")

    # Calculate various lookback means
    for lookback in [30, 60, 120, 240]:
        rolling_high = df['high'].rolling(lookback).max()
        rolling_low = df['low'].rolling(lookback).min()
        mean_price = (rolling_high + rolling_low) / 2
        distance_pct = ((df['close'] - mean_price) / mean_price * 100)

        valid = distance_pct.dropna()

        print(f"Lookback {lookback} candles ({lookback} min = {lookback/60:.1f}h):")
        print(f"  Distance range: {valid.min():.2f}% to {valid.max():.2f}%")
        print(f"  Std dev: {valid.std():.2f}%")

        # Count threshold crossings
        for threshold in [0.3, 0.5, 1.0, 1.5, 2.0]:
            crosses = (abs(valid) >= threshold).sum()
            pct = crosses / len(valid) * 100 if len(valid) > 0 else 0
            print(f"    Cruza ±{threshold}%: {crosses} veces ({pct:.1f}%)")

        print()

    # Overall statistics
    print("Estadísticas generales:")
    print(f"  Precio min: ${df['low'].min():.2f}")
    print(f"  Precio max: ${df['high'].max():.2f}")
    print(f"  Rango total: {(df['high'].max() - df['low'].min()) / df['close'].mean() * 100:.2f}%")

    # Daily ranges
    df['date'] = pd.to_datetime(df['timestamp']).dt.date
    daily_stats = df.groupby('date').agg({
        'high': 'max',
        'low': 'min',
        'close': 'mean'
    })
    daily_stats['range_pct'] = (daily_stats['high'] - daily_stats['low']) / daily_stats['close'] * 100

    print(f"\nRangos diarios:")
    for date, row in daily_stats.iterrows():
        print(f"  {date}: {row['range_pct']:.2f}%")

    print(f"\nPromedio rango diario: {daily_stats['range_pct'].mean():.2f}%")

    # Recommendation
    avg_range = daily_stats['range_pct'].mean()
    print("\n" + "=" * 70)
    print("RECOMENDACIÓN:")
    print("=" * 70)

    if avg_range < 2:
        print("⚠️ Mercado MUY estable (rango diario < 2%)")
        print("   Usar thresholds: ±0.3%, ±0.6%")
        print("   O cambiar a timeframe 5m/15m")
    elif avg_range < 4:
        print("✓ Mercado estable (rango diario 2-4%)")
        print("   Usar thresholds: ±0.5%, ±1.0%")
    else:
        print("✓ Mercado volátil (rango diario > 4%)")
        print("   Usar thresholds: ±1.0%, ±2.0%")

except Exception as e:
    print(f"\n✗ ERROR: {e}")
    print("\nPosiblemente no hay datos descargados.")
    print("Corre: python3 download_1m_data.py")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
