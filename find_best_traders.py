#!/usr/bin/env python3
"""
Find Best Hyperliquid Traders for Reverse Engineering

Traders are better than vaults because:
- More realistic win rates (60-80%)
- Use technical indicators (EMAs, RSI)
- Longer holding times (replicable)
- Not professional HFT firms
"""

import requests
import json
import sys

print("=" * 70)
print("🔍 FINDING BEST HYPERLIQUID TRADERS")
print("=" * 70)

url = "https://api.hyperliquid.xyz/info"

def analyze_trader(trader_address, symbol=None):
    """Analyze a trader's performance"""

    print(f"\n📊 Analyzing trader: {trader_address[:10]}...")
    print("-" * 70)

    # Fetch trades
    payload = {"type": "userFills", "user": trader_address}

    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code != 200:
            print(f"❌ API Error {response.status_code}")
            return None

        trades = response.json()

        if not isinstance(trades, list) or len(trades) == 0:
            print(f"❌ No trades found")
            return None

        print(f"✅ Total trades: {len(trades)}")

        # Filter by symbol if provided
        if symbol:
            trades = [t for t in trades if t.get('coin') == symbol]
            print(f"   Filtered to {symbol}: {len(trades)} trades")

        if len(trades) < 10:
            print(f"⚠️  Too few trades to analyze")
            return None

        # Analyze trades
        import pandas as pd
        df = pd.DataFrame(trades)

        # Basic stats
        df['timestamp'] = pd.to_datetime(df['time'].astype(int), unit='ms')
        df['price'] = df['px'].astype(float)
        df['size'] = df['sz'].astype(float)
        df['pnl'] = df.get('closedPnl', 0).astype(float)

        # Symbol distribution
        symbols = df['coin'].value_counts()
        print(f"\n📈 Symbols traded:")
        for sym, count in symbols.head(3).items():
            print(f"   {sym}: {count} trades")

        # Date range
        print(f"\n📅 Period:")
        print(f"   From: {df['timestamp'].min()}")
        print(f"   To: {df['timestamp'].max()}")
        days = (df['timestamp'].max() - df['timestamp'].min()).days
        print(f"   Duration: {days} days")

        # PnL analysis
        total_pnl = df['pnl'].sum()
        winners = df[df['pnl'] > 0]
        losers = df[df['pnl'] <= 0]

        win_rate = (len(winners) / len(df)) * 100 if len(df) > 0 else 0

        print(f"\n💰 Performance:")
        print(f"   Total PnL: ${total_pnl:.2f}")
        print(f"   Win Rate: {win_rate:.1f}%")
        print(f"   Winners: {len(winners)}")
        print(f"   Losers: {len(losers)}")

        if len(winners) > 0:
            print(f"   Avg Win: ${winners['pnl'].mean():.2f}")
        if len(losers) > 0:
            print(f"   Avg Loss: ${losers['pnl'].mean():.2f}")

        # Holding time estimation (requires position reconstruction)
        print(f"\n⏱️  Trade Frequency:")
        trades_per_day = len(df) / max(days, 1)
        print(f"   Trades/day: {trades_per_day:.1f}")

        # Time between trades
        df_sorted = df.sort_values('timestamp')
        time_diffs = df_sorted['timestamp'].diff().dt.total_seconds() / 60
        avg_time_between = time_diffs.median()
        print(f"   Median time between trades: {avg_time_between:.0f} mins")

        # Assessment
        print(f"\n✅ ASSESSMENT:")

        score = 0
        reasons = []

        # Win rate
        if 60 <= win_rate <= 85:
            score += 3
            reasons.append("✅ Good win rate (60-85%)")
        elif win_rate > 85:
            score += 1
            reasons.append("⚠️  High win rate (>85%) - might be too good")
        else:
            reasons.append("⚠️  Low win rate (<60%)")

        # Trade count
        if len(df) > 100:
            score += 2
            reasons.append("✅ Sufficient trades (>100)")
        elif len(df) > 50:
            score += 1
            reasons.append("⚠️  Moderate trades (50-100)")

        # PnL
        if total_pnl > 500:
            score += 2
            reasons.append("✅ Good total PnL (>$500)")
        elif total_pnl > 0:
            score += 1
            reasons.append("⚠️  Positive but small PnL")

        # Time between trades
        if avg_time_between > 30:
            score += 3
            reasons.append("✅ Good holding time (>30 mins)")
        elif avg_time_between > 10:
            score += 1
            reasons.append("⚠️  Short holding time (10-30 mins)")
        else:
            reasons.append("❌ Very short holding (<10 mins) - HFT")

        # Symbol
        top_symbol = symbols.index[0] if len(symbols) > 0 else None
        if top_symbol in ['BTC', 'ETH', 'SOL', 'AVAX']:
            score += 2
            reasons.append(f"✅ Trades popular symbol ({top_symbol})")
        else:
            reasons.append(f"⚠️  Exotic symbol ({top_symbol})")

        print()
        for reason in reasons:
            print(f"   {reason}")

        print(f"\n🎯 SCORE: {score}/12")

        if score >= 10:
            verdict = "🌟 EXCELLENT - Highly replicable!"
        elif score >= 7:
            verdict = "✅ GOOD - Worth analyzing"
        elif score >= 5:
            verdict = "⚠️  MODERATE - May work"
        else:
            verdict = "❌ POOR - Not recommended"

        print(f"   {verdict}")

        # Recommendation
        if score >= 7:
            print(f"\n💡 NEXT STEP:")
            print(f"   python3 reverse_engineer_vault_complete.py \\")
            print(f"     --vault {trader_address} \\")
            print(f"     --symbol {top_symbol} \\")
            print(f"     --timeframe 5m")

        return {
            'address': trader_address,
            'trades': len(df),
            'win_rate': win_rate,
            'pnl': total_pnl,
            'score': score,
            'symbol': top_symbol
        }

    except Exception as e:
        print(f"❌ Error: {e}")
        return None


print("\n💡 HOW TO FIND GOOD TRADERS:")
print("=" * 70)
print("""
1️⃣  VIA HYPERLIQUID LEADERBOARD:
   • Go to: https://app.hyperliquid.xyz/leaderboard
   • Look at top traders by PnL
   • Filter by timeframe (7d, 30d)
   • Click on trader to see details

2️⃣  VIA HYPERLIQUID EXPLORER:
   • Go to: https://app.hyperliquid.xyz/explorer
   • Browse recent large trades
   • Find traders with consistent wins
   • Copy their address (0x...)

3️⃣  CRITERIA FOR GOOD TRADERS:
   ✅ Win rate: 60-85%
   ✅ Symbol: BTC, ETH, SOL, AVAX
   ✅ Time between trades: > 30 mins
   ✅ Total trades: > 100
   ✅ Total PnL: > $500
   ✅ Active in last 7 days

4️⃣  TEST A TRADER:
   python3 find_best_traders.py <trader_address>

   Optional - filter by symbol:
   python3 find_best_traders.py <trader_address> SOL
""")

print("=" * 70)

# CLI mode
if len(sys.argv) > 1:
    trader_addr = sys.argv[1]
    symbol_filter = sys.argv[2] if len(sys.argv) > 2 else None

    result = analyze_trader(trader_addr, symbol_filter)

    if result and result['score'] >= 7:
        print("\n" + "=" * 70)
        print("✅ This trader looks GOOD for reverse engineering!")
        print("=" * 70)
else:
    print("\n📝 EXAMPLE USAGE:")
    print("   python3 find_best_traders.py 0xTRADER_ADDRESS")
    print("   python3 find_best_traders.py 0xTRADER_ADDRESS SOL")
    print()
