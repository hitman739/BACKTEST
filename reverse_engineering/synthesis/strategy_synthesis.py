"""
Strategy Synthesis
Generates executable Python strategies from extracted rules
"""

from pathlib import Path
from datetime import datetime


class StrategySynthesizer:
    """Generates strategy code from rule specifications"""

    def __init__(self, output_dir: Path = Path("strategies/reverse_engineered")):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def synthesize(self, rules: dict, vault_address: str) -> Path:
        """
        Generate strategy Python file from rules

        Returns path to generated strategy file
        """
        print("\n" + "=" * 70)
        print("🔨 STRATEGY SYNTHESIS")
        print("=" * 70)

        vault_short = vault_address[:10]
        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f"vault_{vault_short}_{timestamp}_v1.py"
        filepath = self.output_dir / filename

        code = self._generate_strategy_code(rules, vault_address)

        with open(filepath, 'w') as f:
            f.write(code)

        print(f"\n✅ Strategy generated: {filepath}")
        print(f"   Name: {rules.get('name', 'Unknown')}")

        return filepath

    def _generate_strategy_code(self, rules: dict, vault_address: str) -> str:
        """Generate complete Python strategy class"""

        entry_rules = rules.get('entry', {})
        exit_rules = rules.get('exit', {})
        risk_rules = rules.get('risk', {})

        # Extract parameters
        sl_r = exit_rules.get('stop_loss', {}).get('value', 1.5)
        tp_r = exit_rules.get('take_profit', {}).get('value', 2.0)
        trailing_enabled = exit_rules.get('trailing', {}).get('enabled', False)
        trailing_activation = exit_rules.get('trailing', {}).get('activation', 1.0)
        timeout = exit_rules.get('timeout', 10)

        long_only = risk_rules.get('directional_bias', '') == 'long_only'

        code = f'''"""
Vault Clone Strategy
Auto-generated from reverse engineering Hyperliquid vault {vault_address}
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

from engine.strategy import BaseStrategy, StrategyContext, StrategyState
from engine.orders import Order
from typing import List
import pandas as pd


class VaultCloneStrategy(BaseStrategy):
    """
    {rules.get('name', 'Vault Clone Strategy')}

    Reverse-engineered from Hyperliquid vault trading patterns
    """

    def __init__(self, config: dict = None):
        default_config = {{
            'name': '{rules.get('name', 'Vault Clone')}',

            # Technical indicators
            'ema_fast': 20,
            'ema_slow': 50,
            'rsi_period': 14,
            'atr_period': 14,

            # Entry thresholds (inferred from vault)
            'rsi_oversold': 30,
            'rsi_overbought': 70,

            # Exit parameters (inferred from vault)
            'stop_loss_r': {sl_r},
            'take_profit_r': {tp_r},
            'trailing_enabled': {trailing_enabled},
            'trailing_activation_r': {trailing_activation},
            'trailing_distance_r': 0.5,

            # Risk management (inferred from vault)
            'base_risk_pct': 1.0,
            'max_positions': 1,

            # Filters (inferred from vault)
            'long_only': {long_only},
            'timeout_bars': {timeout},
        }}

        if config:
            default_config.update(config)

        super().__init__(default_config)

        # Extract config
        self.ema_fast = default_config['ema_fast']
        self.ema_slow = default_config['ema_slow']
        self.rsi_period = default_config['rsi_period']
        self.atr_period = default_config['atr_period']

        self.rsi_oversold = default_config['rsi_oversold']
        self.rsi_overbought = default_config['rsi_overbought']

        self.sl_r = default_config['stop_loss_r']
        self.tp_r = default_config['take_profit_r']
        self.trailing_enabled = default_config['trailing_enabled']
        self.trailing_activation_r = default_config['trailing_activation_r']
        self.trailing_distance_r = default_config['trailing_distance_r']

        self.base_risk = default_config['base_risk_pct']
        self.long_only = default_config['long_only']
        self.timeout = default_config['timeout_bars']

    def initialize(self, context: StrategyContext) -> pd.DataFrame:
        """Add indicators"""
        data = context.data.copy()

        # EMAs
        data['ema_fast'] = data['close'].ewm(span=self.ema_fast, adjust=False).mean()
        data['ema_slow'] = data['close'].ewm(span=self.ema_slow, adjust=False).mean()

        # RSI
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        data['rsi'] = 100 - (100 / (1 + rs))

        # ATR
        high_low = data['high'] - data['low']
        high_close = abs(data['high'] - data['close'].shift())
        low_close = abs(data['low'] - data['close'].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        data['atr'] = true_range.rolling(window=self.atr_period).mean()

        return data

    def on_bar(self, bar, bar_index, state, context) -> List[Order]:
        """Entry logic (inferred from vault patterns)"""
        orders = []

        # Only trade if no position
        if state.position_size != 0:
            return orders

        # Skip if insufficient data
        if bar_index < max(self.ema_slow, self.rsi_period, self.atr_period):
            return orders

        # Entry conditions (inferred from vault analysis)
        ema_bullish = bar['ema_fast'] > bar['ema_slow']
        price_above_ema = bar['close'] > bar['ema_fast']
        rsi_not_extreme = self.rsi_oversold < bar['rsi'] < self.rsi_overbought

        # Long entry
        if ema_bullish and price_above_ema and rsi_not_extreme:
            # Calculate position size
            risk_amount = state.equity * (self.base_risk / 100.0)
            atr = bar['atr']
            stop_distance = atr * self.sl_r

            if stop_distance > 0:
                size = risk_amount / stop_distance

                # Create order
                order = Order(
                    symbol=context.symbol,
                    side='long',
                    order_type='market',
                    size=size,
                    timestamp=bar['timestamp']
                )
                orders.append(order)

                # Set stops
                state.stop_loss = bar['close'] - stop_distance
                state.take_profit = bar['close'] + (stop_distance * self.tp_r)

                # Store R value for trailing
                state.custom_data['r_value'] = stop_distance
                state.custom_data['trailing_active'] = False

        return orders

    def on_exit(self, bar, bar_index, state, context) -> List[Order]:
        """Exit logic (inferred from vault patterns)"""
        orders = []

        if state.position_size == 0:
            return orders

        is_long = state.position_size > 0
        current_price = bar['close']

        # Timeout
        bars_in_trade = bar_index - state.entry_bar_index
        if bars_in_trade > self.timeout:
            return [self._create_exit_order(bar, bar_index, state, context, 'timeout')]

        # Stop loss
        if state.stop_loss:
            if (is_long and current_price <= state.stop_loss) or \\
               (not is_long and current_price >= state.stop_loss):
                return [self._create_exit_order(bar, bar_index, state, context, 'stop_loss')]

        # Trailing stop
        if self.trailing_enabled:
            r_value = state.custom_data.get('r_value', bar['atr'])
            profit = (current_price - state.entry_price) if is_long else (state.entry_price - current_price)

            if profit >= r_value * self.trailing_activation_r and not state.custom_data.get('trailing_active'):
                state.custom_data['trailing_active'] = True
                trail_distance = r_value * self.trailing_distance_r
                state.stop_loss = current_price - trail_distance if is_long else current_price + trail_distance

            # Update trail
            if state.custom_data.get('trailing_active'):
                trail_distance = r_value * self.trailing_distance_r
                if is_long:
                    new_stop = current_price - trail_distance
                    if new_stop > state.stop_loss:
                        state.stop_loss = new_stop
                else:
                    new_stop = current_price + trail_distance
                    if new_stop < state.stop_loss:
                        state.stop_loss = new_stop

        # Take profit
        if state.take_profit:
            if (is_long and current_price >= state.take_profit) or \\
               (not is_long and current_price <= state.take_profit):
                return [self._create_exit_order(bar, bar_index, state, context, 'take_profit')]

        return orders

    def _create_exit_order(self, bar, bar_index, state, context, reason):
        """Helper to create exit order"""
        return Order(
            symbol=context.symbol,
            side='sell' if state.position_size > 0 else 'buy',
            order_type='market',
            size=abs(state.position_size),
            timestamp=bar['timestamp']
        )
'''

        return code
