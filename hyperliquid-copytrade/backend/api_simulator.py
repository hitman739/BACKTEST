"""
Simulator API - Clean FastAPI endpoints for proportional copy trading simulation

Endpoints:
- POST /sim/start - Start simulating a wallet
- POST /sim/stop - Stop simulating a wallet
- GET /sim/snapshot - Get current state of a simulation
- GET /sim/wallets - List all active simulations
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn
import logging

from simulator_engine import simulator_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Hyperliquid Copy Trading Simulator",
    description="Simulate proportional copy trading with real Hyperliquid data",
    version="3.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request models
class StartSimulationRequest(BaseModel):
    wallet: str


class StopSimulationRequest(BaseModel):
    wallet: str


# Root endpoint
@app.get("/")
async def root():
    """API information"""
    return {
        "name": "Hyperliquid Copy Trading Simulator",
        "version": "3.0.0",
        "description": "Simulates a 10,000 USDT account copying a trader proportionally",
        "endpoints": {
            "POST /sim/start": "Start simulating a wallet",
            "POST /sim/stop": "Stop simulating a wallet",
            "GET /sim/snapshot": "Get simulation snapshot",
            "GET /sim/wallets": "List all active simulations"
        },
        "active_simulations": len(simulator_engine.simulations)
    }


@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "active_simulations": len(simulator_engine.simulations),
        "running": simulator_engine.running
    }


@app.post("/sim/start")
async def start_simulation(req: StartSimulationRequest):
    """
    Start simulating a wallet from NOW

    - Registers the wallet for simulation
    - Sets start_time = now
    - Initializes equity_sim_actual = 10,000
    - Only processes fills AFTER start_time
    """
    try:
        wallet = req.wallet.strip()

        # Validate wallet format
        if not wallet.startswith('0x') or len(wallet) != 42:
            raise HTTPException(
                status_code=400,
                detail="Invalid wallet address. Must start with 0x and be 42 characters long"
            )

        logger.info(f"Starting simulation for wallet: {wallet}")

        # Start simulation
        simulation = await simulator_engine.start_simulation(wallet)

        return {
            "success": True,
            "message": f"Simulation started for {wallet}",
            "wallet": wallet,
            "start_time": simulation.start_time,
            "equity_sim_initial": simulation.equity_sim_initial,
            "trader_equity": simulation.last_trader_equity
        }

    except Exception as e:
        logger.error(f"Error starting simulation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sim/stop")
async def stop_simulation(req: StopSimulationRequest):
    """
    Stop simulating a wallet

    - Removes the wallet from active simulations
    - Stops background updates if no wallets left
    """
    try:
        wallet = req.wallet.strip()

        logger.info(f"Stopping simulation for wallet: {wallet}")

        # Stop simulation
        success = await simulator_engine.stop_simulation(wallet)

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"No active simulation found for {wallet}"
            )

        return {
            "success": True,
            "message": f"Simulation stopped for {wallet}",
            "wallet": wallet
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping simulation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sim/snapshot")
async def get_snapshot(wallet: str):
    """
    Get current snapshot of a simulation

    Returns:
    - wallet: wallet address
    - equity_sim_actual: current simulated equity
    - pnl_total_sim: total PnL (realized + unrealized)
    - pnl_pct_sim: PnL percentage
    - realized_pnl_sim: PnL from closed positions
    - unrealized_pnl_sim: PnL from open positions
    - open_positions: list of open positions with details
    - trades_count_sim: number of simulated trades
    """
    try:
        wallet = wallet.strip()

        # Get simulation
        simulation = simulator_engine.get_simulation(wallet)

        if not simulation:
            raise HTTPException(
                status_code=404,
                detail=f"No active simulation found for {wallet}"
            )

        # Get snapshot
        snapshot = simulation.get_snapshot()

        return snapshot

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting snapshot: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sim/wallets")
async def get_wallets():
    """
    Get list of all active simulations

    Returns summary for each wallet:
    - wallet: wallet address
    - equity_sim_actual: current simulated equity
    - pnl_total_sim: total PnL
    - pnl_pct_sim: PnL percentage
    - trades_count_sim: number of simulated trades
    - start_time: when simulation started
    """
    try:
        wallets = simulator_engine.get_all_wallets()

        return {
            "count": len(wallets),
            "wallets": wallets
        }

    except Exception as e:
        logger.error(f"Error getting wallets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down simulator...")
    await simulator_engine.stop_background_updates()


if __name__ == "__main__":
    # Run the server
    uvicorn.run(
        "api_simulator:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
