"""
Rule Extraction
Converts ML patterns into human-readable, structured rules
"""

import json
from pathlib import Path
from typing import Dict, List


class RuleExtractor:
    """Extracts trading rules from pattern analysis"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.rules = {}

    def extract_rules(self, analysis_results: dict) -> dict:
        """
        Convert analysis results into structured rules

        Returns RuleSpec dict that can be used to generate strategies
        """
        print("\n" + "=" * 70)
        print("📋 RULE EXTRACTION")
        print("=" * 70)

        rules = {
            'name': 'Vault Clone Strategy v1',
            'entry': self._extract_entry_rules(analysis_results.get('entry', {})),
            'exit': self._extract_exit_rules(analysis_results.get('exit', {})),
            'risk': self._extract_risk_rules(analysis_results.get('risk', {}))
        }

        # Save rules
        filepath = self.output_dir / "rule_spec.json"
        with open(filepath, 'w') as f:
            json.dump(rules, f, indent=2)

        print(f"\n💾 Rules saved to: {filepath}")

        self.rules = rules
        return rules

    def _extract_entry_rules(self, entry_analysis: dict) -> dict:
        """Extract entry rules from analysis"""

        print("\n📈 Entry Rules:")

        rules = {
            'long': {},
            'short': {}
        }

        # Extract top features
        feature_importance = entry_analysis.get('feature_importance', [])
        if feature_importance:
            top_features = [f for f in feature_importance[:5] if f['importance'] > 0.05]

            conditions = []
            for feat in top_features:
                name = feat['feature']

                # Convert feature names to conditions
                if 'ema_bullish' in name:
                    conditions.append("EMA(20) > EMA(50)")
                elif 'price_above_ema' in name:
                    conditions.append("close > EMA(20)")
                elif 'rsi_oversold' in name:
                    conditions.append("RSI < 30")
                elif 'rsi_overbought' in name:
                    conditions.append("RSI > 70")
                elif 'atr_percentile' in name:
                    conditions.append("ATR in top 30% (high volatility)")

            rules['long']['conditions'] = conditions

        # Extract time patterns
        patterns = entry_analysis.get('patterns', {})
        if 'active_hours' in patterns:
            rules['long']['active_hours'] = patterns['active_hours']
            print(f"  • Active hours: {patterns['active_hours']}")

        # Directional bias
        if patterns.get('ema_bullish_pct', 0) > 70:
            rules['long']['preferred'] = True
            rules['short']['enabled'] = False
            print(f"  • Strategy: LONG ONLY")
        elif patterns.get('ema_bullish_pct', 0) < 30:
            rules['long']['enabled'] = False
            rules['short']['preferred'] = True
            print(f"  • Strategy: SHORT ONLY")

        if conditions:
            print(f"  • Entry conditions:")
            for cond in conditions:
                print(f"    - {cond}")

        return rules

    def _extract_exit_rules(self, exit_analysis: dict) -> dict:
        """Extract exit rules from analysis"""

        print("\n📉 Exit Rules:")

        rules = {
            'stop_loss': {},
            'take_profit': {},
            'trailing': {}
        }

        mfe_mae = exit_analysis.get('mfe_mae', {})

        # Stop loss (from MAE)
        mae_losers = mfe_mae.get('avg_mae_losers', 0)
        if mae_losers != 0:
            sl_r = abs(mae_losers) * 1.2  # Add 20% buffer
            rules['stop_loss']['type'] = 'fixed_r'
            rules['stop_loss']['value'] = round(sl_r, 2)
            print(f"  • Stop Loss: {sl_r:.2f}R")

        # Take profit (from MFE)
        mfe_winners = mfe_mae.get('avg_mfe_winners', 0)
        if mfe_winners > 0:
            tp_r = mfe_winners * 0.8  # Conservative TP
            rules['take_profit']['type'] = 'fixed_r'
            rules['take_profit']['value'] = round(tp_r, 2)
            print(f"  • Take Profit: {tp_r:.2f}R")

        # Infer trailing
        exit_type = exit_analysis.get('exit_type', '')
        if exit_type == 'trailing':
            rules['trailing']['enabled'] = True
            rules['trailing']['activation'] = round(tp_r * 0.5, 2) if tp_r else 1.0
            rules['trailing']['distance'] = 0.5
            print(f"  • Trailing Stop: Enabled")
            print(f"    - Activation: {rules['trailing']['activation']}R")

        # Holding time
        holding = exit_analysis.get('holding', {})
        if holding:
            avg_holding = holding.get('avg', 0)
            if avg_holding < 30:
                rules['timeout'] = 10  # bars
                print(f"  • Timeout: 10 bars (scalping)")
            elif avg_holding < 120:
                rules['timeout'] = 20  # bars
                print(f"  • Timeout: 20 bars")

        return rules

    def _extract_risk_rules(self, risk_analysis: dict) -> dict:
        """Extract risk management rules"""

        print("\n💰 Risk Management:")

        rules = {}

        # Position sizing
        sizing = risk_analysis.get('sizing', {})
        if sizing:
            cv = sizing.get('cv', 0)
            if cv < 0.2:
                rules['position_sizing'] = {
                    'type': 'fixed',
                    'size': round(sizing.get('avg', 0), 4)
                }
                print(f"  • Position Size: FIXED ({rules['position_sizing']['size']})")
            else:
                rules['position_sizing'] = {
                    'type': 'risk_based',
                    'risk_pct': 1.0
                }
                print(f"  • Position Size: RISK-BASED (1% per trade)")

        # Directional bias
        bias = risk_analysis.get('directional_bias', {})
        if bias:
            long_pct = bias.get('long_pct', 50)
            if long_pct > 80:
                rules['directional_bias'] = 'long_only'
                print(f"  • Direction: LONG ONLY")
            elif long_pct < 20:
                rules['directional_bias'] = 'short_only'
                print(f"  • Direction: SHORT ONLY")

        # Win rate
        win_rate = risk_analysis.get('win_rate', 0)
        rules['expected_win_rate'] = round(win_rate, 1)
        print(f"  • Expected Win Rate: {win_rate:.1f}%")

        return rules

    def print_summary(self):
        """Print human-readable rule summary"""

        if not self.rules:
            return

        print("\n" + "=" * 70)
        print("📝 RULE SUMMARY")
        print("=" * 70)

        print(f"\nStrategy: {self.rules['name']}")

        # Entry
        entry = self.rules.get('entry', {})
        if entry.get('long', {}).get('conditions'):
            print(f"\nEntry (Long):")
            for cond in entry['long']['conditions']:
                print(f"  ✓ {cond}")

        # Exit
        exit_rules = self.rules.get('exit', {})
        if exit_rules:
            print(f"\nExit:")
            if exit_rules.get('stop_loss'):
                print(f"  • SL: {exit_rules['stop_loss'].get('value', 0)}R")
            if exit_rules.get('take_profit'):
                print(f"  • TP: {exit_rules['take_profit'].get('value', 0)}R")
            if exit_rules.get('trailing', {}).get('enabled'):
                print(f"  • Trailing: Yes (activate at {exit_rules['trailing'].get('activation', 0)}R)")

        # Risk
        risk = self.rules.get('risk', {})
        if risk:
            print(f"\nRisk Management:")
            if risk.get('position_sizing'):
                sizing = risk['position_sizing']
                print(f"  • Sizing: {sizing.get('type', 'unknown')}")
            if risk.get('expected_win_rate'):
                print(f"  • Expected WR: {risk['expected_win_rate']}%")
