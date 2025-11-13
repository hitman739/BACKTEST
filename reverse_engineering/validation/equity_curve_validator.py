"""
Equity Curve Validator
Compares inferred strategy performance with original vault performance
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple, List
import json
from pathlib import Path


class EquityCurveValidator:
    """
    Validates the inferred strategy by comparing equity curves:
    - Original vault equity curve
    - Simulated equity curve from extracted rules
    - Statistical comparison (correlation, drawdown, returns)
    - Trade-by-trade comparison
    """

    def __init__(self):
        self.vault_curve = None
        self.simulated_curve = None
        self.comparison_metrics = {}

    def validate(self, vault_positions: pd.DataFrame, simulated_positions: pd.DataFrame = None) -> Dict:
        """
        Validate inferred strategy against vault performance

        Args:
            vault_positions: Actual vault positions
            simulated_positions: Positions from backtested inferred strategy (optional)

        Returns:
            Comprehensive validation metrics
        """
        print("\n🔬 EQUITY CURVE VALIDATION")
        print("=" * 70)

        validation = {
            'vault_performance': {},
            'similarity_metrics': {},
            'trade_pattern_match': {},
            'recommendations': []
        }

        # Vault performance
        validation['vault_performance'] = self._analyze_vault_performance(vault_positions)

        # Build equity curves
        vault_curve = self._build_equity_curve(vault_positions)
        validation['vault_equity_curve'] = self._summarize_equity_curve(vault_curve, 'vault')

        # If simulated data available, compare
        if simulated_positions is not None and len(simulated_positions) > 0:
            sim_curve = self._build_equity_curve(simulated_positions)
            validation['simulated_equity_curve'] = self._summarize_equity_curve(sim_curve, 'simulated')

            # Comparison
            validation['similarity_metrics'] = self._compare_curves(vault_curve, sim_curve)
            validation['trade_pattern_match'] = self._compare_trade_patterns(
                vault_positions, simulated_positions
            )

            # Recommendations
            validation['recommendations'] = self._generate_recommendations(validation)

        print("\n✅ Validation complete")
        return validation

    def _analyze_vault_performance(self, positions: pd.DataFrame) -> Dict:
        """Analyze vault performance metrics"""

        if positions.empty:
            return {}

        total_pnl = positions['pnl'].sum()
        winners = positions[positions['pnl'] > 0]
        losers = positions[positions['pnl'] <= 0]

        metrics = {
            'total_trades': len(positions),
            'total_pnl': float(total_pnl),
            'win_rate': (len(winners) / len(positions)) * 100 if len(positions) > 0 else 0,
            'avg_win': float(winners['pnl'].mean()) if len(winners) > 0 else 0,
            'avg_loss': float(losers['pnl'].mean()) if len(losers) > 0 else 0,
            'profit_factor': abs(winners['pnl'].sum() / losers['pnl'].sum()) if len(losers) > 0 and losers['pnl'].sum() != 0 else 0,
            'avg_holding_mins': float(positions['holding_time_mins'].mean()),
            'largest_win': float(winners['pnl'].max()) if len(winners) > 0 else 0,
            'largest_loss': float(losers['pnl'].min()) if len(losers) > 0 else 0,
        }

        # Return metrics
        if 'return_pct' in positions.columns:
            returns = positions['return_pct'].dropna()
            if len(returns) > 0:
                metrics['avg_return_pct'] = float(returns.mean())
                metrics['return_std'] = float(returns.std())
                metrics['sharpe_ratio'] = (returns.mean() / returns.std()) if returns.std() > 0 else 0

        # R-multiples
        if 'r_multiple' in positions.columns:
            r_mult = positions['r_multiple'].replace([np.inf, -np.inf], np.nan).dropna()
            if len(r_mult) > 0:
                metrics['avg_r_multiple'] = float(r_mult.mean())
                metrics['median_r_multiple'] = float(r_mult.median())

        return metrics

    def _build_equity_curve(self, positions: pd.DataFrame) -> pd.DataFrame:
        """Build cumulative equity curve from positions"""

        if positions.empty:
            return pd.DataFrame()

        # Sort by exit time
        df = positions.sort_values('exit_time').copy()

        # Cumulative PnL
        df['cumulative_pnl'] = df['pnl'].cumsum()

        # Drawdown
        df['peak_pnl'] = df['cumulative_pnl'].cumsum().expanding().max()
        df['drawdown'] = df['cumulative_pnl'] - df['peak_pnl']
        df['drawdown_pct'] = (df['drawdown'] / (df['peak_pnl'] + 1)) * 100

        return df[['exit_time', 'pnl', 'cumulative_pnl', 'peak_pnl', 'drawdown', 'drawdown_pct']]

    def _summarize_equity_curve(self, equity_curve: pd.DataFrame, label: str) -> Dict:
        """Summarize equity curve statistics"""

        if equity_curve.empty:
            return {}

        max_dd = equity_curve['drawdown'].min()
        max_dd_pct = equity_curve['drawdown_pct'].min()

        return {
            'label': label,
            'final_pnl': float(equity_curve['cumulative_pnl'].iloc[-1]),
            'max_drawdown': float(max_dd),
            'max_drawdown_pct': float(max_dd_pct),
            'total_trades': len(equity_curve),
            'start_date': str(equity_curve['exit_time'].min()),
            'end_date': str(equity_curve['exit_time'].max())
        }

    def _compare_curves(self, vault_curve: pd.DataFrame, sim_curve: pd.DataFrame) -> Dict:
        """Compare two equity curves"""

        if vault_curve.empty or sim_curve.empty:
            return {'error': 'Missing data'}

        # Align curves by time (simplified - match by trade number)
        min_len = min(len(vault_curve), len(sim_curve))

        vault_pnl = vault_curve['cumulative_pnl'].iloc[:min_len].values
        sim_pnl = sim_curve['cumulative_pnl'].iloc[:min_len].values

        # Correlation
        correlation = np.corrcoef(vault_pnl, sim_pnl)[0, 1]

        # PnL difference
        pnl_diff = vault_pnl[-1] - sim_pnl[-1]
        pnl_diff_pct = (pnl_diff / abs(vault_pnl[-1])) * 100 if vault_pnl[-1] != 0 else 0

        # Drawdown comparison
        vault_dd = vault_curve['drawdown'].min()
        sim_dd = sim_curve['drawdown'].min()
        dd_diff_pct = ((sim_dd - vault_dd) / abs(vault_dd)) * 100 if vault_dd != 0 else 0

        # Mean squared error
        mse = np.mean((vault_pnl - sim_pnl) ** 2)
        rmse = np.sqrt(mse)

        # Direction accuracy (are they moving in same direction?)
        vault_returns = np.diff(vault_pnl)
        sim_returns = np.diff(sim_pnl)
        same_direction = np.sign(vault_returns) == np.sign(sim_returns)
        direction_accuracy = same_direction.sum() / len(same_direction) * 100

        return {
            'correlation': float(correlation),
            'final_pnl_diff': float(pnl_diff),
            'final_pnl_diff_pct': float(pnl_diff_pct),
            'drawdown_diff_pct': float(dd_diff_pct),
            'rmse': float(rmse),
            'direction_accuracy_pct': float(direction_accuracy),
            'trades_compared': min_len,
            'similarity_score': float(correlation * 0.5 + (direction_accuracy / 100) * 0.5)  # Composite score
        }

    def _compare_trade_patterns(self, vault_pos: pd.DataFrame, sim_pos: pd.DataFrame) -> Dict:
        """Compare trade-level patterns"""

        comparison = {}

        # Win rate comparison
        vault_wr = (vault_pos['pnl'] > 0).sum() / len(vault_pos) * 100
        sim_wr = (sim_pos['pnl'] > 0).sum() / len(sim_pos) * 100

        comparison['win_rate'] = {
            'vault': float(vault_wr),
            'simulated': float(sim_wr),
            'diff': float(sim_wr - vault_wr)
        }

        # Holding time comparison
        comparison['holding_time'] = {
            'vault_median_mins': float(vault_pos['holding_time_mins'].median()),
            'simulated_median_mins': float(sim_pos['holding_time_mins'].median()),
            'diff_mins': float(sim_pos['holding_time_mins'].median() - vault_pos['holding_time_mins'].median())
        }

        # Trade frequency
        vault_freq = len(vault_pos) / ((vault_pos['exit_time'].max() - vault_pos['entry_time'].min()).total_seconds() / 86400)
        sim_freq = len(sim_pos) / ((sim_pos['exit_time'].max() - sim_pos['entry_time'].min()).total_seconds() / 86400)

        comparison['trade_frequency'] = {
            'vault_trades_per_day': float(vault_freq),
            'simulated_trades_per_day': float(sim_freq),
            'diff': float(sim_freq - vault_freq)
        }

        # Directional bias
        vault_long_ratio = (vault_pos['side'] == 'long').sum() / len(vault_pos) * 100
        sim_long_ratio = (sim_pos['side'] == 'long').sum() / len(sim_pos) * 100

        comparison['directional_bias'] = {
            'vault_long_pct': float(vault_long_ratio),
            'simulated_long_pct': float(sim_long_ratio),
            'diff': float(sim_long_ratio - vault_long_ratio)
        }

        return comparison

    def _generate_recommendations(self, validation: Dict) -> List[str]:
        """Generate recommendations for improving strategy accuracy"""

        recommendations = []

        similarity = validation.get('similarity_metrics', {})
        trade_match = validation.get('trade_pattern_match', {})

        # Correlation
        corr = similarity.get('correlation', 0)
        if corr < 0.5:
            recommendations.append("LOW CORRELATION: Strategy differs significantly from vault. Review entry/exit rules.")
        elif corr < 0.7:
            recommendations.append("MODERATE CORRELATION: Strategy captures some patterns. Fine-tune timing and sizing.")
        else:
            recommendations.append("HIGH CORRELATION: Strategy closely matches vault behavior!")

        # Direction accuracy
        dir_acc = similarity.get('direction_accuracy_pct', 0)
        if dir_acc < 60:
            recommendations.append("LOW DIRECTION ACCURACY: Entry signals may be incorrect. Review feature importance.")
        elif dir_acc < 75:
            recommendations.append("MODERATE DIRECTION ACCURACY: Entry logic partially correct. Check timing filters.")

        # Win rate difference
        wr = trade_match.get('win_rate', {})
        wr_diff = abs(wr.get('diff', 0))
        if wr_diff > 10:
            recommendations.append(f"WIN RATE MISMATCH ({wr_diff:.1f}%): Review stop loss and take profit levels.")

        # Trade frequency
        freq = trade_match.get('trade_frequency', {})
        freq_diff = abs(freq.get('diff', 0))
        if freq_diff > 5:
            recommendations.append(f"FREQUENCY MISMATCH: Vault trades {freq.get('vault_trades_per_day', 0):.1f}/day, simulated {freq.get('simulated_trades_per_day', 0):.1f}/day. Check timing filters.")

        # Holding time
        holding = trade_match.get('holding_time', {})
        holding_diff = abs(holding.get('diff_mins', 0))
        if holding_diff > 30:
            recommendations.append(f"HOLDING TIME MISMATCH: Review exit conditions (trailing stop, time-based exit).")

        if not recommendations:
            recommendations.append("Strategy validation looks good! Consider live testing with small size.")

        return recommendations

    def save_validation_report(self, validation: Dict, output_dir: str):
        """Save validation report to file"""

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save JSON
        json_path = output_path / "validation_report.json"
        with open(json_path, 'w') as f:
            json.dump(validation, f, indent=2, default=str)

        print(f"💾 Validation report saved to: {json_path}")

        # Generate text report
        text_report = self._generate_text_report(validation)
        text_path = output_path / "validation_report.txt"
        with open(text_path, 'w') as f:
            f.write(text_report)

        print(f"💾 Text report saved to: {text_path}")

    def _generate_text_report(self, validation: Dict) -> str:
        """Generate human-readable validation report"""

        lines = []

        lines.append("=" * 70)
        lines.append("STRATEGY VALIDATION REPORT")
        lines.append("=" * 70)

        # Vault performance
        vault_perf = validation.get('vault_performance', {})
        lines.append("\n📊 VAULT PERFORMANCE:")
        lines.append(f"  Total Trades: {vault_perf.get('total_trades', 0)}")
        lines.append(f"  Win Rate: {vault_perf.get('win_rate', 0):.1f}%")
        lines.append(f"  Total PnL: ${vault_perf.get('total_pnl', 0):.2f}")
        lines.append(f"  Profit Factor: {vault_perf.get('profit_factor', 0):.2f}")
        lines.append(f"  Avg R-Multiple: {vault_perf.get('avg_r_multiple', 0):.2f}")

        # Similarity metrics
        similarity = validation.get('similarity_metrics', {})
        if similarity:
            lines.append("\n📈 SIMILARITY METRICS:")
            lines.append(f"  Correlation: {similarity.get('correlation', 0):.3f}")
            lines.append(f"  Direction Accuracy: {similarity.get('direction_accuracy_pct', 0):.1f}%")
            lines.append(f"  Similarity Score: {similarity.get('similarity_score', 0):.3f}")
            lines.append(f"  Final PnL Difference: {similarity.get('final_pnl_diff_pct', 0):.1f}%")

        # Recommendations
        recommendations = validation.get('recommendations', [])
        if recommendations:
            lines.append("\n💡 RECOMMENDATIONS:")
            for rec in recommendations:
                lines.append(f"  • {rec}")

        lines.append("\n" + "=" * 70)

        return "\n".join(lines)
