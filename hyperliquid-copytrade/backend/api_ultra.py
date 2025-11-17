"""
Ultra-Low Latency Copy Trading API
Minimal API to control ultra copy trader
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import asyncio
import logging
from ultra_copytrader import UltraCopyTrader

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - [%(levelname)s] - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Ultra Copy Trading API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global copy trader instance
copy_trader: Optional[UltraCopyTrader] = None


class StartCopyTradingRequest(BaseModel):
    api_key: str
    api_secret: str
    target_wallet: str
    copy_ratio: float = 1.0  # 1.0 = copy 100% of positions
    testnet: bool = False


@app.post("/start")
async def start_copy_trading(request: StartCopyTradingRequest):
    """
    Start ultra-low latency copy trading

    Args:
        api_key: Your Hyperliquid API key
        api_secret: Your Hyperliquid API secret
        target_wallet: Wallet address to copy
        copy_ratio: How much to copy (1.0 = 100%, 0.5 = 50%)
        testnet: Use testnet or mainnet

    Returns:
        Status message
    """
    global copy_trader

    try:
        # Check if already running
        if copy_trader and copy_trader.is_running:
            raise HTTPException(status_code=400, detail="Copy trading already running")

        # Validate copy ratio
        if not 0 < request.copy_ratio <= 10:
            raise HTTPException(status_code=400, detail="Copy ratio must be between 0 and 10")

        # Create copy trader
        copy_trader = UltraCopyTrader(
            api_key=request.api_key,
            api_secret=request.api_secret,
            target_wallet=request.target_wallet,
            copy_ratio=request.copy_ratio,
            testnet=request.testnet
        )

        # Start in background
        asyncio.create_task(copy_trader.start())

        logger.info(f"✅ Copy trading started")
        logger.info(f"   Target: {request.target_wallet}")
        logger.info(f"   Copy Ratio: {request.copy_ratio * 100}%")

        return {
            "status": "started",
            "target_wallet": request.target_wallet,
            "copy_ratio": request.copy_ratio,
            "testnet": request.testnet,
            "message": "Copy trading started successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting copy trading: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/stop")
async def stop_copy_trading():
    """Stop copy trading"""
    global copy_trader

    try:
        if not copy_trader:
            raise HTTPException(status_code=400, detail="Copy trading not running")

        await copy_trader.stop()

        stats = copy_trader.get_stats()

        copy_trader = None

        logger.info("🛑 Copy trading stopped")

        return {
            "status": "stopped",
            "stats": stats,
            "message": "Copy trading stopped successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping copy trading: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status")
async def get_status():
    """Get copy trading status"""
    global copy_trader

    if not copy_trader:
        return {
            "is_running": False,
            "message": "Copy trading not active"
        }

    stats = copy_trader.get_stats()

    return {
        "is_running": True,
        "stats": stats,
        "target_wallet": copy_trader.target_wallet,
        "copy_ratio": copy_trader.copy_ratio
    }


@app.get("/health")
async def health_check():
    """Health check"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    logger.info("=" * 60)
    logger.info("🚀 Ultra-Low Latency Copy Trading API")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Key Features:")
    logger.info("  ⚡ WebSocket-based (no polling)")
    logger.info("  🎯 Evento → Orden < 100ms")
    logger.info("  💾 In-memory state (no DB)")
    logger.info("  🔥 Non-blocking execution")
    logger.info("")
    logger.info("Starting server on http://0.0.0.0:8000")
    logger.info("=" * 60)

    uvicorn.run(app, host="0.0.0.0", port=8000)
