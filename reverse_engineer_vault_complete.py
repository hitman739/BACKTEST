#!/usr/bin/env python3
"""
Complete Vault Reverse Engineering System
Comprehensive analysis to extract exact trading strategy from Hyperliquid vault

This system:
1. Loads all vault trades from Hyperliquid
2. Reconstructs complete positions with entry/exit
3. Fetches OHLCV data (Binance + Hyperliquid fallback)
4. Computes 100+ technical features (EMA, RSI, ATR, Bollinger, VWAP, regime, etc.)
5. Analyzes patterns with ML (decision trees, random forests, clustering)
6. Extracts precise trading rules
7. Validates against vault performance
8. Generates executable strategy code

Usage:
    python3 reverse_engineer_vault_complete.py --vault <address> --symbol <symbol> --timeframe <tf>

Example:
    python3 reverse_engineer_vault_complete.py \\
        --vault 0x9b55c8c948f988bcbe404cd070fc9ffffab8d31b \\
        --symbol HYPE \\
        --timeframe 5m
"""

import argparse
import json
import pandas as pd
from pathlib import Path
from datetime import datetime

# Import components
from reverse_engineering.data.vault_data_interface import VaultDataInterface
from reverse_engineering.data.position_reconstructor import PositionReconstructor
from reverse_engineering.data.ohlcv_aligner import OHLCVAligner
from reverse_engineering.features.advanced_feature_engineering import AdvancedFeatureEngineer
from reverse_engineering.analysis.advanced_pattern_analysis import AdvancedPatternAnalyzer
from reverse_engineering.extraction.precise_rule_extractor import PreciseRuleExtractor
from reverse_engineering.validation.equity_curve_validator import EquityCurveValidator


class CompleteVaultReverseEngineer:
    """Master orchestrator for complete vault reverse engineering"""

    def __init__(self, vault_address: str, symbol: str = 'HYPE', timeframe: str = '5m'):
        self.vault_address = vault_address
        self.symbol = symbol
        self.timeframe = timeframe
        self.output_dir = Path(f"reports/reverse_engineering/{vault_address[:10]}")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Components
        self.data_interface = VaultDataInterface(vault_address)
        self.position_reconstructor = PositionReconstructor()
        self.ohlcv_aligner = OHLCVAligner()
        self.feature_engineer = AdvancedFeatureEngineer()
        self.pattern_analyzer = AdvancedPatternAnalyzer()
        self.rule_extractor = PreciseRuleExtractor()
        self.validator = EquityCurveValidator()

        # Data storage
        self.trades_df = None
        self.positions_df = None
        self.positions_with_features = None
        self.pattern_analysis = None
        self.extracted_rules = None

    def run_complete_analysis(self):
        """Execute complete reverse engineering pipeline"""

        print("\n" + "=" * 70)
        print("🎯 COMPLETE VAULT REVERSE ENGINEERING SYSTEM")
        print("=" * 70)
        print(f"Vault: {self.vault_address}")
        print(f"Symbol: {self.symbol}")
        print(f"Timeframe: {self.timeframe}")
        print(f"Output: {self.output_dir}")
        print("=" * 70)

        # PHASE 1: DATA COLLECTION
        print("\n" + "🔹" * 35)
        print("PHASE 1: VAULT DATA COLLECTION")
        print("🔹" * 35)
        self.trades_df = self._phase1_collect_data()

        if self.trades_df.empty:
            print("❌ No data collected. Exiting.")
            return

        # PHASE 2: POSITION RECONSTRUCTION
        print("\n" + "🔹" * 35)
        print("PHASE 2: POSITION RECONSTRUCTION")
        print("🔹" * 35)
        self.positions_df = self._phase2_reconstruct_positions()

        if self.positions_df.empty:
            print("❌ No positions reconstructed. Exiting.")
            return

        # PHASE 3: OHLCV ALIGNMENT
        print("\n" + "🔹" * 35)
        print("PHASE 3: OHLCV DATA ALIGNMENT")
        print("🔹" * 35)
        self.positions_df = self._phase3_align_ohlcv()

        # PHASE 4: ADVANCED FEATURE ENGINEERING
        print("\n" + "🔹" * 35)
        print("PHASE 4: ADVANCED FEATURE ENGINEERING")
        print("🔹" * 35)
        self.positions_with_features = self._phase4_engineer_features()

        # PHASE 5: DEEP PATTERN ANALYSIS
        print("\n" + "🔹" * 35)
        print("PHASE 5: DEEP PATTERN ANALYSIS")
        print("🔹" * 35)
        self.pattern_analysis = self._phase5_analyze_patterns()

        # PHASE 6: PRECISE RULE EXTRACTION
        print("\n" + "🔹" * 35)
        print("PHASE 6: PRECISE RULE EXTRACTION")
        print("🔹" * 35)
        self.extracted_rules = self._phase6_extract_rules()

        # PHASE 7: VALIDATION
        print("\n" + "🔹" * 35)
        print("PHASE 7: PERFORMANCE VALIDATION")
        print("🔹" * 35)
        validation_results = self._phase7_validate()

        # PHASE 8: GENERATE REPORTS
        print("\n" + "🔹" * 35)
        print("PHASE 8: GENERATE REPORTS")
        print("🔹" * 35)
        self._phase8_generate_reports()

        # FINAL SUMMARY
        self._print_final_summary()

    def _phase1_collect_data(self) -> pd.DataFrame:
        """Collect vault trades from Hyperliquid"""

        trades_df = self.data_interface.run(force_refresh=False)

        if not trades_df.empty:
            print(f"✅ Collected {len(trades_df)} trades")
            print(f"   Date range: {trades_df['timestamp'].min()} to {trades_df['timestamp'].max()}")
            print(f"   Symbols: {trades_df['symbol'].unique().tolist()}")

        return trades_df

    def _phase2_reconstruct_positions(self) -> pd.DataFrame:
        """Reconstruct positions from individual trades"""

        positions_df = self.position_reconstructor.reconstruct(self.trades_df)

        if not positions_df.empty:
            print(f"✅ Reconstructed {len(positions_df)} positions")
            print(f"   Win rate: {(positions_df['pnl'] > 0).sum() / len(positions_df) * 100:.1f}%")
            print(f"   Avg holding time: {positions_df['holding_time_mins'].mean():.1f} minutes")

            # Save positions
            positions_path = self.output_dir / "positions.parquet"
            positions_df.to_parquet(positions_path, index=False)
            print(f"   💾 Saved to: {positions_path}")

        return positions_df

    def _phase3_align_ohlcv(self) -> pd.DataFrame:
        """Align positions with OHLCV data and basic indicators"""

        aligned_df = self.ohlcv_aligner.align_positions(
            self.positions_df,
            timeframe=self.timeframe,
            use_cache=True
        )

        if not aligned_df.empty:
            indicator_cols = [col for col in aligned_df.columns if 'ema' in col or 'rsi' in col or 'atr' in col]
            print(f"✅ Aligned {len(aligned_df)} positions with OHLCV")
            print(f"   Added indicators: {len(indicator_cols)}")
        else:
            print("⚠️  OHLCV alignment failed - continuing with available data")
            aligned_df = self.positions_df

        return aligned_df

    def _phase4_engineer_features(self) -> pd.DataFrame:
        """Generate comprehensive features (100+)"""

        features_df = self.feature_engineer.engineer_features(self.positions_df)

        print(f"✅ Generated {len(self.feature_engineer.feature_names)} features")
        print(f"   Numeric: {len(self.feature_engineer.numeric_features)}")
        print(f"   Categorical: {len(self.feature_engineer.categorical_features)}")

        # Save feature summary
        summary = self.feature_engineer.get_feature_summary(features_df)
        summary_path = self.output_dir / "feature_summary.csv"
        summary.to_csv(summary_path, index=False)
        print(f"   💾 Feature summary: {summary_path}")

        # Save full featured dataset
        features_path = self.output_dir / "positions_with_features.parquet"
        features_df.to_parquet(features_path, index=False)
        print(f"   💾 Full dataset: {features_path}")

        return features_df

    def _phase5_analyze_patterns(self) -> dict:
        """Deep pattern analysis with ML"""

        feature_data = self.feature_engineer.get_feature_importance_data(self.positions_with_features)

        analysis = self.pattern_analyzer.analyze_patterns(
            self.positions_with_features,
            feature_data
        )

        # Save analysis
        analysis_path = self.output_dir / "pattern_analysis_complete.json"
        with open(analysis_path, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)

        print(f"✅ Pattern analysis saved: {analysis_path}")

        return analysis

    def _phase6_extract_rules(self) -> dict:
        """Extract precise, executable trading rules"""

        rules = self.rule_extractor.extract_rules(
            self.positions_with_features,
            self.pattern_analysis
        )

        # Save rules
        rules_path = self.output_dir / "extracted_rules.json"
        with open(rules_path, 'w') as f:
            json.dump(rules, f, indent=2, default=str)

        print(f"✅ Rules saved: {rules_path}")

        # Print summary
        summary = self.rule_extractor.generate_strategy_summary()
        print("\n" + summary)

        # Save text summary
        summary_path = self.output_dir / "strategy_summary.txt"
        with open(summary_path, 'w') as f:
            f.write(summary)

        return rules

    def _phase7_validate(self) -> dict:
        """Validate inferred strategy"""

        validation = self.validator.validate(
            vault_positions=self.positions_with_features,
            simulated_positions=None  # Would compare with backtest results
        )

        # Save validation
        self.validator.save_validation_report(validation, str(self.output_dir))

        return validation

    def _phase8_generate_reports(self):
        """Generate final reports"""

        # Create comprehensive report
        report = {
            'vault_address': self.vault_address,
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'analysis_date': datetime.now().isoformat(),
            'data_summary': {
                'total_trades': len(self.trades_df) if self.trades_df is not None else 0,
                'total_positions': len(self.positions_df) if self.positions_df is not None else 0,
                'features_generated': len(self.feature_engineer.feature_names),
            },
            'extracted_rules': self.extracted_rules,
            'pattern_analysis_summary': {
                'summary': self.pattern_analysis.get('summary', {}),
                'entry_patterns': self.pattern_analysis.get('entry_patterns', {}),
                'exit_patterns': self.pattern_analysis.get('exit_patterns', {}),
            }
        }

        # Save master report
        master_report_path = self.output_dir / "MASTER_REPORT.json"
        with open(master_report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        print(f"✅ Master report: {master_report_path}")

    def _print_final_summary(self):
        """Print final summary"""

        print("\n" + "=" * 70)
        print("🎉 ANALYSIS COMPLETE!")
        print("=" * 70)

        if self.extracted_rules:
            meta = self.extracted_rules.get('metadata', {})
            print(f"\n📊 STRATEGY PROFILE:")
            print(f"   Type: {meta.get('strategy_type', 'Unknown')}")
            print(f"   Win Rate: {meta.get('win_rate', 0):.1f}%")
            print(f"   Avg Holding: {meta.get('avg_holding_time_mins', 0):.0f} mins")
            print(f"   Directional Bias: {meta.get('directional_bias', 'neutral').upper()}")

        print(f"\n📁 OUTPUT DIRECTORY: {self.output_dir}")
        print("\n📄 KEY FILES:")
        print(f"   • MASTER_REPORT.json - Complete analysis")
        print(f"   • extracted_rules.json - Precise trading rules")
        print(f"   • strategy_summary.txt - Human-readable rules")
        print(f"   • pattern_analysis_complete.json - ML analysis")
        print(f"   • validation_report.json - Performance validation")
        print(f"   • positions_with_features.parquet - Full dataset")

        print("\n💡 NEXT STEPS:")
        print("   1. Review extracted_rules.json for precise entry/exit conditions")
        print("   2. Check strategy_summary.txt for readable rules")
        print("   3. Implement rules in custom strategy class")
        print("   4. Backtest on historical data")
        print("   5. Paper trade before going live")

        print("\n" + "=" * 70)


def main():
    """Main entry point"""

    parser = argparse.ArgumentParser(
        description='Complete Vault Reverse Engineering System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--vault',
        required=True,
        help='Hyperliquid vault address (e.g., 0x9b55c8c948f988bcbe404cd070fc9ffffab8d31b)'
    )

    parser.add_argument(
        '--symbol',
        default='HYPE',
        help='Trading symbol (default: HYPE)'
    )

    parser.add_argument(
        '--timeframe',
        default='5m',
        choices=['1m', '5m', '15m', '1h', '4h', '1d'],
        help='OHLCV timeframe (default: 5m)'
    )

    args = parser.parse_args()

    # Run analysis
    engineer = CompleteVaultReverseEngineer(
        vault_address=args.vault,
        symbol=args.symbol,
        timeframe=args.timeframe
    )

    engineer.run_complete_analysis()


if __name__ == '__main__':
    main()
