"""
Volatility Compression Breakout (VCB) Strategy

Concept: Low volatility leads to high volatility
- Detects when ATR compresses below historical average
- Waits for breakout with volume confirmation
- Rides the momentum in breakout direction

Author: Claude (Original Strategy)
"""

from typing import List
import pandas as pd
import numpy as np
from engine.strategy import BaseStrategy, StrategyContext, StrategyState
from engine.orders import Order, OrderType, OrderSide
from engine.indicators import Indicators


class VCBStrategy(BaseStrategy):
    """Volatility Compression Breakout"""

    def __init__(self, config: dict = None):
        if config is None:
            config = {
                'name': 'Volatility Compression Breakout',

                # Compression detection
                'atr_period': 14,
                'atr_lookback': 50,  # Compare ATR to 50-period average
                'compression_ratio': 0.6,  # ATR < 60% of average = compressed

                # Breakout criteria
                'breakout_atr_mult': 1.5,  # Candle range > 1.5x ATR
                'min_volume_mult': 1.5,  # Volume > 1.5x average
                'consolidation_candles': 3,  # At least 3 compressed candles

                # Trend filter
                'ema_fast': 20,
                'ema_slow': 50,

                # Risk management
                'stop_atr_mult': 2.0,
                'tp1_r': 2.0,
                'tp2_r': 4.0,
                'tp_partial': 0.5,
                'trailing_atr': 1.5,

                'risk_pct': 1.0,
            }

        super().__init__(config)

        self.atr_period = config['atr_period']
        self.atr_lookback = config['atr_lookback']
        self.compression_ratio = config['compression_ratio']
        self.breakout_atr_mult = config['breakout_atr_mult']
        self.min_volume_mult = config['min_volume_mult']
        self.consolidation_candles = config['consolidation_candles']
        self.ema_fast = config['ema_fast']
        self.ema_slow = config['ema_slow']
        self.stop_atr_mult = config['stop_atr_mult']
        self.tp1_r = config['tp1_r']
        self.tp2_r = config['tp2_r']
        self.tp_partial = config['tp_partial']
        self.trailing_atr = config['trailing_atr']
        self.risk_pct = config['risk_pct']

    def initialize(self, context: StrategyContext) -> pd.DataFrame:
        df = context.data.copy()

        # ATR and moving average of ATR
        df['atr'] = Indicators.atr(df['high'], df['low'], df['close'], self.atr_period)
        df['atr_ma'] = df['atr'].rolling(self.atr_lookback).mean()

        # EMAs
        df['ema_fast'] = Indicators.ema(df['close'], self.ema_fast)
        df['ema_slow'] = Indicators.ema(df['close'], self.ema_slow)

        # Volume
        df['volume_ma'] = df['volume'].rolling(20).mean()

        # Candle characteristics
        df['candle_range'] = df['high'] - df['low']
        df['candle_body'] = abs(df['close'] - df['open'])

        return df

    def on_bar(self, bar: pd.Series, bar_index: int, state: StrategyState, context: StrategyContext) -> List[Order]:
        if bar_index < self.atr_lookback + 20 or state.position_size != 0:
            return []

        data = context.data.iloc[:bar_index+1]

        # Check for compression breakout LONG
        if self._check_compression_breakout_long(data, bar_index):
            return self._enter_long(bar, bar_index, state, context, data)

        # Check for compression breakout SHORT
        if self._check_compression_breakout_short(data, bar_index):
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

        tp1_hit = state.custom_data.get('tp1_hit', False)
        tp2_hit = state.custom_data.get('tp2_hit', False)
        position_side = 'long' if state.position_size > 0 else 'short'

        if position_side == 'long':
            pnl_r = (current_price - state.entry_price) / risk if risk > 0 else 0

            if not tp1_hit and pnl_r >= self.tp1_r:
                orders.append(Order(
                    order_id=f'tp1_{bar_index}',
                    symbol=context.symbol,
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=abs(state.position_size) * self.tp_partial,
                    reduce_only=True,
                    tags={'exit_reason': f'TP1_{self.tp1_r}R'}
                ))
                state.custom_data['tp1_hit'] = True

            if not tp2_hit and pnl_r >= self.tp2_r:
                orders.append(Order(
                    order_id=f'tp2_{bar_index}',
                    symbol=context.symbol,
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=abs(state.position_size) * self.tp_partial,
                    reduce_only=True,
                    tags={'exit_reason': f'TP2_{self.tp2_r}R'}
                ))
                state.custom_data['tp2_hit'] = True

            if tp1_hit:
                trailing_stop = current_price - (atr * self.trailing_atr)
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
                orders.append(Order(
                    order_id=f'tp1_{bar_index}',
                    symbol=context.symbol,
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    quantity=abs(state.position_size) * self.tp_partial,
                    reduce_only=True,
                    tags={'exit_reason': f'TP1_{self.tp1_r}R'}
                ))
                state.custom_data['tp1_hit'] = True

            if not tp2_hit and pnl_r >= self.tp2_r:
                orders.append(Order(
                    order_id=f'tp2_{bar_index}',
                    symbol=context.symbol,
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    quantity=abs(state.position_size) * self.tp_partial,
                    reduce_only=True,
                    tags={'exit_reason': f'TP2_{self.tp2_r}R'}
                ))
                state.custom_data['tp2_hit'] = True

            if tp1_hit:
                trailing_stop = current_price + (atr * self.trailing_atr)
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

    def _check_compression_breakout_long(self, data, idx):
        """Check for bullish compression breakout"""

        # 1. Must be in uptrend
        if data['ema_fast'].iloc[idx] <= data['ema_slow'].iloc[idx]:
            return False

        # 2. Check for recent compression (last N candles had low ATR)
        recent_atr = data['atr'].iloc[idx-self.consolidation_candles:idx]
        recent_atr_ma = data['atr_ma'].iloc[idx-self.consolidation_candles:idx]

        compressed_candles = sum(recent_atr < recent_atr_ma * self.compression_ratio)
        if compressed_candles < self.consolidation_candles:
            return False

        # 3. Current candle is breakout (large range)
        current_range = data['candle_range'].iloc[idx]
        current_atr = data['atr'].iloc[idx]
        if current_range < current_atr * self.breakout_atr_mult:
            return False

        # 4. Bullish candle (close > open)
        if data['close'].iloc[idx] <= data['open'].iloc[idx]:
            return False

        # 5. Volume confirmation
        vol_ratio = data['volume'].iloc[idx] / data['volume_ma'].iloc[idx]
        if vol_ratio < self.min_volume_mult:
            return False

        # 6. Breaking above recent high
        recent_high = data['high'].iloc[idx-self.consolidation_candles:idx].max()
        if data['close'].iloc[idx] <= recent_high:
            return False

        return True

    def _check_compression_breakout_short(self, data, idx):
        """Check for bearish compression breakout"""

        # 1. Must be in downtrend
        if data['ema_fast'].iloc[idx] >= data['ema_slow'].iloc[idx]:
            return False

        # 2. Check for recent compression
        recent_atr = data['atr'].iloc[idx-self.consolidation_candles:idx]
        recent_atr_ma = data['atr_ma'].iloc[idx-self.consolidation_candles:idx]

        compressed_candles = sum(recent_atr < recent_atr_ma * self.compression_ratio)
        if compressed_candles < self.consolidation_candles:
            return False

        # 3. Current candle is breakout
        current_range = data['candle_range'].iloc[idx]
        current_atr = data['atr'].iloc[idx]
        if current_range < current_atr * self.breakout_atr_mult:
            return False

        # 4. Bearish candle
        if data['close'].iloc[idx] >= data['open'].iloc[idx]:
            return False

        # 5. Volume confirmation
        vol_ratio = data['volume'].iloc[idx] / data['volume_ma'].iloc[idx]
        if vol_ratio < self.min_volume_mult:
            return False

        # 6. Breaking below recent low
        recent_low = data['low'].iloc[idx-self.consolidation_candles:idx].min()
        if data['close'].iloc[idx] >= recent_low:
            return False

        return True

    def _enter_long(self, bar, bar_index, state, context, data):
        entry_price = bar['close']
        atr = data['atr'].iloc[bar_index]
        stop_loss = entry_price - (atr * self.stop_atr_mult)

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
            tags={'setup': 'VCB_LONG', 'stop_loss': stop_loss}
        )]

    def _enter_short(self, bar, bar_index, state, context, data):
        entry_price = bar['close']
        atr = data['atr'].iloc[bar_index]
        stop_loss = entry_price + (atr * self.stop_atr_mult)

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
            tags={'setup': 'VCB_SHORT', 'stop_loss': stop_loss}
        )]
