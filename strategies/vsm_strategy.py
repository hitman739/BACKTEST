"""
Volume Spike Momentum (VSM) Strategy

Concept: Ride momentum when volume surges
- Detects volume spikes (>2.5x average)
- Confirms with RSI momentum breakout
- Rides the wave with trailing stops

Author: Claude (Original Strategy)
"""

from typing import List
import pandas as pd
from engine.strategy import BaseStrategy, StrategyContext, StrategyState
from engine.orders import Order, OrderType, OrderSide
from engine.indicators import Indicators


class VSMStrategy(BaseStrategy):
    """Volume Spike Momentum"""

    def __init__(self, config: dict = None):
        if config is None:
            config = {
                'name': 'Volume Spike Momentum',

                # Volume criteria
                'volume_spike_mult': 2.5,  # Volume > 2.5x average
                'volume_ma_period': 20,

                # Momentum criteria
                'rsi_period': 14,
                'rsi_long_min': 60,  # RSI must be >60 for LONG
                'rsi_short_max': 40,  # RSI must be <40 for SHORT

                # Candle criteria
                'min_body_ratio': 0.6,  # Body >= 60% of range (strong candle)
                'min_range_atr': 1.0,  # Range >= 1.0 ATR

                # Trend filter
                'ema_period': 50,

                # Risk management
                'stop_atr_mult': 1.5,
                'use_trailing': True,
                'trailing_atr': 1.0,
                'breakeven_r': 1.5,

                'risk_pct': 1.0,
            }

        super().__init__(config)

        self.volume_spike_mult = config['volume_spike_mult']
        self.volume_ma_period = config['volume_ma_period']
        self.rsi_period = config['rsi_period']
        self.rsi_long_min = config['rsi_long_min']
        self.rsi_short_max = config['rsi_short_max']
        self.min_body_ratio = config['min_body_ratio']
        self.min_range_atr = config['min_range_atr']
        self.ema_period = config['ema_period']
        self.stop_atr_mult = config['stop_atr_mult']
        self.use_trailing = config['use_trailing']
        self.trailing_atr = config['trailing_atr']
        self.breakeven_r = config['breakeven_r']
        self.risk_pct = config['risk_pct']

    def initialize(self, context: StrategyContext) -> pd.DataFrame:
        df = context.data.copy()

        # Volume
        df['volume_ma'] = df['volume'].rolling(self.volume_ma_period).mean()

        # RSI
        df['rsi'] = Indicators.rsi(df['close'], self.rsi_period)

        # ATR
        df['atr'] = Indicators.atr(df['high'], df['low'], df['close'], 14)

        # EMA for trend
        df['ema'] = Indicators.ema(df['close'], self.ema_period)

        # Candle characteristics
        df['candle_range'] = df['high'] - df['low']
        df['candle_body'] = abs(df['close'] - df['open'])
        df['body_ratio'] = df['candle_body'] / df['candle_range']

        return df

    def on_bar(self, bar: pd.Series, bar_index: int, state: StrategyState, context: StrategyContext) -> List[Order]:
        if bar_index < 60 or state.position_size != 0:
            return []

        data = context.data.iloc[:bar_index+1]

        # Check for bullish volume spike
        if self._check_bullish_volume_spike(data, bar_index):
            return self._enter_long(bar, bar_index, state, context, data)

        # Check for bearish volume spike
        if self._check_bearish_volume_spike(data, bar_index):
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

            # Move to breakeven
            if not breakeven_moved and pnl_r >= self.breakeven_r:
                state.stop_loss = state.entry_price
                state.custom_data['breakeven_moved'] = True

            # Trailing stop (aggressive - ride the momentum)
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

        return orders

    def _check_bullish_volume_spike(self, data, idx):
        """Check for bullish volume spike with momentum"""

        # 1. Volume spike
        vol_ratio = data['volume'].iloc[idx] / data['volume_ma'].iloc[idx]
        if vol_ratio < self.volume_spike_mult:
            return False

        # 2. Strong bullish candle
        if data['close'].iloc[idx] <= data['open'].iloc[idx]:
            return False

        body_ratio = data['body_ratio'].iloc[idx]
        if body_ratio < self.min_body_ratio:
            return False

        # 3. Large candle
        range_atr_ratio = data['candle_range'].iloc[idx] / data['atr'].iloc[idx]
        if range_atr_ratio < self.min_range_atr:
            return False

        # 4. RSI showing momentum
        if data['rsi'].iloc[idx] < self.rsi_long_min:
            return False

        # 5. Trend filter (price above EMA50)
        if data['close'].iloc[idx] < data['ema'].iloc[idx]:
            return False

        return True

    def _check_bearish_volume_spike(self, data, idx):
        """Check for bearish volume spike with momentum"""

        # 1. Volume spike
        vol_ratio = data['volume'].iloc[idx] / data['volume_ma'].iloc[idx]
        if vol_ratio < self.volume_spike_mult:
            return False

        # 2. Strong bearish candle
        if data['close'].iloc[idx] >= data['open'].iloc[idx]:
            return False

        body_ratio = data['body_ratio'].iloc[idx]
        if body_ratio < self.min_body_ratio:
            return False

        # 3. Large candle
        range_atr_ratio = data['candle_range'].iloc[idx] / data['atr'].iloc[idx]
        if range_atr_ratio < self.min_range_atr:
            return False

        # 4. RSI showing momentum
        if data['rsi'].iloc[idx] > self.rsi_short_max:
            return False

        # 5. Trend filter (price below EMA50)
        if data['close'].iloc[idx] > data['ema'].iloc[idx]:
            return False

        return True

    def _enter_long(self, bar, bar_index, state, context, data):
        entry_price = bar['close']
        atr = data['atr'].iloc[bar_index]

        # Stop below low of momentum candle
        stop_loss = bar['low'] - (atr * self.stop_atr_mult)

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
            tags={'setup': 'VSM_LONG', 'stop_loss': stop_loss}
        )]

    def _enter_short(self, bar, bar_index, state, context, data):
        entry_price = bar['close']
        atr = data['atr'].iloc[bar_index]

        # Stop above high of momentum candle
        stop_loss = bar['high'] + (atr * self.stop_atr_mult)

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
            tags={'setup': 'VSM_SHORT', 'stop_loss': stop_loss}
        )]
