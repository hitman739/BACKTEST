"""
Simple EMA Crossover Strategy (Programmatic)
"""

from typing import List
import pandas as pd
from engine.strategy import BaseStrategy, StrategyContext, StrategyState
from engine.orders import Order, OrderType, OrderSide
from engine.indicators import Indicators


class SimpleEMACross(BaseStrategy):
    """Simple EMA crossover strategy"""

    def __init__(self, config: dict = None):
        if config is None:
            config = {
                'name': 'Simple EMA Crossover',
                'fast_ema': 20,
                'slow_ema': 50,
                'atr_period': 14,
                'stop_loss_atr': 2.0,
                'take_profit_atr': 3.0,
                'risk_pct': 1.0,
                'leverage': 5
            }
        super().__init__(config)
        self.fast_period = config.get('fast_ema', 20)
        self.slow_period = config.get('slow_ema', 50)
        self.atr_period = config.get('atr_period', 14)
        self.stop_atr_mult = config.get('stop_loss_atr', 2.0)
        self.tp_atr_mult = config.get('take_profit_atr', 3.0)
        self.risk_pct = config.get('risk_pct', 1.0)
        self.leverage = config.get('leverage', 5)

    def initialize(self, context: StrategyContext) -> pd.DataFrame:
        """Add indicators"""
        df = context.data.copy()
        df['ema_fast'] = Indicators.ema(df['close'], self.fast_period)
        df['ema_slow'] = Indicators.ema(df['close'], self.slow_period)
        df['atr'] = Indicators.atr(df['high'], df['low'], df['close'], self.atr_period)
        return df

    def on_bar(self, bar: pd.Series, bar_index: int, state: StrategyState, context: StrategyContext) -> List[Order]:
        """Entry logic"""
        orders = []
        if state.position_size != 0 or bar_index < 1:
            return orders
        if pd.isna(bar['ema_fast']) or pd.isna(bar['ema_slow']) or pd.isna(bar['atr']):
            return orders

        prev_bar = context.data.iloc[bar_index - 1]
        if pd.isna(prev_bar['ema_fast']) or pd.isna(prev_bar['ema_slow']):
            return orders

        # Bullish cross
        if bar['ema_fast'] > bar['ema_slow'] and prev_bar['ema_fast'] <= prev_bar['ema_slow']:
            entry_price = bar['close']
            atr = bar['atr']
            stop_loss = entry_price - (atr * self.stop_atr_mult)
            risk_amount = context.account_equity * (self.risk_pct / 100)
            price_risk = entry_price - stop_loss
            position_size = risk_amount / price_risk if price_risk > 0 else 0
            max_notional = context.account_equity * 0.5 * self.leverage
            max_size = max_notional / entry_price
            position_size = min(position_size, max_size)
            
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
                state.take_profit = entry_price + (atr * self.tp_atr_mult)

        # Bearish cross
        elif bar['ema_fast'] < bar['ema_slow'] and prev_bar['ema_fast'] >= prev_bar['ema_slow']:
            entry_price = bar['close']
            atr = bar['atr']
            stop_loss = entry_price + (atr * self.stop_atr_mult)
            risk_amount = context.account_equity * (self.risk_pct / 100)
            price_risk = stop_loss - entry_price
            position_size = risk_amount / price_risk if price_risk > 0 else 0
            max_notional = context.account_equity * 0.5 * self.leverage
            max_size = max_notional / entry_price
            position_size = min(position_size, max_size)
            
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
                state.take_profit = entry_price - (atr * self.tp_atr_mult)

        return orders

    def on_exit(self, bar: pd.Series, bar_index: int, state: StrategyState, context: StrategyContext) -> List[Order]:
        """Exit logic"""
        orders = []
        if state.position_size == 0:
            return orders

        is_long = state.position_size > 0
        current_price = bar['close']

        # Stop loss
        if state.stop_loss:
            if (is_long and current_price <= state.stop_loss) or (not is_long and current_price >= state.stop_loss):
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

        # Take profit
        if state.take_profit:
            if (is_long and current_price >= state.take_profit) or (not is_long and current_price <= state.take_profit):
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
