"""
Pattern Analysis
Uses ML to infer entry/exit logic and risk management from vault trades
"""

import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.ensemble import RandomForestClassifier
import json
from pathlib import Path


class PatternAnalyzer:
    """Analyzes patterns in vault trades using interpretable ML"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.entry_model = None
        self.entry_rules = {}
        self.exit_patterns = {}
        self.risk_patterns = {}

    def analyze(self, features_df: pd.DataFrame, feature_names: list) -> dict:
        """
        Complete pattern analysis

        Returns dict with:
        - entry_analysis
        - exit_analysis
        - risk_analysis
        """
        print("\n" + "=" * 70)
        print("🔍 PATTERN ANALYSIS")
        print("=" * 70)

        results = {}

        # 1. Entry analysis
        print("\n📈 Analyzing entry patterns...")
        results['entry'] = self._analyze_entry(features_df, feature_names)

        # 2. Exit analysis
        print("\n📉 Analyzing exit patterns...")
        results['exit'] = self._analyze_exit(features_df)

        # 3. Risk management analysis
        print("\n💰 Analyzing risk management...")
        results['risk'] = self._analyze_risk(features_df)

        # Save results
        self._save_analysis(results)

        return results

    def _analyze_entry(self, df: pd.DataFrame, feature_names: list) -> dict:
        """Infer entry logic using decision tree"""

        # Prepare data
        X_cols = [col for col in feature_names
                  if col in df.columns and df[col].dtype in [np.float64, np.int64]]

        if not X_cols:
            print("  ⚠️  No numeric features available")
            return {}

        X = df[X_cols].fillna(0)
        y = df['is_winner']

        # Train interpretable decision tree
        tree = DecisionTreeClassifier(
            max_depth=4,
            min_samples_split=max(5, len(df) // 20),
            min_samples_leaf=max(2, len(df) // 50),
            random_state=42
        )

        tree.fit(X, y)

        # Get feature importance
        importance = pd.DataFrame({
            'feature': X_cols,
            'importance': tree.feature_importances_
        }).sort_values('importance', ascending=False)

        print(f"\n  📊 Top Features for Winning Trades:")
        for idx, row in importance.head(10).iterrows():
            if row['importance'] > 0.01:
                print(f"    • {row['feature']}: {row['importance']:.3f}")

        # Extract rules as text
        tree_rules = export_text(tree, feature_names=X_cols)

        # Get common patterns for winners
        winners = df[df['is_winner'] == 1]
        patterns = self._extract_common_patterns(winners)

        self.entry_model = tree
        self.entry_rules = {
            'feature_importance': importance.to_dict('records'),
            'tree_rules': tree_rules,
            'patterns': patterns
        }

        return self.entry_rules

    def _analyze_exit(self, df: pd.DataFrame) -> dict:
        """Analyze exit patterns"""

        patterns = {}

        # MFE/MAE analysis
        if 'mfe_r' in df.columns and 'mae_r' in df.columns:
            winners = df[df['is_winner'] == 1]
            losers = df[df['is_winner'] == 0]

            patterns['mfe_mae'] = {
                'avg_mfe_winners': winners['mfe_r'].mean() if len(winners) > 0 else 0,
                'avg_mae_winners': winners['mae_r'].mean() if len(winners) > 0 else 0,
                'avg_mae_losers': losers['mae_r'].mean() if len(losers) > 0 else 0,
            }

            print(f"  • Winners MFE: {patterns['mfe_mae']['avg_mfe_winners']:.2f}R")
            print(f"  • Winners MAE: {patterns['mfe_mae']['avg_mae_winners']:.2f}R")
            print(f"  • Losers MAE: {patterns['mfe_mae']['avg_mae_losers']:.2f}R")

        # Holding time analysis
        if 'holding_time_mins' in df.columns:
            patterns['holding'] = {
                'avg': df['holding_time_mins'].mean(),
                'median': df['holding_time_mins'].median(),
                'p25': df['holding_time_mins'].quantile(0.25),
                'p75': df['holding_time_mins'].quantile(0.75)
            }

            print(f"  • Avg holding: {patterns['holding']['avg']:.1f} mins")
            print(f"  • Median holding: {patterns['holding']['median']:.1f} mins")

        # Infer exit type
        mfe_avg = patterns.get('mfe_mae', {}).get('avg_mfe_winners', 0)
        if mfe_avg > 0:
            if mfe_avg < 2.0:
                patterns['exit_type'] = 'tight_tp'
                print(f"  📌 Exit style: TIGHT TPs (~{mfe_avg:.1f}R)")
            elif mfe_avg < 3.5:
                patterns['exit_type'] = 'moderate_tp'
                print(f"  📌 Exit style: MODERATE TPs (~{mfe_avg:.1f}R)")
            else:
                patterns['exit_type'] = 'trailing'
                print(f"  📌 Exit style: TRAILING (MFE {mfe_avg:.1f}R)")

        self.exit_patterns = patterns
        return patterns

    def _analyze_risk(self, df: pd.DataFrame) -> dict:
        """Analyze risk management patterns"""

        patterns = {}

        # Position sizing
        if 'size' in df.columns:
            patterns['sizing'] = {
                'avg': df['size'].mean(),
                'std': df['size'].std(),
                'cv': df['size'].std() / df['size'].mean() if df['size'].mean() > 0 else 0
            }

            if patterns['sizing']['cv'] < 0.2:
                print(f"  📌 Position sizing: FIXED (~{patterns['sizing']['avg']:.4f})")
            else:
                print(f"  📌 Position sizing: VARIABLE (CV: {patterns['sizing']['cv']:.2f})")

        # Directional bias
        if 'side' in df.columns:
            longs = (df['side'] == 'long').sum()
            shorts = (df['side'] == 'short').sum()
            total = len(df)

            patterns['directional_bias'] = {
                'long_pct': longs / total * 100 if total > 0 else 0,
                'short_pct': shorts / total * 100 if total > 0 else 0
            }

            print(f"  • Long: {patterns['directional_bias']['long_pct']:.1f}%")
            print(f"  • Short: {patterns['directional_bias']['short_pct']:.1f}%")

        # Win rate
        if 'is_winner' in df.columns:
            patterns['win_rate'] = df['is_winner'].mean() * 100
            print(f"  • Win Rate: {patterns['win_rate']:.1f}%")

        self.risk_patterns = patterns
        return patterns

    def _extract_common_patterns(self, df: pd.DataFrame) -> dict:
        """Extract common patterns from winning trades"""

        patterns = {}

        # Most common hour
        if 'entry_hour' in df.columns:
            patterns['active_hours'] = df['entry_hour'].value_counts().head(3).index.tolist()

        # Most common session
        if 'session' in df.columns:
            patterns['active_session'] = df['session'].mode()[0] if len(df) > 0 else None

        # EMA trend
        if 'ema_bullish' in df.columns:
            patterns['ema_bullish_pct'] = df['ema_bullish'].mean() * 100

        return patterns

    def _save_analysis(self, results: dict):
        """Save analysis results"""

        # Save as JSON
        filepath = self.output_dir / "pattern_analysis.json"
        with open(filepath, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n💾 Analysis saved to: {filepath}")
