"""
Micro Mean Reversion - Extremely tight risk control

Key changes from other MR strategies:
- VERY tight hard stop: 0.8% (with 5x leverage = 4% account risk max)
- Small position sizes: 0.3% per layer (vs 0.4-0.5%)
- Wider thresholds: ±1.0%, ±2.0% (better entries)
- Quick exits: 0.2% from mean
- Short mean lookback: 30min (responsive)
"""

from engine.mean_reversion import MeanReversionEngine, MeanReversionState


class MicroMRStrategy(MeanReversionEngine):
    """
    Micro mean reversion with extremely tight risk control
    """

    def __init__(self):
        config = {
            'name': 'Micro MR',

            # Mean calculation
            'mean_type': 'midrange',
            'mean_lookback': 30,  # 30 min only

            # Entry thresholds - Wider for better entries
            'long_thresholds': [-1.0, -2.0],
            'short_thresholds': [1.0, 2.0],
            'max_layers_long': 2,
            'max_layers_short': 2,
            'min_time_between_layers': 5,

            # Position sizing - VERY conservative
            'total_risk_cap_long': 0.6,  # Only 0.6% of equity
            'total_risk_cap_short': 0.6,
            'layer_multipliers': [0.3, 0.3],  # Each layer 0.3%

            # Exit conditions - TIGHT
            'mean_reentry_band': 0.2,    # Exit at ±0.2% from mean
            'target_pnl_pct': 0.6,       # Take profit at 0.6%
            'max_hold_bars': 120,        # Max 2 hours
            'hard_stop_distance': 0.8,   # *** CRITICAL: 0.8% max loss ***

            # Filters - Very relaxed
            'min_atr_ratio': 0.3,
            'max_atr_ratio': 10.0,
            'min_vol_ratio': 0.3,
            'max_vol_ratio': 10.0,
            'min_daily_range_pct': None,

            # Session filters - NONE
            'trading_hours': None,

            # Risk controls - STRICT
            'max_account_dd': 10.0,  # Stop trading at -10% DD
            'max_daily_loss': 3.0,   # Stop at -3% daily
            'one_side_only': True,
            'cooldown_hours': 1,
        }
        super().__init__(config)


def get_strategy_config():
    """Factory function for backtest integration"""
    return {
        'name': 'Micro MR',
        'class': MicroMRStrategy,
        'description': 'Ultra-tight risk control: 0.8% stop, 0.3% positions',
        'recommended_pairs': ['SOLUSDT', 'ETHUSDT', 'BTCUSDT'],
        'recommended_timeframes': ['1m'],
    }
