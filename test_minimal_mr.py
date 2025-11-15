#!/usr/bin/env python3
"""
Test mínimo - Crear datos sintéticos para probar la lógica
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from engine.strategy import StrategyContext
from strategies.simple_mean_revert import SimpleMeanRevertStrategy
from engine.mean_reversion import MeanReversionState

print("=" * 70)
print("TEST MÍNIMO: Datos sintéticos con desviación garantizada")
print("=" * 70)

# Create synthetic data that DEFINITELY crosses thresholds
dates = pd.date_range(start='2025-01-01', periods=200, freq='1min')

# Create price that oscillates around 100
base_price = 100
oscillation = np.sin(np.linspace(0, 4*np.pi, 200)) * 5  # ±5 oscillation
prices = base_price + oscillation

# Add some volume
volume = np.random.uniform(1000, 2000, 200)

# Create DataFrame
data = pd.DataFrame({
    'timestamp': dates,
    'open': prices,
    'high': prices + 0.1,
    'low': prices - 0.1,
    'close': prices,
    'volume': volume
})

print(f"Created synthetic data: {len(data)} candles")
print(f"Price range: {data['close'].min():.2f} - {data['close'].max():.2f}")
print(f"Price oscillation: ±{(data['close'].max() - base_price):.2f}")
print()

# Initialize strategy
strategy = SimpleMeanRevertStrategy()
print(f"Strategy: {strategy.name}")
print(f"Long thresholds: {strategy.long_thresholds}")
print(f"Short thresholds: {strategy.short_thresholds}")
print()

# Create context
context = StrategyContext(
    symbol='TESTUSDT',
    timeframe='1m',
    leverage=5.0,
    account_equity=10000,
    position_size=0,
    data=data
)

# Initialize strategy (calculate indicators)
print("Initializing strategy...")
data = strategy.initialize(context)

# Update context with new data
context.data = data

print("✓ Indicators calculated")
print()

# Check distance_pct
valid_data = data.dropna(subset=['distance_pct', 'mean_price'])
print(f"Valid data (non-NaN): {len(valid_data)} / {len(data)}")

if len(valid_data) > 0:
    dist = valid_data['distance_pct']
    print(f"\nDistance statistics:")
    print(f"  Min: {dist.min():.2f}%")
    print(f"  Max: {dist.max():.2f}%")
    print(f"  Mean: {dist.mean():.2f}%")

    # Check crossings
    long_t1 = strategy.long_thresholds[0]
    short_t1 = strategy.short_thresholds[0]

    long_cross = (dist <= long_t1).sum()
    short_cross = (dist >= short_t1).sum()

    print(f"\nThreshold crossings:")
    print(f"  distance <= {long_t1}%: {long_cross} times")
    print(f"  distance >= {short_t1}%: {short_cross} times")

    if long_cross > 0 or short_cross > 0:
        print("\n✓ Thresholds ARE crossed")

        # Now manually test on_bar on a crossing point
        print("\n" + "=" * 70)
        print("MANUAL TEST: Calling on_bar on crossing points")
        print("=" * 70)

        # Find a long crossing
        long_bars = valid_data[valid_data['distance_pct'] <= long_t1]
        if len(long_bars) > 0:
            test_bar = long_bars.iloc[0]
            test_index = long_bars.index[0]

            print(f"\nTest bar (long opportunity):")
            print(f"  Index: {test_index}")
            print(f"  Timestamp: {test_bar['timestamp']}")
            print(f"  Close: {test_bar['close']:.2f}")
            print(f"  Mean: {test_bar['mean_price']:.2f}")
            print(f"  Distance: {test_bar['distance_pct']:.2f}%")
            print(f"  ATR ratio: {test_bar.get('atr_ratio', 'NaN')}")
            print(f"  Vol ratio: {test_bar.get('vol_ratio', 'NaN')}")

            # Create state
            state = strategy.get_initial_state()

            # Update context
            context.account_equity = 10000
            context.position_size = 0

            # Call on_bar
            print(f"\nCalling strategy.on_bar()...")
            orders = strategy.on_bar(test_bar, test_index, state, context)

            print(f"Orders returned: {len(orders)}")

            if len(orders) > 0:
                print("\n✓✓✓ SUCCESS! Orders generated:")
                for i, order in enumerate(orders):
                    print(f"  Order {i+1}:")
                    print(f"    Side: {order.side.value}")
                    print(f"    Type: {order.order_type.value}")
                    print(f"    Quantity: {order.quantity:.4f}")
                    print(f"    Symbol: {order.symbol}")
            else:
                print("\n❌ NO ORDERS GENERATED")
                print("\nDebugging why...")

                # Check filters manually
                print(f"\n1. Checking _check_global_limits...")
                if not strategy._check_global_limits(test_bar, state, context):
                    print("   ❌ Global limits failed")
                else:
                    print("   ✓ Global limits passed")

                print(f"\n2. Checking _check_regime_filters...")
                if not strategy._check_regime_filters(test_bar):
                    print("   ❌ Regime filters failed")
                    print(f"      ATR ratio: {test_bar.get('atr_ratio')}")
                    print(f"      Vol ratio: {test_bar.get('vol_ratio')}")
                else:
                    print("   ✓ Regime filters passed")

                print(f"\n3. Checking _check_session_filters...")
                if not strategy._check_session_filters(test_bar):
                    print("   ❌ Session filters failed")
                else:
                    print("   ✓ Session filters passed")

                print(f"\n4. Checking distance_pct...")
                distance_pct = test_bar.get('distance_pct')
                mean_price = test_bar.get('mean_price')
                print(f"   distance_pct: {distance_pct}")
                print(f"   mean_price: {mean_price}")
                print(f"   Is NaN? {pd.isna(distance_pct) or pd.isna(mean_price)}")

                if not (pd.isna(distance_pct) or pd.isna(mean_price)):
                    print(f"\n5. Checking _check_layer_entries...")
                    layer_orders = strategy._check_layer_entries(
                        distance_pct,
                        test_bar['close'],
                        mean_price,
                        'long',
                        test_bar,
                        state,
                        context
                    )
                    print(f"   Layer orders: {len(layer_orders)}")

                    if len(layer_orders) == 0:
                        print("\n   Debugging _check_layer_entries logic:")
                        basket = state.long_basket
                        print(f"     Basket layers: {basket.num_layers}")
                        print(f"     Max layers: {strategy.max_layers_long}")
                        print(f"     Thresholds: {strategy.long_thresholds}")
                        print(f"     abs(distance): {abs(distance_pct):.2f}")
                        print(f"     abs(threshold[0]): {abs(strategy.long_thresholds[0]):.2f}")
                        print(f"     Crosses? {abs(distance_pct) >= abs(strategy.long_thresholds[0])}")

    else:
        print("\n❌ Thresholds NEVER crossed")
        print("   Synthetic data not oscillating enough")

else:
    print("\n❌ All data is NaN!")

print("\n" + "=" * 70)
