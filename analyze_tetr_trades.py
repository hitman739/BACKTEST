#!/usr/bin/env python3
"""
Analyze TETR trades in detail
Shows actual trade examples from the backtest
"""

from engine.backtester import Backtester
from strategies.tetr_strategy import TETRStrategy
import pandas as pd

print("="*70)
print("🔍 TETR TRADE ANALYSIS")
print("="*70)

# Run backtest
backtester = Backtester(
    strategy=TETRStrategy(),
    symbol='BTCUSDT',
    timeframe='5m',
    start_date='2024-08-01',
    end_date='2024-09-29',
    initial_balance=10000,
    data_dir='./data/binance',
    use_cache=True
)

results = backtester.run()
trades_df = results['trades']

print(f"\nTotal trades: {len(trades_df)}")
print(f"Winners: {len(trades_df[trades_df['pnl'] > 0])}")
print(f"Losers: {len(trades_df[trades_df['pnl'] <= 0])}")

# Show best trades
print("\n" + "="*70)
print("🏆 TOP 5 BEST TRADES")
print("="*70)

best_trades = trades_df.nlargest(5, 'pnl')
for idx, trade in best_trades.iterrows():
    entry_time = trade['entry_time']
    exit_time = trade['exit_time']
    entry_price = trade['entry_price']
    exit_price = trade['exit_price']
    pnl = trade['pnl']
    duration = trade.get('duration_bars', 0)
    exit_reason = trade.get('exit_reason', 'unknown')

    print(f"\n#{idx+1}")
    print(f"  Entry:  {entry_time} @ ${entry_price:,.2f}")
    print(f"  Exit:   {exit_time} @ ${exit_price:,.2f}")
    print(f"  P&L:    ${pnl:,.2f}")
    print(f"  Duration: {duration} bars ({duration*5} mins)")
    print(f"  Exit reason: {exit_reason}")

    if trade['side'] == 'buy':
        move = ((exit_price - entry_price) / entry_price) * 100
        print(f"  Move: +{move:.2f}%")
    else:
        move = ((entry_price - exit_price) / entry_price) * 100
        print(f"  Move: +{move:.2f}%")

# Show worst trades
print("\n" + "="*70)
print("💀 TOP 5 WORST TRADES")
print("="*70)

worst_trades = trades_df.nsmallest(5, 'pnl')
for idx, trade in worst_trades.iterrows():
    entry_time = trade['entry_time']
    exit_time = trade['exit_time']
    entry_price = trade['entry_price']
    exit_price = trade['exit_price']
    pnl = trade['pnl']
    duration = trade.get('duration_bars', 0)
    exit_reason = trade.get('exit_reason', 'unknown')

    print(f"\n#{idx+1}")
    print(f"  Entry:  {entry_time} @ ${entry_price:,.2f}")
    print(f"  Exit:   {exit_time} @ ${exit_price:,.2f}")
    print(f"  P&L:    ${pnl:,.2f}")
    print(f"  Duration: {duration} bars ({duration*5} mins)")
    print(f"  Exit reason: {exit_reason}")

    if trade['side'] == 'buy':
        move = ((exit_price - entry_price) / entry_price) * 100
        print(f"  Move: {move:.2f}%")
    else:
        move = ((entry_price - exit_price) / entry_price) * 100
        print(f"  Move: {move:.2f}%")

# Exit reason breakdown
print("\n" + "="*70)
print("📊 EXIT REASON BREAKDOWN")
print("="*70)

if 'exit_reason' in trades_df.columns:
    exit_counts = trades_df['exit_reason'].value_counts()

    for reason, count in exit_counts.items():
        pct = (count / len(trades_df)) * 100

        # Calculate avg P&L for this exit reason
        reason_trades = trades_df[trades_df['exit_reason'] == reason]
        avg_pnl = reason_trades['pnl'].mean()

        print(f"\n{reason}:")
        print(f"  Count: {count} ({pct:.1f}%)")
        print(f"  Avg P&L: ${avg_pnl:.2f}")

        # Show if profitable
        if avg_pnl > 0:
            print(f"  ✅ Profitable exit type")
        else:
            print(f"  ❌ Loss-making exit type")

# Long vs Short performance
print("\n" + "="*70)
print("📈 LONG vs SHORT PERFORMANCE")
print("="*70)

long_trades = trades_df[trades_df['side'] == 'buy']
short_trades = trades_df[trades_df['side'] == 'sell']

print(f"\nLONG Trades: {len(long_trades)}")
if len(long_trades) > 0:
    long_winners = len(long_trades[long_trades['pnl'] > 0])
    long_wr = (long_winners / len(long_trades)) * 100
    long_total_pnl = long_trades['pnl'].sum()
    long_avg_pnl = long_trades['pnl'].mean()

    print(f"  Win Rate: {long_wr:.1f}%")
    print(f"  Total P&L: ${long_total_pnl:.2f}")
    print(f"  Avg P&L: ${long_avg_pnl:.2f}")

print(f"\nSHORT Trades: {len(short_trades)}")
if len(short_trades) > 0:
    short_winners = len(short_trades[short_trades['pnl'] > 0])
    short_wr = (short_winners / len(short_trades)) * 100
    short_total_pnl = short_trades['pnl'].sum()
    short_avg_pnl = short_trades['pnl'].mean()

    print(f"  Win Rate: {short_wr:.1f}%")
    print(f"  Total P&L: ${short_total_pnl:.2f}")
    print(f"  Avg P&L: ${short_avg_pnl:.2f}")

# Trade duration analysis
print("\n" + "="*70)
print("⏱️  TRADE DURATION ANALYSIS")
print("="*70)

if 'duration_bars' in trades_df.columns:
    avg_duration = trades_df['duration_bars'].mean()
    min_duration = trades_df['duration_bars'].min()
    max_duration = trades_df['duration_bars'].max()
    median_duration = trades_df['duration_bars'].median()

    print(f"\nAverage: {avg_duration:.1f} bars ({avg_duration*5:.0f} mins)")
    print(f"Median:  {median_duration:.1f} bars ({median_duration*5:.0f} mins)")
    print(f"Min:     {min_duration:.0f} bars ({min_duration*5:.0f} mins)")
    print(f"Max:     {max_duration:.0f} bars ({max_duration*5:.0f} mins)")

    # Duration vs profitability
    winners = trades_df[trades_df['pnl'] > 0]
    losers = trades_df[trades_df['pnl'] <= 0]

    if len(winners) > 0:
        winner_avg_duration = winners['duration_bars'].mean()
        print(f"\nWinners avg duration: {winner_avg_duration:.1f} bars ({winner_avg_duration*5:.0f} mins)")

    if len(losers) > 0:
        loser_avg_duration = losers['duration_bars'].mean()
        print(f"Losers avg duration:  {loser_avg_duration:.1f} bars ({loser_avg_duration*5:.0f} mins)")

print("\n" + "="*70)
print("✅ ANALYSIS COMPLETE")
print("="*70)
