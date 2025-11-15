#!/usr/bin/env python3
"""
Quick test of SimpleMeanRevert strategy
"""

from engine.backtester import Backtester
from strategies.simple_mean_revert import SimpleMeanRevertStrategy

print("Testing SimpleMeanRevert strategy...")
print("=" * 60)

strategy = SimpleMeanRevertStrategy()

# Show config
print(f"Strategy: {strategy.name}")
print(f"Mean type: {strategy.mean_type.value}")
print(f"Mean lookback: {strategy.mean_lookback} candles")
print(f"Long thresholds: {strategy.long_thresholds}")
print(f"Short thresholds: {strategy.short_thresholds}")
print(f"ATR filter: {strategy.min_atr_ratio} - {strategy.max_atr_ratio}")
print(f"Vol filter: {strategy.min_vol_ratio} - {strategy.max_vol_ratio}")
print(f"Trading hours: {strategy.trading_hours}")
print("=" * 60)
print()

# Note: This will fail in Docker without internet
# User must run on Mac
print("NOTE: Run this on your Mac (not Docker) where you have internet access")
print()
print("Command:")
print("  cd ~/BACKTEST")
print("  git pull")
print("  python3 test_simple_mr.py")
