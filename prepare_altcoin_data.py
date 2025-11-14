#!/usr/bin/env python3
"""
Download data for volatile altcoins testing

Downloads 1h data for AVAX, LINK, DOT, ADA, ATOM
"""

import time
from datetime import datetime, timedelta
from engine.data_loader import load_data


# Configuration
PAIRS = [
    'AVAXUSDT',   # Avalanche
    'LINKUSDT',   # Chainlink
    'DOTUSDT',    # Polkadot
    'ADAUSDT',    # Cardano
    'ATOMUSDT',   # Cosmos
]

TIMEFRAME = '1h'  # Changed from 15m - less noise, cleaner signals
DAYS_BACK = 60


def download_pair_data(symbol, max_retries=3):
    """Download data for a single pair with retry logic"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=DAYS_BACK)

    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')

    for attempt in range(max_retries):
        try:
            print(f"📥 Downloading {symbol} {TIMEFRAME} data...")
            print(f"   Period: {start_str} to {end_str}")

            df = load_data(
                symbol=symbol,
                timeframe=TIMEFRAME,
                start_date=start_str,
                end_date=end_str,
                use_cache=False  # Force fresh download
            )

            print(f"✅ {symbol}: {len(df)} candles downloaded")
            return {'success': True, 'candles': len(df)}

        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                print(f"⚠️  Attempt {attempt + 1} failed: {e}")
                print(f"   Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"❌ {symbol}: Failed after {max_retries} attempts")
                return {'success': False, 'error': str(e)}


def main():
    print("=" * 80)
    print("📥 DOWNLOADING VOLATILE ALTCOIN DATA")
    print("=" * 80)
    print()
    print(f"Pairs: {', '.join(PAIRS)}")
    print(f"Timeframe: {TIMEFRAME}")
    print(f"Days back: {DAYS_BACK}")
    print()
    print("=" * 80)
    print()

    results = []
    successful = 0
    failed = 0

    for symbol in PAIRS:
        result = download_pair_data(symbol)
        results.append({'symbol': symbol, **result})

        if result['success']:
            successful += 1
        else:
            failed += 1

        print()

    # Summary
    print("=" * 80)
    print("📊 DOWNLOAD SUMMARY")
    print("=" * 80)
    print()

    for result in results:
        if result['success']:
            print(f"✅ {result['symbol']:12s}: {result['candles']} candles")
        else:
            print(f"❌ {result['symbol']:12s}: {result['error']}")

    print()
    print(f"Successful: {successful}/{len(PAIRS)}")
    print(f"Failed:     {failed}/{len(PAIRS)}")
    print()

    if successful == len(PAIRS):
        print("✅ All data downloaded successfully!")
        print()
        print("Next step:")
        print("  python3 compare_tetr_altcoins.py")
    else:
        print("⚠️  Some downloads failed")
        print("   Check your internet connection and try again")

    print()


if __name__ == '__main__':
    main()
