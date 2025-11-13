"""
Reverse Engineering CLI
Command-line interface for the full vault reverse-engineering pipeline
"""

import argparse
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from reverse_engineering import DEFAULT_VAULT
from reverse_engineering.data.vault_data_interface import VaultDataInterface
from reverse_engineering.data.position_reconstructor import PositionReconstructor
from reverse_engineering.data.ohlcv_aligner import OHLCVAligner
from reverse_engineering.features.feature_engineering import FeatureEngineer
from reverse_engineering.analysis.pattern_analysis import PatternAnalyzer
from reverse_engineering.extraction.rule_extraction import RuleExtractor
from reverse_engineering.synthesis.strategy_synthesis import StrategySynthesizer
from reverse_engineering.evaluation.evaluation import Evaluator


class ReversEngineeringCLI:
    """Main CLI orchestrator"""

    def __init__(self, vault_address: str):
        self.vault_address = vault_address
        self.output_dir = Path(f"reports/reverse_engineering/{vault_address[:10]}")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run_full_pipeline(self, timeframe: str = '5m', symbol: str = 'HYPE'):
        """Execute complete reverse-engineering pipeline"""

        print("=" * 70)
        print("🔍 VAULT REVERSE ENGINEERING PIPELINE")
        print("=" * 70)
        print(f"\nVault: {self.vault_address}")
        print(f"Output: {self.output_dir}")
        print()

        # PHASE 1: Data Collection
        print("\n" + "🔹" * 35)
        print("PHASE 1: DATA COLLECTION")
        print("🔹" * 35)

        vault_interface = VaultDataInterface(self.vault_address)
        trades_df = vault_interface.run()

        if trades_df.empty:
            print("❌ No trades found. Aborting.")
            return

        # PHASE 2: Position Reconstruction
        print("\n" + "🔹" * 35)
        print("PHASE 2: POSITION RECONSTRUCTION")
        print("🔹" * 35)

        reconstructor = PositionReconstructor()
        positions_df = reconstructor.reconstruct(trades_df)

        if positions_df.empty:
            print("⚠️  Could not reconstruct positions. Using individual trades.")
            positions_df = trades_df

        # PHASE 3: OHLCV Alignment
        print("\n" + "🔹" * 35)
        print("PHASE 3: OHLCV ALIGNMENT")
        print("🔹" * 35)

        aligner = OHLCVAligner()
        aligned_df = aligner.align_positions(positions_df, timeframe=timeframe)

        if aligned_df.empty:
            aligned_df = positions_df  # Fallback

        # Save aligned data
        aligned_df.to_parquet(self.output_dir / "features.parquet", index=False)

        # PHASE 4: Feature Engineering
        print("\n" + "🔹" * 35)
        print("PHASE 4: FEATURE ENGINEERING")
        print("🔹" * 35)

        engineer = FeatureEngineer()
        features_df = engineer.engineer_features(aligned_df)

        # PHASE 5: Pattern Analysis
        print("\n" + "🔹" * 35)
        print("PHASE 5: PATTERN ANALYSIS (ML)")
        print("🔹" * 35)

        analyzer = PatternAnalyzer(self.output_dir)
        analysis_results = analyzer.analyze(features_df, engineer.feature_names)

        # PHASE 6: Rule Extraction
        print("\n" + "🔹" * 35)
        print("PHASE 6: RULE EXTRACTION")
        print("🔹" * 35)

        extractor = RuleExtractor(self.output_dir)
        rules = extractor.extract_rules(analysis_results)
        extractor.print_summary()

        # PHASE 7: Strategy Synthesis
        print("\n" + "🔹" * 35)
        print("PHASE 7: STRATEGY SYNTHESIS")
        print("🔹" * 35)

        synthesizer = StrategySynthesizer()
        strategy_path = synthesizer.synthesize(rules, self.vault_address)

        # PHASE 8: Evaluation
        print("\n" + "🔹" * 35)
        print("PHASE 8: EVALUATION")
        print("🔹" * 35)

        evaluator = Evaluator(self.output_dir)

        # Prepare vault metrics for comparison
        vault_metrics = {
            'total_pnl': positions_df['pnl'].sum() if 'pnl' in positions_df.columns else 0,
            'win_rate': (positions_df['pnl'] > 0).mean() * 100 if 'pnl' in positions_df.columns else 0,
            'total_trades': len(positions_df)
        }

        comparison = evaluator.evaluate(
            strategy_path=strategy_path,
            vault_data=vault_metrics,
            symbol=symbol,
            timeframe=timeframe
        )

        # FINAL SUMMARY
        print("\n" + "=" * 70)
        print("✅ PIPELINE COMPLETE")
        print("=" * 70)

        print(f"\n📁 All artifacts saved to: {self.output_dir}")
        print(f"\n📝 Generated strategy: {strategy_path}")

        print(f"\n🎯 NEXT STEPS:")
        print(f"   1. Review rule spec: {self.output_dir}/rule_spec.json")
        print(f"   2. Review pattern analysis: {self.output_dir}/pattern_analysis.json")
        print(f"   3. Test strategy:")
        print(f"      python run_backtest.py \\")
        print(f"        --strategy {strategy_path} \\")
        print(f"        --symbol {symbol} --timeframe {timeframe} \\")
        print(f"        --from 2025-09-14 --to 2025-11-13 \\")
        print(f"        --equity 10000 --leverage 10")

        print(f"\n   4. Refine parameters in: {strategy_path}")

    def run_single_phase(self, phase: str):
        """Run individual pipeline phase"""

        if phase == 'fetch':
            vault_interface = VaultDataInterface(self.vault_address)
            vault_interface.run(force_refresh=True)

        elif phase == 'analyze':
            # Load data and run analysis only
            vault_interface = VaultDataInterface(self.vault_address)
            trades_df = vault_interface.load_data()

            if not trades_df.empty:
                reconstructor = PositionReconstructor()
                positions_df = reconstructor.reconstruct(trades_df)

                engineer = FeatureEngineer()
                features_df = engineer.engineer_features(positions_df)

                analyzer = PatternAnalyzer(self.output_dir)
                analyzer.analyze(features_df, engineer.feature_names)

        else:
            print(f"Unknown phase: {phase}")


def main():
    parser = argparse.ArgumentParser(
        description='Reverse Engineer Hyperliquid Vault Trading Strategies'
    )

    parser.add_argument(
        '--vault-id',
        type=str,
        default=DEFAULT_VAULT,
        help='Hyperliquid vault address'
    )

    parser.add_argument(
        '--symbol',
        type=str,
        default='HYPE',
        help='Symbol to backtest (default: HYPE)'
    )

    parser.add_argument(
        '--timeframe',
        type=str,
        default='5m',
        help='Timeframe for backtest (default: 5m)'
    )

    parser.add_argument(
        '--phase',
        type=str,
        choices=['all', 'fetch', 'analyze'],
        default='all',
        help='Pipeline phase to run (default: all)'
    )

    args = parser.parse_args()

    cli = ReversEngineeringCLI(args.vault_id)

    if args.phase == 'all':
        cli.run_full_pipeline(timeframe=args.timeframe, symbol=args.symbol)
    else:
        cli.run_single_phase(args.phase)


if __name__ == '__main__':
    main()
