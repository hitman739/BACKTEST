#!/usr/bin/env python3
"""
Simple TradingView Data Downloader
Downloads OHLCV data directly without complex dependencies

MANUAL METHOD - Most reliable:
1. Go to TradingView: https://www.tradingview.com/chart/
2. Search symbol (e.g., HYPERLIQUID:HYPE or BINANCE:BTCUSDT)
3. Set timeframe (5m, 15m, 1h, etc.)
4. Right click on chart → "Export chart data..."
5. Save CSV file
6. Run: python3 load_tradingview_simple.py <csv_file> <trader_address>
"""

import pandas as pd
import sys
from pathlib import Path

def load_tradingview_csv(csv_path, trader_address=None):
    """Load TradingView exported CSV"""

    print("=" * 70)
    print("📊 LOADING TRADINGVIEW DATA FROM CSV")
    print("=" * 70)

    print(f"\n📂 Loading: {csv_path}")

    try:
        # TradingView CSV format
        df = pd.read_csv(csv_path)

        print(f"✅ Loaded {len(df)} rows")
        print(f"\nColumns found: {df.columns.tolist()}")

        # TradingView export format usually has these columns:
        # time, open, high, low, close, Volume (or volume)

        # Standardize column names
        df.columns = [col.lower().strip() for col in df.columns]

        # Map common variations
        column_mapping = {
            'time': 'timestamp',
            'date': 'timestamp',
            'datetime': 'timestamp',
            'vol': 'volume',
        }

        for old, new in column_mapping.items():
            if old in df.columns and new not in df.columns:
                df.rename(columns={old: new}, inplace=True)

        # Verify required columns
        required = ['timestamp', 'open', 'high', 'low', 'close']
        missing = [col for col in required if col not in df.columns]

        if missing:
            print(f"\n❌ Missing columns: {missing}")
            print(f"   Found: {df.columns.tolist()}")
            print("\nTradingView CSV should have:")
            print("   time, open, high, low, close, volume")
            return None

        # Add volume if missing
        if 'volume' not in df.columns:
            print("⚠️  Volume column missing, setting to 0")
            df['volume'] = 0

        # Parse timestamp
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Select and order columns
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

        # Sort by time
        df = df.sort_values('timestamp').reset_index(drop=True)

        # Remove duplicates
        df = df.drop_duplicates(subset='timestamp')

        print(f"\n✅ Processed successfully")
        print(f"   Candles: {len(df)}")
        print(f"   From: {df['timestamp'].min()}")
        print(f"   To: {df['timestamp'].max()}")
        print(f"   Days: {(df['timestamp'].max() - df['timestamp'].min()).days}")

        # Show sample
        print(f"\n📊 Sample (first 3 rows):")
        print(df.head(3).to_string(index=False))

        # Detect symbol from filename
        symbol = Path(csv_path).stem.split('_')[0].upper()
        if len(symbol) > 10:
            symbol = 'UNKNOWN'

        # Save
        if trader_address:
            vault_id = trader_address[:10]
            output_dir = Path(f"reports/reverse_engineering/{vault_id}")
        else:
            output_dir = Path(f"data/tradingview/{symbol}")

        output_dir.mkdir(parents=True, exist_ok=True)

        # Save as parquet
        parquet_path = output_dir / "ohlcv_tradingview.parquet"
        df.to_parquet(parquet_path, index=False)
        print(f"\n💾 Saved to: {parquet_path}")

        # Also CSV for reference
        csv_out_path = output_dir / "ohlcv_tradingview.csv"
        df.to_csv(csv_out_path, index=False)
        print(f"💾 Also saved: {csv_out_path}")

        print("\n" + "=" * 70)
        print("✅ TRADINGVIEW DATA LOADED")
        print("=" * 70)

        if trader_address:
            print("\n💡 NEXT STEPS:")
            print(f"   1. Now re-run the analysis to use this REAL data")
            print(f"   2. The system will use precise OHLCV for indicators")
            print(f"\n   python3 reanalyze_with_indicators.py")

        return df

    except Exception as e:
        print(f"\n❌ Error loading CSV: {e}")
        return None


def print_instructions():
    """Print instructions for exporting from TradingView"""

    print("\n" + "=" * 70)
    print("📖 HOW TO EXPORT DATA FROM TRADINGVIEW")
    print("=" * 70)

    print("""
STEP 1: Go to TradingView
   → https://www.tradingview.com/chart/

STEP 2: Search for your symbol
   Examples:
   • HYPERLIQUID:HYPE (for Hyperliquid HYPE)
   • BINANCE:BTCUSDT (for Bitcoin)
   • BINANCE:SOLUSDT (for Solana)
   • BYBIT:BTCUSDT (alternative exchange)

STEP 3: Set timeframe
   • Click timeframe selector (top toolbar)
   • Choose: 1m, 5m, 15m, 1h, 4h, 1D

STEP 4: Set date range
   • Zoom out to see more history
   • Or use range selector (bottom right)

STEP 5: Export data
   • Right-click on chart
   • Click "Export chart data..."
   • Save CSV file (e.g., "HYPE_5m.csv")

STEP 6: Load the CSV
   python3 load_tradingview_simple.py HYPE_5m.csv

   Or with trader address:
   python3 load_tradingview_simple.py HYPE_5m.csv 0xTRADER_ADDRESS
""")

    print("=" * 70)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 load_tradingview_simple.py <csv_file> [trader_address]")
        print("\nExamples:")
        print("  python3 load_tradingview_simple.py HYPE_5m.csv")
        print("  python3 load_tradingview_simple.py HYPE_5m.csv 0x8bae3527...")

        print_instructions()
        sys.exit(1)

    csv_file = sys.argv[1]
    trader = sys.argv[2] if len(sys.argv) > 2 else None

    if not Path(csv_file).exists():
        print(f"❌ File not found: {csv_file}")
        print("\nMake sure you've exported data from TradingView first.")
        print_instructions()
        sys.exit(1)

    load_tradingview_csv(csv_file, trader)
