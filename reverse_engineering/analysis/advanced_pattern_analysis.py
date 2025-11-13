"""
Advanced Pattern Analysis
Deep ML-based analysis to extract vault strategy patterns
"""

import pandas as pd
import numpy as np
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.ensemble import RandomForestClassifier
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from typing import Dict, List, Tuple
import json


class AdvancedPatternAnalyzer:
    """
    Analyzes trade patterns using multiple ML techniques:
    - Decision trees for interpretable rules
    - Random forests for feature importance
    - Clustering for strategy regime detection
    - Correlation analysis for feature relationships
    - Entry/exit/sizing pattern extraction
    """

    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.scaler = StandardScaler()

    def analyze_patterns(self, df: pd.DataFrame, feature_data: Dict) -> Dict:
        """
        Complete pattern analysis

        Returns comprehensive insights about:
        - Entry conditions (long vs short)
        - Exit patterns (stop loss, take profit, time-based)
        - Sizing rules
        - Timing patterns
        - Risk management rules
        """
        print("\n🔍 ADVANCED PATTERN ANALYSIS")
        print("=" * 70)

        results = {
            'summary': {},
            'entry_patterns': {},
            'exit_patterns': {},
            'sizing_patterns': {},
            'timing_patterns': {},
            'risk_patterns': {},
            'correlations': {},
            'clusters': {},
            'rules': {}
        }

        # Basic statistics
        results['summary'] = self._compute_summary_stats(df)

        # Entry pattern analysis
        print("\n📊 Analyzing entry patterns...")
        results['entry_patterns'] = self._analyze_entry_patterns(df, feature_data)

        # Exit pattern analysis
        print("📊 Analyzing exit patterns...")
        results['exit_patterns'] = self._analyze_exit_patterns(df)

        # Sizing analysis
        print("📊 Analyzing position sizing...")
        results['sizing_patterns'] = self._analyze_sizing_patterns(df)

        # Timing analysis
        print("📊 Analyzing timing patterns...")
        results['timing_patterns'] = self._analyze_timing_patterns(df)

        # Risk management
        print("📊 Analyzing risk management...")
        results['risk_patterns'] = self._analyze_risk_patterns(df)

        # Feature correlations
        print("📊 Computing feature correlations...")
        results['correlations'] = self._analyze_correlations(df, feature_data)

        # Cluster analysis
        print("📊 Detecting strategy clusters...")
        results['clusters'] = self._analyze_clusters(df, feature_data)

        # Extract precise rules
        print("📊 Extracting decision rules...")
        results['rules'] = self._extract_decision_rules(df, feature_data)

        print("\n✅ Pattern analysis complete")
        return results

    def _compute_summary_stats(self, df: pd.DataFrame) -> Dict:
        """Basic strategy statistics"""

        total_trades = len(df)
        winners = df[df['is_winner'] == 1]
        losers = df[df['is_winner'] == 0]

        long_trades = df[df['side'] == 'long']
        short_trades = df[df['side'] == 'short']

        return {
            'total_trades': total_trades,
            'win_rate': (len(winners) / total_trades) * 100 if total_trades > 0 else 0,
            'avg_pnl': df['pnl'].mean(),
            'total_pnl': df['pnl'].sum(),
            'avg_holding_time_mins': df['holding_time_mins'].mean(),
            'long_ratio': (len(long_trades) / total_trades) * 100 if total_trades > 0 else 0,
            'short_ratio': (len(short_trades) / total_trades) * 100 if total_trades > 0 else 0,
            'avg_return_pct': df['return_pct'].mean() if 'return_pct' in df.columns else None,
            'sharpe_approx': (df['return_pct'].mean() / df['return_pct'].std()) if 'return_pct' in df.columns else None
        }

    def _analyze_entry_patterns(self, df: pd.DataFrame, feature_data: Dict) -> Dict:
        """Analyze what triggers entries (long vs short)"""

        X = feature_data['X']
        feature_names = feature_data['feature_names']

        patterns = {
            'long': {},
            'short': {},
            'feature_importance': {}
        }

        # Separate long and short trades
        long_indices = df.loc[X.index][df.loc[X.index]['side'] == 'long'].index
        short_indices = df.loc[X.index][df.loc[X.index]['side'] == 'short'].index

        if len(long_indices) > 5:
            patterns['long'] = self._analyze_side_entry(
                X.loc[long_indices],
                df.loc[long_indices],
                feature_names,
                'LONG'
            )

        if len(short_indices) > 5:
            patterns['short'] = self._analyze_side_entry(
                X.loc[short_indices],
                df.loc[short_indices],
                feature_names,
                'SHORT'
            )

        # Overall feature importance for winning trades
        if 'y' in feature_data and len(feature_data['y']) > 10:
            rf = RandomForestClassifier(
                n_estimators=100,
                max_depth=6,
                random_state=self.random_state
            )
            rf.fit(X, feature_data['y'])

            importance_df = pd.DataFrame({
                'feature': feature_names,
                'importance': rf.feature_importances_
            }).sort_values('importance', ascending=False)

            patterns['feature_importance'] = importance_df.head(15).to_dict('records')

        return patterns

    def _analyze_side_entry(self, X: pd.DataFrame, trades_df: pd.DataFrame,
                           feature_names: List, side: str) -> Dict:
        """Analyze entry conditions for a specific side"""

        # Decision tree for interpretability
        y = trades_df['is_winner'].values

        if len(y) < 5 or y.sum() == 0 or y.sum() == len(y):
            return {'insufficient_data': True}

        tree = DecisionTreeClassifier(
            max_depth=4,
            min_samples_split=max(5, len(y) // 10),
            min_samples_leaf=max(2, len(y) // 20),
            random_state=self.random_state
        )

        tree.fit(X, y)

        # Extract rules as text
        rules_text = export_text(tree, feature_names=feature_names)

        # Feature importance
        importance = pd.DataFrame({
            'feature': feature_names,
            'importance': tree.feature_importances_
        }).sort_values('importance', ascending=False)

        # Top conditions (mean values for winners)
        winners = trades_df[trades_df['is_winner'] == 1]
        top_features = importance.head(10)['feature'].tolist()

        conditions = {}
        for feat in top_features:
            if feat in trades_df.columns:
                conditions[feat] = {
                    'winner_mean': float(winners[feat].mean()) if len(winners) > 0 else None,
                    'winner_median': float(winners[feat].median()) if len(winners) > 0 else None,
                    'all_mean': float(trades_df[feat].mean()),
                    'all_median': float(trades_df[feat].median())
                }

        return {
            'num_trades': len(trades_df),
            'win_rate': (y.sum() / len(y)) * 100,
            'decision_tree_rules': rules_text,
            'top_features': importance.head(10).to_dict('records'),
            'winner_conditions': conditions
        }

    def _analyze_exit_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze exit behavior"""

        patterns = {}

        if 'mfe' in df.columns and 'mae' in df.columns and 'pnl' in df.columns:
            # MFE/MAE analysis
            df_clean = df.dropna(subset=['mfe', 'mae', 'pnl'])

            winners = df_clean[df_clean['is_winner'] == 1]
            losers = df_clean[df_clean['is_winner'] == 0]

            patterns['mfe_mae_analysis'] = {
                'avg_mfe_pct': df_clean['mfe_pct'].mean() if 'mfe_pct' in df_clean.columns else None,
                'avg_mae_pct': df_clean['mae_pct'].mean() if 'mae_pct' in df_clean.columns else None,
                'avg_winner_mfe_pct': winners['mfe_pct'].mean() if 'mfe_pct' in winners.columns and len(winners) > 0 else None,
                'avg_loser_mae_pct': abs(losers['mae_pct'].mean()) if 'mae_pct' in losers.columns and len(losers) > 0 else None,
                'capture_efficiency': df_clean['capture_efficiency'].mean() if 'capture_efficiency' in df_clean.columns else None
            }

            # Infer stop loss
            if len(losers) > 0 and 'mae_pct' in losers.columns:
                mae_abs = losers['mae_pct'].abs()
                patterns['inferred_stop_loss'] = {
                    'median_mae_pct': float(mae_abs.median()),
                    'mean_mae_pct': float(mae_abs.mean()),
                    'percentile_75_mae_pct': float(mae_abs.quantile(0.75)),
                    'max_mae_pct': float(mae_abs.max())
                }

            # Infer take profit
            if len(winners) > 0 and 'mfe_pct' in winners.columns:
                patterns['inferred_take_profit'] = {
                    'median_mfe_pct': float(winners['mfe_pct'].median()),
                    'mean_mfe_pct': float(winners['mfe_pct'].mean()),
                    'percentile_75_mfe_pct': float(winners['mfe_pct'].quantile(0.75))
                }

            # R-multiples
            if 'r_multiple' in df_clean.columns:
                patterns['r_multiple_stats'] = {
                    'avg_r': float(df_clean['r_multiple'].mean()),
                    'median_r': float(df_clean['r_multiple'].median()),
                    'winner_avg_r': float(winners['r_multiple'].mean()) if len(winners) > 0 else None,
                    'loser_avg_r': float(losers['r_multiple'].mean()) if len(losers) > 0 else None
                }

        # Holding time analysis
        if 'holding_time_mins' in df.columns:
            patterns['holding_time'] = {
                'median_mins': float(df['holding_time_mins'].median()),
                'mean_mins': float(df['holding_time_mins'].mean()),
                'percentile_25': float(df['holding_time_mins'].quantile(0.25)),
                'percentile_75': float(df['holding_time_mins'].quantile(0.75)),
                'max_mins': float(df['holding_time_mins'].max())
            }

        return patterns

    def _analyze_sizing_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze position sizing logic"""

        if 'size' not in df.columns:
            return {}

        patterns = {
            'size_stats': {
                'mean': float(df['size'].mean()),
                'median': float(df['size'].median()),
                'std': float(df['size'].std()),
                'cv': float(df['size'].std() / df['size'].mean())  # Coefficient of variation
            }
        }

        # Check if sizing varies with volatility
        if 'atr_pct' in df.columns:
            corr = df[['size', 'atr_pct']].corr().iloc[0, 1]
            patterns['size_volatility_correlation'] = float(corr)
            patterns['adaptive_sizing'] = abs(corr) > 0.3

        # Check if sizing varies with time
        if 'entry_time' in df.columns:
            df_sorted = df.sort_values('entry_time')
            df_sorted['trade_num'] = range(len(df_sorted))
            corr_time = df_sorted[['size', 'trade_num']].corr().iloc[0, 1]
            patterns['size_time_correlation'] = float(corr_time)

        # Size regimes
        if 'size_regime' in df.columns:
            size_counts = df['size_regime'].value_counts()
            patterns['size_distribution'] = size_counts.to_dict()

        return patterns

    def _analyze_timing_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze timing and frequency patterns"""

        patterns = {}

        # Hour distribution
        if 'entry_hour' in df.columns:
            hour_dist = df['entry_hour'].value_counts().sort_index()
            patterns['hour_distribution'] = hour_dist.to_dict()

            # Most active hours
            top_hours = hour_dist.sort_values(ascending=False).head(5)
            patterns['most_active_hours'] = top_hours.to_dict()

        # Day of week
        if 'entry_day_of_week' in df.columns:
            dow_dist = df['entry_day_of_week'].value_counts().sort_index()
            patterns['day_of_week_distribution'] = dow_dist.to_dict()

        # Session distribution
        if 'session' in df.columns:
            session_dist = df['session'].value_counts()
            patterns['session_distribution'] = session_dist.to_dict()

        # Trade frequency
        if 'time_since_last_trade_mins' in df.columns:
            time_between = df['time_since_last_trade_mins'].dropna()
            patterns['trade_frequency'] = {
                'median_mins_between_trades': float(time_between.median()),
                'mean_mins_between_trades': float(time_between.mean()),
                'trades_per_day_approx': float(1440 / time_between.median()) if time_between.median() > 0 else 0
            }

        # Frequency regime
        if 'frequency_regime' in df.columns:
            freq_dist = df['frequency_regime'].value_counts()
            patterns['frequency_regime_distribution'] = freq_dist.to_dict()

        return patterns

    def _analyze_risk_patterns(self, df: pd.DataFrame) -> Dict:
        """Analyze risk management patterns"""

        patterns = {}

        # Win rate by various conditions
        if 'is_winner' in df.columns:
            # Overall
            patterns['overall_win_rate'] = (df['is_winner'].sum() / len(df)) * 100

            # By side
            if 'side' in df.columns:
                by_side = df.groupby('side')['is_winner'].agg(['sum', 'count'])
                patterns['win_rate_by_side'] = {
                    side: (row['sum'] / row['count']) * 100
                    for side, row in by_side.iterrows()
                }

            # By volatility regime
            if 'atr_regime' in df.columns:
                by_vol = df.groupby('atr_regime')['is_winner'].agg(['sum', 'count'])
                patterns['win_rate_by_volatility'] = {
                    str(regime): (row['sum'] / row['count']) * 100
                    for regime, row in by_vol.iterrows()
                }

            # By trend regime
            if 'trend_regime' in df.columns:
                by_trend = df.groupby('trend_regime')['is_winner'].agg(['sum', 'count'])
                patterns['win_rate_by_trend'] = {
                    str(regime): (row['sum'] / row['count']) * 100
                    for regime, row in by_trend.iterrows()
                }

        # Risk metrics
        if 'estimated_stop_pct' in df.columns:
            patterns['estimated_stop_loss_pct'] = float(df['estimated_stop_pct'].iloc[0])

        if 'risk_reward_ratio' in df.columns:
            rr = df['risk_reward_ratio'].replace([np.inf, -np.inf], np.nan).dropna()
            if len(rr) > 0:
                patterns['avg_risk_reward_ratio'] = float(rr.mean())

        return patterns

    def _analyze_correlations(self, df: pd.DataFrame, feature_data: Dict) -> Dict:
        """Analyze feature correlations"""

        X = feature_data['X']

        # Correlation with outcome
        correlations = []
        for col in X.columns:
            corr = df.loc[X.index][[col, 'is_winner']].corr().iloc[0, 1]
            if not np.isnan(corr):
                correlations.append({
                    'feature': col,
                    'correlation_with_win': float(corr)
                })

        correlations = sorted(correlations, key=lambda x: abs(x['correlation_with_win']), reverse=True)

        return {
            'top_positive_correlations': correlations[:10],
            'top_negative_correlations': correlations[-10:]
        }

    def _analyze_clusters(self, df: pd.DataFrame, feature_data: Dict) -> Dict:
        """Detect strategy clusters/regimes"""

        X = feature_data['X']

        if len(X) < 10:
            return {'insufficient_data': True}

        # Standardize features
        X_scaled = self.scaler.fit_transform(X)

        # Determine optimal number of clusters (2-5)
        best_k = 3
        inertias = []

        for k in range(2, min(6, len(X) // 5 + 1)):
            kmeans = KMeans(n_clusters=k, random_state=self.random_state, n_init=10)
            kmeans.fit(X_scaled)
            inertias.append(kmeans.inertia_)

        # Use 3 clusters as default (or find elbow)
        kmeans = KMeans(n_clusters=best_k, random_state=self.random_state, n_init=10)
        clusters = kmeans.fit_predict(X_scaled)

        # Add clusters to dataframe
        df_clustered = df.loc[X.index].copy()
        df_clustered['cluster'] = clusters

        # Analyze each cluster
        cluster_profiles = []
        for cluster_id in range(best_k):
            cluster_df = df_clustered[df_clustered['cluster'] == cluster_id]

            profile = {
                'cluster_id': int(cluster_id),
                'size': len(cluster_df),
                'win_rate': (cluster_df['is_winner'].sum() / len(cluster_df)) * 100,
                'avg_pnl': float(cluster_df['pnl'].mean()),
                'avg_holding_mins': float(cluster_df['holding_time_mins'].mean()),
                'long_ratio': (cluster_df['side'] == 'long').sum() / len(cluster_df) * 100
            }

            cluster_profiles.append(profile)

        return {
            'num_clusters': best_k,
            'cluster_profiles': cluster_profiles
        }

    def _extract_decision_rules(self, df: pd.DataFrame, feature_data: Dict) -> Dict:
        """Extract precise decision rules"""

        X = feature_data['X']
        y = feature_data['y']

        # Deep decision tree for rule extraction
        tree = DecisionTreeClassifier(
            max_depth=5,
            min_samples_split=max(10, len(X) // 20),
            min_samples_leaf=max(5, len(X) // 40),
            random_state=self.random_state
        )

        tree.fit(X, y)

        # Export as text rules
        rules_text = export_text(tree, feature_names=feature_data['feature_names'])

        # Extract important thresholds
        feature_importance = pd.DataFrame({
            'feature': feature_data['feature_names'],
            'importance': tree.feature_importances_
        }).sort_values('importance', ascending=False)

        top_features = feature_importance.head(10)

        # For each top feature, find key thresholds
        thresholds = {}
        for feat in top_features['feature'].values:
            if feat in df.columns:
                winners = df[df['is_winner'] == 1]
                losers = df[df['is_winner'] == 0]

                thresholds[feat] = {
                    'winner_median': float(winners[feat].median()) if len(winners) > 0 else None,
                    'loser_median': float(losers[feat].median()) if len(losers) > 0 else None,
                    'overall_median': float(df[feat].median()),
                    'optimal_threshold': float(df[feat].median())  # Simplified
                }

        return {
            'decision_tree_depth': tree.get_depth(),
            'decision_tree_rules': rules_text,
            'feature_importance': top_features.to_dict('records'),
            'key_thresholds': thresholds
        }
