from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from models.database import get_db
from models.user import User
from auth.encryption import encryption
from services.hyperliquid import hyperliquid_service
from auth.dependencies import get_current_user

router = APIRouter(prefix="/api/account", tags=["account"])


class SetWalletRequest(BaseModel):
    wallet_address: str


class WalletResponse(BaseModel):
    message: str
    wallet_address: str
    is_valid: bool


class AccountStatusResponse(BaseModel):
    user: dict
    hyperliquid_connected: bool
    wallet_address: str | None


@router.post("/set-wallet", response_model=WalletResponse)
async def set_hyperliquid_wallet(
    req: SetWalletRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Set Hyperliquid wallet address for the user"""

    # Validate wallet address format (Ethereum address)
    wallet = req.wallet_address.strip()
    if not wallet.startswith("0x") or len(wallet) != 42:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid wallet address format. Must be a valid Ethereum address (0x...)"
        )

    # Validate wallet exists on Hyperliquid
    is_valid = await hyperliquid_service.validate_wallet_address(wallet)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Wallet address not found on Hyperliquid. Please verify the address."
        )

    # Store wallet address
    current_user.hyperliquid_wallet_address = wallet
    db.commit()

    return {
        "message": "Wallet address saved successfully",
        "wallet_address": wallet,
        "is_valid": True
    }


@router.get("/status", response_model=AccountStatusResponse)
async def get_account_status(
    current_user: User = Depends(get_current_user)
):
    """Get current account connection status"""

    return {
        "user": current_user.to_dict(),
        "hyperliquid_connected": current_user.hyperliquid_wallet_address is not None,
        "wallet_address": current_user.hyperliquid_wallet_address
    }


@router.delete("/wallet")
async def remove_wallet(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove Hyperliquid wallet from account"""

    current_user.hyperliquid_wallet_address = None
    db.commit()

    return {"message": "Wallet removed successfully"}


@router.get("/hyperliquid/state")
async def get_hyperliquid_state(
    current_user: User = Depends(get_current_user)
):
    """Get Hyperliquid account state for connected wallet"""

    if not current_user.hyperliquid_wallet_address:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No wallet address connected"
        )

    state = await hyperliquid_service.get_user_state(current_user.hyperliquid_wallet_address)

    if state is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch account state from Hyperliquid"
        )

    return state
