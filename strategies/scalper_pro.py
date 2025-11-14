"""
Scalper Pro Strategy

High-frequency mean reversion scalping strategy targeting 2-4% weekly returns.

Core Logic:
- RSI oversold/overbought entries (RSI < 30 buy, > 70 sell)
- Volume confirmation (volume > 1.5x average)
- Tight stops (0.7%)
- Quick profit targets (1%)
- High win rate (65-70% target)

Best for: 5m timeframe, volatile altcoins
Trade frequency: 50-80 per week
"""

from typing import List
import pandas as pd
from engine.strategy import BaseStrategy, StrategyContext, StrategyState
from engine.orders import Order, OrderType, OrderSide
from engine.indicators import Indicators


class ScalperProStrategy(BaseStrategy):
    """Mean reversion scalping with tight risk management"""

    def __init__(self, config: dict = None):
        if config is None:
            config = {
                'name': 'Scalper Pro',

                # RSI settings
                'rsi_period': 14,
                'rsi_oversold': 30,
                'rsi_overbought': 70,
                'rsi_exit': 50,

                # Volume filter
                'min_volume_mult': 1.5,
                'volume_period': 20,

                # Risk management (aggressive for scalping)
                'stop_loss_pct': 0.007,  # 0.7%
                'take_profit_pct': 0.010,  # 1.0%
                'breakeven_pct': 0.004,  # Move to BE at 0.4%

                # Filters
                'min_candle_size': 0.002,  # Min 0.2% range
                'max_spread_pct': 0.001,  # Max 0.1% spread

                'risk_pct': 1.0,  # 1% risk per trade
            }

        super().__init__(config)

        self.rsi_period = config['rsi_period']
        self.rsi_oversold = config['rsi_oversold']
        self.rsi_overbought = config['rsi_overbought']
        self.rsi_exit = config['rsi_exit']
        self.min_volume_mult = config['min_volume_mult']
        self.volume_period = config['volume_period']
        self.stop_loss_pct = config['stop_loss_pct']
        self.take_profit_pct = config['take_profit_pct']
        self.breakeven_pct = config['breakeven_pct']
        self.min_candle_size = config['min_candle_size']
        self.max_spread_pct = config['max_spread_pct']
        self.risk_pct = config['risk_pct']

    def initialize(self, context: StrategyContext) -> pd.DataFrame:
        """Add required indicators"""
        df = context.data.copy()

        # RSI
        df['rsi'] = Indicators.rsi(df['close'], self.rsi_period)

        # Volume
        df['volume_ma'] = Indicators.volume_ma(df['volume'], self.volume_period)
        df['volume_ratio'] = df['volume'] / df['volume_ma']

        # Candle metrics
        df['candle_range'] = (df['high'] - df['low']) / df['low']
        df['spread'] = (df['high'] - df['low']) / df['close']

        return df

    def on_bar(self, bar: pd.Series, bar_index: int, state: StrategyState, context: StrategyContext) -> List[Order]:
        """Entry logic - only trades when no position"""
        if bar_index < self.rsi_period or state.position_size != 0:
            return []

        data = context.data.iloc[:bar_index+1]

        # Get values
        rsi = data['rsi'].iloc[bar_index]
        volume_ratio = data['volume_ratio'].iloc[bar_index]
        candle_range = data['candle_range'].iloc[bar_index]
        spread = data['spread'].iloc[bar_index]

        # Filters
        if candle_range < self.min_candle_size:
            return []
        if spread > self.max_spread_pct:
            return []

        # Long setup: RSI oversold + volume
        if rsi < self.rsi_oversold and volume_ratio > self.min_volume_mult:
            if bar['close'] > bar['open']:  # Bullish candle
                return self._enter_long(bar, bar_index, state, context)

        # Short setup: RSI overbought + volume
        # (Disabled for crypto - focus on longs)

        return []

    def on_exit(self, bar: pd.Series, bar_index: int, state: StrategyState, context: StrategyContext) -> List[Order]:
        """Exit logic - manage open positions"""
        if state.position_size == 0 or not state.entry_price:
            return []

        orders = []
        current_price = bar['close']
        data = context.data.iloc[:bar_index+1]
        rsi = data['rsi'].iloc[bar_index]

        if state.position_size > 0:  # Long position
            pnl_pct = (current_price - state.entry_price) / state.entry_price

            # Stop loss
            if pnl_pct <= -self.stop_loss_pct:
                orders.append(Order(
                    order_id=f'sl_{bar_index}',
                    symbol=context.symbol,
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=abs(state.position_size),
                    reduce_only=True,
                    tags={'exit_reason': 'STOP_LOSS'}
                ))

            # Take profit
            elif pnl_pct >= self.take_profit_pct:
                orders.append(Order(
                    order_id=f'tp_{bar_index}',
                    symbol=context.symbol,
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=abs(state.position_size),
                    reduce_only=True,
                    tags={'exit_reason': 'TAKE_PROFIT'}
                ))

            # Exit if RSI back to neutral
            elif rsi >= self.rsi_exit and pnl_pct > 0:
                orders.append(Order(
                    order_id=f'rsi_exit_{bar_index}',
                    symbol=context.symbol,
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=abs(state.position_size),
                    reduce_only=True,
                    tags={'exit_reason': 'RSI_NEUTRAL'}
                ))

        return orders

    def _enter_long(self, bar: pd.Series, bar_index: int, state: StrategyState, context: StrategyContext) -> List[Order]:
        """Enter long position"""
        entry_price = bar['close']

        # Calculate position size (1% risk)
        risk_amount = context.account_equity * (self.risk_pct / 100)
        stop_distance = entry_price * self.stop_loss_pct
        position_size = risk_amount / stop_distance

        # Max 20% of balance
        max_size = (context.account_equity * 0.20) / entry_price
        position_size = min(position_size, max_size)

        # Set stops
        state.stop_loss = entry_price * (1 - self.stop_loss_pct)
        state.take_profit = entry_price * (1 + self.take_profit_pct)
        state.entry_price = entry_price
        state.custom_data['entry_rsi'] = context.data['rsi'].iloc[bar_index]

        return [Order(
            order_id=f'scalp_long_{bar_index}',
            symbol=context.symbol,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=position_size,
            tags={'strategy': 'scalper_pro', 'setup': 'rsi_oversold'}
        )]
