#!/usr/bin/env python3
"""
Hyperliquid Vault Analyzer V2 - Advanced Analysis
Extracts comprehensive strategy patterns from Hyperliquid vaults
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from typing import Dict, List, Tuple
from collections import defaultdict


class HyperliquidVaultAnalyzerV2:
    """Advanced analyzer with position reconstruction and pattern detection"""

    def __init__(self, vault_address: str):
        self.vault_address = vault_address
        self.api_url = "https://api.hyperliquid.xyz/info"
        self.trades = []
        self.positions = {}
        self.reconstructed_trades = []

    def fetch_all_data(self, limit: int = 2000):
        """Fetch comprehensive vault data"""
        print(f"📥 Fetching comprehensive data from vault {self.vault_address[:10]}...")

        # 1. User fills (trades)
        payload = {"type": "userFills", "user": self.vault_address}
        try:
            response = requests.post(self.api_url, json=payload)
            self.trades = response.json()[:limit] if isinstance(response.json(), list) else []
            print(f"✅ Downloaded {len(self.trades)} trades")
        except Exception as e:
            print(f"❌ Error fetching trades: {e}")

        # 2. Current state
        payload = {"type": "clearinghouseState", "user": self.vault_address}
        try:
            response = requests.post(self.api_url, json=payload)
            state = response.json()
            if isinstance(state, dict):
                print(f"✅ Got clearinghouse state")
                # Print useful info
                if 'assetPositions' in state:
                    print(f"   Current positions: {len(state['assetPositions'])}")
                if 'marginSummary' in state:
                    margin = state['marginSummary']
                    print(f"   Account value: ${float(margin.get('accountValue', 0)):,.2f}")
        except Exception as e:
            print(f"⚠️  Could not fetch clearinghouse state: {e}")

        # 3. Vault details
        payload = {"type": "vaultDetails", "vaultAddress": self.vault_address}
        try:
            response = requests.post(self.api_url, json=payload)
            vault_info = response.json()
            if isinstance(vault_info, dict):
                print(f"✅ Got vault details")
                print(f"   Vault name: {vault_info.get('name', 'Unknown')}")
                print(f"   Leader: {vault_info.get('leader', 'Unknown')[:10]}...")
        except Exception as e:
            print(f"⚠️  Could not fetch vault details: {e}")

    def reconstruct_positions(self) -> List[Dict]:
        """Reconstruct complete position entries/exits from individual trades"""
        print("\n🔄 Reconstructing positions from trades...")

        df = pd.DataFrame(self.trades) if self.trades else pd.DataFrame()
        if df.empty:
            print("  ⚠️  No trades to reconstruct")
            return []

        # Parse essential fields
        df['time'] = pd.to_datetime(df['time'].astype(int), unit='ms')
        df['price'] = df['px'].astype(float)
        df['size'] = df['sz'].astype(float)
        df['side'] = df['side']  # 'B' = buy, 'A' = sell
        df['coin'] = df['coin']
        df['closed_pnl'] = df.get('closedPnl', 0).astype(float)
        df = df.sort_values('time')

        # Track positions per coin
        positions_by_coin = defaultdict(list)
        current_position = defaultdict(lambda: {'size': 0, 'entry_price': 0, 'entry_time': None, 'trades': []})

        reconstructed = []

        for idx, trade in df.iterrows():
            coin = trade['coin']
            side = trade['side']
            size = trade['size']
            price = trade['price']
            time = trade['time']
            pnl = trade['closed_pnl']

            pos = current_position[coin]

            # Determine if opening, closing, or flipping
            if pos['size'] == 0:
                # Opening new position
                pos['size'] = size if side == 'B' else -size
                pos['entry_price'] = price
                pos['entry_time'] = time
                pos['trades'].append(trade)
                pos['entry_side'] = 'long' if side == 'B' else 'short'

            elif (pos['size'] > 0 and side == 'A') or (pos['size'] < 0 and side == 'B'):
                # Closing or reducing position
                pos['trades'].append(trade)

                if abs(size) >= abs(pos['size']):
                    # Full close
                    exit_price = price
                    exit_time = time
                    holding_time = (exit_time - pos['entry_time']).total_seconds() / 60  # minutes

                    reconstructed.append({
                        'coin': coin,
                        'entry_time': pos['entry_time'],
                        'exit_time': exit_time,
                        'entry_price': pos['entry_price'],
                        'exit_price': exit_price,
                        'side': pos['entry_side'],
                        'size': abs(pos['size']),
                        'holding_time_mins': holding_time,
                        'pnl': pnl,
                        'num_trades': len(pos['trades'])
                    })

                    # Reset position
                    remaining = abs(size) - abs(pos['size'])
                    if remaining > 0:
                        # Flipped to opposite side
                        pos['size'] = remaining if side == 'B' else -remaining
                        pos['entry_price'] = price
                        pos['entry_time'] = time
                        pos['trades'] = [trade]
                        pos['entry_side'] = 'long' if side == 'B' else 'short'
                    else:
                        pos['size'] = 0
                        pos['trades'] = []
                else:
                    # Partial close
                    pos['size'] = pos['size'] + (size if side == 'A' else -size)

            else:
                # Adding to position (same direction)
                old_size = abs(pos['size'])
                new_size = old_size + size
                # Weighted average entry
                pos['entry_price'] = (pos['entry_price'] * old_size + price * size) / new_size
                pos['size'] = new_size if pos['size'] > 0 else -new_size
                pos['trades'].append(trade)

        self.reconstructed_trades = reconstructed
        print(f"✅ Reconstructed {len(reconstructed)} complete positions")
        return reconstructed

    def analyze_reconstructed_positions(self) -> Dict:
        """Deep analysis of reconstructed positions"""
        if not self.reconstructed_trades:
            print("\n⚠️  No reconstructed positions to analyze")
            return {}

        df = pd.DataFrame(self.reconstructed_trades)

        print("\n" + "=" * 70)
        print("📊 RECONSTRUCTED POSITIONS ANALYSIS")
        print("=" * 70)

        # Basic stats
        total_positions = len(df)
        winners = df[df['pnl'] > 0]
        losers = df[df['pnl'] < 0]
        breakeven = df[df['pnl'] == 0]

        print(f"\n🎯 Overall Performance:")
        print(f"  • Total positions: {total_positions}")
        print(f"  • Winners: {len(winners)} ({len(winners)/total_positions*100:.1f}%)")
        print(f"  • Losers: {len(losers)} ({len(losers)/total_positions*100:.1f}%)")
        print(f"  • Breakeven: {len(breakeven)}")
        print(f"  • Total PnL: ${df['pnl'].sum():,.2f}")

        if len(winners) > 0 and len(losers) > 0:
            avg_win = winners['pnl'].mean()
            avg_loss = losers['pnl'].mean()
            print(f"  • Avg Win: ${avg_win:.2f}")
            print(f"  • Avg Loss: ${avg_loss:.2f}")
            print(f"  • Win/Loss Ratio: {abs(avg_win/avg_loss):.2f}")

            profit_factor = winners['pnl'].sum() / abs(losers['pnl'].sum())
            print(f"  • Profit Factor: {profit_factor:.2f}")

        # Holding time analysis
        print(f"\n⏱️  Holding Time:")
        print(f"  • Avg: {df['holding_time_mins'].mean():.1f} minutes")
        print(f"  • Median: {df['holding_time_mins'].median():.1f} minutes")
        print(f"  • Min: {df['holding_time_mins'].min():.1f} minutes")
        print(f"  • Max: {df['holding_time_mins'].max():.1f} minutes")

        # Convert to hours for better understanding
        avg_hours = df['holding_time_mins'].mean() / 60
        if avg_hours < 1:
            print(f"  📌 Strategy type: SCALPING (avg {df['holding_time_mins'].mean():.0f} min holds)")
        elif avg_hours < 24:
            print(f"  📌 Strategy type: INTRADAY (avg {avg_hours:.1f} hour holds)")
        else:
            print(f"  📌 Strategy type: SWING (avg {avg_hours/24:.1f} day holds)")

        # Directional bias
        longs = df[df['side'] == 'long']
        shorts = df[df['side'] == 'short']
        print(f"\n📈 Directional Bias:")
        print(f"  • Longs: {len(longs)} ({len(longs)/total_positions*100:.1f}%)")
        print(f"  • Shorts: {len(shorts)} ({len(shorts)/total_positions*100:.1f}%)")

        if len(longs) > 0 and len(shorts) > 0:
            long_wr = len(longs[longs['pnl'] > 0]) / len(longs) * 100
            short_wr = len(shorts[shorts['pnl'] > 0]) / len(shorts) * 100
            print(f"  • Long Win Rate: {long_wr:.1f}%")
            print(f"  • Short Win Rate: {short_wr:.1f}%")

        # Coins traded
        print(f"\n💎 Coins Traded:")
        coin_stats = df.groupby('coin').agg({
            'pnl': ['count', 'sum', 'mean'],
            'holding_time_mins': 'mean'
        }).round(2)
        print(coin_stats)

        # Time of day analysis
        df['hour'] = df['entry_time'].dt.hour
        hourly = df.groupby('hour')['pnl'].agg(['count', 'sum', 'mean']).sort_values('count', ascending=False)

        print(f"\n🕐 Most Active Hours (UTC):")
        print(hourly.head(5))

        return {
            'total_positions': total_positions,
            'win_rate': len(winners) / total_positions * 100 if total_positions > 0 else 0,
            'avg_holding_mins': df['holding_time_mins'].mean(),
            'total_pnl': df['pnl'].sum(),
            'coins': df['coin'].unique().tolist(),
            'long_short_ratio': len(longs) / len(shorts) if len(shorts) > 0 else float('inf')
        }


def main():
    vault_address = "0x9b55c8c948f988bcbe404cd070fc9ffffab8d31b"

    print("=" * 70)
    print("🔍 HYPERLIQUID VAULT REVERSE ENGINEERING V2")
    print("=" * 70)
    print(f"\nVault: {vault_address}\n")

    analyzer = HyperliquidVaultAnalyzerV2(vault_address)

    # Fetch all data
    analyzer.fetch_all_data(limit=2000)

    # Reconstruct positions
    positions = analyzer.reconstruct_positions()

    # Analyze
    if positions:
        summary = analyzer.analyze_reconstructed_positions()

        # Save
        filename = f"vault_analysis_v2_{vault_address[:10]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump({
                'vault': vault_address,
                'analyzed_at': datetime.now().isoformat(),
                'summary': summary,
                'positions': positions[:50]  # Save first 50 positions as examples
            }, f, indent=2, default=str)
        print(f"\n💾 Analysis saved to: {filename}")

    print("\n" + "=" * 70)
    print("✅ Analysis Complete!")
    print("=" * 70)


if __name__ == '__main__':
    main()
