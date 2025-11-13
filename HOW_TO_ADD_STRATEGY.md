# How to Add a Strategy

This guide explains how to create and run new trading strategies using the backtesting engine.

## Table of Contents
1. [Quick Start](#quick-start)
2. [Declarative Strategies (YAML/JSON)](#declarative-strategies-yamljson)
3. [Programmatic Strategies (Python)](#programmatic-strategies-python)
4. [Running Your Strategy](#running-your-strategy)
5. [Examples](#examples)

---

## Quick Start

There are two ways to create a strategy:

1. **Declarative (YAML/JSON)**: Best for simple rule-based strategies
2. **Programmatic (Python)**: Best for complex logic requiring custom code

---

## Declarative Strategies (YAML/JSON)

### Step 1: Create Strategy File

Create a new YAML file in `strategies/` (e.g., `strategies/my_strategy.yaml`):

```yaml
name: "My Strategy Name"

# Define indicators
indicators:
  indicator_name:
    type: indicator_type
    period: value
    source: close  # Optional: open, high, low, close

# Entry conditions
entry_conditions:
  long:    # List of conditions (all must be true)
    - "condition_1"
    - "condition_2"
  short:   # Optional: conditions for short entries
    - "condition_1"
    - "condition_2"

# Exit rules
exit_rules:
  stop_loss_atr_multiple: 2.0        # Stop loss distance (ATR multiples)
  take_profit_atr_multiple: 3.0      # Take profit distance (ATR multiples)
  trailing_stop_atr_multiple: 1.5    # Optional: trailing stop

# Risk management
risk:
  risk_per_trade_pct: 1.0            # % of account to risk per trade
  max_equity_per_trade: 0.5          # Max % of equity per trade
  leverage: 5                         # Leverage multiplier

# Market filters (optional)
filters:
  min_atr: 0                          # Minimum ATR to trade
  min_volume: 0                       # Minimum volume to trade
```

### Step 2: Available Indicators

The following indicators are supported:

| Indicator | Type | Parameters |
|-----------|------|------------|
| Simple Moving Average | `sma` | `period`, `source` |
| Exponential Moving Average | `ema` | `period`, `source` |
| Weighted Moving Average | `wma` | `period`, `source` |
| Relative Strength Index | `rsi` | `period`, `source` |
| Average True Range | `atr` | `period` |
| Volume Weighted Avg Price | `vwap` | - |
| Volume Moving Average | `volume_ma` | `period` |
| Bollinger Bands | `bbands` | `period`, `std_dev`, `source` |
| MACD | `macd` | `fast`, `slow`, `signal`, `source` |

### Step 3: Writing Entry Conditions

Conditions are evaluated as Python expressions. Available operators:

- Comparison: `>`, `<`, `>=`, `<=`, `==`, `!=`
- Reference previous bar: `indicator[1]` (e.g., `ema_fast[1]`)
- Combine: Use multiple conditions in the list (all must be true)

**Examples:**

```yaml
# EMA Crossover
entry_conditions:
  long:
    - "ema_fast > ema_slow"           # Current: fast above slow
    - "ema_fast[1] <= ema_slow[1]"    # Previous: fast was below/equal slow

# RSI Oversold
entry_conditions:
  long:
    - "rsi < 30"                       # RSI below 30
    - "rsi[1] >= 30"                   # Previous RSI was above 30

# Multiple Confirmations
entry_conditions:
  long:
    - "close > sma_200"                # Above long-term MA
    - "rsi > 50"                       # Bullish momentum
    - "volume > volume_ma"             # High volume
```

### Complete Example: RSI Mean Reversion

```yaml
name: "RSI Mean Reversion"

indicators:
  rsi:
    type: rsi
    period: 14
    source: close
  sma_50:
    type: sma
    period: 50
    source: close
  atr:
    type: atr
    period: 14

entry_conditions:
  long:
    - "rsi < 30"                       # Oversold
    - "close > sma_50"                 # Above MA (uptrend)
  short:
    - "rsi > 70"                       # Overbought
    - "close < sma_50"                 # Below MA (downtrend)

exit_rules:
  stop_loss_atr_multiple: 2.0
  take_profit_atr_multiple: 2.5

risk:
  risk_per_trade_pct: 1.0
  max_equity_per_trade: 0.3
  leverage: 3

filters:
  min_volume: 1000
```

---

## Programmatic Strategies (Python)

For complex strategies requiring custom logic, create a Python class.

### Step 1: Create Strategy File

Create `strategies/my_strategy.py`:

```python
from typing import List
import pandas as pd
from engine.strategy import BaseStrategy, StrategyContext, StrategyState
from engine.orders import Order, OrderType, OrderSide
from engine.indicators import Indicators


class MyStrategy(BaseStrategy):
    """My custom strategy description"""

    def __init__(self, config: dict = None):
        # Set default configuration
        if config is None:
            config = {
                'name': 'My Strategy Name',
                # Add your parameters here
                'parameter1': value1,
                'parameter2': value2,
            }
        super().__init__(config)

        # Store parameters as instance variables
        self.param1 = config.get('parameter1', default_value)
        self.param2 = config.get('parameter2', default_value)

    def initialize(self, context: StrategyContext) -> pd.DataFrame:
        """
        Called once at the start of backtest.
        Add indicators to the data here.

        Args:
            context: Strategy context with symbol, timeframe, data

        Returns:
            DataFrame with added indicator columns
        """
        df = context.data.copy()

        # Add your indicators
        df['my_indicator'] = Indicators.ema(df['close'], 20)

        return df

    def on_bar(
        self,
        bar: pd.Series,
        bar_index: int,
        state: StrategyState,
        context: StrategyContext
    ) -> List[Order]:
        """
        Called on each bar to check for entry signals.

        Args:
            bar: Current bar data (has all OHLCV + indicators)
            bar_index: Index of current bar in the dataset
            state: Current strategy state (position_size, stop_loss, etc.)
            context: Strategy context (account_equity, symbol, etc.)

        Returns:
            List of orders to execute (empty list if no signal)
        """
        orders = []

        # Skip if already in position
        if state.position_size != 0:
            return orders

        # Your entry logic here
        if self._check_entry_conditions(bar, bar_index, context):
            order = self._create_entry_order(bar, bar_index, state, context)
            orders.append(order)

        return orders

    def on_exit(
        self,
        bar: pd.Series,
        bar_index: int,
        state: StrategyState,
        context: StrategyContext
    ) -> List[Order]:
        """
        Called on each bar when in position to check for exits.

        Args:
            bar: Current bar data
            bar_index: Index of current bar
            state: Current strategy state
            context: Strategy context

        Returns:
            List of exit orders (empty list if no exit signal)
        """
        orders = []

        # Skip if not in position
        if state.position_size == 0:
            return orders

        # Your exit logic here
        if self._check_exit_conditions(bar, state):
            order = self._create_exit_order(bar, bar_index, state, context)
            orders.append(order)

        return orders

    # Helper methods (optional but recommended)

    def _check_entry_conditions(self, bar, bar_index, context):
        """Check if entry conditions are met"""
        # Your logic
        return True  # or False

    def _create_entry_order(self, bar, bar_index, state, context):
        """Create entry order"""
        # Calculate position size
        position_size = self._calculate_position_size(bar, context)

        # Create order
        order = Order(
            order_id=f"entry_{bar_index}",
            symbol=context.symbol,
            side=OrderSide.BUY,  # or OrderSide.SELL
            order_type=OrderType.MARKET,
            quantity=position_size,
            timestamp=bar['timestamp']
        )

        # Set stop loss and take profit in state
        state.stop_loss = # ... your calculation
        state.take_profit = # ... your calculation

        return order

    def _calculate_position_size(self, bar, context):
        """Calculate position size based on risk"""
        # Example: Risk 1% of equity
        risk_amount = context.account_equity * 0.01
        price_risk = # ... calculate risk per unit
        position_size = risk_amount / price_risk
        return position_size

    def _check_exit_conditions(self, bar, state):
        """Check if exit conditions are met"""
        # Your logic
        return False

    def _create_exit_order(self, bar, bar_index, state, context):
        """Create exit order"""
        is_long = state.position_size > 0
        side = OrderSide.SELL if is_long else OrderSide.BUY

        order = Order(
            order_id=f"exit_{bar_index}",
            symbol=context.symbol,
            side=side,
            order_type=OrderType.MARKET,
            quantity=abs(state.position_size),
            timestamp=bar['timestamp'],
            tags={'exit_reason': 'your_reason'}
        )
        return order
```

### Key Objects and Attributes

#### StrategyContext
- `symbol`: Trading symbol (str)
- `timeframe`: Timeframe (str)
- `leverage`: Leverage (float)
- `account_equity`: Current account equity (float)
- `position_size`: Current position size (float, signed)
- `data`: Full DataFrame with all historical data and indicators

#### StrategyState
- `position_size`: Current position size (float)
- `entry_price`: Entry price (float)
- `stop_loss`: Stop loss price (float)
- `take_profit`: Take profit price (float)
- `entry_bar_index`: Bar index when entered (int)
- `current_bar_index`: Current bar index (int)
- `custom_data`: Dictionary for custom state variables

#### Order
```python
Order(
    order_id="unique_id",
    symbol="BTCUSDT",
    side=OrderSide.BUY,  # or OrderSide.SELL
    order_type=OrderType.MARKET,  # or LIMIT, STOP_MARKET, STOP_LIMIT
    quantity=1.5,
    price=None,  # For LIMIT orders
    stop_price=None,  # For STOP orders
    timestamp=bar['timestamp'],
    tags={'custom_key': 'value'}  # Optional metadata
)
```

### Complete Example: Bollinger Band Breakout

```python
from typing import List
import pandas as pd
from engine.strategy import BaseStrategy, StrategyContext, StrategyState
from engine.orders import Order, OrderType, OrderSide
from engine.indicators import Indicators


class BollingerBreakout(BaseStrategy):
    """Bollinger Band breakout strategy"""

    def __init__(self, config: dict = None):
        if config is None:
            config = {
                'name': 'Bollinger Breakout',
                'bb_period': 20,
                'bb_std': 2.0,
                'atr_period': 14,
                'risk_pct': 1.0
            }
        super().__init__(config)

        self.bb_period = config.get('bb_period', 20)
        self.bb_std = config.get('bb_std', 2.0)
        self.atr_period = config.get('atr_period', 14)
        self.risk_pct = config.get('risk_pct', 1.0)

    def initialize(self, context: StrategyContext) -> pd.DataFrame:
        """Add Bollinger Bands and ATR"""
        df = context.data.copy()

        # Add Bollinger Bands
        bb_mid, bb_upper, bb_lower = Indicators.bollinger_bands(
            df['close'], self.bb_period, self.bb_std
        )
        df['bb_mid'] = bb_mid
        df['bb_upper'] = bb_upper
        df['bb_lower'] = bb_lower

        # Add ATR for stop loss
        df['atr'] = Indicators.atr(df['high'], df['low'], df['close'], self.atr_period)

        return df

    def on_bar(self, bar: pd.Series, bar_index: int, state: StrategyState,
               context: StrategyContext) -> List[Order]:
        """Look for breakouts"""
        orders = []

        # Skip if in position or not enough data
        if state.position_size != 0 or bar_index < 1:
            return orders

        # Check for valid indicators
        if pd.isna(bar['bb_upper']) or pd.isna(bar['atr']):
            return orders

        prev_bar = context.data.iloc[bar_index - 1]

        # Bullish breakout: close breaks above upper band
        if bar['close'] > bar['bb_upper'] and prev_bar['close'] <= prev_bar['bb_upper']:
            entry_price = bar['close']
            stop_loss = bar['bb_mid']  # Stop at middle band
            atr = bar['atr']

            # Position size based on risk
            risk_amount = context.account_equity * (self.risk_pct / 100)
            price_risk = entry_price - stop_loss
            position_size = risk_amount / price_risk if price_risk > 0 else 0

            if position_size > 0:
                order = Order(
                    order_id=f"long_{bar_index}",
                    symbol=context.symbol,
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    quantity=position_size,
                    timestamp=bar['timestamp']
                )
                orders.append(order)

                state.stop_loss = stop_loss
                state.take_profit = entry_price + (2 * atr)  # 2x ATR target

        # Bearish breakout: close breaks below lower band
        elif bar['close'] < bar['bb_lower'] and prev_bar['close'] >= prev_bar['bb_lower']:
            entry_price = bar['close']
            stop_loss = bar['bb_mid']
            atr = bar['atr']

            risk_amount = context.account_equity * (self.risk_pct / 100)
            price_risk = stop_loss - entry_price
            position_size = risk_amount / price_risk if price_risk > 0 else 0

            if position_size > 0:
                order = Order(
                    order_id=f"short_{bar_index}",
                    symbol=context.symbol,
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=position_size,
                    timestamp=bar['timestamp']
                )
                orders.append(order)

                state.stop_loss = stop_loss
                state.take_profit = entry_price - (2 * atr)

        return orders

    def on_exit(self, bar: pd.Series, bar_index: int, state: StrategyState,
                context: StrategyContext) -> List[Order]:
        """Exit on stop or target"""
        orders = []

        if state.position_size == 0:
            return orders

        is_long = state.position_size > 0
        current_price = bar['close']

        # Check stop loss
        if state.stop_loss:
            if (is_long and current_price <= state.stop_loss) or \
               (not is_long and current_price >= state.stop_loss):
                side = OrderSide.SELL if is_long else OrderSide.BUY
                order = Order(
                    order_id=f"exit_sl_{bar_index}",
                    symbol=context.symbol,
                    side=side,
                    order_type=OrderType.MARKET,
                    quantity=abs(state.position_size),
                    timestamp=bar['timestamp'],
                    tags={'exit_reason': 'stop_loss'}
                )
                orders.append(order)
                return orders

        # Check take profit
        if state.take_profit:
            if (is_long and current_price >= state.take_profit) or \
               (not is_long and current_price <= state.take_profit):
                side = OrderSide.SELL if is_long else OrderSide.BUY
                order = Order(
                    order_id=f"exit_tp_{bar_index}",
                    symbol=context.symbol,
                    side=side,
                    order_type=OrderType.MARKET,
                    quantity=abs(state.position_size),
                    timestamp=bar['timestamp'],
                    tags={'exit_reason': 'take_profit'}
                )
                orders.append(order)
                return orders

        return orders
```

---

## Running Your Strategy

### Command Line

```bash
# Declarative strategy (YAML/JSON)
python run_backtest.py \
    --strategy strategies/my_strategy.yaml \
    --symbol BTCUSDT \
    --timeframe 5m \
    --from 2024-01-01 \
    --to 2024-06-01 \
    --equity 10000 \
    --leverage 5

# Programmatic strategy (Python)
python run_backtest.py \
    --strategy strategies/my_strategy.py \
    --symbol ETHUSDT \
    --timeframe 15m \
    --from 2024-01-01 \
    --to 2024-06-01 \
    --equity 50000 \
    --leverage 3 \
    --report_name eth_test_001
```

### From Python Code

```python
from engine.backtester import Backtester
from engine.strategy import load_strategy_from_file

# Load strategy
strategy = load_strategy_from_file('strategies/my_strategy.yaml')

# Create backtester
backtester = Backtester(
    strategy=strategy,
    symbol='BTCUSDT',
    timeframe='5m',
    start_date='2024-01-01',
    end_date='2024-06-01',
    initial_balance=10000,
    leverage=5
)

# Run
results = backtester.run()

# Access results
print(f"Total PnL: ${results['metrics']['total_pnl']:.2f}")
print(f"Win Rate: {results['metrics']['win_rate_pct']:.2f}%")
```

---

## Examples

### Example 1: Simple Moving Average Cross

**Declarative** (`strategies/examples/sma_cross.yaml`):
```yaml
name: "SMA Cross"

indicators:
  sma_20:
    type: sma
    period: 20
  sma_50:
    type: sma
    period: 50
  atr:
    type: atr
    period: 14

entry_conditions:
  long:
    - "sma_20 > sma_50"
    - "sma_20[1] <= sma_50[1]"

exit_rules:
  stop_loss_atr_multiple: 2.0
  take_profit_atr_multiple: 3.0

risk:
  risk_per_trade_pct: 1.0
  leverage: 3
```

### Example 2: RSI + Volume Confirmation

**Declarative**:
```yaml
name: "RSI Volume"

indicators:
  rsi:
    type: rsi
    period: 14
  volume_ma:
    type: volume_ma
    period: 20
  atr:
    type: atr
    period: 14

entry_conditions:
  long:
    - "rsi < 35"
    - "volume > volume_ma"
  short:
    - "rsi > 65"
    - "volume > volume_ma"

exit_rules:
  stop_loss_atr_multiple: 1.5
  take_profit_atr_multiple: 2.0

risk:
  risk_per_trade_pct: 0.5
  leverage: 2
```

### Example 3: Custom Multi-Factor Strategy

**Programmatic** (implement complex logic like time filters, multiple timeframe confirmation, dynamic position sizing, etc.)

---

## Tips for Success

1. **Start Simple**: Begin with basic logic, add complexity gradually
2. **Validate Indicators**: Print indicator values to ensure they're calculating correctly
3. **Test on Small Datasets**: Use short date ranges for quick iteration
4. **Risk Management**: Always use stops and size positions appropriately
5. **Avoid Lookahead Bias**: Never access future data (bars beyond current index)
6. **Document Logic**: Add comments explaining your strategy rationale
7. **Version Control**: Keep track of strategy versions and parameters

## Common Issues

### No Trades Generated
- Indicators may need warmup period (first N bars are NaN)
- Entry conditions might be too strict
- Check that `state.position_size` is being checked correctly
- Verify position sizing isn't returning 0

### Unexpected Results
- Ensure you're not using future data (lookahead bias)
- Verify stop/target calculations
- Check that orders have correct side (BUY vs SELL)
- Review slippage and fee settings

### Strategy Won't Load
- For YAML: Check indentation (use spaces, not tabs)
- For Python: Ensure class inherits from `BaseStrategy`
- Verify file paths are correct
- Check for syntax errors

---

## Next Steps

1. Create your strategy file (YAML or Python)
2. Run a backtest on a small date range
3. Review the reports in `reports/your_run_id/`
4. Iterate and improve
5. Test on different symbols and timeframes
6. Validate with walk-forward analysis

Happy strategy development! 📈
