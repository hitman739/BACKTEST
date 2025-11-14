"""
TETR Ultra - Optimized with ADX Filter

Improvements over original TETR:
- ADX filter: Only trade when trend is strong (ADX > 25)
- Wider stops: Less whipsaws
- Better breakeven: Move to BE at 0.75R instead of 1R
- Tighter EMAs: Better for current market conditions

Author: Claude (Optimized Version)
"""

from typing import List
import pandas as pd
from engine.strategy import BaseStrategy, StrategyContext, StrategyState
from engine.orders import Order, OrderType, OrderSide
from engine.indicators import Indicators


class TETRUltraStrategy(BaseStrategy):
    """TETR Ultra - Optimized with ADX"""

    def __init__(self, config: dict = None):
        if config is None:
            config = {
                'name': 'TETR Ultra (ADX Filter)',

                # EMAs - tighter for faster response
                'ema_fast': 8,
                'ema_mid': 21,
                'ema_slow': 55,

                # Entry criteria - more lenient
                'pullback_tolerance': 0.005,  # 0.5% (was 0.3%)
                'min_ema_separation': 0.0015,  # 0.15% (was 0.2%)

                # ADX filter - NEW
                'use_adx_filter': True,
                'min_adx': 25,  # Only trade when ADX > 25

                # Volume filter
                'min_volume_mult': 1.1,  # Reduced from 1.2

                # Risk management - improved
                'stop_below_ema': 55,
                'stop_atr_buffer': 0.8,  # Wider stops (was 0.5)
                'use_trailing': True,
                'trailing_atr': 2.5,  # Wider trailing (was 2.0)
                'breakeven_r': 0.75,  # Faster BE (was 1.0)

                'risk_pct': 1.0,
            }

        super().__init__(config)

        self.ema_fast = config['ema_fast']
        self.ema_mid = config['ema_mid']
        self.ema_slow = config['ema_slow']
        self.pullback_tolerance = config['pullback_tolerance']
        self.min_ema_separation = config['min_ema_separation']
        self.use_adx_filter = config['use_adx_filter']
        self.min_adx = config['min_adx']
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

        # ADX for trend strength
        df['adx'] = Indicators.adx(df['high'], df['low'], df['close'], 14)

        # Volume
        df['volume_ma'] = df['volume'].rolling(20).mean()

        return df

    def on_bar(self, bar: pd.Series, bar_index: int, state: StrategyState, context: StrategyContext) -> List[Order]:
        if bar_index < 60 or state.position_size != 0:
            return []

        data = context.data.iloc[:bar_index+1]

        # Check for LONG setup
        if self._check_long_setup(data, bar_index):
            return self._enter_long(bar, bar_index, state, context, data)

        # Check for SHORT setup
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

            # Move to breakeven at 0.75R (faster than original)
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
        """Check for bullish EMA alignment + pullback + ADX"""

        ema_fast = data['ema_fast'].iloc[idx]
        ema_mid = data['ema_mid'].iloc[idx]
        ema_slow = data['ema_slow'].iloc[idx]
        close = data['close'].iloc[idx]
        low = data['low'].iloc[idx]

        # 1. EMAs must be aligned
        if not (ema_fast > ema_mid > ema_slow):
            return False

        # 2. EMAs must be separated
        sep1 = (ema_fast - ema_mid) / ema_mid
        sep2 = (ema_mid - ema_slow) / ema_slow
        if sep1 < self.min_ema_separation or sep2 < self.min_ema_separation:
            return False

        # 3. ADX filter - NEW (trend strength)
        if self.use_adx_filter:
            adx = data['adx'].iloc[idx]
            if adx < self.min_adx:
                return False  # Skip if trend is weak

        # 4. Price pulled back to EMA21
        distance_to_mid = abs(low - ema_mid) / ema_mid
        if low > ema_mid or distance_to_mid > self.pullback_tolerance:
            return False

        # 5. Now bouncing back up
        if close <= ema_mid:
            return False

        # 6. Volume confirmation
        vol_ratio = data['volume'].iloc[idx] / data['volume_ma'].iloc[idx]
        if vol_ratio < self.min_volume_mult:
            return False

        return True

    def _check_short_setup(self, data, idx):
        """Check for bearish EMA alignment + pullback + ADX"""

        ema_fast = data['ema_fast'].iloc[idx]
        ema_mid = data['ema_mid'].iloc[idx]
        ema_slow = data['ema_slow'].iloc[idx]
        close = data['close'].iloc[idx]
        high = data['high'].iloc[idx]

        # 1. EMAs must be aligned
        if not (ema_fast < ema_mid < ema_slow):
            return False

        # 2. EMAs must be separated
        sep1 = (ema_mid - ema_fast) / ema_mid
        sep2 = (ema_slow - ema_mid) / ema_slow
        if sep1 < self.min_ema_separation or sep2 < self.min_ema_separation:
            return False

        # 3. ADX filter - NEW
        if self.use_adx_filter:
            adx = data['adx'].iloc[idx]
            if adx < self.min_adx:
                return False

        # 4. Price pulled back to EMA21
        distance_to_mid = abs(high - ema_mid) / ema_mid
        if high < ema_mid or distance_to_mid > self.pullback_tolerance:
            return False

        # 5. Now bouncing back down
        if close >= ema_mid:
            return False

        # 6. Volume confirmation
        vol_ratio = data['volume'].iloc[idx] / data['volume_ma'].iloc[idx]
        if vol_ratio < self.min_volume_mult:
            return False

        return True

    def _enter_long(self, bar, bar_index, state, context, data):
        entry_price = bar['close']
        atr = data['atr'].iloc[bar_index]
        ema_slow = data['ema_slow'].iloc[bar_index]

        # Wider stop (0.8 ATR instead of 0.5)
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
            tags={'setup': 'TETR_ULTRA_LONG', 'stop_loss': stop_loss}
        )]

    def _enter_short(self, bar, bar_index, state, context, data):
        entry_price = bar['close']
        atr = data['atr'].iloc[bar_index]
        ema_slow = data['ema_slow'].iloc[bar_index]

        # Wider stop
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
            tags={'setup': 'TETR_ULTRA_SHORT', 'stop_loss': stop_loss}
        )]
