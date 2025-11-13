#!/usr/bin/env python3
"""
Load OHLCV data from TradingView

TradingView has accurate data for most symbols including Hyperliquid.

Installation:
    pip install tvdatafeed

Usage:
    python3 load_tradingview_data.py HYPE 5m 30
    python3 load_tradingview_data.py BTC 15m 60
"""

import sys
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

def load_from_tradingview(symbol, timeframe, days_back=30):
    """Load OHLCV from TradingView"""

    print("=" * 70)
    print("📊 LOADING DATA FROM TRADINGVIEW")
    print("=" * 70)

    try:
        from tvDatafeed import TvDatafeed, Interval
    except ImportError:
        print("\n❌ ERROR: tvdatafeed not installed")
        print("\nInstall it:")
        print("  pip install tvdatafeed")
        print("\nOr:")
        print("  pip3 install tvdatafeed")
        return None

    print(f"\n📈 Symbol: {symbol}")
    print(f"⏱️  Timeframe: {timeframe}")
    print(f"📅 Days back: {days_back}")

    # Initialize TradingView datafeed
    tv = TvDatafeed()

    # Map timeframe to TradingView interval
    interval_map = {
        '1m': Interval.in_1_minute,
        '5m': Interval.in_5_minute,
        '15m': Interval.in_15_minute,
        '30m': Interval.in_30_minute,
        '1h': Interval.in_1_hour,
        '2h': Interval.in_2_hour,
        '4h': Interval.in_4_hour,
        '1d': Interval.in_daily,
    }

    if timeframe not in interval_map:
        print(f"❌ Unsupported timeframe: {timeframe}")
        print(f"   Available: {list(interval_map.keys())}")
        return None

    interval = interval_map[timeframe]

    # Calculate bars needed
    bars = int(days_back * 24 * 60 / {
        '1m': 1,
        '5m': 5,
        '15m': 15,
        '30m': 30,
        '1h': 60,
        '2h': 120,
        '4h': 240,
        '1d': 1440
    }[timeframe])

    print(f"\n📥 Fetching {bars} bars from TradingView...")

    # Try different exchanges for the symbol
    exchanges = ['HYPERLIQUID', 'BINANCE', 'BYBIT', 'OKX', 'COINBASE']

    df = None
    for exchange in exchanges:
        try:
            print(f"\n   Trying {exchange}:{symbol}...")
            df = tv.get_hist(
                symbol=symbol,
                exchange=exchange,
                interval=interval,
                n_bars=bars
            )

            if df is not None and not df.empty:
                print(f"   ✅ Success! Got {len(df)} bars from {exchange}")
                break
        except Exception as e:
            print(f"   ❌ Failed: {str(e)[:50]}")
            continue

    if df is None or df.empty:
        print(f"\n❌ Could not fetch data for {symbol}")
        print("   Tried exchanges:", exchanges)
        return None

    # Process data
    df = df.reset_index()
    df.columns = [col.lower() for col in df.columns]

    # Rename columns to match our format
    if 'datetime' in df.columns:
        df.rename(columns={'datetime': 'timestamp'}, inplace=True)
    elif 'time' in df.columns:
        df.rename(columns={'time': 'timestamp'}, inplace=True)

    # Ensure we have required columns
    required = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    for col in required:
        if col not in df.columns:
            print(f"❌ Missing column: {col}")
            return None

    df = df[required]
    df = df.sort_values('timestamp').reset_index(drop=True)

    print(f"\n✅ Data loaded successfully")
    print(f"   Bars: {len(df)}")
    print(f"   From: {df['timestamp'].min()}")
    print(f"   To: {df['timestamp'].max()}")

    # Show sample
    print(f"\n📊 Sample data:")
    print(df.head(3))

    return df


def save_for_analysis(df, symbol, output_dir=None):
    """Save data for vault analysis"""

    if output_dir is None:
        output_dir = Path(f"data/tradingview/{symbol}")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save as parquet
    output_path = output_dir / "ohlcv.parquet"
    df.to_parquet(output_path, index=False)

    print(f"\n💾 Saved to: {output_path}")

    # Also save as CSV for manual inspection
    csv_path = output_dir / "ohlcv.csv"
    df.to_csv(csv_path, index=False)
    print(f"💾 Also saved as CSV: {csv_path}")

    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 load_tradingview_data.py <symbol> <timeframe> [days_back]")
        print("\nExamples:")
        print("  python3 load_tradingview_data.py HYPE 5m 30")
        print("  python3 load_tradingview_data.py BTC 15m 60")
        print("  python3 load_tradingview_data.py SOL 1h 90")
        print("\nTimeframes: 1m, 5m, 15m, 30m, 1h, 2h, 4h, 1d")
        sys.exit(1)

    symbol = sys.argv[1]
    timeframe = sys.argv[2]
    days_back = int(sys.argv[3]) if len(sys.argv) > 3 else 30

    # Load data
    df = load_from_tradingview(symbol, timeframe, days_back)

    if df is not None:
        # Save
        save_for_analysis(df, symbol)

        print("\n" + "=" * 70)
        print("✅ READY FOR ANALYSIS")
        print("=" * 70)
        print("\nNext steps:")
        print(f"1. You now have REAL OHLCV data for {symbol}")
        print(f"2. Use this data for precise indicator calculations")
        print(f"3. Data location: data/tradingview/{symbol}/ohlcv.parquet")
