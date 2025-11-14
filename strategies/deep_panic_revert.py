"""
Deep Panic Revert - Aggressive Mean Reversion Strategy

Entry philosophy:
- Only activate in extreme panic/pump events
- Catch violent reversions after cascades
- Large DD expected but infrequent
- Few trades but massive R when it works

Target profile:
- Win rate: 55-65%
- Average R: 4.0-6.0
- Max DD per basket: ~5-8%
- Sharpe: 0.4-0.7 (tolerates drawdown)
"""

from engine.mean_reversion import MeanReversionEngine, MeanReversionState


class DeepPanicRevertStrategy(MeanReversionEngine):
    """
    Aggressive mean reversion for extreme events

    Configuration:
    - Mean: MIDRANGE (mid of high/low last 720 candles ≈ 12h on 1m)
    - Entry thresholds: -5%, -8%, -11% (long) / +5%, +8%, +11% (short)
    - Max 3 layers per side
    - Exit when price returns within ±2% of 12h mean or +4-5% PnL
    - Hard stop at ±15% distance
    - Regime filters: Only trade if daily range ≥ 5%, vol ≥ 1.5x
    - Avoid dead sessions (need real event)
    """

    def __init__(self):
        config = {
            'name': 'Deep Panic Revert',

            # Mean calculation
            'mean_type': 'midrange',  # Mid of high/low
            'mean_lookback': 720,  # 720 candles on 1m = 12 hours

            # Entry thresholds (% distance from mean) - VERY aggressive
            'long_thresholds': [-5.0, -8.0, -11.0],  # Only extreme panic
            'short_thresholds': [5.0, 8.0, 11.0],     # Only extreme pump
            'max_layers_long': 3,
            'max_layers_short': 3,
            'min_time_between_layers': 15,  # 15 minutes between layers

            # Position sizing (% of equity risk per side)
            'total_risk_cap_long': 3.0,   # Max 3% total risk for long side
            'total_risk_cap_short': 3.0,  # Max 3% total risk for short side
            'layer_multipliers': [0.8, 1.0, 1.2],  # L1: 0.8%, L2: 1.0%, L3: 1.2% = 3.0%

            # Exit conditions
            'mean_reentry_band': 2.0,     # Exit when within ±2% of 12h mean
            'target_pnl_pct': 4.5,        # Exit at +4.5% of equity PnL (massive target)
            'max_hold_bars': None,        # No time limit (may take hours to revert)
            'hard_stop_distance': 15.0,   # Hard cut at ±15% distance

            # Regime filters - VERY strict (only real events)
            'min_atr_ratio': 0.5,   # Allow any volatility
            'max_atr_ratio': 10.0,  # Even in extreme crash, trade it
            'min_vol_ratio': 1.5,   # Must have real volume (1.5x+ average)
            'max_vol_ratio': 10.0,  # No upper limit (cascades have huge vol)
            'min_daily_range_pct': 5.0,  # Only trade if daily range ≥ 5% (real event)

            # Session filters (UTC hours)
            'trading_hours': None,  # Trade anytime (events happen 24/7)

            # Global risk controls
            'max_account_dd': 20.0,      # Max 20% account drawdown
            'max_daily_loss': 8.0,       # Higher daily loss tolerance (8%)
            'one_side_only': True,       # Only long OR short at a time

            # Cooldown after hard stop
            'cooldown_hours': 24,  # 24 hour cooldown after hitting hard stop (wait for next event)
        }
        super().__init__(config)


def get_strategy_config():
    """Factory function for backtest integration"""
    return {
        'name': 'Deep Panic Revert',
        'class': DeepPanicRevertStrategy,
        'description': 'Aggressive mean reversion for extreme panic/pump events',
        'recommended_pairs': ['BTCUSDT', 'ETHUSDT', 'SOLUSDT'],
        'recommended_timeframes': ['1m', '5m'],
        'expected_winrate': 0.60,
        'expected_sharpe': 0.55,
        'max_expected_dd': 8.0,
        'note': 'Infrequent trades, high R, tolerates large DD',
    }
