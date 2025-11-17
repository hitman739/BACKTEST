"""Ultra copy trading module for real trading on Hyperliquid"""

from .service import ultra_copy_service, UltraCopyConfig, UltraPosition, UltraTrade
from .routes import router

__all__ = [
    "ultra_copy_service",
    "UltraCopyConfig",
    "UltraPosition",
    "UltraTrade",
    "router",
]
