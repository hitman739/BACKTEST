"""
Hyperliquid Copy Trading Backend
FastAPI server with WebSocket support for real-time trade copying
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import logging
from typing import Optional
from copytrade import CopyTradeManager
from paper_trading import PaperTradingManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Hyperliquid CopyTrade API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite and React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global managers
copy_manager: Optional[CopyTradeManager] = None
paper_managers: dict[str, PaperTradingManager] = {}  # Multiple paper trading sessions
MAX_PAPER_WALLETS = 15  # Maximum number of wallets to test simultaneously


class StartCopyRequest(BaseModel):
    api_key: str = ""
    api_secret: str = ""
    target_wallet: str
    testnet: bool = True
    paper_mode: bool = False  # Paper trading mode (no real money)
    initial_balance: float = 10000.0  # For paper trading


class AddWalletRequest(BaseModel):
    target_wallet: str
    testnet: bool = True
    initial_balance: float = 10000.0


class ConnectionManager:
    """Manage WebSocket connections for real-time updates"""
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Send message to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error sending message to client: {e}")


manager = ConnectionManager()


@app.get("/")
async def root():
    return {
        "app": "Hyperliquid CopyTrade",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "copy_active": copy_manager is not None and copy_manager.is_running
    }


@app.post("/start")
async def start_copy(request: StartCopyRequest):
    """Start copying trades from target wallet"""
    global copy_manager, paper_manager

    try:
        # Check if something is already running
        if copy_manager and copy_manager.is_running:
            raise HTTPException(status_code=400, detail="Real copy trading already running. Stop it first.")

        if paper_manager and paper_manager.is_running:
            raise HTTPException(status_code=400, detail="Paper trading already running. Stop it first.")

        if request.paper_mode:
            # Start Paper Trading
            paper_manager = PaperTradingManager(
                target_wallet=request.target_wallet,
                initial_balance=request.initial_balance,
                testnet=request.testnet,
                callback=broadcast_update
            )

            # Start monitoring in background
            asyncio.create_task(paper_manager.start())

            await broadcast_update({
                "type": "status",
                "status": "started",
                "message": f"Paper trading iniciado: ${request.initial_balance:,.2f}",
                "paper_mode": True,
                "testnet": request.testnet
            })

            return {
                "status": "started",
                "target_wallet": request.target_wallet,
                "paper_mode": True,
                "initial_balance": request.initial_balance,
                "testnet": request.testnet
            }

        else:
            # Start Real Copy Trading
            if not request.api_key or not request.api_secret:
                raise HTTPException(status_code=400, detail="API key and secret required for real trading")

            copy_manager = CopyTradeManager(
                api_key=request.api_key,
                api_secret=request.api_secret,
                target_wallet=request.target_wallet,
                testnet=request.testnet,
                callback=broadcast_update
            )

            # Start monitoring in background
            asyncio.create_task(copy_manager.start())

            await broadcast_update({
                "type": "status",
                "status": "started",
                "message": f"Started copying {request.target_wallet}",
                "paper_mode": False,
                "testnet": request.testnet
            })

            return {
                "status": "started",
                "target_wallet": request.target_wallet,
                "paper_mode": False,
                "testnet": request.testnet
            }

    except Exception as e:
        logger.error(f"Error starting copy trading: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/stop")
async def stop_copy():
    """Stop copying trades"""
    global copy_manager, paper_manager

    if not copy_manager and not paper_manager:
        raise HTTPException(status_code=400, detail="No trading session active")

    try:
        if paper_manager:
            await paper_manager.stop()
            paper_manager = None
            message = "Paper trading stopped"

        if copy_manager:
            await copy_manager.stop()
            copy_manager = None
            message = "Copy trading stopped"

        await broadcast_update({
            "type": "status",
            "status": "stopped",
            "message": message
        })

        return {"status": "stopped"}

    except Exception as e:
        logger.error(f"Error stopping trading: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status")
async def get_status():
    """Get current copy trading status"""
    # Check if multi-wallet paper trading
    if paper_managers:
        wallets = []
        for wallet_addr, manager in paper_managers.items():
            stats = manager.get_stats()
            wallets.append({
                "wallet": wallet_addr,
                "is_running": stats["is_running"],
                "initial_balance": stats["initial_balance"],
                "current_balance": stats["current_balance"],
                "total_pnl": stats["total_pnl"],
                "total_fees_paid": stats["total_fees_paid"],
                "roi": stats["roi"],
                "trades_copied": stats["trades_copied"],
                "open_positions": stats["open_positions"]
            })

        return {
            "active": True,
            "paper_mode": True,
            "multi_wallet": True,
            "wallets": wallets,
            "total_wallets": len(wallets)
        }

    # Check real copy trading
    if copy_manager:
        return {
            "active": copy_manager.is_running,
            "paper_mode": False,
            "multi_wallet": False,
            "target_wallet": copy_manager.target_wallet,
            "trades_copied": copy_manager.trades_copied,
            "testnet": copy_manager.testnet
        }

    # Nothing running
    return {
        "active": False,
        "paper_mode": False,
        "multi_wallet": False,
        "wallets": []
    }


@app.post("/add-wallet")
async def add_wallet(request: AddWalletRequest):
    """Add a wallet to paper trade testing"""
    global paper_managers

    try:
        # Validate wallet
        if not request.target_wallet.startswith("0x"):
            raise HTTPException(status_code=400, detail="Wallet must start with 0x")

        # Check if already exists
        if request.target_wallet in paper_managers:
            raise HTTPException(status_code=400, detail="Wallet already being tested")

        # Check limit
        if len(paper_managers) >= MAX_PAPER_WALLETS:
            raise HTTPException(status_code=400, detail=f"Maximum {MAX_PAPER_WALLETS} wallets allowed")

        # Create new paper trading manager
        manager = PaperTradingManager(
            target_wallet=request.target_wallet,
            initial_balance=request.initial_balance,
            testnet=request.testnet,
            callback=broadcast_update
        )

        # Start monitoring in background
        asyncio.create_task(manager.start())

        # Add to dict
        paper_managers[request.target_wallet] = manager

        await broadcast_update({
            "type": "wallet_added",
            "wallet": request.target_wallet,
            "initial_balance": request.initial_balance,
            "total_wallets": len(paper_managers)
        })

        return {
            "status": "added",
            "wallet": request.target_wallet,
            "initial_balance": request.initial_balance,
            "total_wallets": len(paper_managers)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding wallet: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/remove-wallet/{wallet}")
async def remove_wallet(wallet: str):
    """Remove a wallet from paper trading"""
    global paper_managers

    try:
        if wallet not in paper_managers:
            raise HTTPException(status_code=404, detail="Wallet not found")

        # Stop manager
        manager = paper_managers[wallet]
        await manager.stop()

        # Remove from dict
        del paper_managers[wallet]

        await broadcast_update({
            "type": "wallet_removed",
            "wallet": wallet,
            "total_wallets": len(paper_managers)
        })

        return {
            "status": "removed",
            "wallet": wallet,
            "remaining_wallets": len(paper_managers)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing wallet: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/stop-all")
async def stop_all_wallets():
    """Stop all paper trading wallets"""
    global paper_managers

    try:
        count = len(paper_managers)

        # Stop all managers
        for manager in paper_managers.values():
            await manager.stop()

        # Clear dict
        paper_managers.clear()

        await broadcast_update({
            "type": "all_stopped",
            "message": f"Stopped {count} wallets"
        })

        return {
            "status": "stopped",
            "wallets_stopped": count
        }

    except Exception as e:
        logger.error(f"Error stopping all wallets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)

    try:
        # Send initial status
        if copy_manager:
            await websocket.send_json({
                "type": "status",
                "active": copy_manager.is_running,
                "target_wallet": copy_manager.target_wallet,
                "trades_copied": copy_manager.trades_copied
            })

        # Keep connection alive and receive messages
        while True:
            data = await websocket.receive_text()
            # Echo back for heartbeat
            await websocket.send_json({"type": "heartbeat", "message": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def broadcast_update(update: dict):
    """Broadcast update to all WebSocket clients"""
    await manager.broadcast(update)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
