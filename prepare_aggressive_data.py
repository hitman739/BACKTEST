#!/usr/bin/env python3
"""
Download data for aggressive strategy testing

Downloads both 5m and 15m data for volatile altcoin pairs.
These are the most liquid and volatile pairs for high-frequency trading.
"""

import time
from datetime import datetime, timedelta
from engine.data_loader import load_data


# Configuration
PAIRS = [
    'AVAXUSDT',    # Avalanche - proven performer
    'DOTUSDT',     # Polkadot - good in 1h
    'NEARUSDT',    # Near Protocol - very volatile
    'RNDRUSDT',    # Render - extremely volatile
    'PENDLEUSDT',  # Pendle - high volatility
]

TIMEFRAMES = ['5m', '15m']  # Scalper needs 5m, others need 15m
DAYS_BACK = 60


def download_data(symbol, timeframe, max_retries=3):
    """Download data for a single pair/timeframe with retry logic"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=DAYS_BACK)

    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')

    for attempt in range(max_retries):
        try:
            print(f"📥 Downloading {symbol} {timeframe}... ", end='', flush=True)

            df = load_data(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_str,
                end_date=end_str,
                use_cache=False  # Force fresh download
            )

            print(f"✅ {len(df)} candles")
            return {'success': True, 'candles': len(df)}

        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"⚠️  Retry in {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"❌ Failed: {str(e)[:50]}")
                return {'success': False, 'error': str(e)}


def main():
    print("=" * 80)
    print("📥 DOWNLOADING AGGRESSIVE STRATEGY DATA")
    print("=" * 80)
    print()
    print(f"Pairs: {', '.join(PAIRS)}")
    print(f"Timeframes: {', '.join(TIMEFRAMES)}")
    print(f"Period: Last {DAYS_BACK} days")
    print()
    print("Why these pairs?")
    print("  ✅ High volatility (good for scalping & breakouts)")
    print("  ✅ Good liquidity (low slippage)")
    print("  ✅ AVAX & DOT proven performers in previous tests")
    print()
    print("=" * 80)
    print()

    total_downloads = len(PAIRS) * len(TIMEFRAMES)
    successful = 0
    failed = 0

    for timeframe in TIMEFRAMES:
        print(f"\n📊 {timeframe} Timeframe")
        print("-" * 80)

        for symbol in PAIRS:
            result = download_data(symbol, timeframe)

            if result['success']:
                successful += 1
            else:
                failed += 1

            time.sleep(0.5)  # Be nice to API

    # Summary
    print()
    print("=" * 80)
    print("📊 DOWNLOAD SUMMARY")
    print("=" * 80)
    print()
    print(f"Total downloads: {total_downloads}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print()

    if successful == total_downloads:
        print("✅ All data downloaded successfully!")
        print()
        print("Next step:")
        print("  python3 compare_aggressive_strategies.py")
        print()
        print("This will test:")
        print("  - Scalper Pro (5m)")
        print("  - Momentum Hunter (15m)")
        print("  - Hybrid Alpha (15m)")
        print()
        print("Target: 3-5% weekly returns")
    elif successful > 0:
        print(f"⚠️  Partial success ({successful}/{total_downloads})")
        print("   You can still run comparison with downloaded data")
    else:
        print("❌ All downloads failed")
        print("   Check internet connection and try again")

    print()


if __name__ == '__main__':
    main()
