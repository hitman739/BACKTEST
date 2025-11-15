"""
Simple Mean Revert - Minimal version for testing

Simplified version with:
- Shorter lookbacks to avoid NaN issues
- Relaxed regime filters
- Clear debugging
"""

from engine.mean_reversion import MeanReversionEngine, MeanReversionState


class SimpleMeanRevertStrategy(MeanReversionEngine):
    """
    Simplified mean reversion for testing

    Configuration:
    - Mean: MIDRANGE (60 candles = 1h on 1m)
    - Entry: -2%, -4% (long) / +2%, +4% (short)
    - Max 2 layers
    - Relaxed filters
    """

    def __init__(self):
        config = {
            'name': 'Simple Mean Revert',

            # Mean calculation - SHORTER lookback
            'mean_type': 'midrange',
            'mean_lookback': 60,  # Only 60 candles = 1 hour

            # Entry thresholds
            'long_thresholds': [-2.0, -4.0],
            'short_thresholds': [2.0, 4.0],
            'max_layers_long': 2,
            'max_layers_short': 2,
            'min_time_between_layers': 10,

            # Position sizing
            'total_risk_cap_long': 1.0,
            'total_risk_cap_short': 1.0,
            'layer_multipliers': [0.5, 0.5],

            # Exit conditions
            'mean_reentry_band': 0.8,
            'target_pnl_pct': 1.5,
            'max_hold_bars': None,
            'hard_stop_distance': 8.0,

            # RELAXED regime filters
            'min_atr_ratio': 0.5,  # Very permissive
            'max_atr_ratio': 5.0,  # Very permissive
            'min_vol_ratio': 0.5,  # Very permissive
            'max_vol_ratio': 5.0,  # Very permissive
            'min_daily_range_pct': None,  # No minimum

            # Session filters - NONE (trade 24/7)
            'trading_hours': None,

            # Risk controls
            'max_account_dd': 20.0,
            'max_daily_loss': 10.0,
            'one_side_only': True,
            'cooldown_hours': 2,
        }
        super().__init__(config)


def get_strategy_config():
    """Factory function for backtest integration"""
    return {
        'name': 'Simple Mean Revert',
        'class': SimpleMeanRevertStrategy,
        'description': 'Simplified mean reversion for testing',
        'recommended_pairs': ['BTCUSDT', 'ETHUSDT'],
        'recommended_timeframes': ['1m', '5m'],
    }
