#!/usr/bin/env python3
"""
Download 1m data for Mean Reversion Strategy testing

Mean reversion strategies work best on lower timeframes (1m, 5m)
to catch quick reversions to mean.
"""

from engine.data_loader import load_data
from datetime import datetime, timedelta

# Pairs for mean reversion testing
PAIRS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
TIMEFRAME = '1m'
DAYS_BACK = 30  # Last 30 days

# Calculate date range
end_date = datetime.now()
start_date = end_date - timedelta(days=DAYS_BACK)

start_str = start_date.strftime('%Y-%m-%d')
end_str = end_date.strftime('%Y-%m-%d')

print(f"Downloading 1m data for Mean Reversion strategies")
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
        print(f"✓ {symbol}: {len(df)} candles downloaded ({len(df)/60/24:.1f} days)")
    except Exception as e:
        print(f"✗ {symbol}: Error - {e}")

print("\n" + "=" * 60)
print("Download complete!")
print("\nNow run: python3 compare_mean_reversion.py")
