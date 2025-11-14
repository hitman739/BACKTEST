#!/usr/bin/env python3
"""
Prepare Data for Backtesting

Downloads data from Binance for multiple pairs
Designed for Mac with robust error handling
"""

import sys
from datetime import datetime, timedelta
from engine.data_loader import load_data
import time

# Configuration
PAIRS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
TIMEFRAME = '15m'
DAYS_BACK = 60

# Calculate dates
end_date = datetime.now()
start_date = end_date - timedelta(days=DAYS_BACK)
start_str = start_date.strftime('%Y-%m-%d')
end_str = end_date.strftime('%Y-%m-%d')

print("="*80)
print("📥 DATA PREPARATION FOR BACKTESTING")
print("="*80)
print(f"\nConfiguration:")
print(f"  Pairs:      {', '.join(PAIRS)}")
print(f"  Timeframe:  {TIMEFRAME}")
print(f"  Period:     {start_str} to {end_str} ({DAYS_BACK} days)")
print(f"  Data dir:   ./data/binance/")
print("\n" + "="*80)

def download_pair_data(symbol, max_retries=3):
    """Download data for a single pair with retry logic"""

    print(f"\n📊 Downloading {symbol} {TIMEFRAME}...")
    print(f"   Period: {start_str} to {end_str}")

    for attempt in range(max_retries):
        try:
            print(f"   Attempt {attempt + 1}/{max_retries}...", end=' ')

            df = load_data(
                symbol=symbol,
                timeframe=TIMEFRAME,
                start_date=start_str,
                end_date=end_str,
                data_dir='./data/binance',
                use_cache=False  # Force fresh download
            )

            print(f"✅ Success!")
            print(f"   Downloaded {len(df)} candles")
            print(f"   Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")

            return {
                'success': True,
                'symbol': symbol,
                'candles': len(df),
                'start': df['timestamp'].min(),
                'end': df['timestamp'].max()
            }

        except Exception as e:
            print(f"❌ Failed")
            print(f"   Error: {e}")

            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"   Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"   ❌ All retries failed for {symbol}")
                return {
                    'success': False,
                    'symbol': symbol,
                    'error': str(e)
                }

def main():
    """Download data for all pairs"""

    results = []

    for i, symbol in enumerate(PAIRS):
        result = download_pair_data(symbol)
        results.append(result)

        # Small pause between pairs to avoid rate limiting
        if i < len(PAIRS) - 1:
            print(f"\n   Waiting 2 seconds before next pair...")
            time.sleep(2)

    # Summary
    print("\n" + "="*80)
    print("📊 DOWNLOAD SUMMARY")
    print("="*80)

    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]

    print(f"\nSuccessful: {len(successful)}/{len(PAIRS)}")
    print(f"Failed:     {len(failed)}/{len(PAIRS)}")

    if successful:
        print("\n✅ Successfully downloaded:")
        for r in successful:
            print(f"   {r['symbol']}: {r['candles']} candles")
            print(f"      Range: {r['start']} to {r['end']}")

    if failed:
        print("\n❌ Failed to download:")
        for r in failed:
            print(f"   {r['symbol']}: {r['error']}")

        print("\n💡 Troubleshooting:")
        print("   1. Check internet connection")
        print("   2. Verify Binance API is accessible from your location")
        print("   3. Try using a VPN if Binance is blocked")
        print("   4. Check if data already exists in ./data/binance/")

    print("\n" + "="*80)

    if len(successful) == len(PAIRS):
        print("✅ ALL DATA READY!")
        print("\nYou can now run:")
        print("   python3 backtest_multi_pairs.py")
    elif len(successful) > 0:
        print(f"⚠️  PARTIAL SUCCESS ({len(successful)}/{len(PAIRS)} pairs)")
        print("\nYou can run backtest on successful pairs:")
        print("   python3 backtest_multi_pairs.py")
    else:
        print("❌ NO DATA DOWNLOADED")
        print("\nPlease fix connectivity issues and try again.")

    print("="*80)

if __name__ == "__main__":
    main()
