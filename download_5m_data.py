#!/usr/bin/env python3
"""
Download 5m data for Scalper Pro strategy testing
"""

from engine.data_loader import load_data
from datetime import datetime, timedelta

# Pairs used in aggressive strategy testing
PAIRS = ['AVAXUSDT', 'DOTUSDT', 'NEARUSDT', 'RNDRUSDT', 'PENDLEUSDT']
TIMEFRAME = '5m'
DAYS_BACK = 60

# Calculate date range
end_date = datetime.now()
start_date = end_date - timedelta(days=DAYS_BACK)

start_str = start_date.strftime('%Y-%m-%d')
end_str = end_date.strftime('%Y-%m-%d')

print(f"Downloading 5m data for Scalper Pro strategy")
print(f"Period: {start_str} to {end_str}")
print(f"Pairs: {', '.join(PAIRS)}")
print("=" * 60)

for symbol in PAIRS:
    print(f"\nDownloading {symbol} {TIMEFRAME}...")
    try:
        df = load_data(
            symbol=symbol,
            timeframe=TIMEFRAME,
            start_date=start_str,
            end_date=end_str,
            data_dir='./data/binance',
            use_cache=False  # Force fresh download
        )
        print(f"✓ {symbol}: {len(df)} candles downloaded")
    except Exception as e:
        print(f"✗ {symbol}: Error - {e}")

print("\n" + "=" * 60)
print("Download complete!")
print("\nNow run: python3 compare_aggressive_strategies.py")
