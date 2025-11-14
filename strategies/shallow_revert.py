"""
Shallow Revert - Conservative Mean Reversion Strategy

Entry philosophy:
- Only enter on moderate deviations from mean
- Quick reversion to mean expected
- Few layers, controlled drawdown
- Many small profitable trades

Target profile:
- Win rate: 65-75%
- Average R: 1.5-2.0
- Max DD per basket: ~1-2%
- Sharpe: 0.8-1.2
"""

from engine.mean_reversion import MeanReversionEngine, MeanReversionState


class ShallowRevertStrategy(MeanReversionEngine):
    """
    Conservative mean reversion for BTC/ETH on 1m and 5m

    Configuration:
    - Mean: MIDRANGE (mid of high/low last 240 candles ≈ 4h)
    - Entry thresholds: -1.5%, -2.5% (long) / +1.5%, +2.5% (short)
    - Max 2 layers per side
    - Exit when price returns within ±0.5% of mean or +1.0% PnL
    - Hard stop at ±4% distance
    - Regime filters: ATR ratio 0.8-2.0, vol ratio 0.8-2.5
    - Session filter: London + NY (08:00-20:00 UTC)
    """

    def __init__(self):
        config = {
            'name': 'Shallow Revert',

            # Mean calculation
            'mean_type': 'midrange',  # Mid of high/low
            'mean_lookback': 240,  # 240 candles on 1m = 4 hours

            # Entry thresholds (% distance from mean)
            'long_thresholds': [-1.5, -2.5],  # Enter long at -1.5%, add at -2.5%
            'short_thresholds': [1.5, 2.5],   # Enter short at +1.5%, add at +2.5%
            'max_layers_long': 2,
            'max_layers_short': 2,
            'min_time_between_layers': 5,  # 5 minutes between layers

            # Position sizing (% of equity risk per side)
            'total_risk_cap_long': 1.0,   # Max 1% total risk for long side
            'total_risk_cap_short': 1.0,  # Max 1% total risk for short side
            'layer_multipliers': [0.4, 0.6],  # Layer 1: 0.4%, Layer 2: 0.6% = 1.0% total

            # Exit conditions
            'mean_reentry_band': 0.5,     # Exit when within ±0.5% of mean
            'target_pnl_pct': 1.0,        # Exit at +1.0% of equity PnL
            'max_hold_bars': None,        # No time limit
            'hard_stop_distance': 4.0,    # Hard cut at ±4% distance

            # Regime filters
            'min_atr_ratio': 0.8,   # ATR(14) / ATR(200) min
            'max_atr_ratio': 2.0,   # ATR(14) / ATR(200) max
            'min_vol_ratio': 0.8,   # Volume / MA(20) min
            'max_vol_ratio': 2.5,   # Volume / MA(20) max
            'min_daily_range_pct': None,  # No minimum daily range

            # Session filters (UTC hours)
            'trading_hours': [(8, 20)],  # London + NY overlap (08:00-20:00 UTC)

            # Global risk controls
            'max_account_dd': 20.0,      # Max 20% account drawdown
            'max_daily_loss': 5.0,       # Max 5% daily loss
            'one_side_only': True,       # Only long OR short at a time

            # Cooldown after hard stop
            'cooldown_hours': 4,  # 4 hour cooldown after hitting hard stop
        }
        super().__init__(config)


def get_strategy_config():
    """Factory function for backtest integration"""
    return {
        'name': 'Shallow Revert',
        'class': ShallowRevertStrategy,
        'description': 'Conservative mean reversion with tight stops',
        'recommended_pairs': ['BTCUSDT', 'ETHUSDT'],
        'recommended_timeframes': ['1m', '5m'],
        'expected_winrate': 0.70,
        'expected_sharpe': 1.0,
        'max_expected_dd': 2.0,
    }
