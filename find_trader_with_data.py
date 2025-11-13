#!/usr/bin/env python3
"""
Find traders that use symbols with available data (BTC, ETH, SOL)

These symbols have data available from Binance API, so we can do
COMPLETE analysis with REAL OHLCV data.
"""

import requests
import sys

GOOD_SYMBOLS = ['BTC', 'ETH', 'SOL', 'AVAX', 'MATIC', 'ARB', 'OP', 'LINK', 'UNI', 'AAVE']

def find_traders_for_symbol(symbol):
    """Find top traders for a specific symbol"""

    print(f"\n🔍 Looking for top {symbol} traders on Hyperliquid...")
    print("=" * 70)

    # This would need the actual Hyperliquid leaderboard API
    # For now, provide manual instructions

    print(f"""
To find good {symbol} traders:

1. Go to: https://app.hyperliquid.xyz/leaderboard

2. Filter by:
   - Symbol: {symbol}
   - Timeframe: 30 days
   - Sort by: PnL

3. Look for traders with:
   ✅ Win rate: 60-85%
   ✅ Total trades: > 100
   ✅ Total PnL: > $1,000
   ✅ Active in last 7 days

4. Copy trader address (0x...)

5. Test: ./test.sh 0xTRADER_ADDRESS

6. If score ≥ 7, analyze:
   python3 reverse_engineer_vault_complete.py \\
     --vault 0xTRADER_ADDRESS \\
     --symbol {symbol} \\
     --timeframe 5m

✅ This will use REAL data from Binance API automatically!
""")

if __name__ == "__main__":
    print("=" * 70)
    print("🎯 FIND TRADERS WITH AVAILABLE DATA")
    print("=" * 70)

    print("\n📊 RECOMMENDED SYMBOLS (have Binance data):")
    print("-" * 70)

    for i, symbol in enumerate(GOOD_SYMBOLS, 1):
        print(f"{i:2d}. {symbol:6s} ← Data available from Binance ✅")

    print("\n💡 WHY THESE SYMBOLS?")
    print("-" * 70)
    print("• BTC, ETH, SOL are available on Binance")
    print("• We can get REAL OHLCV data automatically")
    print("• No manual downloads needed")
    print("• No 403 errors")
    print("• Precise technical indicators")

    print("\n" + "=" * 70)

    # Allow user to select
    if len(sys.argv) > 1:
        symbol = sys.argv[1].upper()
        if symbol in GOOD_SYMBOLS:
            find_traders_for_symbol(symbol)
        else:
            print(f"⚠️  {symbol} not in recommended list")
            print(f"   Recommended: {', '.join(GOOD_SYMBOLS)}")
    else:
        print("\nUsage: python3 find_trader_with_data.py <SYMBOL>")
        print("\nExamples:")
        print("  python3 find_trader_with_data.py BTC")
        print("  python3 find_trader_with_data.py SOL")
        print("  python3 find_trader_with_data.py ETH")
