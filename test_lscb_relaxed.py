#!/usr/bin/env python3
from datetime import datetime
from engine.backtester import Backtester
from strategies.lscb_relaxed import LSCBRelaxedStrategy
from engine.metrics import format_metrics_table

print('=' * 70)
print('🎯 LSCB RELAXED STRATEGY BACKTEST')
print('=' * 70)
print('\nTesting simplified LSCB logic:')
print('  - EMA rejection setups in trending markets')
print('  - Relaxed parameters for real-world conditions')
print('\nRunning...\n')

strategy = LSCBRelaxedStrategy()

backtester = Backtester(
    strategy=strategy,
    symbol='BTCUSDT',
    timeframe='5m',
    start_date='2024-08-01',
    end_date='2024-09-29',
    initial_balance=10000,
    leverage=1.0,
    data_dir='./data/binance',
    use_cache=True
)

results = backtester.run()

print('\n' + '=' * 70)
print('📊 RESULTS')
print('=' * 70)
print(format_metrics_table(results['metrics']))

trades_df = results['trades']
if len(trades_df) > 0:
    print(f'\n📈 {len(trades_df)} trades executed')

    if 'setup' in trades_df.columns:
        for setup in trades_df['setup'].unique():
            count = len(trades_df[trades_df['setup'] == setup])
            print(f'   {setup}: {count}')

    print(f'\nTop 3 best trades (by PnL):')
    top_trades = trades_df.nlargest(3, 'pnl')
    for idx, trade in top_trades.iterrows():
        exit_reason = trade.get('exit_reason', 'unknown')
        print(f'   {trade["entry_time"]}: ${trade["pnl"]:.2f} ({exit_reason})')

    print(f'\nWorst 3 trades (by PnL):')
    worst_trades = trades_df.nsmallest(3, 'pnl')
    for idx, trade in worst_trades.iterrows():
        exit_reason = trade.get('exit_reason', 'unknown')
        print(f'   {trade["entry_time"]}: ${trade["pnl"]:.2f} ({exit_reason})')

else:
    print('\n⚠️  No trades')

print('\n' + '=' * 70)
