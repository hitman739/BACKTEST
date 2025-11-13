#!/usr/bin/env python3
"""
Hyperliquid Vault Analyzer V3 - COMPLETE Analysis
Extracts ALL patterns from individual trades, not just closed positions
"""

import requests
import pandas as pd
import numpy as np
from datetime import datetime
import json


class HyperliquidVaultAnalyzerV3:
    """Analyze ALL trades individually for maximum insight"""

    def __init__(self, vault_address: str):
        self.vault_address = vault_address
        self.api_url = "https://api.hyperliquid.xyz/info"

    def fetch_trades(self, limit: int = 5000):
        """Fetch ALL available trades"""
        print(f"📥 Fetching up to {limit} trades from vault...")

        payload = {"type": "userFills", "user": self.vault_address}

        try:
            response = requests.post(self.api_url, json=payload)
            trades = response.json()

            if isinstance(trades, list):
                trades = trades[:limit]
                print(f"✅ Downloaded {len(trades)} trades")
                return trades
            else:
                print(f"❌ Unexpected response")
                return []
        except Exception as e:
            print(f"❌ Error: {e}")
            return []

    def analyze_all_trades(self, trades):
        """Comprehensive analysis of ALL trades"""

        if not trades:
            print("No trades to analyze")
            return

        df = pd.DataFrame(trades)

        # Parse fields
        df['time'] = pd.to_datetime(df['time'].astype(int), unit='ms')
        df['price'] = df['px'].astype(float)
        df['size'] = df['sz'].astype(float)
        df['closed_pnl'] = df.get('closedPnl', 0).astype(float)
        df['fee'] = df.get('fee', 0).astype(float)
        df['notional'] = df['price'] * df['size']

        print("\n" + "=" * 70)
        print("📊 COMPLETE TRADE ANALYSIS")
        print("=" * 70)

        # 1. BASIC STATS
        print(f"\n📈 Basic Statistics:")
        print(f"  • Total trades: {len(df)}")
        print(f"  • Date range: {df['time'].min()} to {df['time'].max()}")
        print(f"  • Days active: {(df['time'].max() - df['time'].min()).days}")
        print(f"  • Avg trades/day: {len(df) / max((df['time'].max() - df['time'].min()).days, 1):.1f}")

        # 2. COINS
        print(f"\n💎 Coins Traded:")
        coin_counts = df['coin'].value_counts()
        for coin, count in coin_counts.items():
            pct = count / len(df) * 100
            print(f"  • {coin}: {count} trades ({pct:.1f}%)")

        # 3. DIRECTIONAL BIAS
        print(f"\n📊 Directional Bias:")
        buys = df[df['side'] == 'B']
        sells = df[df['side'] == 'A']
        print(f"  • Buys: {len(buys)} ({len(buys)/len(df)*100:.1f}%)")
        print(f"  • Sells: {len(sells)} ({len(sells)/len(df)*100:.1f}%)")

        # 4. SIZE ANALYSIS
        print(f"\n💰 Position Sizing:")
        print(f"  • Avg size: {df['size'].mean():.4f}")
        print(f"  • Min size: {df['size'].min():.4f}")
        print(f"  • Max size: {df['size'].max():.4f}")
        print(f"  • Median size: {df['size'].median():.4f}")
        print(f"  • Avg notional: ${df['notional'].mean():,.2f}")

        size_std = df['size'].std() / df['size'].mean()
        if size_std < 0.3:
            print(f"  📌 Fixed sizing strategy (~{df['size'].mean():.4f})")
        else:
            print(f"  📌 Variable sizing (CV: {size_std:.2f})")

        # 5. PNL ANALYSIS (for closed trades)
        closed = df[df['closed_pnl'] != 0]
        if len(closed) > 0:
            print(f"\n💵 PnL Analysis ({len(closed)} closed trades):")
            winners = closed[closed['closed_pnl'] > 0]
            losers = closed[closed['closed_pnl'] < 0]

            print(f"  • Winners: {len(winners)} ({len(winners)/len(closed)*100:.1f}%)")
            print(f"  • Losers: {len(losers)} ({len(losers)/len(closed)*100:.1f}%)")
            print(f"  • Total PnL: ${closed['closed_pnl'].sum():,.2f}")

            if len(winners) > 0:
                print(f"  • Avg Win: ${winners['closed_pnl'].mean():.2f}")
                print(f"  • Best Win: ${winners['closed_pnl'].max():.2f}")
            if len(losers) > 0:
                print(f"  • Avg Loss: ${losers['closed_pnl'].mean():.2f}")
                print(f"  • Worst Loss: ${losers['closed_pnl'].min():.2f}")

            if len(winners) > 0 and len(losers) > 0:
                rr = abs(winners['closed_pnl'].mean() / losers['closed_pnl'].mean())
                pf = winners['closed_pnl'].sum() / abs(losers['closed_pnl'].sum())
                print(f"  • Win/Loss Ratio: {rr:.2f}")
                print(f"  • Profit Factor: {pf:.2f}")

        # 6. TIME PATTERNS
        df['hour'] = df['time'].dt.hour
        df['day_of_week'] = df['time'].dt.dayofweek

        print(f"\n🕐 Time Patterns:")
        print(f"  Most active hours (UTC):")
        top_hours = df['hour'].value_counts().head(5)
        for hour, count in top_hours.items():
            print(f"    {hour:02d}:00 - {count} trades ({count/len(df)*100:.1f}%)")

        print(f"\n  Most active days:")
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        day_counts = df['day_of_week'].value_counts().sort_index()
        for day_num, count in day_counts.items():
            print(f"    {days[day_num]}: {count} trades ({count/len(df)*100:.1f}%)")

        # 7. PRICE LEVELS
        print(f"\n📊 Price Levels:")
        for coin in coin_counts.head(3).index:
            coin_df = df[df['coin'] == coin]
            print(f"  {coin}:")
            print(f"    Min: ${coin_df['price'].min():,.2f}")
            print(f"    Max: ${coin_df['price'].max():,.2f}")
            print(f"    Avg: ${coin_df['price'].mean():,.2f}")

        # 8. DETECT PATTERNS
        print(f"\n🔍 Pattern Detection:")

        # Time between trades
        df_sorted = df.sort_values('time')
        df_sorted['time_diff'] = df_sorted['time'].diff().dt.total_seconds() / 60
        avg_time_between = df_sorted['time_diff'].median()

        print(f"  • Median time between trades: {avg_time_between:.1f} minutes")

        if avg_time_between < 5:
            print(f"  📌 HIGH FREQUENCY (trades every {avg_time_between:.1f} min)")
        elif avg_time_between < 60:
            print(f"  📌 SCALPING (trades every {avg_time_between:.1f} min)")
        elif avg_time_between < 1440:
            print(f"  📌 INTRADAY (trades every {avg_time_between/60:.1f} hours)")
        else:
            print(f"  📌 SWING (trades every {avg_time_between/1440:.1f} days)")

        # Consecutive same-side trades (pyramiding?)
        consecutive_buys = 0
        consecutive_sells = 0
        max_consecutive_buys = 0
        max_consecutive_sells = 0

        for i in range(1, len(df_sorted)):
            if df_sorted.iloc[i]['side'] == df_sorted.iloc[i-1]['side']:
                if df_sorted.iloc[i]['side'] == 'B':
                    consecutive_buys += 1
                    max_consecutive_buys = max(max_consecutive_buys, consecutive_buys)
                else:
                    consecutive_sells += 1
                    max_consecutive_sells = max(max_consecutive_sells, consecutive_sells)
            else:
                consecutive_buys = 0
                consecutive_sells = 0

        if max_consecutive_buys > 2 or max_consecutive_sells > 2:
            print(f"  • Max consecutive buys: {max_consecutive_buys}")
            print(f"  • Max consecutive sells: {max_consecutive_sells}")
            print(f"  📌 Uses PYRAMIDING (adds to positions)")

        # 9. FEES
        total_fees = df['fee'].sum()
        print(f"\n💸 Fees:")
        print(f"  • Total fees paid: ${abs(total_fees):,.2f}")
        print(f"  • Avg fee/trade: ${abs(df['fee'].mean()):.2f}")

        # 10. SUMMARY
        print(f"\n" + "=" * 70)
        print("🎯 STRATEGY SUMMARY")
        print("=" * 70)

        summary = {
            'total_trades': len(df),
            'coins': coin_counts.to_dict(),
            'buy_sell_ratio': len(buys) / len(sells) if len(sells) > 0 else float('inf'),
            'avg_trade_interval_mins': avg_time_between,
            'avg_size': df['size'].mean(),
            'win_rate': len(winners) / len(closed) * 100 if len(closed) > 0 else 0,
            'total_pnl': closed['closed_pnl'].sum() if len(closed) > 0 else 0,
            'profit_factor': pf if len(winners) > 0 and len(losers) > 0 else 0,
            'most_active_hours': top_hours.head(3).index.tolist(),
            'strategy_type': 'HIGH_FREQ' if avg_time_between < 5 else 'SCALPING' if avg_time_between < 60 else 'INTRADAY'
        }

        print(f"\n📋 Key Findings:")
        print(f"  • Strategy Type: {summary['strategy_type']}")
        print(f"  • Primary Coins: {', '.join(list(summary['coins'].keys())[:3])}")
        print(f"  • Trade Frequency: Every {avg_time_between:.1f} minutes")
        print(f"  • Win Rate: {summary['win_rate']:.1f}%")
        print(f"  • Total PnL: ${summary['total_pnl']:,.2f}")

        if summary['profit_factor'] > 0:
            print(f"  • Profit Factor: {summary['profit_factor']:.2f}")
            if summary['profit_factor'] > 1.5:
                print(f"  ✅ PROFITABLE STRATEGY!")
            elif summary['profit_factor'] > 1.0:
                print(f"  ✅ Marginally profitable")
            else:
                print(f"  ❌ Not profitable")

        # Save detailed analysis
        filename = f"vault_analysis_v3_{self.vault_address[:10]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump({
                'vault': self.vault_address,
                'analyzed_at': datetime.now().isoformat(),
                'summary': summary,
                'sample_trades': trades[:20]  # First 20 trades as examples
            }, f, indent=2, default=str)

        print(f"\n💾 Full analysis saved to: {filename}")

        return summary


def main():
    vault_address = "0x9b55c8c948f988bcbe404cd070fc9ffffab8d31b"

    print("=" * 70)
    print("🔍 HYPERLIQUID VAULT ANALYZER V3 - COMPLETE")
    print("=" * 70)
    print(f"\nVault: {vault_address}\n")

    analyzer = HyperliquidVaultAnalyzerV3(vault_address)
    trades = analyzer.fetch_trades(limit=5000)

    if trades:
        analyzer.analyze_all_trades(trades)

    print("\n" + "=" * 70)
    print("✅ Complete Analysis Done!")
    print("=" * 70)


if __name__ == '__main__':
    main()
