"""
VRR Ultra v2 - Improved 1m Strategy

Improvements over v1:
✅ Wider stops (1.2× setup range) - reduce stop outs from 34.2%
✅ Closer TPs: TP1 1.3R, TP2 2.0R (before 1.5R/2.5R) - more achievable
✅ Earlier trailing: activate at 1.0R (before 1.2R) - protect profits sooner
✅ More patience: timeout 10 bars (before 8)
✅ Better R/R: target Avg Win > Avg Loss

Target metrics:
- Win Rate: >55%
- Profit Factor: >1.0
- Stop Losses: <25% (was 34.2%)
- TPs achieved: >30% (was 21.1%)
"""

from strategies.vrr_strategy import VRRStrategy
from typing import List
import pandas as pd


class VRRUltraV2(VRRStrategy):
    """VRR Ultra v2 - Optimized for 1m with real data"""

    def __init__(self, config: dict = None):
        # Base config
        base_config = {
            'name': 'VRR Ultra v2 - Improved 1m',

            # Core parameters
            'atr_period': 14,
            'atr_period_long': 50,
            'rsi_period': 14,
            'volume_ma_period': 20,
            'volume_ma_short': 10,

            # Entry thresholds - Adjusted
            'directional_move_atr_mult': 1.5,
            'lookback_candles': 5,
            'rsi_overbought': 70,
            'rsi_oversold': 30,
            'rsi_extreme_high': 75,
            'rsi_extreme_low': 25,
            'volume_spike_mult': 1.5,
            'volume_ratio_min': 1.2,
            'wick_percentage_min': 0.30,
            'wick_percentage_extreme': 0.60,

            # Market regime filters
            'atr_volatility_mult': 1.0,
            'trend_filter_enabled': False,
            'trading_hours_start': 0,
            'trading_hours_end': 24,
            'time_filter_enabled': False,

            # Exit parameters - IMPROVED
            'tp1_r_mult': 1.3,              # CLOSER (was 1.5) - more achievable
            'tp1_percentage': 0.5,          # Take 50% profit
            'tp2_r_mult': 2.0,              # CLOSER (was 2.5) - more realistic
            'trailing_activation_r': 1.0,  # EARLIER (was 1.2) - protect sooner
            'trailing_distance_r': 0.5,    # Trail 0.5R behind
            'stop_loss_mult': 1.2,         # WIDER (new) - reduce stop outs

            # Position sizing
            'base_risk_pct': 1.0,
            'size_mult_extreme': 1.0,
            'size_mult_moderate': 0.5,
            'size_mult_confluence': 1.2,

            # Fail-safe - IMPROVED
            'max_candles_wait': 10,             # MORE PATIENCE (was 8)
            'new_impulse_cancel_mult': 2.5,    # Cancel if new 2.5×ATR move

            # DISABLE ALL AGGRESSIVE EXITS
            'vwap_exit_enabled': False,
            'volume_exhaustion_enabled': False,
            'counter_candle_enabled': False,
        }

        # Merge with user config
        if config:
            base_config.update(config)

        super().__init__(base_config)

        # Store flags
        self.vwap_exit_enabled = False
        self.volume_exhaustion_enabled = False
        self.counter_candle_enabled = False
        self.stop_loss_mult = base_config.get('stop_loss_mult', 1.2)

    def on_bar(self, bar, bar_index, state, context):
        """
        Override to implement wider stops
        """
        from engine.orders import Order

        orders = []

        # Skip if insufficient data
        if bar_index < max(self.atr_period_long, self.lookback):
            return orders

        # Only trade if no position
        if state.position_size != 0:
            return orders

        # Check all filters
        if not self._check_volatility_regime(bar):
            return orders

        if self.trend_enabled and not self._check_trend_regime(bar):
            return orders

        if self.time_enabled and not self._check_trading_hours(bar):
            return orders

        # Check for VRR setup
        recent_bars = context.data.iloc[max(0, bar_index - self.lookback):bar_index + 1]

        # 1. Directional move detection
        move_size = self._calculate_directional_move(recent_bars)
        atr_threshold = bar['atr'] * self.dir_move_mult

        if move_size < atr_threshold:
            return orders

        # Determine direction
        is_bullish_move = recent_bars['close'].iloc[-1] > recent_bars['close'].iloc[0]
        is_bearish_move = not is_bullish_move

        # 2. RSI extreme check
        current_rsi = bar['rsi']
        rsi_extreme = False
        direction = None

        if is_bearish_move and current_rsi <= self.rsi_oversold:
            rsi_extreme = True
            direction = 'long'  # Reversal to long
        elif is_bullish_move and current_rsi >= self.rsi_overbought:
            rsi_extreme = True
            direction = 'short'  # Reversal to short

        if not rsi_extreme:
            return orders

        # 3. Volume spike
        if bar['volume'] < bar['volume_ma'] * self.volume_spike:
            return orders

        # 4. Volume divergence
        recent_volume = recent_bars['volume'].iloc[-3:].mean()
        if recent_volume < bar['volume_ma'] * self.volume_ratio:
            return orders

        # 5. Reversal candle check
        reversal_check = self._check_reversal_candle(bar, direction == 'short')
        if not reversal_check['is_reversal']:
            return orders

        # === SETUP CONFIRMED - Calculate wider stop ===

        entry_price = bar['close']
        setup_candle = bar

        # IMPROVEMENT: Wider stop loss (1.2× the setup candle range)
        candle_range = setup_candle['high'] - setup_candle['low']
        stop_distance = candle_range * self.stop_loss_mult

        if direction == 'long':
            stop_loss = entry_price - stop_distance
        else:
            stop_loss = entry_price + stop_distance

        # Calculate position size
        setup_quality = self._assess_setup_quality(bar, reversal_check)
        risk_amount = state.equity * (self.base_risk / 100.0)

        size_multiplier = {
            'extreme': self.size_mult_extreme,
            'high': 1.0,
            'moderate': self.size_mult_moderate
        }.get(setup_quality, 0.5)

        position_size = (risk_amount * size_multiplier) / stop_distance

        # Create entry order
        order = Order(
            symbol=context.symbol,
            side=direction,
            order_type='market',
            size=position_size,
            timestamp=bar['timestamp']
        )
        orders.append(order)

        # Set stop loss
        state.stop_loss = stop_loss

        # Calculate R (risk) - now based on wider stop
        r_value = abs(entry_price - stop_loss)

        # Set targets with IMPROVED R multiples
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
        state.custom_data['setup_quality'] = setup_quality

        return orders

    def on_exit(self, bar, bar_index, state, context):
        """
        CLEAN exit logic - same as Ultra v1
        """
        from engine.orders import Order

        orders = []

        if state.position_size == 0:
            return orders

        is_long = state.position_size > 0
        current_price = bar['close']

        # === FAIL-SAFE 1: Timeout (now 10 bars) ===
        bars_in_trade = bar_index - state.entry_bar_index
        if bars_in_trade > self.max_wait and not state.custom_data.get('tp1_hit', False):
            return [self._create_exit_order(bar, bar_index, state, context, 'timeout')]

        # === FAIL-SAFE 2: New Impulse ===
        if self._detect_new_impulse(bar, context, bar_index):
            return [self._create_exit_order(bar, bar_index, state, context, 'new_impulse')]

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
                state.custom_data['tp1_hit'] = True

        # === TRAILING STOP (now activates at 1.0R) ===
        trail_activation = state.custom_data.get('trail_activation')
        if trail_activation and not state.custom_data.get('trailing_active', False):
            if (is_long and current_price >= trail_activation) or \
               (not is_long and current_price <= trail_activation):
                state.custom_data['trailing_active'] = True
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

        # === TP2 ===
        if state.take_profit:
            if (is_long and current_price >= state.take_profit) or \
               (not is_long and current_price <= state.take_profit):
                return [self._create_exit_order(bar, bar_index, state, context, 'take_profit_2')]

        return orders
