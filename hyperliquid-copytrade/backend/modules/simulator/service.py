"""
Simulator Module for Hyperliquid Copy Trading

This module simulates copy trading without executing real trades.
It allows users to test strategies and analyze performance in a safe environment.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid


class SimulatorConfig(BaseModel):
    """Configuration for a simulator instance"""
    id: str
    user_id: str
    target_trader: str
    initial_balance: float = 10000.0
    leverage: int = 5
    margin_multiplier: float = 1.0
    max_per_trade_pct: float = 0.1
    is_active: bool = True
    created_at: datetime


class SimulatorPosition(BaseModel):
    """Simulated position"""
    id: str
    config_id: str
    symbol: str
    side: str  # "LONG" or "SHORT"
    size: float
    entry_price: float
    current_price: float
    leverage: int
    unrealized_pnl: float
    margin_used: float
    opened_at: datetime


class SimulatorTrade(BaseModel):
    """Simulated trade"""
    id: str
    config_id: str
    symbol: str
    side: str
    size: float
    entry_price: float
    exit_price: Optional[float]
    pnl: Optional[float]
    opened_at: datetime
    closed_at: Optional[datetime]
    status: str  # "OPEN" or "CLOSED"


class SimulatorService:
    """Service to manage simulator instances"""

    def __init__(self):
        self.configs: Dict[str, SimulatorConfig] = {}
        self.positions: Dict[str, List[SimulatorPosition]] = {}
        self.trades: Dict[str, List[SimulatorTrade]] = {}

    def create_config(
        self,
        user_id: str,
        target_trader: str,
        initial_balance: float = 10000.0,
        leverage: int = 5,
        margin_multiplier: float = 1.0
    ) -> SimulatorConfig:
        """Create a new simulator configuration"""
        config_id = str(uuid.uuid4())
        config = SimulatorConfig(
            id=config_id,
            user_id=user_id,
            target_trader=target_trader,
            initial_balance=initial_balance,
            leverage=leverage,
            margin_multiplier=margin_multiplier,
            created_at=datetime.utcnow()
        )

        self.configs[config_id] = config
        self.positions[config_id] = []
        self.trades[config_id] = []

        return config

    def get_config(self, config_id: str) -> Optional[SimulatorConfig]:
        """Get simulator configuration"""
        return self.configs.get(config_id)

    def get_user_configs(self, user_id: str) -> List[SimulatorConfig]:
        """Get all configs for a user"""
        return [cfg for cfg in self.configs.values() if cfg.user_id == user_id]

    def get_positions(self, config_id: str) -> List[SimulatorPosition]:
        """Get all positions for a config"""
        return self.positions.get(config_id, [])

    def get_trades(self, config_id: str) -> List[SimulatorTrade]:
        """Get all trades for a config"""
        return self.trades.get(config_id, [])

    def simulate_trade(
        self,
        config_id: str,
        symbol: str,
        side: str,
        size: float,
        price: float
    ) -> SimulatorTrade:
        """Simulate opening a trade"""
        config = self.configs.get(config_id)
        if not config:
            raise ValueError(f"Config {config_id} not found")

        trade_id = str(uuid.uuid4())
        trade = SimulatorTrade(
            id=trade_id,
            config_id=config_id,
            symbol=symbol,
            side=side,
            size=size,
            entry_price=price,
            exit_price=None,
            pnl=None,
            opened_at=datetime.utcnow(),
            closed_at=None,
            status="OPEN"
        )

        self.trades[config_id].append(trade)

        # Create position
        position_id = str(uuid.uuid4())
        position = SimulatorPosition(
            id=position_id,
            config_id=config_id,
            symbol=symbol,
            side=side,
            size=size,
            entry_price=price,
            current_price=price,
            leverage=config.leverage,
            unrealized_pnl=0.0,
            margin_used=size * price / config.leverage,
            opened_at=datetime.utcnow()
        )

        self.positions[config_id].append(position)

        return trade

    def close_trade(
        self,
        config_id: str,
        trade_id: str,
        exit_price: float
    ) -> SimulatorTrade:
        """Simulate closing a trade"""
        trades = self.trades.get(config_id, [])
        trade = next((t for t in trades if t.id == trade_id), None)

        if not trade:
            raise ValueError(f"Trade {trade_id} not found")

        if trade.status == "CLOSED":
            raise ValueError(f"Trade {trade_id} already closed")

        # Calculate PnL
        if trade.side == "LONG":
            pnl = (exit_price - trade.entry_price) * trade.size
        else:
            pnl = (trade.entry_price - exit_price) * trade.size

        trade.exit_price = exit_price
        trade.pnl = pnl
        trade.closed_at = datetime.utcnow()
        trade.status = "CLOSED"

        # Remove position
        positions = self.positions.get(config_id, [])
        self.positions[config_id] = [p for p in positions if p.id != trade_id]

        return trade

    def get_stats(self, config_id: str) -> Dict:
        """Get simulator statistics"""
        config = self.configs.get(config_id)
        if not config:
            raise ValueError(f"Config {config_id} not found")

        trades = self.trades.get(config_id, [])
        positions = self.positions.get(config_id, [])

        closed_trades = [t for t in trades if t.status == "CLOSED"]
        total_pnl = sum(t.pnl for t in closed_trades if t.pnl)
        winning_trades = [t for t in closed_trades if t.pnl and t.pnl > 0]
        losing_trades = [t for t in closed_trades if t.pnl and t.pnl < 0]

        return {
            "initial_balance": config.initial_balance,
            "current_balance": config.initial_balance + total_pnl,
            "total_pnl": total_pnl,
            "total_trades": len(closed_trades),
            "open_positions": len(positions),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": len(winning_trades) / len(closed_trades) if closed_trades else 0,
            "avg_win": sum(t.pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0,
            "avg_loss": sum(t.pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0,
        }

    def delete_config(self, config_id: str) -> bool:
        """Delete a simulator configuration"""
        if config_id in self.configs:
            del self.configs[config_id]
            self.positions.pop(config_id, None)
            self.trades.pop(config_id, None)
            return True
        return False


# Global simulator service instance
simulator_service = SimulatorService()
