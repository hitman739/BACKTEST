"""
Test script to verify trade detection is working
"""
from hyperliquid.info import Info
from hyperliquid.utils import constants

# Dame una de las wallets que NO detectó trades
wallet = input("Enter wallet address that didn't detect trades: ")

info = Info(constants.MAINNET_API_URL, skip_ws=True)

print(f"\n=== Testing wallet: {wallet} ===\n")

# Get current positions
user_state = info.user_state(wallet)

if user_state and "assetPositions" in user_state:
    positions = []
    for position in user_state["assetPositions"]:
        if "position" in position:
            pos = position["position"]
            coin = pos["coin"]
            size = float(pos["szi"])

            if size != 0:
                positions.append({
                    "coin": coin,
                    "size": size,
                    "entry_px": float(pos.get("entryPx", 0)),
                })

    print(f"Current open positions: {len(positions)}")
    for p in positions:
        print(f"  - {p['coin']}: size={p['size']:.4f}, entry=${p['entry_px']:.2f}")
else:
    print("No positions found")

# Get recent fills
fills = info.user_fills(wallet)
recent_fills = fills[:10] if fills else []

print(f"\nRecent fills (last 10): {len(recent_fills)}")
for i, fill in enumerate(recent_fills):
    print(f"  {i+1}. {fill.get('coin')} - size={fill.get('sz')}, px=${fill.get('px')}, time={fill.get('time')}")

print("\n=== If you see positions/fills above, the API is working ===")
print("=== If simulator shows 0 trades, backend is not detecting them ===")
