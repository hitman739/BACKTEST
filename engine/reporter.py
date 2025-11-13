"""
Report Generation

Handles saving backtest results to files:
- summary.json - all metrics and configuration
- trades.csv - detailed trade log
- equity_curve.csv - equity progression
- config_snapshot.json - exact strategy configuration
"""

import json
from pathlib import Path
from typing import Dict
import pandas as pd
from datetime import datetime


class Reporter:
    """
    Generates and saves backtest reports
    """

    def __init__(self, report_dir: str = "./reports"):
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def create_run_directory(self, run_id: str) -> Path:
        """
        Create directory for a specific run

        Args:
            run_id: Unique run identifier

        Returns:
            Path to run directory
        """
        run_dir = self.report_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def save_summary(
        self,
        run_id: str,
        metrics: Dict,
        config: Dict
    ):
        """
        Save summary with metrics and configuration

        Args:
            run_id: Run identifier
            metrics: Performance metrics
            config: Backtest configuration
        """
        run_dir = self.create_run_directory(run_id)

        summary = {
            'run_id': run_id,
            'timestamp': datetime.now().isoformat(),
            'config': config,
            'metrics': metrics
        }

        summary_path = run_dir / 'summary.json'
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)

        print(f"Summary saved to: {summary_path}")

    def save_trades(
        self,
        run_id: str,
        trades_df: pd.DataFrame
    ):
        """
        Save trades to CSV

        Args:
            run_id: Run identifier
            trades_df: DataFrame with trade details
        """
        run_dir = self.create_run_directory(run_id)

        trades_path = run_dir / 'trades.csv'
        trades_df.to_csv(trades_path, index=False)

        print(f"Trades saved to: {trades_path} ({len(trades_df)} trades)")

    def save_equity_curve(
        self,
        run_id: str,
        equity_curve_df: pd.DataFrame
    ):
        """
        Save equity curve to CSV

        Args:
            run_id: Run identifier
            equity_curve_df: DataFrame with equity progression
        """
        run_dir = self.create_run_directory(run_id)

        equity_path = run_dir / 'equity_curve.csv'
        equity_curve_df.to_csv(equity_path, index=False)

        print(f"Equity curve saved to: {equity_path}")

    def save_config_snapshot(
        self,
        run_id: str,
        config: Dict
    ):
        """
        Save exact configuration snapshot

        Args:
            run_id: Run identifier
            config: Full configuration dictionary
        """
        run_dir = self.create_run_directory(run_id)

        config_path = run_dir / 'config_snapshot.json'
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2, default=str)

        print(f"Config snapshot saved to: {config_path}")

    def save_all(
        self,
        run_id: str,
        metrics: Dict,
        config: Dict,
        trades_df: pd.DataFrame,
        equity_curve_df: pd.DataFrame
    ):
        """
        Save all report files

        Args:
            run_id: Run identifier
            metrics: Performance metrics
            config: Backtest configuration
            trades_df: Trades DataFrame
            equity_curve_df: Equity curve DataFrame
        """
        print(f"\nSaving reports for run: {run_id}")
        print("=" * 60)

        self.save_summary(run_id, metrics, config)
        self.save_config_snapshot(run_id, config)

        if len(trades_df) > 0:
            self.save_trades(run_id, trades_df)
        else:
            print("No trades to save")

        if len(equity_curve_df) > 0:
            self.save_equity_curve(run_id, equity_curve_df)

        print("=" * 60)
        print(f"All reports saved to: {self.report_dir / run_id}\n")


def generate_report(
    run_id: str,
    metrics: Dict,
    config: Dict,
    trades_df: pd.DataFrame,
    equity_curve_df: pd.DataFrame,
    report_dir: str = "./reports"
):
    """
    Convenience function to generate complete report

    Args:
        run_id: Unique run identifier
        metrics: Performance metrics
        config: Backtest configuration
        trades_df: Trades DataFrame
        equity_curve_df: Equity curve DataFrame
        report_dir: Base directory for reports
    """
    reporter = Reporter(report_dir)
    reporter.save_all(run_id, metrics, config, trades_df, equity_curve_df)
