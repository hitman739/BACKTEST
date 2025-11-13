#!/usr/bin/env python3
"""
Test Hyperliquid OHLCV Data Loader
Quick test to verify we can fetch candle data from Hyperliquid
"""

from reverse_engineering.data.hyperliquid_loader import HyperliquidDataLoader
from datetime import datetime, timedelta

print("=" * 70)
print("🧪 TESTING HYPERLIQUID OHLCV DATA LOADER")
print("=" * 70)

loader = HyperliquidDataLoader()

# Test parameters
symbol = 'HYPE'
timeframe = '5m'
end_date = datetime.now()
start_date = end_date - timedelta(days=7)

print(f"\n📊 Fetching {symbol} {timeframe} candles...")
print(f"   Period: {start_date.date()} to {end_date.date()}")

# Fetch data
df = loader.get_data(
    symbol=symbol,
    timeframe=timeframe,
    start_date=start_date.strftime('%Y-%m-%d'),
    end_date=end_date.strftime('%Y-%m-%d'),
    use_cache=False  # Don't use cache for this test
)

if not df.empty:
    print(f"\n✅ SUCCESS - Fetched {len(df)} candles")
    print(f"\n📈 Data Preview:")
    print(df.head(10))

    print(f"\n📊 Data Range:")
    print(f"   Start: {df['timestamp'].min()}")
    print(f"   End: {df['timestamp'].max()}")

    print(f"\n💰 Price Range:")
    print(f"   Low: ${df['low'].min():.4f}")
    print(f"   High: ${df['high'].max():.4f}")

    print(f"\n📉 Last 5 Candles:")
    print(df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].tail())

    print(f"\n✅ Test PASSED - Hyperliquid data loader working!")
else:
    print(f"\n❌ FAILED - No data retrieved")
    print(f"\nℹ️  Note: If running on server with 403 error, try on Mac")

print("\n" + "=" * 70)
