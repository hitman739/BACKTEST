from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional
from auth.dependencies import get_current_user
from models.user import User
from modules.ultra.service import ultra_copy_service, UltraCopyConfig

router = APIRouter(prefix="/api/ultra", tags=["ultra"])


class CreateUltraConfigRequest(BaseModel):
    target_trader: str
    margin_multiplier: float = 1.0
    max_per_trade_pct: float = 0.1
    max_total_exposure_pct: float = 0.5
    stop_loss_pct: Optional[float] = None
    take_profit_pct: Optional[float] = None
    testnet_mode: bool = True


class ExecuteTradeRequest(BaseModel):
    config_id: str
    symbol: str
    side: str
    size: float
    price: float


@router.post("/config")
async def create_ultra_config(
    req: CreateUltraConfigRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new ultra copy trading configuration"""

    # Verify user has Hyperliquid wallet connected
    if not current_user.hyperliquid_wallet_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please connect your Hyperliquid wallet first"
        )

    config = ultra_copy_service.create_config(
        user_id=current_user.id,
        target_trader=req.target_trader,
        margin_multiplier=req.margin_multiplier,
        max_per_trade_pct=req.max_per_trade_pct,
        testnet_mode=req.testnet_mode
    )

    return {
        "message": "Ultra copy configuration created",
        "config": config.dict()
    }


@router.get("/configs")
async def get_ultra_configs(
    current_user: User = Depends(get_current_user)
):
    """Get all ultra copy configurations for current user"""
    configs = ultra_copy_service.get_user_configs(current_user.id)
    return {
        "configs": [cfg.dict() for cfg in configs]
    }


@router.get("/config/{config_id}")
async def get_ultra_config(
    config_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific ultra copy configuration"""
    config = ultra_copy_service.get_config(config_id)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ultra copy configuration not found"
        )

    if config.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this configuration"
        )

    return {"config": config.dict()}


@router.post("/config/{config_id}/start")
async def start_ultra_monitoring(
    config_id: str,
    current_user: User = Depends(get_current_user)
):
    """Start monitoring and copying trades for a configuration"""
    config = ultra_copy_service.get_config(config_id)

    if not config or config.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found or unauthorized"
        )

    try:
        started = await ultra_copy_service.start_monitoring(config_id)

        if started:
            return {
                "message": f"Started monitoring {config.target_trader}",
                "config_id": config_id,
                "is_active": True
            }
        else:
            return {
                "message": "Already monitoring this trader",
                "config_id": config_id,
                "is_active": True
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start monitoring: {str(e)}"
        )


@router.post("/config/{config_id}/stop")
async def stop_ultra_monitoring(
    config_id: str,
    current_user: User = Depends(get_current_user)
):
    """Stop monitoring and copying trades for a configuration"""
    config = ultra_copy_service.get_config(config_id)

    if not config or config.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found or unauthorized"
        )

    stopped = await ultra_copy_service.stop_monitoring(config_id)

    return {
        "message": "Stopped monitoring" if stopped else "Not monitoring",
        "config_id": config_id,
        "is_active": False
    }


@router.get("/config/{config_id}/positions")
async def get_ultra_positions(
    config_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all positions for an ultra copy configuration"""
    config = ultra_copy_service.get_config(config_id)

    if not config or config.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found or unauthorized"
        )

    positions = ultra_copy_service.get_positions(config_id)
    return {
        "positions": [pos.dict() for pos in positions]
    }


@router.get("/config/{config_id}/trades")
async def get_ultra_trades(
    config_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all trades for an ultra copy configuration"""
    config = ultra_copy_service.get_config(config_id)

    if not config or config.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found or unauthorized"
        )

    trades = ultra_copy_service.get_trades(config_id)
    return {
        "trades": [trade.dict() for trade in trades]
    }


@router.get("/config/{config_id}/stats")
async def get_ultra_stats(
    config_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get statistics for an ultra copy configuration"""
    config = ultra_copy_service.get_config(config_id)

    if not config or config.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found or unauthorized"
        )

    stats = ultra_copy_service.get_stats(config_id)
    return {"stats": stats}


@router.post("/trade/execute")
async def execute_copy_trade(
    req: ExecuteTradeRequest,
    current_user: User = Depends(get_current_user)
):
    """Manually execute a copy trade (for testing)"""
    config = ultra_copy_service.get_config(req.config_id)

    if not config or config.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found or unauthorized"
        )

    try:
        trade = await ultra_copy_service.execute_copy_trade(
            config_id=req.config_id,
            symbol=req.symbol,
            side=req.side,
            size=req.size,
            price=req.price
        )

        return {
            "message": "Trade executed successfully",
            "trade": trade.dict()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/config/{config_id}")
async def delete_ultra_config(
    config_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete an ultra copy configuration"""
    config = ultra_copy_service.get_config(config_id)

    if not config or config.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found or unauthorized"
        )

    ultra_copy_service.delete_config(config_id)

    return {"message": "Ultra copy configuration deleted"}
