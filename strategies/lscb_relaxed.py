"""
LSCB Strategy - Relaxed Version

More practical implementation with adjusted parameters
"""

import pandas as pd
import numpy as np
from typing import List
from engine.strategy import BaseStrategy, StrategyContext, StrategyState
from engine.orders import Order, OrderType, OrderSide
from engine.indicators import Indicators


class LSCBRelaxedStrategy(BaseStrategy):
    """LSCB with relaxed parameters for real-world trading"""

    def __init__(self, config: dict = None):
        if config is None:
            config = {
                'name': 'LSCB Relaxed',

                # Swing detection - more lenient
                'swing_lookback': 30,  # Reduced from 50
                'swing_tolerance_pct': 0.2,  # Increased from 0.05%
                'min_touches': 2,  # Reduced from 3

                # Sweep candle - more lenient
                'min_wick_pct': 35,  # Reduced from 50%
                'min_volume_multiple': 1.3,  # Reduced from 2.0x
                'min_sweep_size_pct': 0.15,  # Reduced from 0.5%

                # Compression - more lenient
                'compression_candles': 2,
                'compression_atr_ratio': 0.8,  # Increased from 0.6

                # RSI - more lenient
                'rsi_oversold': 35,  # Relaxed from 30
                'rsi_overbought': 65,  # Relaxed from 70
                'rsi_min_move': 3,  # Reduced from 5

                # Take profit levels
                'tp1_r': 1.5,  # Reduced from 2.0
                'tp2_r': 3.0,  # Reduced from 3.5
                'tp_partial_size': 0.33,

                # Trailing stop
                'trailing_atr_multiple': 1.5,

                # Position sizing
                'risk_pct': 1.0,
            }

        super().__init__(config)

        self.swing_lookback = config['swing_lookback']
        self.swing_tolerance_pct = config['swing_tolerance_pct']
        self.min_touches = config['min_touches']

        self.min_wick_pct = config['min_wick_pct']
        self.min_volume_multiple = config['min_volume_multiple']
        self.min_sweep_size_pct = config['min_sweep_size_pct']

        self.compression_candles = config['compression_candles']
        self.compression_atr_ratio = config['compression_atr_ratio']

        self.rsi_oversold = config['rsi_oversold']
        self.rsi_overbought = config['rsi_overbought']
        self.rsi_min_move = config['rsi_min_move']

        self.tp1_r = config['tp1_r']
        self.tp2_r = config['tp2_r']
        self.tp_partial_size = config['tp_partial_size']

        self.trailing_atr_multiple = config['trailing_atr_multiple']
        self.risk_pct = config['risk_pct']

    def initialize(self, context: StrategyContext) -> pd.DataFrame:
        """Calculate all indicators"""

        df = context.data.copy()

        # EMAs
        df['ema_20'] = Indicators.ema(df['close'], 20)
        df['ema_50'] = Indicators.ema(df['close'], 50)
        df['ema_50_slope'] = df['ema_50'].diff(3)

        # ATR
        df['atr'] = Indicators.atr(df['high'], df['low'], df['close'], 14)

        # RSI
        df['rsi'] = Indicators.rsi(df['close'], 14)

        # Volume MA
        df['volume_ma20'] = Indicators.volume_ma(df['volume'], 20)

        # Candle characteristics
        df['candle_range'] = df['high'] - df['low']
        df['upper_wick'] = df['high'] - df[['open', 'close']].max(axis=1)
        df['lower_wick'] = df[['open', 'close']].min(axis=1) - df['low']

        return df

    def on_bar(self, bar: pd.Series, bar_index: int, state: StrategyState, context: StrategyContext) -> List[Order]:
        """Check for entry"""

        if bar_index < self.swing_lookback + 20 or state.position_size != 0:
            return []

        data = context.data.iloc[:bar_index+1]

        # Simplified LSCB logic:
        # Look for rejection wicks at EMA20 during trending conditions

        # LONG setup: Price rejects off EMA20 in uptrend
        if self._check_simple_long(data, bar_index):
            return self._create_long_entry(bar, bar_index, state, context, data)

        # SHORT setup: Price rejects off EMA20 in downtrend
        if self._check_simple_short(data, bar_index):
            return self._create_short_entry(bar, bar_index, state, context, data)

        return []

    def on_exit(self, bar: pd.Series, bar_index: int, state: StrategyState, context: StrategyContext) -> List[Order]:
        """Manage exits"""

        if state.position_size == 0 or not state.entry_price or not state.stop_loss:
            return []

        orders = []
        current_price = bar['close']
        risk = abs(state.entry_price - state.stop_loss)
        data = context.data.iloc[:bar_index+1]
        atr = data['atr'].iloc[bar_index]

        tp1_hit = state.custom_data.get('tp1_hit', False)
        tp2_hit = state.custom_data.get('tp2_hit', False)
        position_side = 'long' if state.position_size > 0 else 'short'

        if position_side == 'long':
            pnl_r = (current_price - state.entry_price) / risk if risk > 0 else 0

            if not tp1_hit and pnl_r >= self.tp1_r:
                partial_size = abs(state.position_size) * self.tp_partial_size
                orders.append(Order(
                    order_id=f'tp1_{bar_index}',
                    symbol=context.symbol,
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=partial_size,
                    reduce_only=True,
                    tags={'exit_reason': f'TP1_{self.tp1_r}R', 'partial': True}
                ))
                state.custom_data['tp1_hit'] = True

            if not tp2_hit and pnl_r >= self.tp2_r:
                partial_size = abs(state.position_size) * self.tp_partial_size
                orders.append(Order(
                    order_id=f'tp2_{bar_index}',
                    symbol=context.symbol,
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=partial_size,
                    reduce_only=True,
                    tags={'exit_reason': f'TP2_{self.tp2_r}R', 'partial': True}
                ))
                state.custom_data['tp2_hit'] = True

            if tp2_hit:
                trailing_stop = current_price - (atr * self.trailing_atr_multiple)
                if trailing_stop > state.stop_loss:
                    state.stop_loss = trailing_stop

            if current_price <= state.stop_loss:
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

            if not tp1_hit and pnl_r >= self.tp1_r:
                partial_size = abs(state.position_size) * self.tp_partial_size
                orders.append(Order(
                    order_id=f'tp1_{bar_index}',
                    symbol=context.symbol,
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    quantity=partial_size,
                    reduce_only=True,
                    tags={'exit_reason': f'TP1_{self.tp1_r}R', 'partial': True}
                ))
                state.custom_data['tp1_hit'] = True

            if not tp2_hit and pnl_r >= self.tp2_r:
                partial_size = abs(state.position_size) * self.tp_partial_size
                orders.append(Order(
                    order_id=f'tp2_{bar_index}',
                    symbol=context.symbol,
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    quantity=partial_size,
                    reduce_only=True,
                    tags={'exit_reason': f'TP2_{self.tp2_r}R', 'partial': True}
                ))
                state.custom_data['tp2_hit'] = True

            if tp2_hit:
                trailing_stop = current_price + (atr * self.trailing_atr_multiple)
                if trailing_stop < state.stop_loss:
                    state.stop_loss = trailing_stop

            if current_price >= state.stop_loss:
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

    def _check_simple_long(self, data, idx):
        """Simplified LONG: Strong wick rejection at EMA20 in uptrend"""

        candle = data.iloc[idx]

        # 1. Uptrend: EMA20 > EMA50 and rising
        if candle['ema_20'] <= candle['ema_50']:
            return False
        if data['ema_50_slope'].iloc[idx] <= 0:
            return False

        # 2. Price dips to/below EMA20
        if candle['low'] > candle['ema_20']:
            return False

        # 3. Strong rejection wick
        wick_pct = (candle['lower_wick'] / candle['candle_range']) * 100 if candle['candle_range'] > 0 else 0
        if wick_pct < self.min_wick_pct:
            return False

        # 4. Closes above EMA20
        if candle['close'] <= candle['ema_20']:
            return False

        # 5. Volume confirmation
        vol_ratio = candle['volume'] / candle['volume_ma20'] if candle['volume_ma20'] > 0 else 0
        if vol_ratio < self.min_volume_multiple:
            return False

        # 6. RSI not overbought
        if candle['rsi'] > self.rsi_overbought:
            return False

        return True

    def _check_simple_short(self, data, idx):
        """Simplified SHORT: Strong wick rejection at EMA20 in downtrend"""

        candle = data.iloc[idx]

        # 1. Downtrend: EMA20 < EMA50 and falling
        if candle['ema_20'] >= candle['ema_50']:
            return False
        if data['ema_50_slope'].iloc[idx] >= 0:
            return False

        # 2. Price pumps to/above EMA20
        if candle['high'] < candle['ema_20']:
            return False

        # 3. Strong rejection wick
        wick_pct = (candle['upper_wick'] / candle['candle_range']) * 100 if candle['candle_range'] > 0 else 0
        if wick_pct < self.min_wick_pct:
            return False

        # 4. Closes below EMA20
        if candle['close'] >= candle['ema_20']:
            return False

        # 5. Volume confirmation
        vol_ratio = candle['volume'] / candle['volume_ma20'] if candle['volume_ma20'] > 0 else 0
        if vol_ratio < self.min_volume_multiple:
            return False

        # 6. RSI not oversold
        if candle['rsi'] < self.rsi_oversold:
            return False

        return True

    def _create_long_entry(self, bar, bar_index, state, context, data):
        """Create LONG entry"""

        entry_price = bar['close']
        atr = data['atr'].iloc[bar_index]
        ema20 = data['ema_20'].iloc[bar_index]

        # Stop below recent low
        stop_loss = min(bar['low'], ema20) - (atr * 0.3)

        risk = entry_price - stop_loss
        if risk <= 0:
            return []

        account_risk = context.account_equity * (self.risk_pct / 100)
        position_size = account_risk / risk

        state.stop_loss = stop_loss
        state.custom_data['tp1_hit'] = False
        state.custom_data['tp2_hit'] = False

        return [Order(
            order_id=f'long_{bar_index}',
            symbol=context.symbol,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=position_size,
            tags={'setup': 'EMA_REJECTION_LONG', 'stop_loss': stop_loss}
        )]

    def _create_short_entry(self, bar, bar_index, state, context, data):
        """Create SHORT entry"""

        entry_price = bar['close']
        atr = data['atr'].iloc[bar_index]
        ema20 = data['ema_20'].iloc[bar_index]

        # Stop above recent high
        stop_loss = max(bar['high'], ema20) + (atr * 0.3)

        risk = stop_loss - entry_price
        if risk <= 0:
            return []

        account_risk = context.account_equity * (self.risk_pct / 100)
        position_size = account_risk / risk

        state.stop_loss = stop_loss
        state.custom_data['tp1_hit'] = False
        state.custom_data['tp2_hit'] = False

        return [Order(
            order_id=f'short_{bar_index}',
            symbol=context.symbol,
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=position_size,
            tags={'setup': 'EMA_REJECTION_SHORT', 'stop_loss': stop_loss}
        )]
