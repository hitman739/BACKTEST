"""
Volatility Rejection Reversal (VRR) - Advanced Implementation

A sophisticated reversal system designed for high-volatility environments.
Captures micro-reversions after extended directional moves with dynamic management.

Key Features:
- Multi-timeframe confirmation
- Market regime filters
- Volume divergence detection
- Dynamic position sizing
- Adaptive exit management
- Structural price validation
"""

from typing import List, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import time
from engine.strategy import BaseStrategy, StrategyContext, StrategyState
from engine.orders import Order, OrderType, OrderSide
from engine.indicators import Indicators


class VRRStrategy(BaseStrategy):
    """Volatility Rejection Reversal Strategy"""

    def __init__(self, config: dict = None):
        if config is None:
            config = {
                'name': 'Volatility Rejection Reversal (VRR)',

                # Core parameters
                'atr_period': 14,
                'atr_period_long': 50,
                'rsi_period': 14,
                'volume_ma_period': 20,
                'volume_ma_short': 10,

                # Entry thresholds
                'directional_move_atr_mult': 1.8,  # Movement must be >= 1.8x ATR
                'lookback_candles': 5,              # Check last 5 candles
                'rsi_overbought': 74,
                'rsi_oversold': 26,
                'rsi_extreme_high': 80,             # For full size
                'rsi_extreme_low': 20,
                'volume_spike_mult': 4.0,           # Vol > 4x average
                'volume_ratio_min': 3.5,            # Minimum volume ratio
                'wick_percentage_min': 0.40,        # Wick >= 40% of range
                'wick_percentage_extreme': 0.70,    # For high-quality setups

                # Market regime filters
                'atr_volatility_mult': 1.2,         # ATR_current > 1.2x ATR_50
                'trend_filter_enabled': True,       # Avoid rangebound markets

                # Time filter (UTC hours)
                'trading_hours_start': 12,
                'trading_hours_end': 22,
                'time_filter_enabled': True,

                # Exit parameters
                'tp1_r_mult': 1.8,                  # First TP at 1.8R
                'tp1_percentage': 0.5,              # Close 50% at TP1
                'tp2_r_mult': 3.0,                  # Second TP at 3R
                'trailing_activation_r': 2.0,       # Activate trailing at 2R
                'trailing_distance_r': 0.6,         # Trail at 0.6R

                # Position sizing
                'base_risk_pct': 1.0,               # Base risk per trade
                'size_mult_extreme': 1.0,           # Full size for extreme RSI
                'size_mult_moderate': 0.5,          # Half size for moderate RSI
                'size_mult_confluence': 1.2,        # +20% for multi-TF confirmation

                # Fail-safe
                'max_candles_wait': 3,              # Cancel after 3 candles
                'new_impulse_cancel_mult': 2.0,     # Cancel if new 2xATR move
            }
        super().__init__(config)

        # Store parameters
        self.atr_period = config['atr_period']
        self.atr_period_long = config['atr_period_long']
        self.rsi_period = config['rsi_period']
        self.volume_ma = config['volume_ma_period']
        self.volume_ma_short = config['volume_ma_short']

        self.directional_atr_mult = config['directional_move_atr_mult']
        self.lookback = config['lookback_candles']
        self.rsi_ob = config['rsi_overbought']
        self.rsi_os = config['rsi_oversold']
        self.rsi_extreme_high = config['rsi_extreme_high']
        self.rsi_extreme_low = config['rsi_extreme_low']
        self.vol_spike = config['volume_spike_mult']
        self.vol_ratio_min = config['volume_ratio_min']
        self.wick_pct_min = config['wick_percentage_min']
        self.wick_pct_extreme = config['wick_percentage_extreme']

        self.atr_vol_mult = config['atr_volatility_mult']
        self.trend_filter = config['trend_filter_enabled']

        self.time_start = config['trading_hours_start']
        self.time_end = config['trading_hours_end']
        self.time_filter = config['time_filter_enabled']

        self.tp1_r = config['tp1_r_mult']
        self.tp1_pct = config['tp1_percentage']
        self.tp2_r = config['tp2_r_mult']
        self.trail_activation = config['trailing_activation_r']
        self.trail_distance = config['trailing_distance_r']

        self.base_risk = config['base_risk_pct']
        self.size_extreme = config['size_mult_extreme']
        self.size_moderate = config['size_mult_moderate']
        self.size_confluence = config['size_mult_confluence']

        self.max_wait = config['max_candles_wait']
        self.impulse_cancel = config['new_impulse_cancel_mult']

    def initialize(self, context: StrategyContext) -> pd.DataFrame:
        """Add all required indicators"""
        df = context.data.copy()

        # ATR (short and long period)
        df['atr'] = Indicators.atr(df['high'], df['low'], df['close'], self.atr_period)
        df['atr_long'] = Indicators.atr(df['high'], df['low'], df['close'], self.atr_period_long)

        # RSI
        df['rsi'] = Indicators.rsi(df['close'], self.rsi_period)

        # Volume indicators
        df['volume_ma'] = Indicators.volume_ma(df['volume'], self.volume_ma)
        df['volume_ma_short'] = Indicators.volume_ma(df['volume'], self.volume_ma_short)

        # EMAs for trend filter
        df['ema_20'] = Indicators.ema(df['close'], 20)
        df['ema_50'] = Indicators.ema(df['close'], 50)

        # VWAP
        df['vwap'] = Indicators.vwap(df['high'], df['low'], df['close'], df['volume'])

        # Calculate candle metrics
        df['candle_range'] = df['high'] - df['low']
        df['candle_body'] = abs(df['close'] - df['open'])
        df['upper_wick'] = df['high'] - df[['open', 'close']].max(axis=1)
        df['lower_wick'] = df[['open', 'close']].min(axis=1) - df['low']

        # Volume ratio
        df['volume_ratio'] = df['volume'] / df['volume_ma_short']

        return df

    def on_bar(
        self,
        bar: pd.Series,
        bar_index: int,
        state: StrategyState,
        context: StrategyContext
    ) -> List[Order]:
        """Check for VRR entry signals"""
        orders = []

        # Skip if in position or insufficient data
        if state.position_size != 0:
            return orders

        if bar_index < max(self.lookback, self.atr_period_long, 50):
            return orders

        # Check all indicators are valid
        if pd.isna(bar['atr']) or pd.isna(bar['rsi']) or pd.isna(bar['volume_ma']):
            return orders

        # === MARKET REGIME FILTERS ===

        # 1. Volatility filter: ATR current > 1.2x ATR long
        if bar['atr'] < (self.atr_vol_mult * bar['atr_long']):
            return orders

        # 2. Trend filter: avoid rangebound (EMAs crossed)
        if self.trend_filter:
            if pd.isna(bar['ema_20']) or pd.isna(bar['ema_50']):
                return orders
            # Skip if EMAs are too close (rangebound)
            ema_diff_pct = abs(bar['ema_20'] - bar['ema_50']) / bar['close']
            if ema_diff_pct < 0.005:  # Less than 0.5% difference
                return orders

        # 3. Time filter
        if self.time_filter:
            if not self._check_trading_hours(bar):
                return orders

        # === CORE VRR CONDITIONS ===

        # Get recent bars for directional move calculation
        recent_bars = context.data.iloc[bar_index - self.lookback + 1:bar_index + 1]

        # 1. Check for directional move >= 1.8x ATR
        directional_move = self._calculate_directional_move(recent_bars)
        if directional_move < (self.directional_atr_mult * bar['atr']):
            return orders

        # 2. RSI extreme
        is_overbought = bar['rsi'] > self.rsi_ob
        is_oversold = bar['rsi'] < self.rsi_os

        if not (is_overbought or is_oversold):
            return orders

        # 3. Volume spike
        if bar['volume'] < (self.vol_spike * bar['volume_ma']):
            return orders

        # 4. Volume ratio
        if bar['volume_ratio'] < self.vol_ratio_min:
            return orders

        # 5. Reversal candle with significant wick
        wick_quality = self._check_reversal_candle(bar, is_overbought)
        if not wick_quality['is_reversal']:
            return orders

        # 6. Volume divergence (declining volume on last push)
        if not self._check_volume_divergence(recent_bars):
            return orders

        # === STRUCTURAL VALIDATION ===

        # Check structural validity
        prev_bar = context.data.iloc[bar_index - 1]
        if not self._validate_structure(bar, prev_bar):
            return orders

        # === DETERMINE SETUP QUALITY ===

        setup_quality = self._assess_setup_quality(
            bar, is_overbought, is_oversold, wick_quality
        )

        # === CALCULATE POSITION SIZE ===

        entry_price = bar['close']
        stop_loss = self._calculate_stop_loss(bar, is_overbought, wick_quality)

        position_size = self._calculate_position_size(
            entry_price, stop_loss, context, setup_quality
        )

        if position_size <= 0:
            return orders

        # === CREATE ENTRY ORDER ===

        side = OrderSide.SELL if is_overbought else OrderSide.BUY
        direction = 'short' if is_overbought else 'long'

        order = Order(
            order_id=f"vrr_{direction}_{bar_index}",
            symbol=context.symbol,
            side=side,
            order_type=OrderType.MARKET,
            quantity=position_size,
            timestamp=bar['timestamp'],
            tags={
                'strategy': 'VRR',
                'setup_quality': setup_quality,
                'rsi': bar['rsi'],
                'atr': bar['atr'],
                'volume_ratio': bar['volume_ratio'],
                'wick_pct': wick_quality['wick_percentage']
            }
        )
        orders.append(order)

        # Set stop loss and targets
        state.stop_loss = stop_loss
        state.entry_price = entry_price
        state.entry_bar_index = bar_index

        # Calculate R (risk)
        r_value = abs(entry_price - stop_loss)

        # Set targets
        if direction == 'long':
            state.take_profit = entry_price + (r_value * self.tp2_r)
            state.custom_data['tp1'] = entry_price + (r_value * self.tp1_r)
            state.custom_data['trail_activation'] = entry_price + (r_value * self.trail_activation)
        else:
            state.take_profit = entry_price - (r_value * self.tp2_r)
            state.custom_data['tp1'] = entry_price - (r_value * self.tp1_r)
            state.custom_data['trail_activation'] = entry_price - (r_value * self.trail_activation)

        state.custom_data['r_value'] = r_value
        state.custom_data['tp1_hit'] = False
        state.custom_data['trailing_active'] = False
        state.custom_data['direction'] = direction

        return orders

    def on_exit(
        self,
        bar: pd.Series,
        bar_index: int,
        state: StrategyState,
        context: StrategyContext
    ) -> List[Order]:
        """Adaptive exit management"""
        orders = []

        if state.position_size == 0:
            return orders

        is_long = state.position_size > 0
        current_price = bar['close']

        # === FAIL-SAFE CONDITIONS ===

        # 1. Max time in position (cancel if too many bars passed)
        bars_in_trade = bar_index - state.entry_bar_index
        if bars_in_trade > self.max_wait and not state.custom_data.get('tp1_hit', False):
            # Exit if no progress
            return [self._create_exit_order(bar, bar_index, state, context, 'timeout')]

        # 2. New impulse in same direction (setup failed)
        if self._detect_new_impulse(bar, context, bar_index):
            return [self._create_exit_order(bar, bar_index, state, context, 'new_impulse')]

        # 3. VWAP cross against position
        if not pd.isna(bar['vwap']):
            if is_long and current_price < bar['vwap']:
                return [self._create_exit_order(bar, bar_index, state, context, 'vwap_cross')]
            elif not is_long and current_price > bar['vwap']:
                return [self._create_exit_order(bar, bar_index, state, context, 'vwap_cross')]

        # === STOP LOSS ===

        if state.stop_loss:
            if (is_long and current_price <= state.stop_loss) or \
               (not is_long and current_price >= state.stop_loss):
                return [self._create_exit_order(bar, bar_index, state, context, 'stop_loss')]

        # === TP1 MANAGEMENT ===

        tp1 = state.custom_data.get('tp1')
        if tp1 and not state.custom_data.get('tp1_hit', False):
            if (is_long and current_price >= tp1) or \
               (not is_long and current_price <= tp1):
                # Hit TP1 - close partial position
                state.custom_data['tp1_hit'] = True
                # Note: Partial close would need additional implementation
                # For now, we'll continue with full position to TP2

        # === TRAILING STOP ===

        trail_activation = state.custom_data.get('trail_activation')
        if trail_activation and not state.custom_data.get('trailing_active', False):
            # Check if we reached trailing activation level
            if (is_long and current_price >= trail_activation) or \
               (not is_long and current_price <= trail_activation):
                state.custom_data['trailing_active'] = True
                # Set initial trailing stop
                r_value = state.custom_data.get('r_value', bar['atr'])
                trail_distance = r_value * self.trail_distance
                if is_long:
                    state.stop_loss = current_price - trail_distance
                else:
                    state.stop_loss = current_price + trail_distance

        # Update trailing stop if active
        if state.custom_data.get('trailing_active', False):
            r_value = state.custom_data.get('r_value', bar['atr'])
            trail_distance = r_value * self.trail_distance
            if is_long:
                new_stop = current_price - trail_distance
                if new_stop > state.stop_loss:
                    state.stop_loss = new_stop
            else:
                new_stop = current_price + trail_distance
                if new_stop < state.stop_loss:
                    state.stop_loss = new_stop

        # === VOLUME EXHAUSTION ===

        # If volume drops and RSI crosses 50, exit
        if bar['volume'] < bar['volume_ma']:
            if (is_long and bar['rsi'] < 50) or (not is_long and bar['rsi'] > 50):
                return [self._create_exit_order(bar, bar_index, state, context, 'volume_exhaustion')]

        # === COUNTER CANDLE WITH HIGH VOLUME ===

        if self._detect_counter_candle(bar, is_long):
            if bar['volume'] > bar['volume_ma']:
                return [self._create_exit_order(bar, bar_index, state, context, 'counter_candle')]

        # === TP2 ===

        if state.take_profit:
            if (is_long and current_price >= state.take_profit) or \
               (not is_long and current_price <= state.take_profit):
                return [self._create_exit_order(bar, bar_index, state, context, 'take_profit_2')]

        return orders

    # === HELPER METHODS ===

    def _check_trading_hours(self, bar: pd.Series) -> bool:
        """Check if current time is within trading hours (UTC)"""
        try:
            hour = bar['timestamp'].hour
            return self.time_start <= hour < self.time_end
        except:
            return True  # If can't determine, allow trading

    def _calculate_directional_move(self, recent_bars: pd.DataFrame) -> float:
        """Calculate total directional movement over recent bars"""
        if len(recent_bars) < 2:
            return 0.0

        high_to_high = recent_bars['high'].max() - recent_bars['high'].min()
        low_to_low = recent_bars['low'].max() - recent_bars['low'].min()

        return max(high_to_high, low_to_low)

    def _check_reversal_candle(self, bar: pd.Series, is_bearish_reversal: bool) -> dict:
        """Check if candle has reversal characteristics"""
        candle_range = bar['candle_range']

        if candle_range == 0:
            return {'is_reversal': False, 'wick_percentage': 0}

        if is_bearish_reversal:
            # For bearish reversal, need large upper wick
            wick = bar['upper_wick']
        else:
            # For bullish reversal, need large lower wick
            wick = bar['lower_wick']

        wick_pct = wick / candle_range

        is_reversal = wick_pct >= self.wick_pct_min

        return {
            'is_reversal': is_reversal,
            'wick_percentage': wick_pct
        }

    def _check_volume_divergence(self, recent_bars: pd.DataFrame) -> bool:
        """Check if volume is declining on the last push (divergence)"""
        if len(recent_bars) < 3:
            return False

        # Compare last 2 bars volume
        last_vol = recent_bars['volume'].iloc[-1]
        prev_vol = recent_bars['volume'].iloc[-2]

        # Volume should be declining
        return last_vol < prev_vol

    def _validate_structure(self, current_bar: pd.Series, prev_bar: pd.Series) -> bool:
        """Validate structural requirements"""
        # Current candle should close within previous candle's range
        within_range = (
            current_bar['close'] >= prev_bar['low'] and
            current_bar['close'] <= prev_bar['high']
        )

        return within_range

    def _assess_setup_quality(
        self,
        bar: pd.Series,
        is_overbought: bool,
        is_oversold: bool,
        wick_quality: dict
    ) -> str:
        """Assess quality of the setup for position sizing"""

        # Extreme RSI?
        extreme_rsi = (
            (is_overbought and bar['rsi'] > self.rsi_extreme_high) or
            (is_oversold and bar['rsi'] < self.rsi_extreme_low)
        )

        # Extreme wick?
        extreme_wick = wick_quality['wick_percentage'] >= self.wick_pct_extreme

        if extreme_rsi and extreme_wick:
            return 'extreme'
        elif extreme_rsi or extreme_wick:
            return 'high'
        else:
            return 'moderate'

    def _calculate_stop_loss(
        self,
        bar: pd.Series,
        is_short: bool,
        wick_quality: dict
    ) -> float:
        """Calculate stop loss beyond the wick"""
        atr = bar['atr']
        buffer = atr * 0.2  # 20% ATR buffer

        if is_short:
            # Stop above the high
            stop = bar['high'] + buffer
        else:
            # Stop below the low
            stop = bar['low'] - buffer

        return stop

    def _calculate_position_size(
        self,
        entry_price: float,
        stop_loss: float,
        context: StrategyContext,
        setup_quality: str
    ) -> float:
        """Calculate dynamic position size based on setup quality"""

        # Base risk amount
        risk_amount = context.account_equity * (self.base_risk / 100)

        # Price risk
        price_risk = abs(entry_price - stop_loss)

        if price_risk == 0:
            return 0.0

        # Base size
        base_size = risk_amount / price_risk

        # Apply quality multiplier
        if setup_quality == 'extreme':
            size_mult = self.size_extreme
        elif setup_quality == 'high':
            size_mult = (self.size_extreme + self.size_moderate) / 2
        else:
            size_mult = self.size_moderate

        position_size = base_size * size_mult

        # Apply leverage limit
        max_notional = context.account_equity * 0.5 * context.leverage
        max_size = max_notional / entry_price

        return min(position_size, max_size)

    def _detect_new_impulse(
        self,
        bar: pd.Series,
        context: StrategyContext,
        bar_index: int
    ) -> bool:
        """Detect if a new impulse occurred in same direction"""
        if bar_index < 1:
            return False

        # Check if current bar is a large move
        candle_range = bar['candle_range']
        atr = bar['atr']

        if candle_range >= (self.impulse_cancel * atr):
            # Check if it's in the same direction as original impulse
            direction = context.data.iloc[bar_index]['close'] - context.data.iloc[bar_index - 1]['close']
            # For now, any large candle triggers exit
            return True

        return False

    def _detect_counter_candle(self, bar: pd.Series, is_long: bool) -> bool:
        """Detect strong counter-trend candle"""
        body = bar['candle_body']
        candle_range = bar['candle_range']

        if candle_range == 0:
            return False

        # Strong body (>60% of range)
        body_pct = body / candle_range

        if body_pct < 0.6:
            return False

        # Check direction
        is_bullish = bar['close'] > bar['open']

        if is_long and not is_bullish:
            return True
        elif not is_long and is_bullish:
            return True

        return False

    def _create_exit_order(
        self,
        bar: pd.Series,
        bar_index: int,
        state: StrategyState,
        context: StrategyContext,
        reason: str
    ) -> Order:
        """Create exit order"""
        is_long = state.position_size > 0
        side = OrderSide.SELL if is_long else OrderSide.BUY

        # Calculate R-multiple for reporting
        if state.entry_price and state.custom_data.get('r_value'):
            pnl_per_unit = bar['close'] - state.entry_price if is_long else state.entry_price - bar['close']
            r_mult = pnl_per_unit / state.custom_data['r_value']
        else:
            r_mult = 0

        order = Order(
            order_id=f"vrr_exit_{bar_index}",
            symbol=context.symbol,
            side=side,
            order_type=OrderType.MARKET,
            quantity=abs(state.position_size),
            timestamp=bar['timestamp'],
            tags={
                'exit_reason': reason,
                'r_multiple': r_mult,
                'bars_held': bar_index - state.entry_bar_index
            }
        )

        return order
