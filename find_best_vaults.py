#!/usr/bin/env python3
"""
Find Best Hyperliquid Vaults for Reverse Engineering

Criteria for "good" vaults:
- Win rate: 60-90% (too high = HFT/market making)
- Holding time: > 30 mins (not ultra HFT)
- Total PnL: positive
- Trade count: > 50 (enough data)
- Symbols: SOL, BTC, ETH (available on Binance)
"""

import requests
import json
from datetime import datetime, timedelta

print("=" * 70)
print("🔍 FINDING BEST HYPERLIQUID VAULTS")
print("=" * 70)

# Try to get vault list from Hyperliquid API
url = "https://api.hyperliquid.xyz/info"

# Method 1: Get vault metadata (if available)
print("\n📊 Fetching vault data from Hyperliquid...")

# This might not work depending on API structure
# You may need to use their web interface instead

# Common vault addresses (you can add more)
known_vaults = [
    "0x9b55c8c948f988bcbe404cd070fc9ffffab8d31b",  # HYPE vault (HFT)
    # Add more vault addresses here as you discover them
]

print("\n💡 HOW TO FIND VAULTS:")
print("-" * 70)
print("\n1️⃣  VIA HYPERLIQUID WEBSITE:")
print("   • Go to: https://app.hyperliquid.xyz/vaults")
print("   • Sort by: Total PnL or Sharpe Ratio")
print("   • Filter by: Your preferred criteria")
print("   • Look for:")
print("     - Win rate: 60-85% (realistic)")
print("     - Symbol: SOL, BTC, ETH (available on Binance)")
print("     - Total trades: > 100")
print("     - Active in last 30 days")

print("\n2️⃣  CRITERIA FOR REPLICABLE VAULTS:")
print("   ✅ Win rate: 60-85% (not 95-100%)")
print("   ✅ Avg holding time: 30 mins - 4 hours")
print("   ✅ Symbols: SOL, BTC, ETH, AVAX")
print("   ✅ Total PnL: > $1,000")
print("   ✅ Trade frequency: 10-100 trades/day")
print("   ❌ Avoid: Win rate > 95% (likely HFT)")
print("   ❌ Avoid: Holding time < 5 mins (ultra HFT)")
print("   ❌ Avoid: Exotic symbols not on CEX")

print("\n3️⃣  QUICK TEST FOR A VAULT:")

def quick_test_vault(vault_address):
    """Quick test to see if vault is worth analyzing"""

    payload = {"type": "userFills", "user": vault_address}

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            trades = response.json()

            if isinstance(trades, list) and len(trades) > 0:
                print(f"\n   ✅ Vault {vault_address[:10]}... accessible")
                print(f"      Total trades: {len(trades)}")

                # Get symbol
                if 'coin' in trades[0]:
                    symbol = trades[0]['coin']
                    print(f"      Symbol: {symbol}")

                    # Check if symbol is on Binance
                    binance_symbols = ['BTC', 'ETH', 'SOL', 'AVAX', 'MATIC', 'ARB', 'OP']
                    if symbol in binance_symbols:
                        print(f"      ✅ Symbol available on Binance")
                    else:
                        print(f"      ⚠️  Symbol NOT on Binance (will use Hyperliquid data)")

                return True
            else:
                print(f"\n   ❌ No trades for {vault_address[:10]}...")
                return False
        else:
            print(f"\n   ❌ API error {response.status_code} for {vault_address[:10]}...")
            return False

    except Exception as e:
        print(f"\n   ❌ Error: {e}")
        return False

# Test known vaults
print("\n📋 TESTING KNOWN VAULTS:")
print("-" * 70)

for vault in known_vaults:
    quick_test_vault(vault)

print("\n" + "=" * 70)
print("📝 MANUAL SEARCH STEPS:")
print("=" * 70)
print("""
1. Go to Hyperliquid vaults page:
   https://app.hyperliquid.xyz/vaults

2. Look at the leaderboard and filter by:
   - Total PnL (descending)
   - Sharpe Ratio > 2
   - Active in last 7 days

3. For each interesting vault:
   a) Click on it to see details
   b) Check:
      • Symbol (prefer BTC, ETH, SOL)
      • Win rate (60-85% ideal)
      • Avg holding time (> 30 mins)
      • Total trades (> 100)

   c) Copy the vault address (0x...)

   d) Test it:
      python3 find_best_vaults.py test <vault_address>

4. Once you find a good vault, analyze it:
   python3 reverse_engineer_vault_complete.py \\
     --vault <address> \\
     --symbol <symbol> \\
     --timeframe 5m

5. If symbol not on Binance:
   python3 reconstruct_ohlcv_from_trades.py
   python3 reanalyze_with_indicators.py
""")

print("=" * 70)
print("\n💡 EXAMPLE GOOD VAULTS TO LOOK FOR:")
print("   • BTC trend-following vault")
print("   • SOL mean-reversion vault")
print("   • ETH breakout vault")
print("   • Multi-asset balanced vault")
print("\n🚫 AVOID:")
print("   • Ultra-high frequency (< 5 min holding)")
print("   • Perfect win rate (> 95%)")
print("   • Exotic illiquid symbols")
print("   • Very low trade count (< 50 trades)")

print("\n" + "=" * 70)

# Test mode
import sys
if len(sys.argv) > 2 and sys.argv[1] == 'test':
    vault_to_test = sys.argv[2]
    print(f"\n🧪 TESTING VAULT: {vault_to_test}")
    print("=" * 70)
    quick_test_vault(vault_to_test)
