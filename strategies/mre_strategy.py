"""
Mean Reversion Extreme (MRE) Strategy

Concept: Markets revert from extremes
- Identifies oversold/overbought extremes (RSI < 20 or > 80)
- Waits for first sign of reversal
- Quick TP targets (mean reversion is fast)

Author: Claude (Original Strategy)
"""

from typing import List
import pandas as pd
from engine.strategy import BaseStrategy, StrategyContext, StrategyState
from engine.orders import Order, OrderType, OrderSide
from engine.indicators import Indicators


class MREStrategy(BaseStrategy):
    """Mean Reversion Extreme"""

    def __init__(self, config: dict = None):
        if config is None:
            config = {
                'name': 'Mean Reversion Extreme',

                # RSI extremes
                'rsi_period': 14,
                'rsi_oversold': 20,
                'rsi_overbought': 80,
                'rsi_exit_long': 50,  # Exit when RSI reaches 50
                'rsi_exit_short': 50,

                # Volume spike confirmation
                'min_volume_mult': 1.8,

                # Reversal confirmation
                'need_reversal_candle': True,  # Wait for opposite color candle

                # Risk management
                'stop_atr_mult': 3.0,  # Wide stops for mean reversion
                'tp_r': 1.5,  # Quick profit target
                'max_bars': 20,  # Exit if not hit TP in 20 bars

                'risk_pct': 1.5,  # Higher risk for higher win rate strategy
            }

        super().__init__(config)

        self.rsi_period = config['rsi_period']
        self.rsi_oversold = config['rsi_oversold']
        self.rsi_overbought = config['rsi_overbought']
        self.rsi_exit_long = config['rsi_exit_long']
        self.rsi_exit_short = config['rsi_exit_short']
        self.min_volume_mult = config['min_volume_mult']
        self.need_reversal_candle = config['need_reversal_candle']
        self.stop_atr_mult = config['stop_atr_mult']
        self.tp_r = config['tp_r']
        self.max_bars = config['max_bars']
        self.risk_pct = config['risk_pct']

    def initialize(self, context: StrategyContext) -> pd.DataFrame:
        df = context.data.copy()

        # RSI
        df['rsi'] = Indicators.rsi(df['close'], self.rsi_period)

        # ATR for stops
        df['atr'] = Indicators.atr(df['high'], df['low'], df['close'], 14)

        # Volume
        df['volume_ma'] = df['volume'].rolling(20).mean()

        # Candle direction
        df['bullish'] = df['close'] > df['open']

        return df

    def on_bar(self, bar: pd.Series, bar_index: int, state: StrategyState, context: StrategyContext) -> List[Order]:
        if bar_index < 50 or state.position_size != 0:
            return []

        data = context.data.iloc[:bar_index+1]

        # Check for oversold reversal (LONG)
        if self._check_oversold_reversal(data, bar_index):
            return self._enter_long(bar, bar_index, state, context, data)

        # Check for overbought reversal (SHORT)
        if self._check_overbought_reversal(data, bar_index):
            return self._enter_short(bar, bar_index, state, context, data)

        return []

    def on_exit(self, bar: pd.Series, bar_index: int, state: StrategyState, context: StrategyContext) -> List[Order]:
        if state.position_size == 0 or not state.entry_price or not state.stop_loss:
            return []

        orders = []
        current_price = bar['close']
        risk = abs(state.entry_price - state.stop_loss)
        data = context.data.iloc[:bar_index+1]
        rsi = data['rsi'].iloc[bar_index]

        position_side = 'long' if state.position_size > 0 else 'short'
        bars_in_trade = bar_index - state.entry_bar_index

        if position_side == 'long':
            pnl_r = (current_price - state.entry_price) / risk if risk > 0 else 0

            # TP at target R
            if pnl_r >= self.tp_r:
                orders.append(Order(
                    order_id=f'tp_{bar_index}',
                    symbol=context.symbol,
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=abs(state.position_size),
                    reduce_only=True,
                    tags={'exit_reason': f'TP_{self.tp_r}R'}
                ))

            # Exit when RSI reaches 50 (mean)
            elif rsi >= self.rsi_exit_long:
                orders.append(Order(
                    order_id=f'rsi_exit_{bar_index}',
                    symbol=context.symbol,
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=abs(state.position_size),
                    reduce_only=True,
                    tags={'exit_reason': 'RSI_MEAN'}
                ))

            # Time-based exit
            elif bars_in_trade >= self.max_bars:
                orders.append(Order(
                    order_id=f'time_exit_{bar_index}',
                    symbol=context.symbol,
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=abs(state.position_size),
                    reduce_only=True,
                    tags={'exit_reason': 'TIME_LIMIT'}
                ))

            # Stop loss
            elif current_price <= state.stop_loss:
                orders.append(Order(
                    order_id=f'sl_{bar_index}',
                    symbol=context.symbol,
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=abs(state.position_size),
                    reduce_only=True,
                    tags={'exit_reason': 'stop_loss'}
                ))

        else:  # short
            pnl_r = (state.entry_price - current_price) / risk if risk > 0 else 0

            if pnl_r >= self.tp_r:
                orders.append(Order(
                    order_id=f'tp_{bar_index}',
                    symbol=context.symbol,
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    quantity=abs(state.position_size),
                    reduce_only=True,
                    tags={'exit_reason': f'TP_{self.tp_r}R'}
                ))

            elif rsi <= self.rsi_exit_short:
                orders.append(Order(
                    order_id=f'rsi_exit_{bar_index}',
                    symbol=context.symbol,
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    quantity=abs(state.position_size),
                    reduce_only=True,
                    tags={'exit_reason': 'RSI_MEAN'}
                ))

            elif bars_in_trade >= self.max_bars:
                orders.append(Order(
                    order_id=f'time_exit_{bar_index}',
                    symbol=context.symbol,
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    quantity=abs(state.position_size),
                    reduce_only=True,
                    tags={'exit_reason': 'TIME_LIMIT'}
                ))

            elif current_price >= state.stop_loss:
                orders.append(Order(
                    order_id=f'sl_{bar_index}',
                    symbol=context.symbol,
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    quantity=abs(state.position_size),
                    reduce_only=True,
                    tags={'exit_reason': 'stop_loss'}
                ))

        return orders

    def _check_oversold_reversal(self, data, idx):
        """Check for oversold + reversal"""

        current_rsi = data['rsi'].iloc[idx]
        prev_rsi = data['rsi'].iloc[idx-1]

        # RSI was/is oversold
        if current_rsi > self.rsi_oversold:
            return False

        # Volume spike
        vol_ratio = data['volume'].iloc[idx] / data['volume_ma'].iloc[idx]
        if vol_ratio < self.min_volume_mult:
            return False

        # Reversal candle (bullish after oversold)
        if self.need_reversal_candle:
            if not data['bullish'].iloc[idx]:
                return False

        # RSI starting to turn up
        if current_rsi <= prev_rsi:
            return False

        return True

    def _check_overbought_reversal(self, data, idx):
        """Check for overbought + reversal"""

        current_rsi = data['rsi'].iloc[idx]
        prev_rsi = data['rsi'].iloc[idx-1]

        # RSI was/is overbought
        if current_rsi < self.rsi_overbought:
            return False

        # Volume spike
        vol_ratio = data['volume'].iloc[idx] / data['volume_ma'].iloc[idx]
        if vol_ratio < self.min_volume_mult:
            return False

        # Reversal candle (bearish after overbought)
        if self.need_reversal_candle:
            if data['bullish'].iloc[idx]:
                return False

        # RSI starting to turn down
        if current_rsi >= prev_rsi:
            return False

        return True

    def _enter_long(self, bar, bar_index, state, context, data):
        entry_price = bar['close']
        atr = data['atr'].iloc[bar_index]

        # Wide stop for mean reversion
        recent_low = data['low'].iloc[bar_index-10:bar_index+1].min()
        stop_loss = min(recent_low, entry_price - (atr * self.stop_atr_mult))

        risk = entry_price - stop_loss
        if risk <= 0:
            return []

        account_risk = context.account_equity * (self.risk_pct / 100)
        position_size = account_risk / risk

        state.stop_loss = stop_loss
        state.custom_data['entry_rsi'] = data['rsi'].iloc[bar_index]

        return [Order(
            order_id=f'long_{bar_index}',
            symbol=context.symbol,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=position_size,
            tags={'setup': 'MRE_LONG', 'stop_loss': stop_loss}
        )]

    def _enter_short(self, bar, bar_index, state, context, data):
        entry_price = bar['close']
        atr = data['atr'].iloc[bar_index]

        recent_high = data['high'].iloc[bar_index-10:bar_index+1].max()
        stop_loss = max(recent_high, entry_price + (atr * self.stop_atr_mult))

        risk = stop_loss - entry_price
        if risk <= 0:
            return []

        account_risk = context.account_equity * (self.risk_pct / 100)
        position_size = account_risk / risk

        state.stop_loss = stop_loss
        state.custom_data['entry_rsi'] = data['rsi'].iloc[bar_index]

        return [Order(
            order_id=f'short_{bar_index}',
            symbol=context.symbol,
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=position_size,
            tags={'setup': 'MRE_SHORT', 'stop_loss': stop_loss}
        )]
