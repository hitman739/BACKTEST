"""
Session Revert - Intermediate Mean Reversion Strategy

Entry philosophy:
- Capture reversion to session VWAP after aggressive moves
- More DD allowed, higher profit per basket
- 3 layers for deeper averaging
- Targets strong trending days with intraday reversions

Target profile:
- Win rate: 60-70%
- Average R: 2.5-3.5
- Max DD per basket: ~2-4%
- Sharpe: 0.6-0.9
"""

from engine.mean_reversion import MeanReversionEngine, MeanReversionState


class SessionRevertStrategy(MeanReversionEngine):
    """
    Intermediate mean reversion for BTC/ETH/SOL

    Configuration:
    - Mean: VWAP of session (rolling 480 candles ≈ 8h on 1m)
    - Entry thresholds: -3%, -5%, -7% (long) / +3%, +5%, +7% (short)
    - Max 3 layers per side
    - Exit when price returns to VWAP ±0.7% or +2.5% PnL
    - Hard stop at ±10% distance
    - Regime filters: Only trade if daily range ≥ 2.5%, vol ratio 1.0-3.5
    - No new layers if ATR ratio > 2.5 (crash mode)
    """

    def __init__(self):
        config = {
            'name': 'Session Revert',

            # Mean calculation
            'mean_type': 'vwap',  # Volume-weighted average price
            'mean_lookback': 480,  # 480 candles on 1m = 8 hours

            # Entry thresholds (% distance from mean)
            'long_thresholds': [-3.0, -5.0, -7.0],  # More aggressive entries
            'short_thresholds': [3.0, 5.0, 7.0],
            'max_layers_long': 3,
            'max_layers_short': 3,
            'min_time_between_layers': 10,  # 10 minutes between layers

            # Position sizing (% of equity risk per side)
            'total_risk_cap_long': 2.0,   # Max 2% total risk for long side
            'total_risk_cap_short': 2.0,  # Max 2% total risk for short side
            'layer_multipliers': [0.5, 0.7, 0.8],  # L1: 0.5%, L2: 0.7%, L3: 0.8% = 2.0%

            # Exit conditions
            'mean_reentry_band': 0.7,     # Exit when within ±0.7% of VWAP
            'target_pnl_pct': 2.5,        # Exit at +2.5% of equity PnL
            'max_hold_bars': None,        # No time limit
            'hard_stop_distance': 10.0,   # Hard cut at ±10% distance

            # Regime filters
            'min_atr_ratio': 0.5,   # Lower min to catch more setups
            'max_atr_ratio': 2.5,   # Don't add layers in crash mode
            'min_vol_ratio': 1.0,   # Need real volume
            'max_vol_ratio': 3.5,   # Allow higher vol spikes
            'min_daily_range_pct': 2.5,  # Only trade if daily range ≥ 2.5%

            # Session filters (UTC hours)
            'trading_hours': None,  # Trade all sessions (but daily range filter applies)

            # Global risk controls
            'max_account_dd': 20.0,      # Max 20% account drawdown
            'max_daily_loss': 5.0,       # Max 5% daily loss
            'one_side_only': True,       # Only long OR short at a time

            # Cooldown after hard stop
            'cooldown_hours': 6,  # 6 hour cooldown after hitting hard stop
        }
        super().__init__(config)


def get_strategy_config():
    """Factory function for backtest integration"""
    return {
        'name': 'Session Revert',
        'class': SessionRevertStrategy,
        'description': 'Intermediate mean reversion targeting session VWAP',
        'recommended_pairs': ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'],
        'recommended_timeframes': ['1m', '5m'],
        'expected_winrate': 0.65,
        'expected_sharpe': 0.75,
        'max_expected_dd': 4.0,
    }
