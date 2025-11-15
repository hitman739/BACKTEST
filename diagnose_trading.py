#!/usr/bin/env python3
"""
Diagnóstico detallado de por qué no hay trades
"""

from engine.backtester import Backtester
from strategies.simple_mean_revert import SimpleMeanRevertStrategy
from datetime import datetime, timedelta
import pandas as pd

print("=" * 70)
print("DIAGNÓSTICO: Por qué SimpleMeanRevert no genera trades")
print("=" * 70)

strategy = SimpleMeanRevertStrategy()

# Test con últimos 7 días
end_date = datetime.now()
start_date = end_date - timedelta(days=7)

print(f"\nConfiguración de la estrategia:")
print(f"  mean_type: {strategy.mean_type.value}")
print(f"  mean_lookback: {strategy.mean_lookback}")
print(f"  long_thresholds: {strategy.long_thresholds}")
print(f"  short_thresholds: {strategy.short_thresholds}")
print(f"  min_atr_ratio: {strategy.min_atr_ratio}")
print(f"  max_atr_ratio: {strategy.max_atr_ratio}")
print(f"  min_vol_ratio: {strategy.min_vol_ratio}")
print(f"  max_vol_ratio: {strategy.max_vol_ratio}")
print(f"  trading_hours: {strategy.trading_hours}")
print(f"  one_side_only: {strategy.one_side_only}")
print()

print("Creando backtester...")
try:
    backtester = Backtester(
        strategy=strategy,
        symbol='BTCUSDT',
        timeframe='1m',
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d'),
        initial_balance=10000,
        leverage=5.0,
        taker_fee=0.0006,
        slippage_bps=3.0,
        data_dir='./data/binance',
        use_cache=True
    )

    # Load and initialize data
    print("Cargando datos...")
    data = backtester.load_data()
    print(f"✓ Datos cargados: {len(data)} candles")

    print("\nInicializando estrategia (calculando indicadores)...")
    data = backtester.initialize_strategy(data)
    print(f"✓ Indicadores calculados")

    # Check for NaN values
    print("\nVerificando valores NaN:")
    print(f"  mean_price NaN: {data['mean_price'].isna().sum()} / {len(data)}")
    print(f"  distance_pct NaN: {data['distance_pct'].isna().sum()} / {len(data)}")
    print(f"  atr_ratio NaN: {data['atr_ratio'].isna().sum()} / {len(data)}")
    print(f"  vol_ratio NaN: {data['vol_ratio'].isna().sum()} / {len(data)}")

    # Get first valid row
    valid_data = data.dropna(subset=['distance_pct', 'mean_price'])
    print(f"\nDatos válidos (no-NaN): {len(valid_data)} / {len(data)}")

    if len(valid_data) == 0:
        print("\n❌ ERROR: Todos los datos son NaN!")
        print("   El lookback de 60 no debería causar esto.")
        print("   Verifica que los datos se descargaron correctamente.")
    else:
        print(f"✓ Primeros {min(60, len(valid_data))} datos válidos (después de warmup)")

        # Statistics on distance_pct
        dist = valid_data['distance_pct']
        print(f"\nEstadísticas de distance_pct:")
        print(f"  Min: {dist.min():.2f}%")
        print(f"  Max: {dist.max():.2f}%")
        print(f"  Mean: {dist.mean():.2f}%")
        print(f"  Std: {dist.std():.2f}%")

        # Check threshold crossings
        print(f"\nCruces de threshold:")
        long_t1 = strategy.long_thresholds[0]  # -2.0
        long_t2 = strategy.long_thresholds[1]  # -4.0
        short_t1 = strategy.short_thresholds[0]  # +2.0
        short_t2 = strategy.short_thresholds[1]  # +4.0

        long_cross_1 = (dist <= long_t1).sum()
        long_cross_2 = (dist <= long_t2).sum()
        short_cross_1 = (dist >= short_t1).sum()
        short_cross_2 = (dist >= short_t2).sum()

        print(f"  distance <= {long_t1}%: {long_cross_1} veces")
        print(f"  distance <= {long_t2}%: {long_cross_2} veces")
        print(f"  distance >= {short_t1}%: {short_cross_1} veces")
        print(f"  distance >= {short_t2}%: {short_cross_2} veces")

        if long_cross_1 == 0 and short_cross_1 == 0:
            print("\n⚠️ PROBLEMA ENCONTRADO:")
            print("   El precio NUNCA se desvía ±2% de la media.")
            print("   Posibles causas:")
            print("   1. Lookback muy corto (60 candles = 1h)")
            print("   2. Mercado muy estable (bajo rango)")
            print("   3. Media tracking price demasiado cerca")
            print("\n   SOLUCIONES:")
            print("   - Usar lookback más largo (120-240 candles)")
            print("   - Thresholds más pequeños (-1%, +1%)")
            print("   - Usar VWAP en lugar de MIDRANGE")
        else:
            print(f"\n✓ Thresholds SÍ se cruzan")

            # Now check regime filters on crossing points
            print("\nVerificando filtros en puntos de cruce...")

            # Long opportunities
            long_opps = valid_data[dist <= long_t1]
            if len(long_opps) > 0:
                print(f"\n  Oportunidades Long (distance <= {long_t1}%): {len(long_opps)}")

                # Check how many pass ATR filter
                atr_ok = long_opps['atr_ratio'].notna()
                print(f"    Con ATR válido: {atr_ok.sum()}")

                if atr_ok.sum() > 0:
                    atr_vals = long_opps[atr_ok]['atr_ratio']
                    atr_in_range = ((atr_vals >= strategy.min_atr_ratio) &
                                   (atr_vals <= strategy.max_atr_ratio)).sum()
                    print(f"    Con ATR en rango ({strategy.min_atr_ratio}-{strategy.max_atr_ratio}): {atr_in_range}")

                # Check volume filter
                vol_ok = long_opps['vol_ratio'].notna()
                print(f"    Con vol válido: {vol_ok.sum()}")

                if vol_ok.sum() > 0:
                    vol_vals = long_opps[vol_ok]['vol_ratio']
                    vol_in_range = ((vol_vals >= strategy.min_vol_ratio) &
                                   (vol_vals <= strategy.max_vol_ratio)).sum()
                    print(f"    Con vol en rango ({strategy.min_vol_ratio}-{strategy.max_vol_ratio}): {vol_in_range}")

                # All filters
                all_filters = long_opps[
                    (long_opps['atr_ratio'].notna()) &
                    (long_opps['atr_ratio'] >= strategy.min_atr_ratio) &
                    (long_opps['atr_ratio'] <= strategy.max_atr_ratio) &
                    (long_opps['vol_ratio'].notna()) &
                    (long_opps['vol_ratio'] >= strategy.min_vol_ratio) &
                    (long_opps['vol_ratio'] <= strategy.max_vol_ratio)
                ]
                print(f"    ✓ PASANDO TODOS LOS FILTROS: {len(all_filters)}")

                if len(all_filters) > 0:
                    print(f"\n    Primeros 3 válidos:")
                    print(all_filters[['timestamp', 'close', 'mean_price', 'distance_pct', 'atr_ratio', 'vol_ratio']].head(3))
                else:
                    print(f"\n    ❌ Ninguna oportunidad pasa TODOS los filtros")

            # Short opportunities
            short_opps = valid_data[dist >= short_t1]
            if len(short_opps) > 0:
                print(f"\n  Oportunidades Short (distance >= {short_t1}%): {len(short_opps)}")

                all_filters = short_opps[
                    (short_opps['atr_ratio'].notna()) &
                    (short_opps['atr_ratio'] >= strategy.min_atr_ratio) &
                    (short_opps['atr_ratio'] <= strategy.max_atr_ratio) &
                    (short_opps['vol_ratio'].notna()) &
                    (short_opps['vol_ratio'] >= strategy.min_vol_ratio) &
                    (short_opps['vol_ratio'] <= strategy.max_vol_ratio)
                ]
                print(f"    ✓ PASANDO TODOS LOS FILTROS: {len(all_filters)}")

        # Now actually run backtest
        print("\n" + "=" * 70)
        print("Corriendo backtest completo...")
        print("=" * 70)

        results = backtester.run()
        metrics = results['metrics']

        print(f"\nResultado final:")
        print(f"  Total Trades: {metrics['total_trades']}")
        print(f"  Total Return: {metrics['total_return_pct']:.2f}%")

        if metrics['total_trades'] == 0:
            print("\n❌ AÚN 0 TRADES")
            print("\nNecesito ver el código de _check_layer_entries")
            print("Puede haber un bug en la lógica de entrada.")
        else:
            print(f"\n✓✓✓ ÉXITO! {metrics['total_trades']} trades generados")

except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
