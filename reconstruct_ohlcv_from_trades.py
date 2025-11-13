#!/usr/bin/env python3
"""
Reconstruct OHLCV from vault trades and re-run analysis with indicators
"""

import pandas as pd
import numpy as np
from pathlib import Path

print("=" * 70)
print("🔧 RECONSTRUCTING OHLCV FROM VAULT TRADES")
print("=" * 70)

# Load trades
vault_id = "0x9b55c8c9"
trades_path = f"reports/reverse_engineering/{vault_id}/vault_data.parquet"

if not Path(trades_path).exists():
    # Try alternative location
    from reverse_engineering.data.vault_data_interface import VaultDataInterface

    print("\n📥 Loading trades from vault...")
    interface = VaultDataInterface("0x9b55c8c948f988bcbe404cd070fc9ffffab8d31b")
    trades_df = interface.run(force_refresh=False)
else:
    print(f"\n📂 Loading trades from {trades_path}...")
    trades_df = pd.read_parquet(trades_path)

print(f"✅ Loaded {len(trades_df)} trades")
print(f"   Period: {trades_df['timestamp'].min()} to {trades_df['timestamp'].max()}")

# Reconstruct 5-minute OHLCV candles from trades
print("\n🔧 Reconstructing 5-minute OHLCV candles...")

trades_df = trades_df.sort_values('timestamp')
trades_df.set_index('timestamp', inplace=True)

# Resample to 5-minute candles
ohlcv = pd.DataFrame()
ohlcv['open'] = trades_df['price'].resample('5min').first()
ohlcv['high'] = trades_df['price'].resample('5min').max()
ohlcv['low'] = trades_df['price'].resample('5min').min()
ohlcv['close'] = trades_df['price'].resample('5min').last()
ohlcv['volume'] = trades_df['size'].resample('5min').sum()

# Forward fill missing candles
ohlcv = ohlcv.fillna(method='ffill')

# Remove rows where all are NaN (before first trade)
ohlcv = ohlcv.dropna(subset=['close'])

print(f"✅ Reconstructed {len(ohlcv)} candles")

# Calculate technical indicators
print("\n📊 Calculating technical indicators...")

# EMAs
ohlcv['ema_20'] = ohlcv['close'].ewm(span=20, adjust=False).mean()
ohlcv['ema_50'] = ohlcv['close'].ewm(span=50, adjust=False).mean()
ohlcv['ema_200'] = ohlcv['close'].ewm(span=200, adjust=False).mean()

# RSI
delta = ohlcv['close'].diff()
gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
rs = gain / loss
ohlcv['rsi'] = 100 - (100 / (1 + rs))

# ATR
high_low = ohlcv['high'] - ohlcv['low']
high_close = abs(ohlcv['high'] - ohlcv['close'].shift())
low_close = abs(ohlcv['low'] - ohlcv['close'].shift())
true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
ohlcv['atr'] = true_range.rolling(window=14).mean()

# Bollinger Bands
bb_period = 20
ohlcv['bb_middle'] = ohlcv['close'].rolling(window=bb_period).mean()
bb_std = ohlcv['close'].rolling(window=bb_period).std()
ohlcv['bb_upper'] = ohlcv['bb_middle'] + (2 * bb_std)
ohlcv['bb_lower'] = ohlcv['bb_middle'] - (2 * bb_std)

# VWAP (approximate - daily)
ohlcv['date'] = ohlcv.index.date
typical_price = (ohlcv['high'] + ohlcv['low'] + ohlcv['close']) / 3
ohlcv['vwap'] = (typical_price * ohlcv['volume']).groupby(ohlcv['date']).cumsum() / ohlcv['volume'].groupby(ohlcv['date']).cumsum()

print("✅ Calculated indicators:")
print("   - EMA 20, 50, 200")
print("   - RSI (14)")
print("   - ATR (14)")
print("   - Bollinger Bands (20, 2)")
print("   - VWAP (daily)")

# Save reconstructed OHLCV with indicators
output_dir = Path(f"reports/reverse_engineering/{vault_id}")
output_dir.mkdir(parents=True, exist_ok=True)

ohlcv_path = output_dir / "reconstructed_ohlcv.parquet"
ohlcv.reset_index().to_parquet(ohlcv_path, index=False)
print(f"\n💾 Saved to: {ohlcv_path}")

# Show sample
print("\n📈 Sample candles with indicators:")
print(ohlcv[['open', 'high', 'low', 'close', 'volume', 'ema_20', 'ema_50', 'rsi', 'atr']].tail(10))

# Now align positions with this OHLCV
print("\n" + "=" * 70)
print("🔧 ALIGNING POSITIONS WITH INDICATORS")
print("=" * 70)

positions_path = output_dir / "positions.parquet"
if positions_path.exists():
    positions = pd.read_parquet(positions_path)
    print(f"\n📂 Loaded {len(positions)} positions")

    # Reset index of ohlcv for merging
    ohlcv_reset = ohlcv.reset_index()
    ohlcv_reset.rename(columns={'timestamp': 'candle_time'}, inplace=True)

    # For each position, find nearest candle at entry and exit
    aligned_positions = []

    for idx, pos in positions.iterrows():
        entry_time = pos['entry_time']
        exit_time = pos['exit_time']

        # Find nearest candles
        entry_candle = ohlcv_reset.iloc[(ohlcv_reset['candle_time'] - entry_time).abs().argsort()[:1]]
        exit_candle = ohlcv_reset.iloc[(ohlcv_reset['candle_time'] - exit_time).abs().argsort()[:1]]

        if not entry_candle.empty and not exit_candle.empty:
            # Add entry indicators
            pos['entry_close'] = entry_candle['close'].values[0]
            pos['entry_ema_20'] = entry_candle['ema_20'].values[0]
            pos['entry_ema_50'] = entry_candle['ema_50'].values[0]
            pos['entry_ema_200'] = entry_candle['ema_200'].values[0]
            pos['entry_rsi'] = entry_candle['rsi'].values[0]
            pos['entry_atr'] = entry_candle['atr'].values[0]
            pos['entry_bb_upper'] = entry_candle['bb_upper'].values[0]
            pos['entry_bb_lower'] = entry_candle['bb_lower'].values[0]
            pos['entry_bb_middle'] = entry_candle['bb_middle'].values[0]
            pos['entry_vwap'] = entry_candle['vwap'].values[0]
            pos['entry_volume'] = entry_candle['volume'].values[0]

            # Add exit indicators
            pos['exit_close'] = exit_candle['close'].values[0]
            pos['exit_rsi'] = exit_candle['rsi'].values[0]
            pos['exit_atr'] = exit_candle['atr'].values[0]

            aligned_positions.append(pos)

    aligned_df = pd.DataFrame(aligned_positions)

    print(f"✅ Aligned {len(aligned_df)} positions with indicators")

    # Save aligned positions
    aligned_path = output_dir / "positions_with_indicators.parquet"
    aligned_df.to_parquet(aligned_path, index=False)
    print(f"💾 Saved to: {aligned_path}")

    # Show sample
    indicator_cols = [col for col in aligned_df.columns if 'entry_' in col and any(x in col for x in ['ema', 'rsi', 'atr', 'bb', 'vwap'])]
    print(f"\n📊 Sample position with indicators:")
    print(aligned_df[['entry_time', 'side'] + indicator_cols[:5]].head(3))

    print("\n" + "=" * 70)
    print("✅ RECONSTRUCTION COMPLETE!")
    print("=" * 70)
    print("\nNext: Re-run analysis with indicators")
    print("Command:")
    print(f"  python3 reanalyze_with_indicators.py")

else:
    print(f"\n❌ Positions file not found: {positions_path}")
    print("   Run the main analysis first")
