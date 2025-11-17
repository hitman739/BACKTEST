"""
New API for Hyperliquid Copy Trading
Uses local database for fast queries, no direct Hyperliquid API calls except initial sync
"""
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import asyncio
import logging
from database import Database
from indexer import HyperliquidIndexer
from metrics_calculator import MetricsCalculator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Hyperliquid CopyTrade API v2")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
database = Database("hyperliquid_data.db")
indexer = HyperliquidIndexer(database, testnet=False)
metrics_calculator = MetricsCalculator(database, testnet=False)


class AddWalletRequest(BaseModel):
    wallet_address: str
    initial_balance: float = 10000.0


class WebSocketManager:
    """Manage WebSocket connections for real-time updates"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting: {e}")


ws_manager = WebSocketManager()


# =====================
# STARTUP/SHUTDOWN
# =====================

@app.on_event("startup")
async def startup_event():
    """Initialize indexer and metrics calculator"""
    logger.info("🚀 Starting Hyperliquid CopyTrade API v2...")

    # Start indexer
    asyncio.create_task(indexer.start())

    # Start periodic metrics updates (every 60 seconds)
    asyncio.create_task(metrics_calculator.start_periodic_updates(interval_seconds=60))

    # Start real-time broadcast (every 1 second)
    asyncio.create_task(broadcast_updates())

    logger.info("✅ API v2 ready!")


async def broadcast_updates():
    """Broadcast wallet updates to all connected clients every second"""
    while True:
        try:
            wallets = database.get_active_wallets()

            updates = []
            for wallet in wallets:
                metrics = metrics_calculator.calculate_metrics(wallet)
                if metrics:
                    updates.append({
                        "wallet": wallet,
                        "metrics": metrics
                    })

            if updates:
                await ws_manager.broadcast({
                    "type": "metrics_update",
                    "data": updates
                })

        except Exception as e:
            logger.error(f"Error in broadcast loop: {e}")

        await asyncio.sleep(1)  # Update every second


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down...")
    await indexer.stop()
    database.close()


# =====================
# WEBSOCKET ENDPOINT
# =====================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await ws_manager.connect(websocket)

    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()

            # Optional: handle client commands here
            if data == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)


# =====================
# WALLET ENDPOINTS
# =====================

@app.post("/wallet/add")
async def add_wallet(request: AddWalletRequest):
    """
    Add a wallet to track
    - Syncs historical data via REST (one-time)
    - Subscribes to WebSocket for live updates
    - Returns immediately, indexing continues in background
    """
    try:
        wallet = request.wallet_address.lower()

        # Check if already tracking
        active_wallets = database.get_active_wallets()
        if wallet in active_wallets:
            raise HTTPException(status_code=400, detail="Wallet already being tracked")

        # Add wallet (indexer will handle sync and subscription)
        asyncio.create_task(indexer.add_wallet(wallet, request.initial_balance))

        return {
            "status": "added",
            "wallet": wallet,
            "message": "Wallet added. Historical data syncing in background."
        }

    except Exception as e:
        logger.error(f"Error adding wallet: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/wallet/{wallet_address}")
async def remove_wallet(wallet_address: str):
    """Remove a wallet from tracking"""
    try:
        wallet = wallet_address.lower()

        await indexer.remove_wallet(wallet)

        return {
            "status": "removed",
            "wallet": wallet
        }

    except Exception as e:
        logger.error(f"Error removing wallet: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/wallet/{wallet_address}/summary")
async def get_wallet_summary(wallet_address: str):
    """Get comprehensive wallet summary"""
    try:
        wallet = wallet_address.lower()

        # Calculate real-time metrics
        metrics = metrics_calculator.calculate_metrics(wallet)

        if not metrics:
            raise HTTPException(status_code=404, detail="Wallet not found")

        return {
            "wallet": wallet,
            "metrics": metrics
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting wallet summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/wallet/{wallet_address}/fills")
async def get_wallet_fills(wallet_address: str, limit: int = 100):
    """Get fills (trades) for a wallet"""
    try:
        wallet = wallet_address.lower()

        fills = database.get_fills(wallet, limit=limit)

        return {
            "wallet": wallet,
            "fills": fills,
            "count": len(fills)
        }

    except Exception as e:
        logger.error(f"Error getting fills: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/wallet/{wallet_address}/positions")
async def get_wallet_positions(wallet_address: str):
    """Get open positions for a wallet"""
    try:
        wallet = wallet_address.lower()

        positions = database.get_positions(wallet)

        return {
            "wallet": wallet,
            "positions": positions,
            "count": len(positions)
        }

    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/wallet/{wallet_address}/equity")
async def get_wallet_equity(wallet_address: str, limit: int = 100):
    """Get equity history for a wallet"""
    try:
        wallet = wallet_address.lower()

        metrics_history = database.get_metrics_history(wallet, limit=limit)

        return {
            "wallet": wallet,
            "history": [
                {
                    "timestamp": m["timestamp"],
                    "equity": m["equity"],
                    "total_pnl": m["total_pnl"],
                    "roi": m["roi"]
                }
                for m in metrics_history
            ]
        }

    except Exception as e:
        logger.error(f"Error getting equity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/wallet/{wallet_address}/fees")
async def get_wallet_fees(wallet_address: str):
    """Get fee statistics and fee factor"""
    try:
        wallet = wallet_address.lower()

        metrics = metrics_calculator.calculate_metrics(wallet)

        if not metrics:
            raise HTTPException(status_code=404, detail="Wallet not found")

        return {
            "wallet": wallet,
            "total_fees": metrics["total_fees"],
            "total_volume": metrics["total_volume"],
            "fee_factor_mixed": metrics["fee_factor_mixed"],
            "fee_factor_taker": metrics["fee_factor_taker"],
            "explanation": {
                "fee_factor_mixed": "Profit retention with 75% maker + 25% taker fees",
                "fee_factor_taker": "Profit retention with 100% taker fees (worst case)",
                "formula": "fee_factor = (profit_after_fees) / (profit_before_fees)"
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting fees: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =====================
# STATUS ENDPOINTS
# =====================

@app.get("/status")
async def get_status():
    """Get overall system status"""
    try:
        wallets = database.get_active_wallets()

        wallet_summaries = []
        for wallet in wallets:
            metrics = metrics_calculator.calculate_metrics(wallet)
            if metrics:
                wallet_summaries.append({
                    "wallet": wallet,
                    "equity": metrics["equity"],
                    "total_pnl": metrics["total_pnl"],
                    "roi": metrics["roi"],
                    "num_trades": metrics["num_trades"],
                    "num_open_positions": metrics["num_open_positions"],
                    "fee_factor_mixed": metrics["fee_factor_mixed"],
                    "fee_factor_taker": metrics["fee_factor_taker"]
                })

        return {
            "status": "running",
            "active_wallets": len(wallets),
            "wallets": wallet_summaries
        }

    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# =====================
# RUN SERVER
# =====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
