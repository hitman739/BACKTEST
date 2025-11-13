"""
Performance Metrics Calculation

Calculates comprehensive trading metrics:
- Return metrics (Total PnL, Return %, ROI)
- Win/Loss metrics (Win Rate, Profit Factor, Expectancy)
- Risk metrics (Sharpe, Sortino, Max Drawdown, Calmar)
- Trade statistics (# Trades, Avg Duration, Avg R)
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime


class PerformanceMetrics:
    """
    Calculate comprehensive performance metrics from trades and equity curve
    """

    def __init__(
        self,
        trades_df: pd.DataFrame,
        equity_curve_df: pd.DataFrame,
        initial_balance: float,
        risk_free_rate: float = 0.0
    ):
        """
        Initialize metrics calculator

        Args:
            trades_df: DataFrame of trades
            equity_curve_df: DataFrame of equity curve
            initial_balance: Starting balance
            risk_free_rate: Risk-free rate for Sharpe/Sortino (annualized)
        """
        self.trades_df = trades_df
        self.equity_curve_df = equity_curve_df
        self.initial_balance = initial_balance
        self.risk_free_rate = risk_free_rate

    def calculate_all(self) -> Dict:
        """
        Calculate all metrics

        Returns:
            Dictionary with all performance metrics
        """
        metrics = {}

        # Basic metrics
        metrics.update(self._calculate_return_metrics())
        metrics.update(self._calculate_trade_metrics())
        metrics.update(self._calculate_win_loss_metrics())
        metrics.update(self._calculate_risk_metrics())
        metrics.update(self._calculate_drawdown_metrics())

        return metrics

    def _calculate_return_metrics(self) -> Dict:
        """Calculate return-based metrics"""
        if len(self.equity_curve_df) == 0:
            return {
                'total_pnl': 0.0,
                'total_return_pct': 0.0,
                'final_equity': self.initial_balance
            }

        final_equity = self.equity_curve_df['equity'].iloc[-1]
        total_pnl = final_equity - self.initial_balance
        total_return_pct = (total_pnl / self.initial_balance) * 100

        return {
            'total_pnl': total_pnl,
            'total_return_pct': total_return_pct,
            'final_equity': final_equity,
            'initial_balance': self.initial_balance
        }

    def _calculate_trade_metrics(self) -> Dict:
        """Calculate trade statistics"""
        if len(self.trades_df) == 0:
            return {
                'total_trades': 0,
                'avg_trade_duration_bars': 0,
                'avg_pnl_per_trade': 0.0,
                'avg_return_per_trade_pct': 0.0
            }

        num_trades = len(self.trades_df)
        avg_duration = self.trades_df['duration_bars'].mean() if 'duration_bars' in self.trades_df else 0
        avg_pnl = self.trades_df['net_pnl'].mean()
        avg_return_pct = self.trades_df['pnl_percent'].mean()

        return {
            'total_trades': num_trades,
            'avg_trade_duration_bars': avg_duration,
            'avg_pnl_per_trade': avg_pnl,
            'avg_return_per_trade_pct': avg_return_pct
        }

    def _calculate_win_loss_metrics(self) -> Dict:
        """Calculate win/loss statistics"""
        if len(self.trades_df) == 0:
            return {
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate_pct': 0.0,
                'profit_factor': 0.0,
                'expectancy': 0.0,
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'avg_r_multiple': 0.0
            }

        winning_trades = self.trades_df[self.trades_df['net_pnl'] > 0]
        losing_trades = self.trades_df[self.trades_df['net_pnl'] <= 0]

        num_wins = len(winning_trades)
        num_losses = len(losing_trades)
        total_trades = len(self.trades_df)

        win_rate = (num_wins / total_trades * 100) if total_trades > 0 else 0

        # Profit factor
        gross_profit = winning_trades['net_pnl'].sum() if num_wins > 0 else 0
        gross_loss = abs(losing_trades['net_pnl'].sum()) if num_losses > 0 else 0
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0

        # Expectancy
        avg_win = winning_trades['net_pnl'].mean() if num_wins > 0 else 0
        avg_loss = losing_trades['net_pnl'].mean() if num_losses > 0 else 0
        win_rate_decimal = win_rate / 100
        expectancy = (win_rate_decimal * avg_win) + ((1 - win_rate_decimal) * avg_loss)

        # R-multiples
        avg_r = 0.0
        if 'r_multiple' in self.trades_df and self.trades_df['r_multiple'].notna().any():
            avg_r = self.trades_df['r_multiple'].mean()

        return {
            'winning_trades': num_wins,
            'losing_trades': num_losses,
            'win_rate_pct': win_rate,
            'profit_factor': profit_factor,
            'expectancy': expectancy,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'avg_r_multiple': avg_r
        }

    def _calculate_risk_metrics(self) -> Dict:
        """Calculate risk-adjusted metrics (Sharpe, Sortino)"""
        if len(self.equity_curve_df) < 2:
            return {
                'sharpe_ratio': 0.0,
                'sortino_ratio': 0.0
            }

        # Calculate returns
        returns = self.equity_curve_df['equity'].pct_change().dropna()

        if len(returns) == 0:
            return {
                'sharpe_ratio': 0.0,
                'sortino_ratio': 0.0
            }

        # Sharpe Ratio
        mean_return = returns.mean()
        std_return = returns.std()

        # Annualize (assume 365 periods per year for crypto)
        periods_per_year = 365
        annualized_return = mean_return * periods_per_year
        annualized_std = std_return * np.sqrt(periods_per_year)

        sharpe = ((annualized_return - self.risk_free_rate) / annualized_std) if annualized_std > 0 else 0

        # Sortino Ratio (downside deviation)
        downside_returns = returns[returns < 0]
        downside_std = downside_returns.std()
        annualized_downside_std = downside_std * np.sqrt(periods_per_year)

        sortino = ((annualized_return - self.risk_free_rate) / annualized_downside_std) if annualized_downside_std > 0 else 0

        return {
            'sharpe_ratio': sharpe,
            'sortino_ratio': sortino
        }

    def _calculate_drawdown_metrics(self) -> Dict:
        """Calculate drawdown statistics"""
        if len(self.equity_curve_df) == 0:
            return {
                'max_drawdown_pct': 0.0,
                'max_drawdown_value': 0.0,
                'calmar_ratio': 0.0
            }

        equity = self.equity_curve_df['equity']
        peak = equity.expanding().max()
        drawdown = (equity - peak) / peak

        max_dd_pct = abs(drawdown.min()) * 100
        max_dd_value = (peak - equity).max()

        # Calmar Ratio (return / max drawdown)
        total_return = (equity.iloc[-1] - self.initial_balance) / self.initial_balance
        calmar = (total_return / (max_dd_pct / 100)) if max_dd_pct > 0 else 0

        return {
            'max_drawdown_pct': max_dd_pct,
            'max_drawdown_value': max_dd_value,
            'calmar_ratio': calmar
        }


def calculate_metrics(
    trades_df: pd.DataFrame,
    equity_curve_df: pd.DataFrame,
    initial_balance: float,
    risk_free_rate: float = 0.0
) -> Dict:
    """
    Convenience function to calculate all metrics

    Args:
        trades_df: DataFrame with trade history
        equity_curve_df: DataFrame with equity curve
        initial_balance: Starting balance
        risk_free_rate: Risk-free rate (annualized)

    Returns:
        Dictionary with all metrics
    """
    calculator = PerformanceMetrics(trades_df, equity_curve_df, initial_balance, risk_free_rate)
    return calculator.calculate_all()


def format_metrics_table(metrics: Dict) -> str:
    """
    Format metrics as a readable table

    Args:
        metrics: Metrics dictionary

    Returns:
        Formatted string
    """
    from tabulate import tabulate

    # Group metrics
    returns = [
        ['Initial Balance', f"${metrics.get('initial_balance', 0):,.2f}"],
        ['Final Equity', f"${metrics.get('final_equity', 0):,.2f}"],
        ['Total PnL', f"${metrics.get('total_pnl', 0):,.2f}"],
        ['Total Return', f"{metrics.get('total_return_pct', 0):.2f}%"],
    ]

    trades = [
        ['Total Trades', metrics.get('total_trades', 0)],
        ['Winning Trades', metrics.get('winning_trades', 0)],
        ['Losing Trades', metrics.get('losing_trades', 0)],
        ['Win Rate', f"{metrics.get('win_rate_pct', 0):.2f}%"],
        ['Avg Trade Duration', f"{metrics.get('avg_trade_duration_bars', 0):.1f} bars"],
    ]

    performance = [
        ['Profit Factor', f"{metrics.get('profit_factor', 0):.2f}"],
        ['Expectancy', f"${metrics.get('expectancy', 0):.2f}"],
        ['Avg Win', f"${metrics.get('avg_win', 0):.2f}"],
        ['Avg Loss', f"${metrics.get('avg_loss', 0):.2f}"],
        ['Avg R-Multiple', f"{metrics.get('avg_r_multiple', 0):.2f}"],
    ]

    risk = [
        ['Max Drawdown', f"{metrics.get('max_drawdown_pct', 0):.2f}%"],
        ['Max DD Value', f"${metrics.get('max_drawdown_value', 0):,.2f}"],
        ['Sharpe Ratio', f"{metrics.get('sharpe_ratio', 0):.2f}"],
        ['Sortino Ratio', f"{metrics.get('sortino_ratio', 0):.2f}"],
        ['Calmar Ratio', f"{metrics.get('calmar_ratio', 0):.2f}"],
    ]

    output = []
    output.append("\n=== RETURN METRICS ===")
    output.append(tabulate(returns, tablefmt='simple'))

    output.append("\n=== TRADE METRICS ===")
    output.append(tabulate(trades, tablefmt='simple'))

    output.append("\n=== PERFORMANCE METRICS ===")
    output.append(tabulate(performance, tablefmt='simple'))

    output.append("\n=== RISK METRICS ===")
    output.append(tabulate(risk, tablefmt='simple'))

    return "\n".join(output)
