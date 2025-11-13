#!/usr/bin/env python3
"""
Download real SOLUSDT data from Binance for backtesting
Uses the DataLoader to fetch and cache real market data
"""

import asyncio
from datetime import datetime, timedelta
from engine.data_loader import BinanceDataLoader


async def download_data():
    """Download real SOLUSDT data from Binance"""

    loader = BinanceDataLoader(data_dir='./data/binance')

    # Calculate dates
    end_date = datetime(2025, 11, 13)
    start_date = end_date - timedelta(days=60)

    print("=" * 70)
    print("📥 DOWNLOADING REAL BINANCE DATA")
    print("=" * 70)
    print(f"\nSymbol: SOLUSDT")
    print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"Duration: 60 days")
    print()

    # Download 1m data
    print("Downloading 1m timeframe...")
    data_1m = await loader.get_data(
        symbol='SOLUSDT',
        timeframe='1m',
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d'),
        use_cache=False  # Force fresh download
    )
    print(f"✅ Downloaded {len(data_1m)} candles for 1m")
    print(f"   Price range: ${data_1m['close'].min():.2f} - ${data_1m['close'].max():.2f}")
    print(f"   Date range: {data_1m['timestamp'].min()} to {data_1m['timestamp'].max()}")
    print()

    # Download 5m data
    print("Downloading 5m timeframe...")
    data_5m = await loader.get_data(
        symbol='SOLUSDT',
        timeframe='5m',
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d'),
        use_cache=False  # Force fresh download
    )
    print(f"✅ Downloaded {len(data_5m)} candles for 5m")
    print(f"   Price range: ${data_5m['close'].min():.2f} - ${data_5m['close'].max():.2f}")
    print(f"   Date range: {data_5m['timestamp'].min()} to {data_5m['timestamp'].max()}")
    print()

    # Download 15m data
    print("Downloading 15m timeframe...")
    data_15m = await loader.get_data(
        symbol='SOLUSDT',
        timeframe='15m',
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d'),
        use_cache=False  # Force fresh download
    )
    print(f"✅ Downloaded {len(data_15m)} candles for 15m")
    print(f"   Price range: ${data_15m['close'].min():.2f} - ${data_15m['close'].max():.2f}")
    print(f"   Date range: {data_15m['timestamp'].min()} to {data_15m['timestamp'].max()}")
    print()

    print("=" * 70)
    print("✅ ALL DATA DOWNLOADED AND CACHED")
    print("=" * 70)
    print("\nNow you can run backtests with real data:")
    print("  python3 test_vrr_ultra_real_1m.py")
    print("  python3 test_vrr_ultra_real_5m.py")
    print("  python3 test_vrr_ultra_real_15m.py")


if __name__ == '__main__':
    print("\n🌐 Connecting to Binance API...")
    print("⏳ This may take a few minutes for 60 days of data...\n")

    try:
        asyncio.run(download_data())
    except Exception as e:
        print(f"\n❌ Error downloading data: {e}")
        import traceback
        traceback.print_exc()
        print("\n💡 Make sure you have internet connection")
        print("💡 Binance API may have rate limits - try again in a minute")
