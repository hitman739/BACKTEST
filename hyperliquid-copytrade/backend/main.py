from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import settings
from models.database import init_db
from routes import auth, account


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup: Initialize database
    print("Initializing database...")
    init_db()
    print("Database initialized successfully")
    yield
    # Shutdown: cleanup
    print("Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="Hyperliquid Copy Trading API",
    description="API for copy trading on Hyperliquid",
    version="1.0.0",
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


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Hyperliquid Copy Trading API",
        "version": "1.0.0",
        "status": "online"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
