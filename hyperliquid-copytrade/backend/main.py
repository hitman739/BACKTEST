from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import settings
from models.database import init_db
from routes import auth, account
from modules.simulator import routes as simulator_routes
from modules.ultra import routes as ultra_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup: Initialize database
    print("=" * 80)
    print("🚀 Starting Hyperliquid Copy Trading API")
    print("=" * 80)
    print("\n📦 Initializing database...")
    init_db()
    print("✅ Database initialized successfully")
    print("\n📊 Available modules:")
    print("   • Authentication (/api/auth)")
    print("   • Account Management (/api/account)")
    print("   • Simulator (/api/simulator) - Safe copy trading simulation")
    print("   • Ultra Copy Trading (/api/ultra) - REAL trading on Hyperliquid")
    print("\n🌐 Server ready on http://0.0.0.0:8000")
    print("📖 API Docs: http://0.0.0.0:8000/docs")
    print("=" * 80)
    yield
    # Shutdown: cleanup
    print("\n" + "=" * 80)
    print("🛑 Shutting down Hyperliquid Copy Trading API")
    print("=" * 80)


# Create FastAPI app
app = FastAPI(
    title="Hyperliquid Copy Trading API - Unified",
    description="""
    Unified API for Hyperliquid Copy Trading with two modules:

    ## Modules

    ### 1. Simulator (`/api/simulator/*`)
    Safe copy trading simulation without real money.
    - Create simulator configurations
    - Simulate trades and track performance
    - Test strategies without risk

    ### 2. Ultra Copy Trading (`/api/ultra/*`)
    **REAL** copy trading on Hyperliquid.
    - Monitor target traders via WebSocket
    - Automatic trade execution
    - Real-time position management

    ## Authentication
    All endpoints require authentication via Bearer token.
    Use `/api/auth/login` or `/api/auth/register` to get started.
    """,
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(account.router)
app.include_router(simulator_routes.router)
app.include_router(ultra_routes.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Hyperliquid Copy Trading API - Unified",
        "version": "2.0.0",
        "status": "online",
        "modules": {
            "simulator": {
                "status": "active",
                "prefix": "/api/simulator",
                "description": "Safe copy trading simulation"
            },
            "ultra": {
                "status": "active",
                "prefix": "/api/ultra",
                "description": "REAL copy trading on Hyperliquid"
            }
        },
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "modules": {
            "simulator": "active",
            "ultra": "active"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
