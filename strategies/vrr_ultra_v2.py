"""
VRR Ultra v2 - Improved 1m Strategy

Improvements over v1:
✅ Closer TPs: TP1 1.3R, TP2 2.0R (before 1.5R/2.5R) - more achievable
✅ Earlier trailing: activate at 1.0R (before 1.2R) - protect profits sooner
✅ More patience: timeout 10 bars (before 8)
✅ Better R/R: target Avg Win > Avg Loss

Target metrics:
- Win Rate: >55%
- Profit Factor: >1.0
- Stop Losses: <30% (was 34.2%)
- TPs achieved: >30% (was 21.1%)
"""

from strategies.vrr_ultra import VRRUltra


class VRRUltraV2(VRRUltra):
    """VRR Ultra v2 - Optimized for 1m with real data"""

    def __init__(self, config: dict = None):
        # Base config with IMPROVED parameters
        base_config = {
            'name': 'VRR Ultra v2 - Improved 1m',

            # Core parameters
            'atr_period': 14,
            'atr_period_long': 50,
            'rsi_period': 14,
            'volume_ma_period': 20,
            'volume_ma_short': 10,

            # Entry thresholds - Same as v1
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
            'trailing_distance_r': 0.4,    # TIGHTER (was 0.5) - lock profits

            # Position sizing
            'base_risk_pct': 1.0,
            'size_mult_extreme': 1.0,
            'size_mult_moderate': 0.5,
            'size_mult_confluence': 1.2,

            # Fail-safe - IMPROVED
            'max_candles_wait': 10,             # MORE PATIENCE (was 8)
            'new_impulse_cancel_mult': 2.5,    # Same as v1

            # DISABLE ALL AGGRESSIVE EXITS
            'vwap_exit_enabled': False,
            'volume_exhaustion_enabled': False,
            'counter_candle_enabled': False,
        }

        # Merge with user config
        if config:
            base_config.update(config)

        # Call parent (VRRUltra) constructor
        super().__init__(base_config)
