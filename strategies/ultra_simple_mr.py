"""
Ultra Simple Mean Revert - Para mercados estables

THRESHOLDS MUY PEQUEÑOS para capturar movimientos mínimos
Diseñado para BTC que no se mueve mucho en rangos de 1 hora
"""

from engine.mean_reversion import MeanReversionEngine, MeanReversionState


class UltraSimpleMRStrategy(MeanReversionEngine):
    """
    Ultra simple mean reversion con thresholds muy pequeños

    Para mercados que se mueven poco (BTC en rangos)
    """

    def __init__(self):
        config = {
            'name': 'Ultra Simple MR',

            # Mean calculation - MUY corto
            'mean_type': 'midrange',
            'mean_lookback': 30,  # Solo 30 min

            # Entry thresholds - MUY PEQUEÑOS
            'long_thresholds': [-0.5, -1.0],  # Apenas -0.5%
            'short_thresholds': [0.5, 1.0],   # Apenas +0.5%
            'max_layers_long': 2,
            'max_layers_short': 2,
            'min_time_between_layers': 5,

            # Position sizing
            'total_risk_cap_long': 1.0,
            'total_risk_cap_short': 1.0,
            'layer_multipliers': [0.5, 0.5],

            # Exit conditions - Rápido
            'mean_reentry_band': 0.2,  # Salir cuando vuelve ±0.2%
            'target_pnl_pct': 0.8,     # O gana 0.8%
            'max_hold_bars': None,
            'hard_stop_distance': 3.0,

            # FILTROS MUY RELAJADOS
            'min_atr_ratio': 0.3,
            'max_atr_ratio': 10.0,
            'min_vol_ratio': 0.3,
            'max_vol_ratio': 10.0,
            'min_daily_range_pct': None,

            # Session filters - NINGUNO
            'trading_hours': None,

            # Risk controls
            'max_account_dd': 20.0,
            'max_daily_loss': 10.0,
            'one_side_only': True,
            'cooldown_hours': 1,
        }
        super().__init__(config)


def get_strategy_config():
    """Factory function for backtest integration"""
    return {
        'name': 'Ultra Simple MR',
        'class': UltraSimpleMRStrategy,
        'description': 'Ultra simple with tiny thresholds (±0.5%)',
        'recommended_pairs': ['BTCUSDT', 'ETHUSDT'],
        'recommended_timeframes': ['1m'],
    }
