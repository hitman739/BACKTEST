from pydantic_settings import BaseSettings
from typing import List
import secrets


class Settings(BaseSettings):
    # Security
    SECRET_KEY: str = secrets.token_hex(32)
    ENCRYPTION_KEY: str = secrets.token_hex(32)
    ALGORITHM: str = "HS256"

    # Token expiration
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database
    DATABASE_URL: str = "sqlite:///./copytrade.db"

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Hyperliquid
    HYPERLIQUID_API_URL: str = "https://api.hyperliquid.xyz/info"
    HYPERLIQUID_TESTNET: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
