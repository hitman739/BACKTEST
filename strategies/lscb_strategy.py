"""
LSCB Strategy (Liquidity Sweep Compression Breakout)

Complete implementation of LSCB pattern:
1. Swing high/low detection (3-touch, 50 candles lookback)
2. Liquidity sweep candle (wick ≥50%, volume ≥2x MA20)
3. Rejection candle (closes back inside previous range)
4. Compression (2 candles, range <0.6 ATR, volume decreasing)
5. RSI moving toward 50 from extremes
6. Confirmation candle (breaks sweep high/low with volume)
7. Entry on close
8. Stop beyond sweep wick
9. Partial TPs: 33% @ 2R, 33% @ 3.5R, 33% ATR trailing

Author: Reverse-engineered from market structure
"""

import pandas as pd
import numpy as np
from typing import List, Optional
from engine.strategy import BaseStrategy, StrategyContext, StrategyState
from engine.orders import Order, OrderType, OrderSide
from engine.indicators import Indicators


class LSCBStrategy(BaseStrategy):
    """
    Liquidity Sweep Compression Breakout Strategy

    Trades liquidity sweeps followed by compression and breakout.
    """

    def __init__(self, config: dict = None):
        if config is None:
            config = {
                'name': 'LSCB Strategy',

                # Swing detection
                'swing_lookback': 50,
                'swing_tolerance_pct': 0.05,  # 0.05% tolerance
                'min_touches': 3,

                # Sweep candle criteria
                'min_wick_pct': 50,  # Minimum wick percentage
                'min_volume_multiple': 2.0,  # Volume must be 2x MA20
                'min_sweep_size_pct': 0.5,  # Sweep must be at least 0.5%

                # Compression criteria
                'compression_candles': 2,
                'compression_atr_ratio': 0.6,

                # RSI criteria
                'rsi_oversold': 30,
                'rsi_overbought': 70,
                'rsi_min_move': 5,

                # Take profit levels
                'tp1_r': 2.0,
                'tp2_r': 3.5,
                'tp_partial_size': 0.33,

                # Trailing stop
                'trailing_atr_multiple': 1.5,

                # Position sizing
                'risk_pct': 1.0,  # Risk 1% per trade
            }

        super().__init__(config)

        # Store parameters
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

        # EMAs for trend filter
        df['ema_50'] = Indicators.ema(df['close'], 50)
        df['ema_50_slope'] = df['ema_50'].diff(5)  # 5-candle slope

        # ATR for stops and compression detection
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

    def on_bar(
        self,
        bar: pd.Series,
        bar_index: int,
        state: StrategyState,
        context: StrategyContext
    ) -> List[Order]:
        """Check for LSCB setup on each bar"""

        # Need enough history
        if bar_index < self.swing_lookback + 20:
            return []

        # Only trade if flat
        if state.position_size != 0:
            return []

        data = context.data.iloc[:bar_index+1]

        # Check for LONG setup
        long_setup = self._check_long_setup(data, bar_index)
        if long_setup:
            return self._create_long_entry(bar, bar_index, state, context, data)

        # Check for SHORT setup
        short_setup = self._check_short_setup(data, bar_index)
        if short_setup:
            return self._create_short_entry(bar, bar_index, state, context, data)

        return []

    def on_exit(
        self,
        bar: pd.Series,
        bar_index: int,
        state: StrategyState,
        context: StrategyContext
    ) -> List[Order]:
        """Manage position with partial TPs and trailing stop"""

        if state.position_size == 0:
            return []

        if not state.entry_price or not state.stop_loss:
            return []

        orders = []
        current_price = bar['close']
        risk = abs(state.entry_price - state.stop_loss)

        data = context.data.iloc[:bar_index+1]
        atr = data['atr'].iloc[bar_index]

        position_side = 'long' if state.position_size > 0 else 'short'

        # Get TP hit flags from custom_data
        tp1_hit = state.custom_data.get('tp1_hit', False)
        tp2_hit = state.custom_data.get('tp2_hit', False)

        if position_side == 'long':
            pnl_r = (current_price - state.entry_price) / risk if risk > 0 else 0

            # TP1: 2R
            if not tp1_hit and pnl_r >= self.tp1_r:
                partial_size = abs(state.position_size) * self.tp_partial_size
                orders.append(Order(
                    order_id=f'tp1_{bar_index}',
                    symbol=context.symbol,
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=partial_size,
                    reduce_only=True,
                    tags={'exit_reason': 'TP1_2R', 'partial': True}
                ))
                state.custom_data['tp1_hit'] = True

            # TP2: 3.5R
            if not tp2_hit and pnl_r >= self.tp2_r:
                partial_size = abs(state.position_size) * self.tp_partial_size
                orders.append(Order(
                    order_id=f'tp2_{bar_index}',
                    symbol=context.symbol,
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=partial_size,
                    reduce_only=True,
                    tags={'exit_reason': 'TP2_3.5R', 'partial': True}
                ))
                state.custom_data['tp2_hit'] = True

            # Trailing stop after TP2
            if tp2_hit:
                trailing_stop = current_price - (atr * self.trailing_atr_multiple)
                if trailing_stop > state.stop_loss:
                    state.stop_loss = trailing_stop

            # Check stop loss
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

            # TP1: 2R
            if not tp1_hit and pnl_r >= self.tp1_r:
                partial_size = abs(state.position_size) * self.tp_partial_size
                orders.append(Order(
                    order_id=f'tp1_{bar_index}',
                    symbol=context.symbol,
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    quantity=partial_size,
                    reduce_only=True,
                    tags={'exit_reason': 'TP1_2R', 'partial': True}
                ))
                state.custom_data['tp1_hit'] = True

            # TP2: 3.5R
            if not tp2_hit and pnl_r >= self.tp2_r:
                partial_size = abs(state.position_size) * self.tp_partial_size
                orders.append(Order(
                    order_id=f'tp2_{bar_index}',
                    symbol=context.symbol,
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    quantity=partial_size,
                    reduce_only=True,
                    tags={'exit_reason': 'TP2_3.5R', 'partial': True}
                ))
                state.custom_data['tp2_hit'] = True

            # Trailing stop after TP2
            if tp2_hit:
                trailing_stop = current_price + (atr * self.trailing_atr_multiple)
                if trailing_stop < state.stop_loss:
                    state.stop_loss = trailing_stop

            # Check stop loss
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

    def _check_long_setup(self, data, index):
        """Check if LONG LSCB setup is valid"""

        # 1. Trend filter: EMA50 must be rising
        if data['ema_50_slope'].iloc[index] <= 0:
            return False

        # 2. Find swing low
        swing_low = self._find_swing_low(data, index)
        if swing_low is None:
            return False

        # 3. Find sweep candle
        sweep_idx = self._find_sweep_candle(data, index, swing_low, 'long')
        if sweep_idx is None:
            return False

        # 4. Check rejection
        if not self._check_rejection(data, sweep_idx, 'long'):
            return False

        # 5. Check compression
        if not self._check_compression(data, sweep_idx):
            return False

        # 6. Check RSI
        if not self._check_rsi_long(data, index):
            return False

        # 7. Check confirmation
        if not self._check_confirmation_long(data, index, sweep_idx):
            return False

        return True

    def _check_short_setup(self, data, index):
        """Check if SHORT LSCB setup is valid"""

        # 1. Trend filter: EMA50 must be falling
        if data['ema_50_slope'].iloc[index] >= 0:
            return False

        # 2. Find swing high
        swing_high = self._find_swing_high(data, index)
        if swing_high is None:
            return False

        # 3. Find sweep candle
        sweep_idx = self._find_sweep_candle(data, index, swing_high, 'short')
        if sweep_idx is None:
            return False

        # 4. Check rejection
        if not self._check_rejection(data, sweep_idx, 'short'):
            return False

        # 5. Check compression
        if not self._check_compression(data, sweep_idx):
            return False

        # 6. Check RSI
        if not self._check_rsi_short(data, index):
            return False

        # 7. Check confirmation
        if not self._check_confirmation_short(data, index, sweep_idx):
            return False

        return True

    def _find_swing_low(self, data, current_idx):
        """Find swing low with 3-touch rule"""

        lookback_data = data.iloc[max(0, current_idx - self.swing_lookback):current_idx]

        if len(lookback_data) < 10:
            return None

        lows = lookback_data['low'].values
        min_low = lows.min()
        tolerance = min_low * (self.swing_tolerance_pct / 100)

        touches = sum(1 for low in lows if abs(low - min_low) <= tolerance)

        if touches >= self.min_touches:
            return min_low

        return None

    def _find_swing_high(self, data, current_idx):
        """Find swing high with 3-touch rule"""

        lookback_data = data.iloc[max(0, current_idx - self.swing_lookback):current_idx]

        if len(lookback_data) < 10:
            return None

        highs = lookback_data['high'].values
        max_high = highs.max()
        tolerance = max_high * (self.swing_tolerance_pct / 100)

        touches = sum(1 for high in highs if abs(high - max_high) <= tolerance)

        if touches >= self.min_touches:
            return max_high

        return None

    def _find_sweep_candle(self, data, current_idx, swing_level, direction):
        """Find sweep candle in last few candles"""

        for i in range(max(0, current_idx - 5), current_idx):
            candle = data.iloc[i]

            if direction == 'long':
                if candle['low'] < swing_level:
                    sweep_size = swing_level - candle['low']

                    if (sweep_size / candle['close']) * 100 < self.min_sweep_size_pct:
                        continue

                    if candle['lower_wick'] / candle['candle_range'] * 100 < self.min_wick_pct:
                        continue

                    if candle['volume'] < candle['volume_ma20'] * self.min_volume_multiple:
                        continue

                    return i

            else:  # short
                if candle['high'] > swing_level:
                    sweep_size = candle['high'] - swing_level

                    if (sweep_size / candle['close']) * 100 < self.min_sweep_size_pct:
                        continue

                    if candle['upper_wick'] / candle['candle_range'] * 100 < self.min_wick_pct:
                        continue

                    if candle['volume'] < candle['volume_ma20'] * self.min_volume_multiple:
                        continue

                    return i

        return None

    def _check_rejection(self, data, sweep_idx, direction):
        """Check if next candle closes back inside previous range"""

        if sweep_idx + 1 >= len(data):
            return False

        if sweep_idx == 0:
            return False

        prev_candle = data.iloc[sweep_idx - 1]
        rejection_candle = data.iloc[sweep_idx + 1]

        prev_high = prev_candle['high']
        prev_low = prev_candle['low']
        rejection_close = rejection_candle['close']

        return prev_low <= rejection_close <= prev_high

    def _check_compression(self, data, sweep_idx):
        """Check for 2 compression candles after sweep"""

        compression_start = sweep_idx + 2

        if compression_start + self.compression_candles > len(data):
            return False

        compression_candles = data.iloc[compression_start:compression_start + self.compression_candles]

        for i in range(len(compression_candles) - 1):
            current = compression_candles.iloc[i]
            next_candle = compression_candles.iloc[i + 1]

            if current['candle_range'] >= current['atr'] * self.compression_atr_ratio:
                return False

            if next_candle['volume'] >= current['volume']:
                return False

        return True

    def _check_rsi_long(self, data, index):
        """Check RSI moving from oversold toward 50"""

        current_rsi = data['rsi'].iloc[index]
        recent_rsi = data['rsi'].iloc[max(0, index - 10):index + 1]
        min_rsi = recent_rsi.min()

        if min_rsi > self.rsi_oversold:
            return False

        if current_rsi - min_rsi < self.rsi_min_move:
            return False

        return True

    def _check_rsi_short(self, data, index):
        """Check RSI moving from overbought toward 50"""

        current_rsi = data['rsi'].iloc[index]
        recent_rsi = data['rsi'].iloc[max(0, index - 10):index + 1]
        max_rsi = recent_rsi.max()

        if max_rsi < self.rsi_overbought:
            return False

        if max_rsi - current_rsi < self.rsi_min_move:
            return False

        return True

    def _check_confirmation_long(self, data, current_idx, sweep_idx):
        """Check confirmation candle breaks sweep high with volume"""

        current = data.iloc[current_idx]
        sweep = data.iloc[sweep_idx]

        if current['high'] <= sweep['high']:
            return False

        if current['volume'] <= data['volume'].iloc[current_idx - 1]:
            return False

        return True

    def _check_confirmation_short(self, data, current_idx, sweep_idx):
        """Check confirmation candle breaks sweep low with volume"""

        current = data.iloc[current_idx]
        sweep = data.iloc[sweep_idx]

        if current['low'] >= sweep['low']:
            return False

        if current['volume'] <= data['volume'].iloc[current_idx - 1]:
            return False

        return True

    def _create_long_entry(self, bar, bar_index, state, context, data):
        """Create LONG entry order"""

        # Find sweep candle to set stop
        sweep_idx = None
        for i in range(max(0, bar_index - 10), bar_index):
            if data['low'].iloc[i] < data['low'].iloc[bar_index]:
                sweep_idx = i
                break

        if sweep_idx is None:
            return []

        sweep_low = data['low'].iloc[sweep_idx]
        entry_price = bar['close']
        atr = data['atr'].iloc[bar_index]
        stop_loss = sweep_low - (atr * 0.2)

        risk = entry_price - stop_loss
        if risk <= 0:
            return []

        # Position sizing
        account_risk = context.account_equity * (self.risk_pct / 100)
        position_size = account_risk / risk

        # Store state
        state.stop_loss = stop_loss
        state.custom_data['tp1_hit'] = False
        state.custom_data['tp2_hit'] = False

        return [Order(
            order_id=f'long_{bar_index}',
            symbol=context.symbol,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=position_size,
            tags={'setup': 'LSCB_LONG', 'stop_loss': stop_loss}
        )]

    def _create_short_entry(self, bar, bar_index, state, context, data):
        """Create SHORT entry order"""

        # Find sweep candle to set stop
        sweep_idx = None
        for i in range(max(0, bar_index - 10), bar_index):
            if data['high'].iloc[i] > data['high'].iloc[bar_index]:
                sweep_idx = i
                break

        if sweep_idx is None:
            return []

        sweep_high = data['high'].iloc[sweep_idx]
        entry_price = bar['close']
        atr = data['atr'].iloc[bar_index]
        stop_loss = sweep_high + (atr * 0.2)

        risk = stop_loss - entry_price
        if risk <= 0:
            return []

        # Position sizing
        account_risk = context.account_equity * (self.risk_pct / 100)
        position_size = account_risk / risk

        # Store state
        state.stop_loss = stop_loss
        state.custom_data['tp1_hit'] = False
        state.custom_data['tp2_hit'] = False

        return [Order(
            order_id=f'short_{bar_index}',
            symbol=context.symbol,
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=position_size,
            tags={'setup': 'LSCB_SHORT', 'stop_loss': stop_loss}
        )]
