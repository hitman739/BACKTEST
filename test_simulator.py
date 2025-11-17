#!/usr/bin/env python3
"""
Test script to verify the backtester works correctly with synthetic data
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

from engine.backtester import Backtester
from engine.strategy import DeclarativeStrategy

# Generate synthetic OHLCV data
def generate_test_data(days=14, timeframe_minutes=5):
    """Generate synthetic price data for testing"""

    # Calculate number of candles
    candles_per_day = (24 * 60) // timeframe_minutes
    total_candles = days * candles_per_day

    # Generate timestamps
    start_date = datetime(2024, 10, 1)
    timestamps = [start_date + timedelta(minutes=i * timeframe_minutes) for i in range(total_candles)]

    # Generate prices with trend and volatility
    np.random.seed(42)
    base_price = 60000
    trend = np.linspace(0, 2000, total_candles)  # Upward trend
    noise = np.random.randn(total_candles) * 500  # Volatility

    close_prices = base_price + trend + noise

    # Generate OHLC from close
    opens = close_prices + np.random.randn(total_candles) * 50
    highs = np.maximum(opens, close_prices) + abs(np.random.randn(total_candles) * 100)
    lows = np.minimum(opens, close_prices) - abs(np.random.randn(total_candles) * 100)
    volumes = abs(np.random.randn(total_candles) * 1000000 + 5000000)

    df = pd.DataFrame({
        'timestamp': timestamps,
        'open': opens,
        'high': highs,
        'low': lows,
        'close': close_prices,
        'volume': volumes
    })

    return df

# Test strategy configuration
strategy_config = {
    'name': 'Test EMA Cross Strategy',
    'indicators': {
        'ema_fast': {
            'type': 'ema',
            'period': 20,
            'source': 'close'
        },
        'ema_slow': {
            'type': 'ema',
            'period': 50,
            'source': 'close'
        },
        'atr': {
            'type': 'atr',
            'period': 14
        }
    },
    'entry_conditions': {
        'long': [
            "ema_fast > ema_slow",
            "ema_fast[1] <= ema_slow[1]"
        ]
    },
    'exit_rules': {
        'stop_loss_atr_multiple': 2.0,
        'take_profit_atr_multiple': 3.0
    },
    'risk': {
        'risk_per_trade_pct': 1.0,
        'max_equity_per_trade': 0.5,
        'leverage': 5
    },
    'filters': {
        'min_atr': 0,
        'min_volume': 0
    }
}

def test_backtester():
    """Test the backtester with synthetic data"""

    print("=" * 60)
    print("BACKTESTER FUNCTIONALITY TEST")
    print("=" * 60)
    print()

    # Generate test data
    print("1. Generating synthetic test data...")
    test_data = generate_test_data(days=14, timeframe_minutes=5)
    print(f"   ✓ Generated {len(test_data)} candles")
    print(f"   Price range: ${test_data['close'].min():.2f} - ${test_data['close'].max():.2f}")
    print()

    # Create strategy
    print("2. Initializing strategy...")
    strategy = DeclarativeStrategy(strategy_config)
    print(f"   ✓ Strategy: {strategy.name}")
    print()

    # Create backtester
    print("3. Creating backtester...")
    backtester = Backtester(
        strategy=strategy,
        symbol='TESTUSDT',
        timeframe='5m',
        start_date='2024-10-01',
        end_date='2024-10-15',
        initial_balance=10000,
        leverage=5.0,
        maker_fee=0.0002,
        taker_fee=0.0004,
        slippage_bps=2.0
    )
    print("   ✓ Backtester initialized")
    print()

    # Inject test data (bypass data loader)
    print("4. Loading test data into backtester...")
    backtester.data = test_data
    print("   ✓ Data loaded")
    print()

    # Initialize strategy with data
    print("5. Computing indicators...")
    from engine.strategy import StrategyContext
    context = StrategyContext(
        symbol='TESTUSDT',
        timeframe='5m',
        leverage=5.0,
        account_equity=10000,
        position_size=0.0,
        data=backtester.data
    )
    backtester.data = strategy.initialize(context)
    print(f"   ✓ Indicators computed")
    print(f"   Columns: {', '.join(backtester.data.columns.tolist())}")
    print()

    # Run backtest simulation
    print("6. Running backtest simulation...")
    print("-" * 60)

    # Manually run the simulation loop
    from engine.strategy import StrategyState
    state = StrategyState()

    trades_executed = 0
    for idx in range(len(backtester.data)):
        bar = backtester.data.iloc[idx]
        bar_dict = {
            'timestamp': bar['timestamp'],
            'open': bar['open'],
            'high': bar['high'],
            'low': bar['low'],
            'close': bar['close'],
            'volume': bar['volume']
        }

        # Update context
        context.account_equity = backtester.account.equity
        context.position_size = backtester.account.position_size

        # Update state
        state.position_size = backtester.account.position_size
        state.current_bar_index = idx

        # Check for exits first
        if backtester.account.position_size != 0:
            exit_orders = strategy.on_exit(bar, idx, state, context)

            for order in exit_orders:
                executed_order = backtester.execution_engine.execute_order(
                    order, bar_dict, backtester.account.position_size
                )

                if executed_order.is_filled:
                    tags = executed_order.tags.copy()
                    tags['duration_bars'] = idx - state.entry_bar_index

                    backtester.account.close_position(
                        exit_price=executed_order.filled_price,
                        fee=executed_order.fee,
                        timestamp=bar_dict['timestamp'],
                        tags=tags
                    )

                    trades_executed += 1
                    print(f"   Trade #{trades_executed} closed at bar {idx}")

                    # Reset state
                    state.position_size = 0.0
                    state.entry_price = None
                    state.stop_loss = None
                    state.take_profit = None

        # Check for entry signals
        entry_orders = strategy.on_bar(bar, idx, state, context)

        for order in entry_orders:
            executed_order = backtester.execution_engine.execute_order(
                order, bar_dict, backtester.account.position_size
            )

            if executed_order.is_filled:
                leveraged_size = executed_order.filled_quantity * backtester.leverage

                backtester.account.open_position(
                    symbol='TESTUSDT',
                    side='buy' if executed_order.side.value == 'buy' else 'sell',
                    size=leveraged_size,
                    entry_price=executed_order.filled_price,
                    leverage=backtester.leverage,
                    fee=executed_order.fee,
                    timestamp=bar_dict['timestamp']
                )

                print(f"   Trade opened at bar {idx}")

                # Update state
                state.position_size = backtester.account.position_size
                if state.entry_price is None:
                    state.entry_price = executed_order.filled_price
                    state.entry_bar_index = idx

        # Update position
        backtester.account.update_position(bar['close'], bar['timestamp'])

    # Close any remaining position
    if backtester.account.position_size != 0:
        final_bar = backtester.data.iloc[-1]
        backtester.account.close_position(
            exit_price=final_bar['close'],
            fee=abs(backtester.account.position_size) * final_bar['close'] * backtester.taker_fee,
            timestamp=final_bar['timestamp'],
            tags={'exit_reason': 'end_of_backtest'}
        )
        trades_executed += 1

    print("-" * 60)
    print(f"   ✓ Simulation complete")
    print(f"   Total trades executed: {trades_executed}")
    print()

    # Calculate metrics
    print("7. Calculating performance metrics...")
    from engine.metrics import calculate_metrics, format_metrics_table

    trades_df = backtester.account.get_trades_df()
    equity_curve_df = backtester.account.get_equity_curve_df()

    metrics = calculate_metrics(
        trades_df,
        equity_curve_df,
        backtester.initial_balance
    )

    print("   ✓ Metrics calculated")
    print()

    # Display results
    print("=" * 60)
    print("TEST RESULTS")
    print("=" * 60)
    print(format_metrics_table(metrics))
    print("=" * 60)
    print()

    # Validate results
    print("8. Validating backtester functionality...")
    issues_found = []

    # Check if data was processed
    if len(backtester.data) == 0:
        issues_found.append("No data was processed")

    # Check if indicators were computed
    required_indicators = ['ema_fast', 'ema_slow', 'atr']
    for ind in required_indicators:
        if ind not in backtester.data.columns:
            issues_found.append(f"Indicator '{ind}' not computed")

    # Check if equity curve was generated
    if len(equity_curve_df) == 0:
        issues_found.append("No equity curve generated")

    # Check for NaN values in metrics
    nan_metrics = [k for k, v in metrics.items() if pd.isna(v)]
    if nan_metrics:
        issues_found.append(f"NaN values in metrics: {nan_metrics}")

    # Check final equity is reasonable
    final_equity = metrics.get('final_equity', 0)
    if final_equity <= 0:
        issues_found.append(f"Invalid final equity: ${final_equity}")

    if issues_found:
        print("   ⚠ Issues found:")
        for issue in issues_found:
            print(f"      - {issue}")
    else:
        print("   ✓ All validation checks passed!")

    print()
    print("=" * 60)
    print("BACKTESTER TEST COMPLETE")
    print("=" * 60)

    return len(issues_found) == 0

if __name__ == '__main__':
    success = test_backtester()
    exit(0 if success else 1)
