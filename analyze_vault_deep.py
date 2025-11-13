#!/usr/bin/env python3
"""
Deep Vault Analysis
Analyzes the HYPE vault data in detail to understand the strategy
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json

# Load the vault data
vault_data_path = Path("reports/reverse_engineering/0x9b55c8c9/vault_data.parquet")
features_path = Path("reports/reverse_engineering/0x9b55c8c9/features.parquet")

print("=" * 70)
print("🔍 DEEP VAULT ANALYSIS - HYPE VAULT")
print("=" * 70)

# Load data
if vault_data_path.exists():
    trades_df = pd.read_parquet(vault_data_path)
    print(f"\n✅ Loaded {len(trades_df)} trades")
else:
    print("\n❌ Vault data not found")
    exit()

if features_path.exists():
    positions_df = pd.read_parquet(features_path)
    print(f"✅ Loaded {len(positions_df)} positions")
else:
    print("⚠️  Features file not found, using trades only")
    positions_df = None

# ============================================================================
# ANALYSIS 1: TIMING PATTERNS
# ============================================================================

print("\n" + "=" * 70)
print("⏰ TIMING ANALYSIS")
print("=" * 70)

trades_df['hour'] = trades_df['timestamp'].dt.hour
trades_df['minute'] = trades_df['timestamp'].dt.minute
trades_df['day_of_week'] = trades_df['timestamp'].dt.day_name()

print("\n📊 Hourly Distribution:")
hourly = trades_df.groupby('hour').size().sort_values(ascending=False)
for hour, count in hourly.head(10).items():
    pct = count / len(trades_df) * 100
    bar = "█" * int(pct / 2)
    print(f"  {hour:02d}h: {count:3d} trades ({pct:5.1f}%) {bar}")

print("\n📊 Most Active Minutes (within hours):")
minute_dist = trades_df.groupby('minute').size().sort_values(ascending=False)
for minute, count in minute_dist.head(10).items():
    pct = count / len(trades_df) * 100
    print(f"  Minute {minute:02d}: {count:3d} trades ({pct:4.1f}%)")

print("\n📊 Day of Week:")
day_dist = trades_df['day_of_week'].value_counts()
for day, count in day_dist.items():
    pct = count / len(trades_df) * 100
    print(f"  {day:9s}: {count:3d} trades ({pct:5.1f}%)")

# ============================================================================
# ANALYSIS 2: TRADE FREQUENCY PATTERNS
# ============================================================================

print("\n" + "=" * 70)
print("⚡ TRADE FREQUENCY ANALYSIS")
print("=" * 70)

trades_df_sorted = trades_df.sort_values('timestamp')
trades_df_sorted['time_diff'] = trades_df_sorted['timestamp'].diff().dt.total_seconds()

print(f"\n📊 Time Between Trades:")
print(f"  • Mean: {trades_df_sorted['time_diff'].mean():.1f} seconds")
print(f"  • Median: {trades_df_sorted['time_diff'].median():.1f} seconds")
print(f"  • Min: {trades_df_sorted['time_diff'].min():.1f} seconds")
print(f"  • Max: {trades_df_sorted['time_diff'].max():.1f} seconds")

# Categorize frequency
freq_bins = [0, 10, 30, 60, 300, 99999]
freq_labels = ['<10s', '10-30s', '30-60s', '1-5min', '>5min']
trades_df_sorted['freq_category'] = pd.cut(
    trades_df_sorted['time_diff'],
    bins=freq_bins,
    labels=freq_labels
)

print(f"\n📊 Trade Frequency Distribution:")
freq_dist = trades_df_sorted['freq_category'].value_counts()
for cat, count in freq_dist.items():
    pct = count / len(freq_dist) * 100
    print(f"  {cat:8s}: {count:3d} trades ({pct:5.1f}%)")

# ============================================================================
# ANALYSIS 3: POSITION SIZING PATTERNS
# ============================================================================

print("\n" + "=" * 70)
print("💰 POSITION SIZING ANALYSIS")
print("=" * 70)

print(f"\n📊 Size Statistics:")
print(f"  • Mean: {trades_df['size'].mean():.4f}")
print(f"  • Median: {trades_df['size'].median():.4f}")
print(f"  • Min: {trades_df['size'].min():.4f}")
print(f"  • Max: {trades_df['size'].max():.4f}")
print(f"  • Std Dev: {trades_df['size'].std():.4f}")
print(f"  • CV (Coefficient of Variation): {trades_df['size'].std() / trades_df['size'].mean():.2f}")

# Size distribution
size_percentiles = [10, 25, 50, 75, 90]
print(f"\n📊 Size Percentiles:")
for p in size_percentiles:
    val = trades_df['size'].quantile(p/100)
    print(f"  • {p}th: {val:.4f}")

# Correlation between size and time
if 'time_diff' in trades_df_sorted.columns:
    corr = trades_df_sorted[['size', 'time_diff']].corr().iloc[0, 1]
    print(f"\n🔗 Size vs Time Correlation: {corr:.3f}")
    if abs(corr) > 0.3:
        print(f"   → {'STRONG' if abs(corr) > 0.5 else 'MODERATE'} correlation")

# ============================================================================
# ANALYSIS 4: DIRECTIONAL PATTERNS
# ============================================================================

print("\n" + "=" * 70)
print("📈 DIRECTIONAL ANALYSIS")
print("=" * 70)

direction_counts = trades_df['side'].value_counts()
print(f"\n📊 Overall Direction:")
for side, count in direction_counts.items():
    pct = count / len(trades_df) * 100
    print(f"  • {side.upper():5s}: {count:3d} trades ({pct:5.1f}%)")

# Direction by hour
print(f"\n📊 Direction by Hour (top 5 hours):")
top_hours = hourly.head(5).index
for hour in top_hours:
    hour_trades = trades_df[trades_df['hour'] == hour]
    long_count = (hour_trades['side'] == 'long').sum()
    short_count = (hour_trades['side'] == 'short').sum()
    long_pct = long_count / len(hour_trades) * 100
    print(f"  {hour:02d}h: Long {long_pct:5.1f}% | Short {100-long_pct:5.1f}%")

# ============================================================================
# ANALYSIS 5: PRICE ACTION
# ============================================================================

print("\n" + "=" * 70)
print("💹 PRICE ACTION ANALYSIS")
print("=" * 70)

print(f"\n📊 Price Range:")
print(f"  • Min: ${trades_df['price'].min():.2f}")
print(f"  • Max: ${trades_df['price'].max():.2f}")
print(f"  • Range: ${trades_df['price'].max() - trades_df['price'].min():.2f}")
print(f"  • Mean: ${trades_df['price'].mean():.2f}")

# Price movement
trades_df_sorted['price_change'] = trades_df_sorted['price'].diff()
trades_df_sorted['price_change_pct'] = trades_df_sorted['price'].pct_change() * 100

print(f"\n📊 Price Movement Between Trades:")
print(f"  • Mean change: {trades_df_sorted['price_change_pct'].mean():.3f}%")
print(f"  • Std Dev: {trades_df_sorted['price_change_pct'].std():.3f}%")

# ============================================================================
# ANALYSIS 6: CLOSED PNL PATTERNS
# ============================================================================

print("\n" + "=" * 70)
print("💵 PNL ANALYSIS")
print("=" * 70)

closed_trades = trades_df[trades_df['closed_pnl'] != 0]
print(f"\n📊 Closed Trades: {len(closed_trades)} / {len(trades_df)}")

if len(closed_trades) > 0:
    winners = closed_trades[closed_trades['closed_pnl'] > 0]
    losers = closed_trades[closed_trades['closed_pnl'] < 0]

    print(f"\n💰 Winners: {len(winners)} ({len(winners)/len(closed_trades)*100:.1f}%)")
    print(f"  • Total: ${winners['closed_pnl'].sum():,.2f}")
    print(f"  • Mean: ${winners['closed_pnl'].mean():.2f}")
    print(f"  • Median: ${winners['closed_pnl'].median():.2f}")
    print(f"  • Best: ${winners['closed_pnl'].max():.2f}")

    if len(losers) > 0:
        print(f"\n❌ Losers: {len(losers)} ({len(losers)/len(closed_trades)*100:.1f}%)")
        print(f"  • Total: ${losers['closed_pnl'].sum():,.2f}")
        print(f"  • Mean: ${losers['closed_pnl'].mean():.2f}")
        print(f"  • Worst: ${losers['closed_pnl'].min():.2f}")

# ============================================================================
# ANALYSIS 7: POSITIONS ANALYSIS (if available)
# ============================================================================

if positions_df is not None and len(positions_df) > 0:
    print("\n" + "=" * 70)
    print("🎯 POSITION-LEVEL ANALYSIS")
    print("=" * 70)

    print(f"\n📊 Holding Times:")
    print(f"  • Mean: {positions_df['holding_time_mins'].mean():.1f} minutes")
    print(f"  • Median: {positions_df['holding_time_mins'].median():.1f} minutes")
    print(f"  • Min: {positions_df['holding_time_mins'].min():.1f} minutes")
    print(f"  • Max: {positions_df['holding_time_mins'].max():.1f} minutes")

    # Categorize positions
    hold_bins = [0, 5, 15, 60, 240, 99999]
    hold_labels = ['<5min', '5-15min', '15-60min', '1-4h', '>4h']
    positions_df['hold_category'] = pd.cut(
        positions_df['holding_time_mins'],
        bins=hold_bins,
        labels=hold_labels
    )

    print(f"\n📊 Holding Time Distribution:")
    hold_dist = positions_df['hold_category'].value_counts()
    for cat, count in hold_dist.items():
        pct = count / len(positions_df) * 100
        print(f"  {cat:8s}: {count:3d} positions ({pct:5.1f}%)")

# ============================================================================
# SUMMARY & INSIGHTS
# ============================================================================

print("\n" + "=" * 70)
print("💡 KEY INSIGHTS & STRATEGY HYPOTHESIS")
print("=" * 70)

# Calculate key metrics
avg_time_between = trades_df_sorted['time_diff'].median()
trades_per_day = len(trades_df) / ((trades_df['timestamp'].max() - trades_df['timestamp'].min()).total_seconds() / 86400)
size_cv = trades_df['size'].std() / trades_df['size'].mean()

print(f"\n🎯 VAULT PROFILE:")
print(f"  • Type: {'HIGH FREQUENCY' if avg_time_between < 60 else 'SCALPING' if avg_time_between < 300 else 'INTRADAY'}")
print(f"  • Frequency: {trades_per_day:.1f} trades/day")
print(f"  • Avg time between trades: {avg_time_between:.1f} seconds")
print(f"  • Position sizing: {'ADAPTIVE' if size_cv > 0.5 else 'SEMI-FIXED'} (CV: {size_cv:.2f})")
print(f"  • Directional bias: {direction_counts.index[0].upper()} ({direction_counts.iloc[0]/len(trades_df)*100:.1f}%)")
print(f"  • Most active: {hourly.index[0]}h UTC")

print(f"\n🔍 LIKELY STRATEGY COMPONENTS:")
strategies = []
if avg_time_between < 60:
    strategies.append("  ✓ Market Making (very fast trades)")
if size_cv > 1.0:
    strategies.append("  ✓ Dynamic Position Sizing (adapts to volatility)")
if len(closed_trades) > 0 and len(closed_trades[closed_trades['closed_pnl'] > 0]) / len(closed_trades) > 0.8:
    strategies.append("  ✓ Very Tight Stop Loss (high win rate)")
if len(hourly) > 0 and hourly.iloc[0] / len(trades_df) > 0.3:
    strategies.append(f"  ✓ Time-based Filter (concentrated at {hourly.index[0]}h)")

for s in strategies:
    print(s)

print(f"\n📝 RECOMMENDED APPROACH:")
print(f"  1. This is likely a PROFESSIONAL HFT/Market Making bot")
print(f"  2. Requires: Low latency, Order flow data, Advanced execution")
print(f"  3. For replication: Focus on timing patterns & risk management")
print(f"  4. Manual trading: NOT RECOMMENDED (too fast)")
print(f"  5. Best use: Study timing/sizing, adapt to slower timeframe")

print("\n" + "=" * 70)
print("✅ ANALYSIS COMPLETE")
print("=" * 70)

# Save summary
summary = {
    'vault_type': 'HIGH FREQUENCY' if avg_time_between < 60 else 'SCALPING',
    'trades_per_day': float(trades_per_day),
    'avg_time_between_trades': float(avg_time_between),
    'size_coefficient_variation': float(size_cv),
    'top_hours': hourly.head(5).to_dict(),
    'directional_bias': direction_counts.to_dict(),
    'total_trades': len(trades_df),
    'date_range': f"{trades_df['timestamp'].min()} to {trades_df['timestamp'].max()}"
}

summary_path = Path("reports/reverse_engineering/0x9b55c8c9/deep_analysis_summary.json")
with open(summary_path, 'w') as f:
    json.dump(summary, f, indent=2, default=str)

print(f"\n💾 Summary saved to: {summary_path}")
