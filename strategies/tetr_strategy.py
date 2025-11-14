"""
Triple EMA Trend Rider (TETR) Strategy

Concept: Ride strong trends with EMA alignment
- Only trades when EMA 9/21/55 are aligned
- Enters on pullbacks to EMA21
- Uses trailing stops to capture big moves

Author: Claude (Original Strategy)
"""

from typing import List
import pandas as pd
from engine.strategy import BaseStrategy, StrategyContext, StrategyState
from engine.orders import Order, OrderType, OrderSide
from engine.indicators import Indicators


class TETRStrategy(BaseStrategy):
    """Triple EMA Trend Rider"""

    def __init__(self, config: dict = None):
        if config is None:
            config = {
                'name': 'Triple EMA Trend Rider',

                # EMAs
                'ema_fast': 9,
                'ema_mid': 21,
                'ema_slow': 55,

                # Entry criteria
                'pullback_tolerance': 0.003,  # 0.3% from EMA21
                'min_ema_separation': 0.002,  # EMAs must be 0.2% apart

                # Volume filter
                'min_volume_mult': 1.2,

                # Risk management
                'stop_below_ema': 55,  # Stop below EMA55
                'stop_atr_buffer': 0.5,  # Extra buffer
                'use_trailing': True,
                'trailing_atr': 2.0,
                'breakeven_r': 1.0,  # Move to BE at 1R

                'risk_pct': 1.0,
            }

        super().__init__(config)

        self.ema_fast = config['ema_fast']
        self.ema_mid = config['ema_mid']
        self.ema_slow = config['ema_slow']
        self.pullback_tolerance = config['pullback_tolerance']
        self.min_ema_separation = config['min_ema_separation']
        self.min_volume_mult = config['min_volume_mult']
        self.stop_below_ema = config['stop_below_ema']
        self.stop_atr_buffer = config['stop_atr_buffer']
        self.use_trailing = config['use_trailing']
        self.trailing_atr = config['trailing_atr']
        self.breakeven_r = config['breakeven_r']
        self.risk_pct = config['risk_pct']

    def initialize(self, context: StrategyContext) -> pd.DataFrame:
        df = context.data.copy()

        # Triple EMAs
        df['ema_fast'] = Indicators.ema(df['close'], self.ema_fast)
        df['ema_mid'] = Indicators.ema(df['close'], self.ema_mid)
        df['ema_slow'] = Indicators.ema(df['close'], self.ema_slow)

        # ATR
        df['atr'] = Indicators.atr(df['high'], df['low'], df['close'], 14)

        # Volume
        df['volume_ma'] = df['volume'].rolling(20).mean()

        return df

    def on_bar(self, bar: pd.Series, bar_index: int, state: StrategyState, context: StrategyContext) -> List[Order]:
        if bar_index < 60 or state.position_size != 0:
            return []

        data = context.data.iloc[:bar_index+1]

        # Check for LONG setup (bullish alignment + pullback)
        if self._check_long_setup(data, bar_index):
            return self._enter_long(bar, bar_index, state, context, data)

        # Check for SHORT setup (bearish alignment + pullback)
        if self._check_short_setup(data, bar_index):
            return self._enter_short(bar, bar_index, state, context, data)

        return []

    def on_exit(self, bar: pd.Series, bar_index: int, state: StrategyState, context: StrategyContext) -> List[Order]:
        if state.position_size == 0 or not state.entry_price or not state.stop_loss:
            return []

        orders = []
        current_price = bar['close']
        risk = abs(state.entry_price - state.stop_loss)
        data = context.data.iloc[:bar_index+1]
        atr = data['atr'].iloc[bar_index]

        position_side = 'long' if state.position_size > 0 else 'short'
        breakeven_moved = state.custom_data.get('breakeven_moved', False)

        if position_side == 'long':
            pnl_r = (current_price - state.entry_price) / risk if risk > 0 else 0

            # Move to breakeven at 1R
            if not breakeven_moved and pnl_r >= self.breakeven_r:
                state.stop_loss = state.entry_price
                state.custom_data['breakeven_moved'] = True

            # Trailing stop
            if self.use_trailing and breakeven_moved:
                trailing_stop = current_price - (atr * self.trailing_atr)
                if trailing_stop > state.stop_loss:
                    state.stop_loss = trailing_stop

            # Stop loss
            if current_price <= state.stop_loss:
                exit_reason = 'breakeven' if breakeven_moved else 'stop_loss'
                orders.append(Order(
                    order_id=f'sl_{bar_index}',
                    symbol=context.symbol,
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=abs(state.position_size),
                    reduce_only=True,
                    tags={'exit_reason': exit_reason}
                ))

            # Exit if EMAs no longer aligned
            elif data['ema_fast'].iloc[bar_index] < data['ema_mid'].iloc[bar_index]:
                orders.append(Order(
                    order_id=f'ema_exit_{bar_index}',
                    symbol=context.symbol,
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=abs(state.position_size),
                    reduce_only=True,
                    tags={'exit_reason': 'EMA_MISALIGN'}
                ))

        else:  # short
            pnl_r = (state.entry_price - current_price) / risk if risk > 0 else 0

            if not breakeven_moved and pnl_r >= self.breakeven_r:
                state.stop_loss = state.entry_price
                state.custom_data['breakeven_moved'] = True

            if self.use_trailing and breakeven_moved:
                trailing_stop = current_price + (atr * self.trailing_atr)
                if trailing_stop < state.stop_loss:
                    state.stop_loss = trailing_stop

            if current_price >= state.stop_loss:
                exit_reason = 'breakeven' if breakeven_moved else 'stop_loss'
                orders.append(Order(
                    order_id=f'sl_{bar_index}',
                    symbol=context.symbol,
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    quantity=abs(state.position_size),
                    reduce_only=True,
                    tags={'exit_reason': exit_reason}
                ))

            elif data['ema_fast'].iloc[bar_index] > data['ema_mid'].iloc[bar_index]:
                orders.append(Order(
                    order_id=f'ema_exit_{bar_index}',
                    symbol=context.symbol,
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    quantity=abs(state.position_size),
                    reduce_only=True,
                    tags={'exit_reason': 'EMA_MISALIGN'}
                ))

        return orders

    def _check_long_setup(self, data, idx):
        """Check for bullish EMA alignment + pullback to EMA21"""

        ema_fast = data['ema_fast'].iloc[idx]
        ema_mid = data['ema_mid'].iloc[idx]
        ema_slow = data['ema_slow'].iloc[idx]
        close = data['close'].iloc[idx]
        low = data['low'].iloc[idx]

        # 1. EMAs must be aligned (fast > mid > slow)
        if not (ema_fast > ema_mid > ema_slow):
            return False

        # 2. EMAs must be separated (strong trend)
        sep1 = (ema_fast - ema_mid) / ema_mid
        sep2 = (ema_mid - ema_slow) / ema_slow
        if sep1 < self.min_ema_separation or sep2 < self.min_ema_separation:
            return False

        # 3. Price pulled back to EMA21 (or below)
        distance_to_mid = abs(low - ema_mid) / ema_mid
        if low > ema_mid or distance_to_mid > self.pullback_tolerance:
            return False

        # 4. Now bouncing back up (close above EMA21)
        if close <= ema_mid:
            return False

        # 5. Volume confirmation
        vol_ratio = data['volume'].iloc[idx] / data['volume_ma'].iloc[idx]
        if vol_ratio < self.min_volume_mult:
            return False

        return True

    def _check_short_setup(self, data, idx):
        """Check for bearish EMA alignment + pullback to EMA21"""

        ema_fast = data['ema_fast'].iloc[idx]
        ema_mid = data['ema_mid'].iloc[idx]
        ema_slow = data['ema_slow'].iloc[idx]
        close = data['close'].iloc[idx]
        high = data['high'].iloc[idx]

        # 1. EMAs must be aligned (fast < mid < slow)
        if not (ema_fast < ema_mid < ema_slow):
            return False

        # 2. EMAs must be separated
        sep1 = (ema_mid - ema_fast) / ema_mid
        sep2 = (ema_slow - ema_mid) / ema_slow
        if sep1 < self.min_ema_separation or sep2 < self.min_ema_separation:
            return False

        # 3. Price pulled back to EMA21 (or above)
        distance_to_mid = abs(high - ema_mid) / ema_mid
        if high < ema_mid or distance_to_mid > self.pullback_tolerance:
            return False

        # 4. Now bouncing back down
        if close >= ema_mid:
            return False

        # 5. Volume confirmation
        vol_ratio = data['volume'].iloc[idx] / data['volume_ma'].iloc[idx]
        if vol_ratio < self.min_volume_mult:
            return False

        return True

    def _enter_long(self, bar, bar_index, state, context, data):
        entry_price = bar['close']
        atr = data['atr'].iloc[bar_index]
        ema_slow = data['ema_slow'].iloc[bar_index]

        # Stop below EMA55 with buffer
        stop_loss = ema_slow - (atr * self.stop_atr_buffer)

        risk = entry_price - stop_loss
        if risk <= 0:
            return []

        account_risk = context.account_equity * (self.risk_pct / 100)
        position_size = account_risk / risk

        state.stop_loss = stop_loss
        state.custom_data['breakeven_moved'] = False

        return [Order(
            order_id=f'long_{bar_index}',
            symbol=context.symbol,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=position_size,
            tags={'setup': 'TETR_LONG', 'stop_loss': stop_loss}
        )]

    def _enter_short(self, bar, bar_index, state, context, data):
        entry_price = bar['close']
        atr = data['atr'].iloc[bar_index]
        ema_slow = data['ema_slow'].iloc[bar_index]

        # Stop above EMA55 with buffer
        stop_loss = ema_slow + (atr * self.stop_atr_buffer)

        risk = stop_loss - entry_price
        if risk <= 0:
            return []

        account_risk = context.account_equity * (self.risk_pct / 100)
        position_size = account_risk / risk

        state.stop_loss = stop_loss
        state.custom_data['breakeven_moved'] = False

        return [Order(
            order_id=f'short_{bar_index}',
            symbol=context.symbol,
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=position_size,
            tags={'setup': 'TETR_SHORT', 'stop_loss': stop_loss}
        )]
