#!/usr/bin/env python3
"""
Hyperliquid Vault Analyzer
Reverse engineers trading strategies from successful Hyperliquid vaults
by analyzing their public on-chain trades
"""

import requests
import pandas as pd
from datetime import datetime
import json
from typing import Dict, List


class HyperliquidVaultAnalyzer:
    """Analyze Hyperliquid vault trades to reverse engineer strategy"""

    def __init__(self, vault_address: str):
        self.vault_address = vault_address
        self.api_url = "https://api.hyperliquid.xyz/info"
        self.trades = []
        self.positions = []

    def fetch_vault_trades(self, limit: int = 500):
        """Fetch all trades from the vault"""
        print(f"📥 Fetching trades from vault {self.vault_address[:10]}...")

        payload = {
            "type": "userFills",
            "user": self.vault_address
        }

        try:
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
            data = response.json()

            if isinstance(data, list):
                self.trades = data[:limit]
                print(f"✅ Downloaded {len(self.trades)} trades")
                return self.trades
            else:
                print(f"❌ Unexpected response format: {type(data)}")
                return []

        except Exception as e:
            print(f"❌ Error fetching trades: {e}")
            return []

    def fetch_vault_info(self):
        """Fetch vault metadata"""
        print(f"📊 Fetching vault info...")

        payload = {
            "type": "vaultDetails",
            "vaultAddress": self.vault_address
        }

        try:
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Error fetching vault info: {e}")
            return None

    def parse_trades_to_dataframe(self) -> pd.DataFrame:
        """Convert trades to pandas DataFrame for analysis"""
        if not self.trades:
            return pd.DataFrame()

        parsed_trades = []

        for trade in self.trades:
            parsed_trades.append({
                'time': pd.to_datetime(int(trade['time']), unit='ms'),
                'coin': trade['coin'],
                'side': trade['side'],  # 'A' = sell, 'B' = buy
                'price': float(trade['px']),
                'size': float(trade['sz']),
                'closed_pnl': float(trade.get('closedPnl', 0)),
                'fee': float(trade.get('fee', 0)),
                'hash': trade.get('hash', ''),
                'start_position': trade.get('startPosition', 0),
                'dir': trade.get('dir', '')
            })

        df = pd.DataFrame(parsed_trades)
        df = df.sort_values('time')
        return df

    def analyze_entry_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze when the vault enters positions"""
        print("\n📈 Analyzing Entry Patterns...")

        # Filter opening trades (when position goes from 0 or opposite side)
        entries = df[df['start_position'] == 0].copy() if 'start_position' in df.columns else df.copy()

        if len(entries) == 0:
            print("  ⚠️  No clear entry trades found")
            return {}

        analysis = {
            'total_entries': len(entries),
            'long_entries': len(entries[entries['side'] == 'B']),
            'short_entries': len(entries[entries['side'] == 'A']),
            'coins_traded': entries['coin'].unique().tolist(),
            'avg_entry_size': entries['size'].mean(),
            'entry_times': entries['time'].dt.hour.value_counts().to_dict()
        }

        print(f"  • Total entries: {analysis['total_entries']}")
        print(f"  • Long/Short: {analysis['long_entries']}/{analysis['short_entries']}")
        print(f"  • Coins traded: {', '.join(analysis['coins_traded'])}")
        print(f"  • Avg entry size: {analysis['avg_entry_size']:.4f}")

        # Most active trading hours
        if analysis['entry_times']:
            top_hours = sorted(analysis['entry_times'].items(), key=lambda x: x[1], reverse=True)[:3]
            print(f"  • Most active hours (UTC): {', '.join([f'{h}h' for h, _ in top_hours])}")

        return analysis

    def analyze_exit_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze when and how the vault exits positions"""
        print("\n📉 Analyzing Exit Patterns...")

        # Trades with closed PnL are exits
        exits = df[df['closed_pnl'] != 0].copy()

        if len(exits) == 0:
            print("  ⚠️  No closed positions found")
            return {}

        winners = exits[exits['closed_pnl'] > 0]
        losers = exits[exits['closed_pnl'] < 0]

        analysis = {
            'total_exits': len(exits),
            'winning_exits': len(winners),
            'losing_exits': len(losers),
            'win_rate': len(winners) / len(exits) * 100 if len(exits) > 0 else 0,
            'avg_win': winners['closed_pnl'].mean() if len(winners) > 0 else 0,
            'avg_loss': losers['closed_pnl'].mean() if len(losers) > 0 else 0,
            'total_pnl': exits['closed_pnl'].sum(),
            'best_trade': exits['closed_pnl'].max(),
            'worst_trade': exits['closed_pnl'].min(),
        }

        print(f"  • Total exits: {analysis['total_exits']}")
        print(f"  • Win Rate: {analysis['win_rate']:.1f}%")
        print(f"  • Avg Win: ${analysis['avg_win']:.2f}")
        print(f"  • Avg Loss: ${analysis['avg_loss']:.2f}")
        print(f"  • Total PnL: ${analysis['total_pnl']:.2f}")
        print(f"  • Best trade: ${analysis['best_trade']:.2f}")
        print(f"  • Worst trade: ${analysis['worst_trade']:.2f}")

        if analysis['avg_loss'] != 0:
            rr_ratio = abs(analysis['avg_win'] / analysis['avg_loss'])
            print(f"  • R/R Ratio: {rr_ratio:.2f}")

        return analysis

    def detect_position_sizing(self, df: pd.DataFrame) -> Dict:
        """Detect position sizing strategy"""
        print("\n💰 Analyzing Position Sizing...")

        entries = df[df['start_position'] == 0].copy() if 'start_position' in df.columns else df.copy()

        if len(entries) == 0:
            return {}

        sizes = entries['size'].values

        analysis = {
            'min_size': float(sizes.min()),
            'max_size': float(sizes.max()),
            'avg_size': float(sizes.mean()),
            'median_size': float(pd.Series(sizes).median()),
            'std_size': float(pd.Series(sizes).std()),
            'size_variation': float(sizes.std() / sizes.mean()) if sizes.mean() != 0 else 0
        }

        print(f"  • Avg size: {analysis['avg_size']:.4f}")
        print(f"  • Size range: {analysis['min_size']:.4f} - {analysis['max_size']:.4f}")
        print(f"  • Size variation: {analysis['size_variation']:.2%}")

        if analysis['size_variation'] < 0.2:
            print(f"  📌 Strategy: Fixed size (~{analysis['avg_size']:.4f})")
        else:
            print(f"  📌 Strategy: Variable sizing (ATR or volatility-based)")

        return analysis

    def generate_strategy_summary(self, df: pd.DataFrame) -> Dict:
        """Generate complete strategy summary"""
        print("\n" + "=" * 70)
        print("🎯 STRATEGY SUMMARY")
        print("=" * 70)

        entry_analysis = self.analyze_entry_patterns(df)
        exit_analysis = self.analyze_exit_patterns(df)
        sizing_analysis = self.detect_position_sizing(df)

        summary = {
            'vault_address': self.vault_address,
            'total_trades': len(df),
            'entry_patterns': entry_analysis,
            'exit_patterns': exit_analysis,
            'position_sizing': sizing_analysis,
            'analyzed_at': datetime.now().isoformat()
        }

        return summary

    def save_analysis(self, summary: Dict, filename: str = None):
        """Save analysis to JSON file"""
        if filename is None:
            filename = f"vault_analysis_{self.vault_address[:10]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(filename, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"\n💾 Analysis saved to: {filename}")


def main():
    # Vault to analyze
    vault_address = "0x9b55c8c948f988bcbe404cd070fc9ffffab8d31b"

    print("=" * 70)
    print("🔍 HYPERLIQUID VAULT REVERSE ENGINEERING")
    print("=" * 70)
    print(f"\nVault: {vault_address}")
    print()

    # Initialize analyzer
    analyzer = HyperliquidVaultAnalyzer(vault_address)

    # Fetch vault info
    vault_info = analyzer.fetch_vault_info()
    if vault_info:
        print(f"📊 Vault Info:")
        print(f"  Name: {vault_info.get('name', 'Unknown')}")
        print(f"  Portfolio Value: ${vault_info.get('portfolio_value', 0):,.2f}")
        print()

    # Fetch trades
    trades = analyzer.fetch_vault_trades(limit=1000)

    if not trades:
        print("❌ No trades found. Vault might be private or address incorrect.")
        return

    # Parse to DataFrame
    df = analyzer.parse_trades_to_dataframe()

    if df.empty:
        print("❌ Could not parse trades")
        return

    print(f"\n📅 Date range: {df['time'].min()} to {df['time'].max()}")
    print(f"📊 Total trades: {len(df)}")

    # Analyze strategy
    summary = analyzer.generate_strategy_summary(df)

    # Save analysis
    analyzer.save_analysis(summary)

    print("\n" + "=" * 70)
    print("✅ Analysis Complete!")
    print("=" * 70)
    print("\n💡 Next steps:")
    print("  1. Review the analysis JSON file")
    print("  2. Implement detected patterns in a strategy")
    print("  3. Backtest on real data")
    print("  4. Compare performance with original vault")


if __name__ == '__main__':
    main()
