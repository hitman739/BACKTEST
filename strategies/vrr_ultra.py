"""
VRR Ultra - Clean Exit Strategy

ONLY exits:
✅ Stop Loss (protección básica)
✅ Take Profit 1 (1.5R) - parcial 50%
✅ Take Profit 2 (2.5R) - resto
✅ Trailing Stop (activación 1.2R, distancia 0.5R)
✅ New Impulse (setup invalidado)
✅ Timeout (máximo 8 bars)

DISABLED aggressive exits:
❌ VWAP cross
❌ Volume exhaustion
❌ Counter candle

Let winners RUN to TP!
"""

from strategies.vrr_strategy import VRRStrategy


class VRRUltra(VRRStrategy):
    """VRR Ultra - Clean exits, let winners run"""

    def __init__(self, config: dict = None):
        # Base config
        base_config = {
            'name': 'VRR Ultra - Clean Exits',

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

            # Exit parameters - CLEAN
            'tp1_r_mult': 1.5,              # TP1 at 1.5R
            'tp1_percentage': 0.5,          # Take 50% profit
            'tp2_r_mult': 2.5,              # TP2 at 2.5R
            'trailing_activation_r': 1.2,  # Activate trailing at 1.2R
            'trailing_distance_r': 0.5,    # Trail 0.5R behind

            # Position sizing
            'base_risk_pct': 1.0,
            'size_mult_extreme': 1.0,
            'size_mult_moderate': 0.5,
            'size_mult_confluence': 1.2,

            # Fail-safe
            'max_candles_wait': 8,              # Max 8 bars
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

    def on_exit(self, bar, bar_index, state, context):
        """
        CLEAN exit logic - only TPs, Trailing, SL, and fail-safes
        """
        from engine.orders import Order

        orders = []

        if state.position_size == 0:
            return orders

        is_long = state.position_size > 0
        current_price = bar['close']

        # === FAIL-SAFE 1: Timeout ===
        bars_in_trade = bar_index - state.entry_bar_index
        if bars_in_trade > self.max_wait and not state.custom_data.get('tp1_hit', False):
            return [self._create_exit_order(bar, bar_index, state, context, 'timeout')]

        # === FAIL-SAFE 2: New Impulse (setup invalidated) ===
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
                # Mark that we hit TP1 (in real implementation would take partial profit)

        # === TRAILING STOP ===
        trail_activation = state.custom_data.get('trail_activation')
        if trail_activation and not state.custom_data.get('trailing_active', False):
            # Check if we reached trailing activation level
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
