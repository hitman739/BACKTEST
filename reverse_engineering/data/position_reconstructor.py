"""
Position Reconstructor
Reconstructs complete positions (entry → exit) from individual fills
"""

import pandas as pd
import numpy as np
from typing import Dict, List
from collections import defaultdict


class PositionReconstructor:
    """Reconstructs full position lifecycle from individual trades"""

    def __init__(self):
        self.positions = []

    def reconstruct(self, trades_df: pd.DataFrame) -> pd.DataFrame:
        """
        Reconstruct complete positions from trades

        Returns DataFrame with columns:
        - symbol, entry_time, exit_time, side, entry_price, exit_price,
          size, holding_time_mins, pnl, num_fills, mfe, mae
        """
        print("🔄 Reconstructing positions...")

        if trades_df.empty:
            return pd.DataFrame()

        # Track positions per symbol
        positions = []
        current_pos = defaultdict(lambda: {
            'size': 0, 'entry_price': 0, 'entry_time': None,
            'trades': [], 'side': None, 'peak_price': 0, 'worst_price': 0
        })

        for idx, trade in trades_df.iterrows():
            symbol = trade['symbol']
            side = trade['side']
            size = trade['size']
            price = trade['price']
            timestamp = trade['timestamp']
            pnl = trade['closed_pnl']

            pos = current_pos[symbol]

            # Opening new position
            if pos['size'] == 0:
                pos['size'] = size
                pos['entry_price'] = price
                pos['entry_time'] = timestamp
                pos['side'] = side
                pos['trades'].append(trade)
                pos['peak_price'] = price
                pos['worst_price'] = price

            # Closing/reducing position
            elif pnl != 0:
                pos['trades'].append(trade)

                # Calculate MFE/MAE
                if pos['side'] == 'long':
                    mfe = pos['peak_price'] - pos['entry_price']
                    mae = pos['worst_price'] - pos['entry_price']
                else:
                    mfe = pos['entry_price'] - pos['worst_price']
                    mae = pos['entry_price'] - pos['peak_price']

                # Store completed position
                holding_time = (timestamp - pos['entry_time']).total_seconds() / 60

                positions.append({
                    'symbol': symbol,
                    'entry_time': pos['entry_time'],
                    'exit_time': timestamp,
                    'side': pos['side'],
                    'entry_price': pos['entry_price'],
                    'exit_price': price,
                    'size': pos['size'],
                    'holding_time_mins': holding_time,
                    'pnl': pnl,
                    'num_fills': len(pos['trades']),
                    'mfe': mfe,
                    'mae': mae
                })

                # Reset position
                pos['size'] = 0
                pos['trades'] = []

            # Update peaks for MFE/MAE tracking
            else:
                if pos['side'] == 'long':
                    pos['peak_price'] = max(pos['peak_price'], price)
                    pos['worst_price'] = min(pos['worst_price'], price)
                else:
                    pos['peak_price'] = min(pos['peak_price'], price)
                    pos['worst_price'] = max(pos['worst_price'], price)

        df = pd.DataFrame(positions)

        if not df.empty:
            print(f"✅ Reconstructed {len(df)} complete positions")
            print(f"   Avg holding: {df['holding_time_mins'].mean():.1f} mins")
            print(f"   Total PnL: ${df['pnl'].sum():,.2f}")
        else:
            print("⚠️  No complete positions found")

        self.positions = df
        return df
