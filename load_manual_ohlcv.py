#!/usr/bin/env python3
"""
Load manual OHLCV data from CSV and re-run analysis with REAL data

Use this when:
- Hyperliquid API is blocked (403)
- Symbol not available on Binance
- You have OHLCV data from another source

CSV Format expected:
timestamp,open,high,low,close,volume
2024-11-01 00:00:00,50.00,50.20,49.80,50.10,1000
2024-11-01 00:05:00,50.10,50.30,50.05,50.25,1200
...
"""

import pandas as pd
import sys
from pathlib import Path

def load_manual_ohlcv(csv_path, trader_address):
    """Load OHLCV from CSV and prepare for analysis"""

    print("=" * 70)
    print("📥 LOADING MANUAL OHLCV DATA")
    print("=" * 70)

    # Load CSV
    print(f"\n📂 Loading: {csv_path}")
    df = pd.read_csv(csv_path)

    print(f"✅ Loaded {len(df)} candles")

    # Validate columns
    required = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    missing = [col for col in required if col not in df.columns]

    if missing:
        print(f"❌ Missing columns: {missing}")
        print(f"   Required: {required}")
        print(f"   Found: {df.columns.tolist()}")
        return False

    # Parse timestamp
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Sort by time
    df = df.sort_values('timestamp').reset_index(drop=True)

    print(f"\n📊 Data range:")
    print(f"   From: {df['timestamp'].min()}")
    print(f"   To: {df['timestamp'].max()}")
    print(f"   Candles: {len(df)}")

    # Save to reports directory
    vault_id = trader_address[:10]
    output_dir = Path(f"reports/reverse_engineering/{vault_id}")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "manual_ohlcv.parquet"
    df.to_parquet(output_path, index=False)

    print(f"\n💾 Saved to: {output_path}")

    print("\n" + "=" * 70)
    print("✅ MANUAL OHLCV LOADED")
    print("=" * 70)

    print("\n💡 NEXT STEPS:")
    print("   1. The system will now use this REAL OHLCV data")
    print("   2. Re-run analysis:")
    print(f"      python3 reanalyze_with_manual_ohlcv.py {trader_address}")

    return True


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 load_manual_ohlcv.py <csv_path> <trader_address>")
        print("\nExample:")
        print("  python3 load_manual_ohlcv.py hyperliquid_hype_5m.csv 0x8bae...")
        print("\nCSV Format:")
        print("  timestamp,open,high,low,close,volume")
        print("  2024-11-01 00:00:00,50.00,50.20,49.80,50.10,1000")
        sys.exit(1)

    csv_path = sys.argv[1]
    trader = sys.argv[2]

    load_manual_ohlcv(csv_path, trader)
