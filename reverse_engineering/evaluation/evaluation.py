"""
Evaluation
Backtests generated strategy and compares with original vault
"""

import importlib.util
import sys
from pathlib import Path
from datetime import datetime, timedelta
from engine.backtester import Backtester
import json


class Evaluator:
    """Evaluates generated strategy against vault performance"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir / "evaluation"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def evaluate(
        self,
        strategy_path: Path,
        vault_data: dict,
        symbol: str = 'HYPE',
        timeframe: str = '5m'
    ) -> dict:
        """
        Backtest generated strategy and compare with vault

        Args:
            strategy_path: Path to generated strategy .py file
            vault_data: Dict with vault performance metrics
            symbol: Symbol to backtest
            timeframe: Timeframe to use

        Returns:
            Comparison results
        """
        print("\n" + "=" * 70)
        print("🔬 EVALUATION")
        print("=" * 70)

        # Load strategy class
        strategy = self._load_strategy(strategy_path)

        if not strategy:
            print("❌ Could not load strategy")
            return {}

        # Run backtest
        print(f"\n🚀 Running backtest...")
        print(f"   Symbol: {symbol}")
        print(f"   Timeframe: {timeframe}")

        # Use same date range as vault
        end_date = datetime.now()
        start_date = end_date - timedelta(days=60)

        backtester = Backtester(
            strategy=strategy,
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            initial_balance=10000,
            leverage=10,
            maker_fee=0.0002,
            taker_fee=0.0004,
            slippage_bps=3.0
        )

        try:
            results = backtester.run()
        except Exception as e:
            print(f"❌ Backtest error: {e}")
            import traceback
            traceback.print_exc()
            return {}

        # Compare results
        comparison = self._compare_results(results, vault_data)

        # Save comparison
        self._save_comparison(comparison)

        return comparison

    def _load_strategy(self, strategy_path: Path):
        """Dynamically load strategy class from file"""

        if not strategy_path.exists():
            return None

        # Load module
        spec = importlib.util.spec_from_file_location("vault_strategy", strategy_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules["vault_strategy"] = module
        spec.loader.exec_module(module)

        # Get strategy class
        return module.VaultCloneStrategy()

    def _compare_results(self, backtest_results: dict, vault_data: dict) -> dict:
        """Compare backtest with vault performance"""

        print("\n📊 COMPARISON")
        print("=" * 70)

        metrics = backtest_results['metrics']
        trades_df = backtest_results['trades']

        comparison = {
            'backtest': {
                'total_pnl': metrics.get('total_pnl', 0),
                'win_rate': metrics.get('win_rate', 0),
                'profit_factor': metrics.get('profit_factor', 0),
                'total_trades': metrics.get('total_trades', 0),
                'sharpe': metrics.get('sharpe_ratio', 0)
            },
            'vault': vault_data,
            'match_score': 0
        }

        # Print comparison
        print(f"\nOriginal Vault:")
        print(f"  • Total PnL: ${vault_data.get('total_pnl', 0):,.2f}")
        print(f"  • Win Rate: {vault_data.get('win_rate', 0):.1f}%")
        print(f"  • Trades: {vault_data.get('total_trades', 0)}")

        print(f"\nBacktested Strategy:")
        print(f"  • Total PnL: ${comparison['backtest']['total_pnl']:,.2f}")
        print(f"  • Win Rate: {comparison['backtest']['win_rate']:.1f}%")
        print(f"  • Trades: {comparison['backtest']['total_trades']}")
        print(f"  • Profit Factor: {comparison['backtest']['profit_factor']:.2f}")

        # Calculate match score
        if vault_data.get('total_pnl', 0) != 0:
            pnl_match = comparison['backtest']['total_pnl'] / vault_data['total_pnl']
            comparison['match_score'] = min(pnl_match, 1.0) * 100

            print(f"\n📈 PnL Match: {comparison['match_score']:.1f}%")

        if comparison['backtest']['profit_factor'] > 1.0:
            print(f"\n✅ Strategy is PROFITABLE (PF > 1.0)")
        else:
            print(f"\n⚠️  Strategy needs optimization (PF < 1.0)")

        return comparison

    def _save_comparison(self, comparison: dict):
        """Save comparison results"""

        filepath = self.output_dir / "comparison.json"
        with open(filepath, 'w') as f:
            json.dump(comparison, f, indent=2, default=str)

        print(f"\n💾 Comparison saved to: {filepath}")
