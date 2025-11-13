"""
Precise Rule Extractor
Converts ML patterns into precise, executable trading rules
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any
import json


class PreciseRuleExtractor:
    """
    Extracts precise trading rules from pattern analysis:
    - Entry conditions (LONG and SHORT with exact thresholds)
    - Exit conditions (stop loss, take profit, trailing, time-based)
    - Position sizing (fixed, adaptive, volatility-based)
    - Timing filters (hours, sessions, frequency limits)
    - Risk management (max drawdown, max positions, etc.)
    """

    def __init__(self):
        self.rules = {}

    def extract_rules(self, df: pd.DataFrame, pattern_analysis: Dict) -> Dict:
        """
        Extract comprehensive trading rules

        Returns:
            Dictionary with executable rules for strategy implementation
        """
        print("\n📋 EXTRACTING PRECISE RULES")
        print("=" * 70)

        self.rules = {
            'metadata': self._extract_metadata(df, pattern_analysis),
            'entry_rules': self._extract_entry_rules(df, pattern_analysis),
            'exit_rules': self._extract_exit_rules(df, pattern_analysis),
            'sizing_rules': self._extract_sizing_rules(df, pattern_analysis),
            'timing_rules': self._extract_timing_rules(df, pattern_analysis),
            'risk_management': self._extract_risk_rules(df, pattern_analysis),
            'filters': self._extract_filters(df, pattern_analysis)
        }

        print("\n✅ Rules extracted successfully")
        return self.rules

    def _extract_metadata(self, df: pd.DataFrame, analysis: Dict) -> Dict:
        """Extract strategy metadata"""

        summary = analysis.get('summary', {})

        return {
            'strategy_type': self._classify_strategy_type(df, analysis),
            'total_trades_analyzed': len(df),
            'win_rate': summary.get('win_rate', 0),
            'avg_holding_time_mins': summary.get('avg_holding_time_mins', 0),
            'directional_bias': 'long' if summary.get('long_ratio', 50) > 60 else ('short' if summary.get('short_ratio', 50) > 60 else 'neutral'),
            'avg_pnl_per_trade': summary.get('avg_pnl', 0),
            'sharpe_approx': summary.get('sharpe_approx', None)
        }

    def _classify_strategy_type(self, df: pd.DataFrame, analysis: Dict) -> str:
        """Classify the strategy type"""

        timing = analysis.get('timing_patterns', {})
        freq = timing.get('trade_frequency', {})

        avg_mins_between = freq.get('median_mins_between_trades', 1000)

        if avg_mins_between < 10:
            return 'HFT/Market Making'
        elif avg_mins_between < 60:
            return 'Scalping'
        elif avg_mins_between < 240:
            return 'Intraday'
        else:
            return 'Swing Trading'

    def _extract_entry_rules(self, df: pd.DataFrame, analysis: Dict) -> Dict:
        """Extract entry conditions for LONG and SHORT"""

        entry_patterns = analysis.get('entry_patterns', {})
        correlations = analysis.get('correlations', {})

        rules = {
            'long': self._extract_side_entry_rules(df, entry_patterns.get('long', {}), 'long'),
            'short': self._extract_side_entry_rules(df, entry_patterns.get('short', {}), 'short'),
            'top_predictive_features': []
        }

        # Top predictive features
        if 'top_positive_correlations' in correlations:
            rules['top_predictive_features'] = correlations['top_positive_correlations'][:5]

        return rules

    def _extract_side_entry_rules(self, df: pd.DataFrame, side_analysis: Dict, side: str) -> Dict:
        """Extract entry rules for a specific side"""

        if side_analysis.get('insufficient_data'):
            return {'enabled': False, 'reason': 'insufficient_data'}

        top_features = side_analysis.get('top_features', [])
        winner_conditions = side_analysis.get('winner_conditions', {})

        # Build conditions list
        conditions = []
        thresholds = {}

        for feature_data in top_features[:5]:  # Top 5 features
            feature = feature_data['feature']
            importance = feature_data['importance']

            if importance > 0.05 and feature in winner_conditions:  # Only if importance > 5%
                cond_data = winner_conditions[feature]
                winner_median = cond_data.get('winner_median')
                all_median = cond_data.get('all_median')

                if winner_median is not None and all_median is not None:
                    # Create condition
                    condition = self._create_condition(feature, winner_median, all_median)
                    if condition:
                        conditions.append(condition)
                        thresholds[feature] = {
                            'winner_value': winner_median,
                            'all_value': all_median,
                            'importance': importance
                        }

        return {
            'enabled': len(conditions) > 0,
            'num_trades': side_analysis.get('num_trades', 0),
            'win_rate': side_analysis.get('win_rate', 0),
            'conditions': conditions,
            'thresholds': thresholds,
            'logic': 'AND'  # All conditions must be true
        }

    def _create_condition(self, feature: str, winner_val: float, all_val: float) -> str:
        """Create a readable condition from feature and values"""

        # Map feature names to readable conditions
        conditions_map = {
            'ema20_above_ema50': 'EMA20 > EMA50' if winner_val > 0.5 else 'EMA20 < EMA50',
            'price_above_ema20': 'Price > EMA20' if winner_val > 0.5 else 'Price < EMA20',
            'price_above_ema50': 'Price > EMA50' if winner_val > 0.5 else 'Price < EMA50',
            'rsi_oversold': 'RSI < 30' if winner_val > 0.5 else 'RSI >= 30',
            'rsi_overbought': 'RSI > 70' if winner_val > 0.5 else 'RSI <= 70',
            'rsi_neutral': '40 <= RSI <= 60' if winner_val > 0.5 else 'RSI outside 40-60',
            'at_bb_upper': 'Price > BB_Upper' if winner_val > 0.5 else 'Price <= BB_Upper',
            'at_bb_lower': 'Price < BB_Lower' if winner_val > 0.5 else 'Price >= BB_Lower',
            'price_above_vwap': 'Price > VWAP' if winner_val > 0.5 else 'Price < VWAP',
            'high_volume': 'Volume > 1.5x MA' if winner_val > 0.5 else 'Volume <= 1.5x MA',
        }

        if feature in conditions_map:
            return conditions_map[feature]

        # For continuous features, create threshold condition
        if 'rsi' in feature.lower() and 'distance' not in feature.lower():
            return f"{feature} {'>' if winner_val > all_val else '<'} {winner_val:.1f}"
        elif 'pct' in feature or 'distance' in feature:
            return f"{feature} {'>' if winner_val > all_val else '<'} {winner_val:.3f}"
        elif 'percentile' in feature:
            return f"{feature} {'>' if winner_val > all_val else '<'} {winner_val:.0f}"
        else:
            return f"{feature} {'>' if winner_val > all_val else '<'} {winner_val:.2f}"

    def _extract_exit_rules(self, df: pd.DataFrame, analysis: Dict) -> Dict:
        """Extract exit conditions"""

        exit_patterns = analysis.get('exit_patterns', {})

        rules = {
            'stop_loss': self._extract_stop_loss(exit_patterns),
            'take_profit': self._extract_take_profit(exit_patterns),
            'trailing_stop': self._extract_trailing_stop(df, exit_patterns),
            'time_based_exit': self._extract_time_exit(df, exit_patterns),
            'exit_on_opposite_signal': False  # Would need more analysis
        }

        return rules

    def _extract_stop_loss(self, exit_patterns: Dict) -> Dict:
        """Extract stop loss rules"""

        inferred_sl = exit_patterns.get('inferred_stop_loss', {})

        if not inferred_sl:
            return {'enabled': False}

        median_mae = inferred_sl.get('median_mae_pct', 0)
        mean_mae = inferred_sl.get('mean_mae_pct', 0)

        # Use median as it's more robust
        sl_pct = median_mae

        return {
            'enabled': sl_pct > 0,
            'type': 'fixed_percentage',
            'value_pct': round(sl_pct, 2),
            'atr_multiple': None,  # Would calculate if ATR available
            'confidence': 'high' if inferred_sl.get('median_mae_pct') else 'medium'
        }

    def _extract_take_profit(self, exit_patterns: Dict) -> Dict:
        """Extract take profit rules"""

        inferred_tp = exit_patterns.get('inferred_take_profit', {})

        if not inferred_tp:
            return {'enabled': False}

        median_mfe = inferred_tp.get('median_mfe_pct', 0)

        return {
            'enabled': median_mfe > 0,
            'type': 'fixed_percentage',
            'value_pct': round(median_mfe, 2),
            'confidence': 'medium'
        }

    def _extract_trailing_stop(self, df: pd.DataFrame, exit_patterns: Dict) -> Dict:
        """Detect if trailing stop is used"""

        mfe_mae = exit_patterns.get('mfe_mae_analysis', {})
        capture_eff = mfe_mae.get('capture_efficiency', 0)

        # If capture efficiency > 70%, likely using trailing stop
        uses_trailing = capture_eff > 0.7

        return {
            'enabled': uses_trailing,
            'activation_r': 1.5,  # Activate after 1.5R profit
            'trail_amount_pct': 0.5,  # Trail by 0.5% (would need more data)
            'confidence': 'low'  # Hard to infer accurately
        }

    def _extract_time_exit(self, df: pd.DataFrame, exit_patterns: Dict) -> Dict:
        """Extract time-based exit rules"""

        holding_time = exit_patterns.get('holding_time', {})

        if not holding_time:
            return {'enabled': False}

        median_mins = holding_time.get('median_mins', 0)
        p75_mins = holding_time.get('percentile_75', 0)

        # If 75th percentile is significantly higher, might have time limit
        has_time_limit = p75_mins > median_mins * 2

        return {
            'enabled': has_time_limit,
            'max_holding_mins': round(p75_mins, 0) if has_time_limit else None,
            'confidence': 'low'
        }

    def _extract_sizing_rules(self, df: pd.DataFrame, analysis: Dict) -> Dict:
        """Extract position sizing rules"""

        sizing_patterns = analysis.get('sizing_patterns', {})

        if not sizing_patterns:
            return {'type': 'fixed', 'value': 1.0}

        size_stats = sizing_patterns.get('size_stats', {})
        cv = size_stats.get('cv', 0)  # Coefficient of variation

        # Check if adaptive sizing
        is_adaptive = sizing_patterns.get('adaptive_sizing', False)
        vol_corr = sizing_patterns.get('size_volatility_correlation', 0)

        if is_adaptive and abs(vol_corr) > 0.3:
            # Inverse correlation = risk-based sizing
            sizing_type = 'volatility_adjusted' if vol_corr < -0.2 else 'volatility_scaled'
        elif cv < 0.2:
            # Low variation = fixed size
            sizing_type = 'fixed'
        else:
            # Some variation = possibly adaptive
            sizing_type = 'adaptive'

        return {
            'type': sizing_type,
            'base_size': round(size_stats.get('median', 1.0), 2),
            'min_size': round(size_stats.get('mean', 1.0) - size_stats.get('std', 0), 2),
            'max_size': round(size_stats.get('mean', 1.0) + size_stats.get('std', 0), 2),
            'volatility_correlation': round(vol_corr, 2),
            'confidence': 'high' if cv < 0.3 else 'medium'
        }

    def _extract_timing_rules(self, df: pd.DataFrame, analysis: Dict) -> Dict:
        """Extract timing filters"""

        timing_patterns = analysis.get('timing_patterns', {})

        rules = {}

        # Active hours
        if 'most_active_hours' in timing_patterns:
            active_hours = list(timing_patterns['most_active_hours'].keys())
            rules['active_hours'] = [int(h) for h in active_hours[:5]]

        # Preferred sessions
        if 'session_distribution' in timing_patterns:
            sessions = timing_patterns['session_distribution']
            total = sum(sessions.values())
            preferred = [s for s, count in sessions.items() if count / total > 0.3]
            rules['preferred_sessions'] = preferred

        # Day of week filter
        if 'day_of_week_distribution' in timing_patterns:
            dow = timing_patterns['day_of_week_distribution']
            total = sum(dow.values())
            active_days = [int(d) for d, count in dow.items() if count / total > 0.1]
            rules['active_days_of_week'] = active_days

        # Trade frequency limits
        if 'trade_frequency' in timing_patterns:
            freq = timing_patterns['trade_frequency']
            rules['min_minutes_between_trades'] = round(freq.get('median_mins_between_trades', 0) * 0.5, 1)
            rules['max_trades_per_day'] = round(freq.get('trades_per_day_approx', 100), 0)

        return rules

    def _extract_risk_rules(self, df: pd.DataFrame, analysis: Dict) -> Dict:
        """Extract risk management rules"""

        risk_patterns = analysis.get('risk_patterns', {})
        summary = analysis.get('summary', {})

        rules = {
            'max_risk_per_trade_pct': 1.0,  # Default, would need account data
            'target_win_rate': round(risk_patterns.get('overall_win_rate', 50), 1),
            'expected_avg_r': round(summary.get('avg_pnl', 0), 2),
        }

        # Risk-reward ratio
        if 'avg_risk_reward_ratio' in risk_patterns:
            rules['target_risk_reward_ratio'] = round(risk_patterns['avg_risk_reward_ratio'], 2)

        # Preferred regimes
        if 'win_rate_by_volatility' in risk_patterns:
            vol_wr = risk_patterns['win_rate_by_volatility']
            best_vol = max(vol_wr.items(), key=lambda x: x[1])[0] if vol_wr else None
            rules['preferred_volatility_regime'] = best_vol

        if 'win_rate_by_trend' in risk_patterns:
            trend_wr = risk_patterns['win_rate_by_trend']
            best_trend = max(trend_wr.items(), key=lambda x: x[1])[0] if trend_wr else None
            rules['preferred_trend_regime'] = best_trend

        return rules

    def _extract_filters(self, df: pd.DataFrame, analysis: Dict) -> Dict:
        """Extract additional filters"""

        filters = {}

        # Volatility filter
        risk_patterns = analysis.get('risk_patterns', {})
        if 'preferred_volatility_regime' in risk_patterns:
            filters['volatility_filter'] = {
                'enabled': True,
                'preferred_regime': risk_patterns['preferred_volatility_regime']
            }

        # Trend filter
        if 'preferred_trend_regime' in risk_patterns:
            filters['trend_filter'] = {
                'enabled': True,
                'preferred_regime': risk_patterns['preferred_trend_regime']
            }

        return filters

    def generate_strategy_summary(self) -> str:
        """Generate human-readable strategy summary"""

        summary_lines = []

        summary_lines.append("=" * 70)
        summary_lines.append("EXTRACTED STRATEGY RULES")
        summary_lines.append("=" * 70)

        # Metadata
        meta = self.rules.get('metadata', {})
        summary_lines.append(f"\n📊 STRATEGY TYPE: {meta.get('strategy_type', 'Unknown')}")
        summary_lines.append(f"   Win Rate: {meta.get('win_rate', 0):.1f}%")
        summary_lines.append(f"   Directional Bias: {meta.get('directional_bias', 'neutral').upper()}")
        summary_lines.append(f"   Avg Holding Time: {meta.get('avg_holding_time_mins', 0):.0f} minutes")

        # Entry rules
        summary_lines.append(f"\n📈 ENTRY RULES:")
        entry = self.rules.get('entry_rules', {})

        long_rules = entry.get('long', {})
        if long_rules.get('enabled'):
            summary_lines.append(f"  LONG ({long_rules.get('win_rate', 0):.1f}% WR):")
            for cond in long_rules.get('conditions', []):
                summary_lines.append(f"    - {cond}")

        short_rules = entry.get('short', {})
        if short_rules.get('enabled'):
            summary_lines.append(f"  SHORT ({short_rules.get('win_rate', 0):.1f}% WR):")
            for cond in short_rules.get('conditions', []):
                summary_lines.append(f"    - {cond}")

        # Exit rules
        summary_lines.append(f"\n📉 EXIT RULES:")
        exit_rules = self.rules.get('exit_rules', {})

        sl = exit_rules.get('stop_loss', {})
        if sl.get('enabled'):
            summary_lines.append(f"  Stop Loss: {sl.get('value_pct', 0):.2f}% ({sl.get('confidence', 'low')} confidence)")

        tp = exit_rules.get('take_profit', {})
        if tp.get('enabled'):
            summary_lines.append(f"  Take Profit: {tp.get('value_pct', 0):.2f}% ({tp.get('confidence', 'low')} confidence)")

        trail = exit_rules.get('trailing_stop', {})
        if trail.get('enabled'):
            summary_lines.append(f"  Trailing Stop: Enabled (activate at {trail.get('activation_r', 0):.1f}R)")

        # Sizing
        summary_lines.append(f"\n📏 POSITION SIZING:")
        sizing = self.rules.get('sizing_rules', {})
        summary_lines.append(f"  Type: {sizing.get('type', 'fixed')}")
        summary_lines.append(f"  Base Size: {sizing.get('base_size', 1.0):.2f}")

        # Timing
        summary_lines.append(f"\n⏰ TIMING RULES:")
        timing = self.rules.get('timing_rules', {})
        if 'active_hours' in timing:
            summary_lines.append(f"  Active Hours: {timing['active_hours']}")
        if 'preferred_sessions' in timing:
            summary_lines.append(f"  Preferred Sessions: {timing['preferred_sessions']}")

        summary_lines.append("\n" + "=" * 70)

        return "\n".join(summary_lines)
