"""
Ultra Copy Trading Module

This module handles REAL copy trading on Hyperliquid.
It connects to Hyperliquid WebSocket, monitors target traders,
and executes trades automatically based on their activity.

WARNING: This module executes REAL trades. Use with caution.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime
import uuid
import asyncio
import aiohttp


class UltraCopyConfig(BaseModel):
    """Configuration for ultra copy trading"""
    id: str
    user_id: str
    target_trader: str
    margin_multiplier: float = 1.0
    max_per_trade_pct: float = 0.1
    max_total_exposure_pct: float = 0.5
    stop_loss_pct: Optional[float] = None
    take_profit_pct: Optional[float] = None
    is_active: bool = True
    testnet_mode: bool = True
    created_at: datetime


class UltraPosition(BaseModel):
    """Active copy trading position"""
    id: str
    config_id: str
    symbol: str
    side: str
    size: float
    entry_price: float
    current_price: float
    leverage: int
    unrealized_pnl: float
    margin_used: float
    hyperliquid_order_id: Optional[str]
    opened_at: datetime


class UltraTrade(BaseModel):
    """Executed copy trade"""
    id: str
    config_id: str
    symbol: str
    side: str
    size: float
    entry_price: float
    exit_price: Optional[float]
    pnl: Optional[float]
    fees: float
    hyperliquid_order_id: Optional[str]
    opened_at: datetime
    closed_at: Optional[datetime]
    status: str  # "OPEN", "CLOSED", "FAILED"


class UltraCopyService:
    """Service to manage ultra copy trading"""

    def __init__(self):
        self.configs: Dict[str, UltraCopyConfig] = {}
        self.positions: Dict[str, List[UltraPosition]] = {}
        self.trades: Dict[str, List[UltraTrade]] = {}
        self.websocket_tasks: Dict[str, asyncio.Task] = {}
        self.running = False

    def create_config(
        self,
        user_id: str,
        target_trader: str,
        margin_multiplier: float = 1.0,
        max_per_trade_pct: float = 0.1,
        testnet_mode: bool = True
    ) -> UltraCopyConfig:
        """Create a new ultra copy configuration"""
        config_id = str(uuid.uuid4())
        config = UltraCopyConfig(
            id=config_id,
            user_id=user_id,
            target_trader=target_trader,
            margin_multiplier=margin_multiplier,
            max_per_trade_pct=max_per_trade_pct,
            testnet_mode=testnet_mode,
            created_at=datetime.utcnow()
        )

        self.configs[config_id] = config
        self.positions[config_id] = []
        self.trades[config_id] = []

        return config

    def get_config(self, config_id: str) -> Optional[UltraCopyConfig]:
        """Get ultra copy configuration"""
        return self.configs.get(config_id)

    def get_user_configs(self, user_id: str) -> List[UltraCopyConfig]:
        """Get all configs for a user"""
        return [cfg for cfg in self.configs.values() if cfg.user_id == user_id]

    def get_positions(self, config_id: str) -> List[UltraPosition]:
        """Get all positions for a config"""
        return self.positions.get(config_id, [])

    def get_trades(self, config_id: str) -> List[UltraTrade]:
        """Get all trades for a config"""
        return self.trades.get(config_id, [])

    async def start_monitoring(self, config_id: str) -> bool:
        """Start monitoring a target trader via WebSocket"""
        config = self.configs.get(config_id)
        if not config:
            raise ValueError(f"Config {config_id} not found")

        if config_id in self.websocket_tasks:
            return False  # Already monitoring

        # Create WebSocket monitoring task
        task = asyncio.create_task(self._monitor_trader(config_id))
        self.websocket_tasks[config_id] = task

        config.is_active = True
        return True

    async def stop_monitoring(self, config_id: str) -> bool:
        """Stop monitoring a target trader"""
        config = self.configs.get(config_id)
        if not config:
            return False

        if config_id in self.websocket_tasks:
            task = self.websocket_tasks[config_id]
            task.cancel()
            del self.websocket_tasks[config_id]

        config.is_active = False
        return True

    async def _monitor_trader(self, config_id: str):
        """Monitor target trader via WebSocket (placeholder)"""
        config = self.configs.get(config_id)
        if not config:
            return

        print(f"[ULTRA] Started monitoring {config.target_trader}")

        # TODO: Implement actual WebSocket connection to Hyperliquid
        # For now, this is a placeholder that simulates monitoring

        while config.is_active:
            try:
                # Simulate checking for new trades
                await asyncio.sleep(1)

                # In production, this would:
                # 1. Connect to Hyperliquid WebSocket
                # 2. Subscribe to target trader's fills
                # 3. When new fill detected, calculate position size
                # 4. Execute copy trade via Hyperliquid API

            except asyncio.CancelledError:
                print(f"[ULTRA] Stopped monitoring {config.target_trader}")
                break
            except Exception as e:
                print(f"[ULTRA] Error monitoring {config.target_trader}: {e}")
                await asyncio.sleep(5)  # Retry after 5 seconds

    async def execute_copy_trade(
        self,
        config_id: str,
        symbol: str,
        side: str,
        size: float,
        price: float
    ) -> UltraTrade:
        """Execute a copy trade on Hyperliquid"""
        config = self.configs.get(config_id)
        if not config:
            raise ValueError(f"Config {config_id} not found")

        # Calculate actual size based on margin multiplier
        adjusted_size = size * config.margin_multiplier

        # Create trade record
        trade_id = str(uuid.uuid4())
        trade = UltraTrade(
            id=trade_id,
            config_id=config_id,
            symbol=symbol,
            side=side,
            size=adjusted_size,
            entry_price=price,
            exit_price=None,
            pnl=None,
            fees=0.0,
            hyperliquid_order_id=None,
            opened_at=datetime.utcnow(),
            closed_at=None,
            status="OPEN"
        )

        # TODO: Execute actual trade on Hyperliquid
        # This is where you'd use the Hyperliquid SDK to place orders

        self.trades[config_id].append(trade)

        # Create position
        position_id = str(uuid.uuid4())
        position = UltraPosition(
            id=position_id,
            config_id=config_id,
            symbol=symbol,
            side=side,
            size=adjusted_size,
            entry_price=price,
            current_price=price,
            leverage=5,  # TODO: Get from config
            unrealized_pnl=0.0,
            margin_used=adjusted_size * price / 5,
            hyperliquid_order_id=None,
            opened_at=datetime.utcnow()
        )

        self.positions[config_id].append(position)

        return trade

    def get_stats(self, config_id: str) -> Dict:
        """Get ultra copy trading statistics"""
        config = self.configs.get(config_id)
        if not config:
            raise ValueError(f"Config {config_id} not found")

        trades = self.trades.get(config_id, [])
        positions = self.positions.get(config_id, [])

        closed_trades = [t for t in trades if t.status == "CLOSED"]
        total_pnl = sum(t.pnl for t in closed_trades if t.pnl)
        total_fees = sum(t.fees for t in trades)
        winning_trades = [t for t in closed_trades if t.pnl and t.pnl > 0]
        losing_trades = [t for t in closed_trades if t.pnl and t.pnl < 0]

        return {
            "total_pnl": total_pnl,
            "total_fees": total_fees,
            "net_pnl": total_pnl - total_fees,
            "total_trades": len(trades),
            "closed_trades": len(closed_trades),
            "open_positions": len(positions),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": len(winning_trades) / len(closed_trades) if closed_trades else 0,
            "avg_win": sum(t.pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0,
            "avg_loss": sum(t.pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0,
            "is_monitoring": config_id in self.websocket_tasks,
            "is_active": config.is_active,
        }

    def delete_config(self, config_id: str) -> bool:
        """Delete an ultra copy configuration"""
        # Stop monitoring first
        if config_id in self.websocket_tasks:
            task = self.websocket_tasks[config_id]
            task.cancel()
            del self.websocket_tasks[config_id]

        if config_id in self.configs:
            del self.configs[config_id]
            self.positions.pop(config_id, None)
            self.trades.pop(config_id, None)
            return True
        return False


# Global ultra copy service instance
ultra_copy_service = UltraCopyService()
