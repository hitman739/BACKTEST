from sqlalchemy import Column, String, DateTime, Boolean
from datetime import datetime
from models.database import Base
from auth.security import hash_password, verify_password
import uuid


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)

    # Hyperliquid credentials (encrypted)
    hyperliquid_api_key = Column(String(500), nullable=True)
    hyperliquid_wallet_address = Column(String(42), nullable=True)

    # Account settings
    is_active = Column(Boolean, default=True)
    testnet_mode = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def set_password(self, password: str):
        """Hash and set password"""
        self.password_hash = hash_password(password)

    def check_password(self, password: str) -> bool:
        """Verify password"""
        return verify_password(password, self.password_hash)

    def to_dict(self):
        """Convert to dictionary (safe for API responses)"""
        return {
            "id": self.id,
            "email": self.email,
            "has_api_key": self.hyperliquid_api_key is not None,
            "wallet_address": self.hyperliquid_wallet_address,
            "testnet_mode": self.testnet_mode,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
