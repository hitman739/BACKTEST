"""
Feature Engineering
Generates comprehensive features for pattern analysis
"""

import pandas as pd
import numpy as np
from typing import Dict


class FeatureEngineer:
    """Generates technical, regime, and microstructure features"""

    def __init__(self):
        self.feature_names = []

    def engineer_features(self, positions_df: pd.DataFrame) -> pd.DataFrame:
        """
        Add comprehensive features to positions

        Features include:
        - Technical indicators (trend, momentum, volatility)
        - Market regime (volatility/trend state)
        - Microstructure (time patterns, position sizing)
        """
        print("🔧 Engineering features...")

        if positions_df.empty:
            return positions_df

        df = positions_df.copy()

        # 1. Technical features at entry
        df = self._add_technical_features(df)

        # 2. Regime features
        df = self._add_regime_features(df)

        # 3. Microstructure features
        df = self._add_microstructure_features(df)

        # 4. Position outcome features
        df = self._add_outcome_features(df)

        # Store feature names
        self.feature_names = [col for col in df.columns
                              if col not in positions_df.columns]

        print(f"✅ Generated {len(self.feature_names)} features")
        return df

    def _add_technical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add technical indicator features"""

        # Trend: EMA relationship
        if 'entry_ema_20' in df.columns and 'entry_ema_50' in df.columns:
            df['ema_bullish'] = (df['entry_ema_20'] > df['entry_ema_50']).astype(int)
            df['ema_distance'] = (df['entry_ema_20'] - df['entry_ema_50']) / df['entry_close']

        # Price vs EMA
        if 'entry_close' in df.columns and 'entry_ema_20' in df.columns:
            df['price_above_ema20'] = (df['entry_close'] > df['entry_ema_20']).astype(int)
            df['price_ema_distance'] = (df['entry_close'] - df['entry_ema_20']) / df['entry_close']

        # RSI regime
        if 'entry_rsi' in df.columns:
            df['rsi_oversold'] = (df['entry_rsi'] < 30).astype(int)
            df['rsi_overbought'] = (df['entry_rsi'] > 70).astype(int)
            df['rsi_neutral'] = ((df['entry_rsi'] >= 40) & (df['entry_rsi'] <= 60)).astype(int)

        # ATR percentile (if we have ATR)
        if 'entry_atr' in df.columns:
            df['atr_percentile'] = df['entry_atr'].rank(pct=True)

        return df

    def _add_regime_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add market regime features"""

        # Volatility regime
        if 'entry_atr' in df.columns and 'entry_close' in df.columns:
            atr_pct = df['entry_atr'] / df['entry_close']
            df['volatility_regime'] = pd.cut(
                atr_pct,
                bins=[0, 0.01, 0.02, 1.0],
                labels=['low', 'medium', 'high']
            )

        # Trend regime (based on EMA relationship)
        if 'ema_distance' in df.columns:
            df['trend_regime'] = pd.cut(
                df['ema_distance'],
                bins=[-1.0, -0.005, 0.005, 1.0],
                labels=['downtrend', 'sideways', 'uptrend']
            )

        return df

    def _add_microstructure_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add microstructure and timing features"""

        # Time of day
        df['entry_hour'] = df['entry_time'].dt.hour
        df['entry_day_of_week'] = df['entry_time'].dt.dayofweek

        # Session (simplified)
        df['session'] = 'other'
        df.loc[(df['entry_hour'] >= 14) & (df['entry_hour'] < 22), 'session'] = 'us_eu'

        # Time since last trade
        df['time_since_last'] = df['entry_time'].diff().dt.total_seconds() / 60

        # Position sizing features
        if 'size' in df.columns:
            df['size_percentile'] = df['size'].rank(pct=True)

        return df

    def _add_outcome_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add features describing the trade outcome"""

        # R-multiple (if we can infer stop distance)
        if 'mfe' in df.columns and 'mae' in df.columns:
            # Infer stop as largest MAE seen
            inferred_stop = df['mae'].abs().median()
            if inferred_stop > 0:
                df['r_multiple'] = df['pnl'] / (inferred_stop * df['size'])
                df['mfe_r'] = df['mfe'] / inferred_stop
                df['mae_r'] = df['mae'] / inferred_stop

        # Win/loss binary
        df['is_winner'] = (df['pnl'] > 0).astype(int)

        # Holding time buckets
        df['holding_bucket'] = pd.cut(
            df['holding_time_mins'],
            bins=[0, 15, 60, 240, 10000],
            labels=['scalp', 'short', 'medium', 'long']
        )

        return df

    def get_feature_importance_data(self, df: pd.DataFrame) -> Dict:
        """Prepare data for feature importance analysis"""

        # Features (X) and target (y)
        feature_cols = [col for col in self.feature_names
                        if not any(x in col for x in ['regime', 'session', 'holding_bucket'])]

        # Select only numeric features
        X_cols = [col for col in feature_cols if df[col].dtype in [np.float64, np.int64]]

        return {
            'X': df[X_cols].dropna(),
            'y': df.loc[df[X_cols].dropna().index, 'is_winner'],
            'feature_names': X_cols
        }
