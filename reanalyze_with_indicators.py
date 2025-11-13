#!/usr/bin/env python3
"""
Re-run pattern analysis and rule extraction with reconstructed indicators
"""

import pandas as pd
import json
from pathlib import Path

from reverse_engineering.features.advanced_feature_engineering import AdvancedFeatureEngineer
from reverse_engineering.analysis.advanced_pattern_analysis import AdvancedPatternAnalyzer
from reverse_engineering.extraction.precise_rule_extractor import PreciseRuleExtractor
from reverse_engineering.validation.equity_curve_validator import EquityCurveValidator

print("=" * 70)
print("🔬 RE-ANALYZING WITH RECONSTRUCTED INDICATORS")
print("=" * 70)

vault_id = "0x9b55c8c9"
output_dir = Path(f"reports/reverse_engineering/{vault_id}")

# Load positions with indicators
positions_path = output_dir / "positions_with_indicators.parquet"

if not positions_path.exists():
    print(f"\n❌ File not found: {positions_path}")
    print("   Run: python3 reconstruct_ohlcv_from_trades.py first")
    exit(1)

print(f"\n📂 Loading positions with indicators...")
positions_df = pd.read_parquet(positions_path)
print(f"✅ Loaded {len(positions_df)} positions")

# Check indicators
indicator_cols = [col for col in positions_df.columns if any(x in col for x in ['ema', 'rsi', 'atr', 'bb', 'vwap'])]
print(f"   Indicators available: {len(indicator_cols)}")

# Feature Engineering
print("\n" + "🔹" * 35)
print("PHASE 1: ADVANCED FEATURE ENGINEERING")
print("🔹" * 35)

feature_engineer = AdvancedFeatureEngineer()
positions_with_features = feature_engineer.engineer_features(positions_df)

print(f"✅ Generated {len(feature_engineer.feature_names)} features")

# Save
features_path = output_dir / "positions_with_features_complete.parquet"
positions_with_features.to_parquet(features_path, index=False)
print(f"💾 Saved to: {features_path}")

# Pattern Analysis
print("\n" + "🔹" * 35)
print("PHASE 2: DEEP PATTERN ANALYSIS")
print("🔹" * 35)

feature_data = feature_engineer.get_feature_importance_data(positions_with_features)
pattern_analyzer = AdvancedPatternAnalyzer()
pattern_analysis = pattern_analyzer.analyze_patterns(positions_with_features, feature_data)

# Save analysis
analysis_path = output_dir / "pattern_analysis_with_indicators.json"
with open(analysis_path, 'w') as f:
    json.dump(pattern_analysis, f, indent=2, default=str)
print(f"\n💾 Analysis saved to: {analysis_path}")

# Rule Extraction
print("\n" + "🔹" * 35)
print("PHASE 3: PRECISE RULE EXTRACTION")
print("🔹" * 35)

rule_extractor = PreciseRuleExtractor()
extracted_rules = rule_extractor.extract_rules(positions_with_features, pattern_analysis)

# Save rules
rules_path = output_dir / "extracted_rules_with_indicators.json"
with open(rules_path, 'w') as f:
    json.dump(extracted_rules, f, indent=2, default=str)
print(f"\n💾 Rules saved to: {rules_path}")

# Generate summary
summary = rule_extractor.generate_strategy_summary()
print("\n" + summary)

# Save text summary
summary_path = output_dir / "strategy_summary_with_indicators.txt"
with open(summary_path, 'w') as f:
    f.write(summary)
print(f"\n💾 Summary saved to: {summary_path}")

# Validation
print("\n" + "🔹" * 35)
print("PHASE 4: PERFORMANCE VALIDATION")
print("🔹" * 35)

validator = EquityCurveValidator()
validation = validator.validate(vault_positions=positions_with_features)
validator.save_validation_report(validation, str(output_dir))

print("\n" + "=" * 70)
print("🎉 COMPLETE ANALYSIS FINISHED!")
print("=" * 70)

print("\n📄 KEY FILES:")
print(f"   • {rules_path.name}")
print(f"   • {summary_path.name}")
print(f"   • {analysis_path.name}")
print(f"   • validation_report.json")

print("\n💡 NEXT STEPS:")
print(f"   1. Review: cat {output_dir}/{summary_path.name}")
print(f"   2. Get rules: cat {output_dir}/{rules_path.name}")
print(f"   3. Implement strategy based on rules")
print(f"   4. Backtest and compare")

print("\n" + "=" * 70)
