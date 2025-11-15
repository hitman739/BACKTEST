"""
Improved Simple MR - Basado en los resultados de UltraSimple

Cambios vs UltraSimple:
- Thresholds más grandes: ±0.8%, ±1.5% (menos trades, mejor calidad)
- Exit band más amplia: ±0.3% (no salir tan rápido)
- Target PnL más alto: 1.2% (dejar correr ganadores)
- Hard stop más ajustado: 2% (limitar pérdidas)
- Lookback más largo: 60min (media más estable)
"""

from engine.mean_reversion import MeanReversionEngine, MeanReversionState


class ImprovedSimpleMRStrategy(MeanReversionEngine):
    """
    Improved simple mean reversion - Optimizado para reducir DD y fees
    """

    def __init__(self):
        config = {
            'name': 'Improved Simple MR',

            # Mean calculation
            'mean_type': 'midrange',
            'mean_lookback': 60,  # 1 hora

            # Entry thresholds - Más selectivos
            'long_thresholds': [-0.8, -1.5],  # Más amplio que UltraSimple
            'short_thresholds': [0.8, 1.5],
            'max_layers_long': 2,
            'max_layers_short': 2,
            'min_time_between_layers': 10,  # Más tiempo entre layers

            # Position sizing
            'total_risk_cap_long': 0.8,  # Más conservador
            'total_risk_cap_short': 0.8,
            'layer_multipliers': [0.4, 0.4],

            # Exit conditions - Optimizadas
            'mean_reentry_band': 0.3,    # Salir cuando vuelve ±0.3%
            'target_pnl_pct': 1.2,       # Target más alto (dejar correr)
            'max_hold_bars': 180,        # Max 3 horas
            'hard_stop_distance': 2.0,   # Stop más ajustado

            # Filtros relajados
            'min_atr_ratio': 0.4,
            'max_atr_ratio': 8.0,
            'min_vol_ratio': 0.4,
            'max_vol_ratio': 8.0,
            'min_daily_range_pct': None,

            # Session filters - NINGUNO
            'trading_hours': None,

            # Risk controls
            'max_account_dd': 15.0,  # Más estricto
            'max_daily_loss': 5.0,
            'one_side_only': True,
            'cooldown_hours': 2,
        }
        super().__init__(config)


def get_strategy_config():
    """Factory function for backtest integration"""
    return {
        'name': 'Improved Simple MR',
        'class': ImprovedSimpleMRStrategy,
        'description': 'Optimized thresholds (±0.8%) for better risk/reward',
        'recommended_pairs': ['SOLUSDT', 'AVAXUSDT', 'ETHUSDT'],
        'recommended_timeframes': ['1m'],
    }
