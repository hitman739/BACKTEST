from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from auth.dependencies import get_current_user
from models.user import User
from modules.simulator.service import simulator_service, SimulatorConfig

router = APIRouter(prefix="/api/simulator", tags=["simulator"])


class CreateSimulatorRequest(BaseModel):
    target_trader: str
    initial_balance: float = 10000.0
    leverage: int = 5
    margin_multiplier: float = 1.0


class SimulateTradeRequest(BaseModel):
    config_id: str
    symbol: str
    side: str  # "LONG" or "SHORT"
    size: float
    price: float


class CloseTradeRequest(BaseModel):
    config_id: str
    trade_id: str
    exit_price: float


@router.post("/config")
async def create_simulator_config(
    req: CreateSimulatorRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new simulator configuration"""
    config = simulator_service.create_config(
        user_id=current_user.id,
        target_trader=req.target_trader,
        initial_balance=req.initial_balance,
        leverage=req.leverage,
        margin_multiplier=req.margin_multiplier
    )

    return {
        "message": "Simulator configuration created",
        "config": config.dict()
    }


@router.get("/configs")
async def get_simulator_configs(
    current_user: User = Depends(get_current_user)
):
    """Get all simulator configurations for current user"""
    configs = simulator_service.get_user_configs(current_user.id)
    return {
        "configs": [cfg.dict() for cfg in configs]
    }


@router.get("/config/{config_id}")
async def get_simulator_config(
    config_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific simulator configuration"""
    config = simulator_service.get_config(config_id)

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulator configuration not found"
        )

    if config.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this configuration"
        )

    return {"config": config.dict()}


@router.get("/config/{config_id}/positions")
async def get_simulator_positions(
    config_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all positions for a simulator configuration"""
    config = simulator_service.get_config(config_id)

    if not config or config.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found or unauthorized"
        )

    positions = simulator_service.get_positions(config_id)
    return {
        "positions": [pos.dict() for pos in positions]
    }


@router.get("/config/{config_id}/trades")
async def get_simulator_trades(
    config_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get all trades for a simulator configuration"""
    config = simulator_service.get_config(config_id)

    if not config or config.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found or unauthorized"
        )

    trades = simulator_service.get_trades(config_id)
    return {
        "trades": [trade.dict() for trade in trades]
    }


@router.get("/config/{config_id}/stats")
async def get_simulator_stats(
    config_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get statistics for a simulator configuration"""
    config = simulator_service.get_config(config_id)

    if not config or config.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found or unauthorized"
        )

    stats = simulator_service.get_stats(config_id)
    return {"stats": stats}


@router.post("/trade")
async def simulate_trade(
    req: SimulateTradeRequest,
    current_user: User = Depends(get_current_user)
):
    """Simulate opening a trade"""
    config = simulator_service.get_config(req.config_id)

    if not config or config.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found or unauthorized"
        )

    try:
        trade = simulator_service.simulate_trade(
            config_id=req.config_id,
            symbol=req.symbol,
            side=req.side,
            size=req.size,
            price=req.price
        )

        return {
            "message": "Trade simulated successfully",
            "trade": trade.dict()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/trade/close")
async def close_simulated_trade(
    req: CloseTradeRequest,
    current_user: User = Depends(get_current_user)
):
    """Close a simulated trade"""
    config = simulator_service.get_config(req.config_id)

    if not config or config.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found or unauthorized"
        )

    try:
        trade = simulator_service.close_trade(
            config_id=req.config_id,
            trade_id=req.trade_id,
            exit_price=req.exit_price
        )

        return {
            "message": "Trade closed successfully",
            "trade": trade.dict()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/config/{config_id}")
async def delete_simulator_config(
    config_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete a simulator configuration"""
    config = simulator_service.get_config(config_id)

    if not config or config.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found or unauthorized"
        )

    simulator_service.delete_config(config_id)

    return {"message": "Simulator configuration deleted"}
