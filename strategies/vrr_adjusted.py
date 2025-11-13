"""
VRR Strategy - Adjusted Parameters for Real Market Conditions

Same logic as VRR but with more realistic thresholds that work
in actual market conditions while maintaining the strategy's edge.
"""

from strategies.vrr_strategy import VRRStrategy


class VRRAdjusted(VRRStrategy):
    """VRR with adjusted parameters for real-world performance"""

    def __init__(self, config: dict = None):
        # Start with base config
        base_config = {
            'name': 'VRR - Adjusted Parameters',

            # Core parameters
            'atr_period': 14,
            'atr_period_long': 50,
            'rsi_period': 14,
            'volume_ma_period': 20,
            'volume_ma_short': 10,

            # Entry thresholds - ADJUSTED
            'directional_move_atr_mult': 1.5,  # Reduced from 1.8 (more signals)
            'lookback_candles': 5,
            'rsi_overbought': 70,               # Reduced from 74 (more signals)
            'rsi_oversold': 30,                 # Increased from 26 (more signals)
            'rsi_extreme_high': 75,             # Reduced from 80
            'rsi_extreme_low': 25,              # Increased from 20
            'volume_spike_mult': 1.5,           # Reduced from 4.0 (KEY FIX)
            'volume_ratio_min': 1.2,            # Reduced from 3.5 (KEY FIX)
            'wick_percentage_min': 0.30,        # Reduced from 0.40
            'wick_percentage_extreme': 0.60,    # Reduced from 0.70

            # Market regime filters - RELAXED
            'atr_volatility_mult': 1.0,         # Reduced from 1.2
            'trend_filter_enabled': False,      # Disabled for testing

            # Time filter - DISABLED for testing
            'trading_hours_start': 0,           # All hours
            'trading_hours_end': 24,
            'time_filter_enabled': False,       # Disabled

            # Exit parameters - SAME
            'tp1_r_mult': 1.8,
            'tp1_percentage': 0.5,
            'tp2_r_mult': 3.0,
            'trailing_activation_r': 2.0,
            'trailing_distance_r': 0.6,

            # Position sizing - SAME
            'base_risk_pct': 1.0,
            'size_mult_extreme': 1.0,
            'size_mult_moderate': 0.5,
            'size_mult_confluence': 1.2,

            # Fail-safe - SAME
            'max_candles_wait': 5,              # Increased from 3
            'new_impulse_cancel_mult': 2.0,
        }

        # Merge with user config if provided
        if config:
            base_config.update(config)

        super().__init__(base_config)
