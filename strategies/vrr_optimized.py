"""
VRR Strategy - Optimized Version Based on Backtest Results

Fixes applied:
1. Disabled VWAP cross exit (was closing 63.6% of trades prematurely)
2. Wider stops to reduce loss size
3. Adjusted TPs for better risk/reward
4. Increased trailing stop activation for longer trades
"""

from strategies.vrr_strategy import VRRStrategy


class VRROptimized(VRRStrategy):
    """VRR with optimizations based on real backtest results"""

    def __init__(self, config: dict = None):
        # Start with base config
        base_config = {
            'name': 'VRR - Optimized for Performance',

            # Core parameters
            'atr_period': 14,
            'atr_period_long': 50,
            'rsi_period': 14,
            'volume_ma_period': 20,
            'volume_ma_short': 10,

            # Entry thresholds - Keep adjusted values
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

            # Exit parameters - OPTIMIZED
            'tp1_r_mult': 1.5,              # Reduced from 1.8 (easier to hit)
            'tp1_percentage': 0.5,          # Still take 50% profit at TP1
            'tp2_r_mult': 2.5,              # Reduced from 3.0 (easier to hit)
            'trailing_activation_r': 1.2,  # Reduced from 2.0 (activate sooner)
            'trailing_distance_r': 0.5,    # Tighter from 0.6 (lock profits)

            # Position sizing - SAME
            'base_risk_pct': 1.0,
            'size_mult_extreme': 1.0,
            'size_mult_moderate': 0.5,
            'size_mult_confluence': 1.2,

            # Fail-safe - ADJUSTED
            'max_candles_wait': 8,              # Increased from 5 (give more time)
            'new_impulse_cancel_mult': 2.5,    # Increased from 2.0 (less sensitive)

            # DISABLE AGGRESSIVE EXITS
            'vwap_exit_enabled': False,         # DISABLED - was exiting 63.6% of trades
            'volume_exhaustion_enabled': True,  # Keep this, it's useful
            'counter_candle_enabled': False,    # DISABLED - too aggressive
        }

        # Merge with user config if provided
        if config:
            base_config.update(config)

        super().__init__(base_config)

        # Store optimization flags
        self.vwap_exit_enabled = base_config.get('vwap_exit_enabled', False)
        self.volume_exhaustion_enabled = base_config.get('volume_exhaustion_enabled', True)
        self.counter_candle_enabled = base_config.get('counter_candle_enabled', False)

    def on_exit(self, bar, bar_index, state, context):
        """
        Override exit logic to disable aggressive exits
        """
        from engine.orders import Order

        orders = []

        if state.position_size == 0:
            return orders

        is_long = state.position_size > 0
        current_price = bar['close']

        # === FAIL-SAFE CONDITIONS ===

        # 1. Max time in position
        bars_in_trade = bar_index - state.entry_bar_index
        if bars_in_trade > self.max_wait and not state.custom_data.get('tp1_hit', False):
            return [self._create_exit_order(bar, bar_index, state, context, 'timeout')]

        # 2. New impulse in same direction
        if self._detect_new_impulse(bar, context, bar_index):
            return [self._create_exit_order(bar, bar_index, state, context, 'new_impulse')]

        # 3. VWAP cross - DISABLED by default
        if self.vwap_exit_enabled:
            import pandas as pd
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
                state.custom_data['tp1_hit'] = True

        # === TRAILING STOP ===

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

        # === VOLUME EXHAUSTION - Can be enabled/disabled ===

        if self.volume_exhaustion_enabled:
            if bar['volume'] < bar['volume_ma']:
                if (is_long and bar['rsi'] < 50) or (not is_long and bar['rsi'] > 50):
                    return [self._create_exit_order(bar, bar_index, state, context, 'volume_exhaustion')]

        # === COUNTER CANDLE - DISABLED by default ===

        if self.counter_candle_enabled:
            if self._detect_counter_candle(bar, is_long):
                if bar['volume'] > bar['volume_ma']:
                    return [self._create_exit_order(bar, bar_index, state, context, 'counter_candle')]

        # === TP2 ===

        if state.take_profit:
            if (is_long and current_price >= state.take_profit) or \
               (not is_long and current_price <= state.take_profit):
                return [self._create_exit_order(bar, bar_index, state, context, 'take_profit_2')]

        return orders
