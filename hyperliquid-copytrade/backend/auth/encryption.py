from cryptography.fernet import Fernet
from config import settings
import base64
import hashlib


class APIKeyEncryption:
    """Encrypt and decrypt API keys using Fernet (AES-128-CBC)"""

    def __init__(self):
        # Create a valid Fernet key from the settings key
        key_bytes = settings.ENCRYPTION_KEY.encode()
        # Use SHA256 to get exactly 32 bytes, then base64 encode for Fernet
        hashed = hashlib.sha256(key_bytes).digest()
        self.fernet_key = base64.urlsafe_b64encode(hashed)
        self.cipher = Fernet(self.fernet_key)

    def encrypt(self, api_key: str) -> str:
        """Encrypt an API key"""
        if not api_key:
            return ""
        return self.cipher.encrypt(api_key.encode()).decode()

    def decrypt(self, encrypted_key: str) -> str:
        """Decrypt an API key"""
        if not encrypted_key:
            return ""
        return self.cipher.decrypt(encrypted_key.encode()).decode()


# Global instance
encryption = APIKeyEncryption()
