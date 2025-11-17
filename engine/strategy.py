"""
Strategy Interface and Loaders

Supports two strategy formats:
1. Declarative (YAML/JSON) - rule-based strategies
2. Programmatic (Python class) - custom logic strategies
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import yaml
import json
from pathlib import Path
import pandas as pd

from engine.orders import Order, OrderType, OrderSide
from engine.indicators import add_indicators


@dataclass
class StrategyContext:
    """Context passed to strategies"""
    symbol: str
    timeframe: str
    leverage: float
    account_equity: float
    position_size: float
    data: pd.DataFrame  # Full historical data with indicators


@dataclass
class StrategyState:
    """Mutable state for strategy execution"""
    position_size: float = 0.0
    entry_price: Optional[float] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    entry_bar_index: int = 0
    current_bar_index: int = 0
    custom_data: Dict = None

    def __post_init__(self):
        if self.custom_data is None:
            self.custom_data = {}


class BaseStrategy(ABC):
    """
    Base class for all strategies
    """

    def __init__(self, config: Dict):
        self.config = config
        self.name = config.get('name', 'Unnamed Strategy')
        self.indicators_config = config.get('indicators', {})

    @abstractmethod
    def initialize(self, context: StrategyContext) -> pd.DataFrame:
        """
        Initialize strategy and compute indicators

        Args:
            context: Strategy context with data

        Returns:
            DataFrame with added indicators
        """
        pass

    @abstractmethod
    def on_bar(
        self,
        bar: pd.Series,
        bar_index: int,
        state: StrategyState,
        context: StrategyContext
    ) -> List[Order]:
        """
        Called on each bar

        Args:
            bar: Current bar data
            bar_index: Index of current bar
            state: Current strategy state
            context: Strategy context

        Returns:
            List of orders to execute
        """
        pass

    @abstractmethod
    def on_exit(
        self,
        bar: pd.Series,
        bar_index: int,
        state: StrategyState,
        context: StrategyContext
    ) -> List[Order]:
        """
        Called to check exit conditions for open positions

        Args:
            bar: Current bar data
            bar_index: Index of current bar
            state: Current strategy state
            context: Strategy context

        Returns:
            List of exit orders
        """
        pass


class DeclarativeStrategy(BaseStrategy):
    """
    Strategy based on declarative spec (YAML/JSON)

    Example spec:
    {
        "name": "EMA Cross",
        "indicators": {
            "ema_fast": {"type": "ema", "period": 20},
            "ema_slow": {"type": "ema", "period": 50},
            "atr": {"type": "atr", "period": 14}
        },
        "entry_conditions": {
            "long": ["ema_fast > ema_slow", "ema_fast[1] <= ema_slow[1]"],
            "short": ["ema_fast < ema_slow", "ema_fast[1] >= ema_slow[1]"]
        },
        "exit_rules": {
            "stop_loss_atr_multiple": 2.0,
            "take_profit_atr_multiple": 3.0,
            "trailing_stop_atr_multiple": 1.5
        },
        "risk": {
            "risk_per_trade_pct": 1.0,
            "max_equity_per_trade": 0.5,
            "leverage": 5
        },
        "filters": {
            "min_atr": 0,
            "min_volume": 0
        }
    }
    """

    def __init__(self, config: Dict):
        super().__init__(config)
        self.entry_conditions = config.get('entry_conditions', {})
        self.exit_rules = config.get('exit_rules', {})
        self.risk_config = config.get('risk', {})
        self.filters = config.get('filters', {})

    def initialize(self, context: StrategyContext) -> pd.DataFrame:
        """Initialize and add indicators"""
        df = context.data.copy()
        df = add_indicators(df, self.indicators_config)
        return df

    def _evaluate_condition(self, condition: str, bar: pd.Series, prev_bar: Optional[pd.Series]) -> bool:
        """
        Evaluate a condition string with restricted evaluation for security

        Args:
            condition: Condition string (e.g., "ema_fast > ema_slow")
            bar: Current bar
            prev_bar: Previous bar (for [1] references)

        Returns:
            True if condition is met
        """
        try:
            # Replace indicator names with values
            eval_str = condition

            # Handle previous bar references (e.g., ema_fast[1])
            import re
            prev_refs = re.findall(r'(\w+)\[1\]', condition)
            for ref in prev_refs:
                if prev_bar is not None and ref in prev_bar:
                    eval_str = eval_str.replace(f'{ref}[1]', str(prev_bar[ref]))
                else:
                    return False

            # Replace current bar references
            for col in bar.index:
                if col in eval_str and f'{col}[1]' not in condition:
                    eval_str = eval_str.replace(col, str(bar[col]))

            # Security: Validate that the expression only contains safe characters
            # Allow: numbers, operators, parentheses, dots (for decimals), spaces
            import string
            allowed_chars = string.digits + string.whitespace + '.<>=!()+-*/%'
            if not all(c in allowed_chars for c in eval_str):
                # Expression contains potentially unsafe characters
                raise ValueError(f"Unsafe characters in expression: {eval_str}")

            # Evaluate with restricted builtins for security
            # Only allow comparison and arithmetic operators
            safe_dict = {
                '__builtins__': {
                    'True': True,
                    'False': False,
                }
            }
            result = eval(eval_str, safe_dict, {})
            return bool(result)

        except Exception as e:
            # If evaluation fails, condition is not met
            return False

    def _check_filters(self, bar: pd.Series) -> bool:
        """Check if market conditions pass filters"""
        if self.filters.get('min_atr', 0) > 0:
            atr_col = None
            for col in bar.index:
                if 'atr' in col.lower():
                    atr_col = col
                    break
            if atr_col and bar[atr_col] < self.filters['min_atr']:
                return False

        if self.filters.get('min_volume', 0) > 0:
            if bar.get('volume', 0) < self.filters['min_volume']:
                return False

        return True

    def _calculate_position_size(
        self,
        entry_price: float,
        stop_loss: float,
        context: StrategyContext
    ) -> float:
        """
        Calculate position size based on risk parameters

        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            context: Strategy context

        Returns:
            Position size
        """
        risk_pct = self.risk_config.get('risk_per_trade_pct', 1.0) / 100
        max_equity_pct = self.risk_config.get('max_equity_per_trade', 0.5)

        # Risk-based sizing
        risk_amount = context.account_equity * risk_pct
        price_risk = abs(entry_price - stop_loss)

        if price_risk > 0:
            size_by_risk = risk_amount / price_risk
        else:
            size_by_risk = 0

        # Max equity limit
        max_notional = context.account_equity * max_equity_pct * context.leverage
        size_by_equity = max_notional / entry_price

        # Use minimum of the two
        return min(size_by_risk, size_by_equity)

    def on_bar(
        self,
        bar: pd.Series,
        bar_index: int,
        state: StrategyState,
        context: StrategyContext
    ) -> List[Order]:
        """Check entry conditions"""
        orders = []

        # Skip if already in position
        if state.position_size != 0:
            return orders

        # Check filters
        if not self._check_filters(bar):
            return orders

        # Get previous bar
        prev_bar = context.data.iloc[bar_index - 1] if bar_index > 0 else None

        # Check long conditions
        if 'long' in self.entry_conditions:
            long_conditions = self.entry_conditions['long']
            if all(self._evaluate_condition(cond, bar, prev_bar) for cond in long_conditions):
                # Generate long entry
                entry_price = bar['close']

                # Calculate stop loss
                atr = None
                for col in bar.index:
                    if 'atr' in col.lower():
                        atr = bar[col]
                        break

                if atr and 'stop_loss_atr_multiple' in self.exit_rules:
                    sl_multiple = self.exit_rules['stop_loss_atr_multiple']
                    stop_loss = entry_price - (atr * sl_multiple)
                else:
                    # Default 2% stop
                    stop_loss = entry_price * 0.98

                # Calculate position size
                size = self._calculate_position_size(entry_price, stop_loss, context)

                if size > 0:
                    order = Order(
                        order_id=f"entry_{bar_index}",
                        symbol=context.symbol,
                        side=OrderSide.BUY,
                        order_type=OrderType.MARKET,
                        quantity=size,
                        timestamp=bar['timestamp']
                    )
                    orders.append(order)

                    # Update state
                    state.stop_loss = stop_loss
                    if 'take_profit_atr_multiple' in self.exit_rules and atr:
                        tp_multiple = self.exit_rules['take_profit_atr_multiple']
                        state.take_profit = entry_price + (atr * tp_multiple)

        # Check short conditions
        elif 'short' in self.entry_conditions:
            short_conditions = self.entry_conditions['short']
            if all(self._evaluate_condition(cond, bar, prev_bar) for cond in short_conditions):
                # Generate short entry
                entry_price = bar['close']

                # Calculate stop loss
                atr = None
                for col in bar.index:
                    if 'atr' in col.lower():
                        atr = bar[col]
                        break

                if atr and 'stop_loss_atr_multiple' in self.exit_rules:
                    sl_multiple = self.exit_rules['stop_loss_atr_multiple']
                    stop_loss = entry_price + (atr * sl_multiple)
                else:
                    # Default 2% stop
                    stop_loss = entry_price * 1.02

                # Calculate position size
                size = self._calculate_position_size(entry_price, stop_loss, context)

                if size > 0:
                    order = Order(
                        order_id=f"entry_{bar_index}",
                        symbol=context.symbol,
                        side=OrderSide.SELL,
                        order_type=OrderType.MARKET,
                        quantity=size,
                        timestamp=bar['timestamp']
                    )
                    orders.append(order)

                    # Update state
                    state.stop_loss = stop_loss
                    if 'take_profit_atr_multiple' in self.exit_rules and atr:
                        tp_multiple = self.exit_rules['take_profit_atr_multiple']
                        state.take_profit = entry_price - (atr * tp_multiple)

        return orders

    def on_exit(
        self,
        bar: pd.Series,
        bar_index: int,
        state: StrategyState,
        context: StrategyContext
    ) -> List[Order]:
        """Check exit conditions"""
        orders = []

        if state.position_size == 0:
            return orders

        is_long = state.position_size > 0
        current_price = bar['close']

        # Check stop loss
        if state.stop_loss:
            if is_long and current_price <= state.stop_loss:
                order = Order(
                    order_id=f"exit_sl_{bar_index}",
                    symbol=context.symbol,
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=abs(state.position_size),
                    timestamp=bar['timestamp'],
                    tags={'exit_reason': 'stop_loss'}
                )
                orders.append(order)
                return orders

            elif not is_long and current_price >= state.stop_loss:
                order = Order(
                    order_id=f"exit_sl_{bar_index}",
                    symbol=context.symbol,
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    quantity=abs(state.position_size),
                    timestamp=bar['timestamp'],
                    tags={'exit_reason': 'stop_loss'}
                )
                orders.append(order)
                return orders

        # Check take profit
        if state.take_profit:
            if is_long and current_price >= state.take_profit:
                order = Order(
                    order_id=f"exit_tp_{bar_index}",
                    symbol=context.symbol,
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=abs(state.position_size),
                    timestamp=bar['timestamp'],
                    tags={'exit_reason': 'take_profit'}
                )
                orders.append(order)
                return orders

            elif not is_long and current_price <= state.take_profit:
                order = Order(
                    order_id=f"exit_tp_{bar_index}",
                    symbol=context.symbol,
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    quantity=abs(state.position_size),
                    timestamp=bar['timestamp'],
                    tags={'exit_reason': 'take_profit'}
                )
                orders.append(order)
                return orders

        return orders


def load_strategy_from_file(file_path: str) -> BaseStrategy:
    """
    Load strategy from YAML, JSON, or Python file

    Args:
        file_path: Path to strategy file

    Returns:
        Strategy instance
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Strategy file not found: {file_path}")

    # Check if it's a Python class file
    if path.suffix == '.py':
        return load_strategy_from_class(file_path)

    # Load declarative configuration
    with open(path, 'r') as f:
        if path.suffix in ['.yaml', '.yml']:
            config = yaml.safe_load(f)
        elif path.suffix == '.json':
            config = json.load(f)
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}")

    # Create strategy instance
    return DeclarativeStrategy(config)


def load_strategy_from_class(class_path: str) -> BaseStrategy:
    """
    Load strategy from Python class

    Args:
        class_path: Path to Python file with strategy class

    Returns:
        Strategy instance
    """
    import importlib.util

    path = Path(class_path)

    if not path.exists():
        raise FileNotFoundError(f"Strategy file not found: {class_path}")

    # Load module
    spec = importlib.util.spec_from_file_location("strategy_module", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Find strategy class (should inherit from BaseStrategy)
    strategy_class = None
    for name in dir(module):
        obj = getattr(module, name)
        if isinstance(obj, type) and issubclass(obj, BaseStrategy) and obj != BaseStrategy:
            strategy_class = obj
            break

    if strategy_class is None:
        raise ValueError(f"No strategy class found in {class_path}")

    # Instantiate with default config
    return strategy_class({})
