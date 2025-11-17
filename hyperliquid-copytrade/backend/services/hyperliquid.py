import aiohttp
from typing import Optional, Dict, Any
from config import settings


class HyperliquidService:
    """Service to interact with Hyperliquid API"""

    def __init__(self):
        self.api_url = settings.HYPERLIQUID_API_URL

    async def validate_wallet_address(self, wallet_address: str) -> bool:
        """Validate a Hyperliquid wallet address by checking if it exists"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    json={
                        "type": "clearinghouseState",
                        "user": wallet_address
                    },
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        # If we get a response, the wallet exists
                        return True
                    return False
        except Exception as e:
            print(f"Error validating wallet: {e}")
            return False

    async def get_user_state(self, wallet_address: str) -> Optional[Dict[str, Any]]:
        """Get user account state from Hyperliquid"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    json={
                        "type": "clearinghouseState",
                        "user": wallet_address
                    },
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except Exception as e:
            print(f"Error getting user state: {e}")
            return None

    async def get_user_fills(self, wallet_address: str, start_time: Optional[int] = None) -> Optional[list]:
        """Get user trade fills from Hyperliquid"""
        try:
            payload = {
                "type": "userFills",
                "user": wallet_address
            }
            if start_time:
                payload["startTime"] = start_time

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.api_url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    return None
        except Exception as e:
            print(f"Error getting user fills: {e}")
            return None


# Global service instance
hyperliquid_service = HyperliquidService()
