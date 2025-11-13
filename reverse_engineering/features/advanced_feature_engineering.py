"""
Advanced Feature Engineering
Comprehensive feature generation for precise vault strategy reverse engineering
"""

import pandas as pd
import numpy as np
from typing import Dict, List


class AdvancedFeatureEngineer:
    """
    Generates exhaustive features for vault strategy reconstruction:
    - Technical indicators (EMA, RSI, ATR, Bollinger, VWAP)
    - Volatility features (realized vol, ATR%, historical percentiles)
    - Trend features (slopes, regime detection)
    - Volume features (relative volume, VWAP deviation)
    - Microstructure (timing, session, trade frequency)
    - Position metrics (MFE, MAE, R-multiples, holding patterns)
    """

    def __init__(self):
        self.feature_names = []
        self.numeric_features = []
        self.categorical_features = []

    def engineer_features(self, positions_df: pd.DataFrame, ohlcv_df: pd.DataFrame = None) -> pd.DataFrame:
        """
        Generate ALL features for pattern analysis

        Args:
            positions_df: DataFrame with reconstructed positions
            ohlcv_df: Optional full OHLCV data for advanced calculations

        Returns:
            DataFrame with 100+ engineered features
        """
        print("🔧 Engineering advanced features...")

        if positions_df.empty:
            return positions_df

        df = positions_df.copy()

        # CATEGORY 1: TREND INDICATORS
        df = self._add_ema_features(df)
        df = self._add_trend_strength_features(df)

        # CATEGORY 2: MOMENTUM INDICATORS
        df = self._add_rsi_features(df)
        df = self._add_momentum_features(df)

        # CATEGORY 3: VOLATILITY INDICATORS
        df = self._add_atr_features(df)
        df = self._add_bollinger_features(df)
        df = self._add_volatility_features(df)

        # CATEGORY 4: VOLUME INDICATORS
        df = self._add_volume_features(df)
        df = self._add_vwap_features(df)

        # CATEGORY 5: REGIME DETECTION
        df = self._add_regime_features(df)

        # CATEGORY 6: MICROSTRUCTURE
        df = self._add_timing_features(df)
        df = self._add_frequency_features(df)
        df = self._add_sizing_features(df)

        # CATEGORY 7: POSITION OUTCOME METRICS
        df = self._add_performance_features(df)
        df = self._add_risk_metrics(df)

        # Store feature lists
        self._categorize_features(df, positions_df)

        print(f"✅ Generated {len(self.feature_names)} features:")
        print(f"   - Numeric: {len(self.numeric_features)}")
        print(f"   - Categorical: {len(self.categorical_features)}")

        return df

    def _add_ema_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """EMA-based trend features"""

        # EMA alignments
        if 'entry_ema_20' in df.columns and 'entry_ema_50' in df.columns:
            df['ema20_above_ema50'] = (df['entry_ema_20'] > df['entry_ema_50']).astype(int)
            df['ema20_ema50_distance_pct'] = ((df['entry_ema_20'] - df['entry_ema_50']) / df['entry_close']) * 100

        # Price vs EMAs
        if 'entry_close' in df.columns:
            if 'entry_ema_20' in df.columns:
                df['price_above_ema20'] = (df['entry_close'] > df['entry_ema_20']).astype(int)
                df['price_ema20_distance_pct'] = ((df['entry_close'] - df['entry_ema_20']) / df['entry_close']) * 100

            if 'entry_ema_50' in df.columns:
                df['price_above_ema50'] = (df['entry_close'] > df['entry_ema_50']).astype(int)
                df['price_ema50_distance_pct'] = ((df['entry_close'] - df['entry_ema_50']) / df['entry_close']) * 100

        return df

    def _add_trend_strength_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Trend strength and slope features"""

        # EMA slope (simplified - would need historical EMAs for true slope)
        if 'entry_ema_20' in df.columns and 'entry_ema_50' in df.columns:
            # Distance between EMAs as proxy for trend strength
            df['trend_strength'] = abs(df['entry_ema_20'] - df['entry_ema_50']) / df['entry_close']

        # Price momentum (using entry vs exit if available)
        if 'entry_price' in df.columns and 'exit_price' in df.columns:
            df['price_change_pct'] = ((df['exit_price'] - df['entry_price']) / df['entry_price']) * 100

        return df

    def _add_rsi_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """RSI-based features"""

        if 'entry_rsi' in df.columns:
            df['rsi_oversold'] = (df['entry_rsi'] < 30).astype(int)
            df['rsi_overbought'] = (df['entry_rsi'] > 70).astype(int)
            df['rsi_neutral'] = ((df['entry_rsi'] >= 40) & (df['entry_rsi'] <= 60)).astype(int)
            df['rsi_extreme'] = ((df['entry_rsi'] < 25) | (df['entry_rsi'] > 75)).astype(int)

            # RSI zones (more granular)
            df['rsi_zone'] = pd.cut(
                df['entry_rsi'],
                bins=[0, 20, 30, 40, 60, 70, 80, 100],
                labels=['extreme_oversold', 'oversold', 'weak', 'neutral', 'strong', 'overbought', 'extreme_overbought']
            )

            # Distance from 50 (equilibrium)
            df['rsi_distance_from_50'] = abs(df['entry_rsi'] - 50)

        return df

    def _add_momentum_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Additional momentum indicators"""

        # RSI change from entry to exit
        if 'entry_rsi' in df.columns and 'exit_rsi' in df.columns:
            df['rsi_change'] = df['exit_rsi'] - df['entry_rsi']
            df['rsi_reversal'] = (
                ((df['entry_rsi'] < 30) & (df['exit_rsi'] > 50)) |
                ((df['entry_rsi'] > 70) & (df['exit_rsi'] < 50))
            ).astype(int)

        return df

    def _add_atr_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """ATR-based volatility features"""

        if 'entry_atr' in df.columns and 'entry_close' in df.columns:
            # ATR as percentage of price
            df['atr_pct'] = (df['entry_atr'] / df['entry_close']) * 100

            # ATR percentile (relative volatility)
            df['atr_percentile'] = df['entry_atr'].rank(pct=True) * 100

            # ATR regime
            df['atr_regime'] = pd.cut(
                df['atr_pct'],
                bins=[0, 1, 2, 3, 100],
                labels=['low_vol', 'normal_vol', 'high_vol', 'extreme_vol']
            )

        return df

    def _add_bollinger_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Bollinger Bands features"""

        # Note: Would need to calculate BB from OHLCV data
        # For now, using proxy with available data
        if 'entry_close' in df.columns and 'entry_ema_20' in df.columns and 'entry_atr' in df.columns:
            # Approximate Bollinger Bands using EMA20 and ATR
            # True BB uses std dev, but ATR is a reasonable proxy
            df['bb_upper'] = df['entry_ema_20'] + (2 * df['entry_atr'])
            df['bb_lower'] = df['entry_ema_20'] - (2 * df['entry_atr'])
            df['bb_middle'] = df['entry_ema_20']

            # Position relative to bands
            df['price_bb_position'] = (df['entry_close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
            df['at_bb_upper'] = (df['entry_close'] > df['bb_upper']).astype(int)
            df['at_bb_lower'] = (df['entry_close'] < df['bb_lower']).astype(int)
            df['bb_squeeze'] = ((df['bb_upper'] - df['bb_lower']) / df['entry_close'] < 0.02).astype(int)

        return df

    def _add_volatility_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Realized volatility features"""

        # Historical volatility using position outcomes
        if 'pnl' in df.columns and 'entry_price' in df.columns:
            # Returns
            df['return_pct'] = (df['pnl'] / (df['entry_price'] * df['size'])) * 100

            # Rolling volatility (realized)
            for window in [5, 10, 20]:
                df[f'realized_vol_{window}'] = df['return_pct'].rolling(window).std()

        return df

    def _add_volume_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Volume-based features"""

        if 'entry_volume' in df.columns:
            # Relative volume
            df['volume_ma20'] = df['entry_volume'].rolling(20).mean()
            df['relative_volume'] = df['entry_volume'] / df['volume_ma20']
            df['high_volume'] = (df['relative_volume'] > 1.5).astype(int)
            df['low_volume'] = (df['relative_volume'] < 0.7).astype(int)

            # Volume percentile
            df['volume_percentile'] = df['entry_volume'].rank(pct=True) * 100

        return df

    def _add_vwap_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """VWAP features (simplified without full tick data)"""

        # Approximate daily VWAP using available data
        if 'entry_close' in df.columns and 'entry_volume' in df.columns:
            # Group by day
            df['date'] = df['entry_time'].dt.date

            # Calculate approximate VWAP per day
            daily_vwap = df.groupby('date').apply(
                lambda x: (x['entry_close'] * x['entry_volume']).sum() / x['entry_volume'].sum()
            )
            df['vwap'] = df['date'].map(daily_vwap)

            # Price vs VWAP
            df['price_above_vwap'] = (df['entry_close'] > df['vwap']).astype(int)
            df['vwap_distance_pct'] = ((df['entry_close'] - df['vwap']) / df['vwap']) * 100

        return df

    def _add_regime_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Market regime detection"""

        # Volatility regime
        if 'atr_pct' in df.columns:
            atr_median = df['atr_pct'].median()
            df['vol_regime_vs_median'] = pd.cut(
                df['atr_pct'],
                bins=[0, atr_median * 0.7, atr_median * 1.3, 100],
                labels=['low_vol', 'normal_vol', 'high_vol']
            )

        # Trend regime
        if 'ema20_ema50_distance_pct' in df.columns:
            df['trend_regime'] = pd.cut(
                df['ema20_ema50_distance_pct'],
                bins=[-100, -0.5, 0.5, 100],
                labels=['downtrend', 'sideways', 'uptrend']
            )

        # Combined regime
        if 'vol_regime_vs_median' in df.columns and 'trend_regime' in df.columns:
            df['market_regime'] = df['vol_regime_vs_median'].astype(str) + '_' + df['trend_regime'].astype(str)

        return df

    def _add_timing_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Timing and session features"""

        df['entry_hour'] = df['entry_time'].dt.hour
        df['entry_minute'] = df['entry_time'].dt.minute
        df['entry_day_of_week'] = df['entry_time'].dt.dayofweek
        df['entry_day_name'] = df['entry_time'].dt.day_name()

        # Trading sessions
        df['session'] = 'other'
        df.loc[(df['entry_hour'] >= 0) & (df['entry_hour'] < 8), 'session'] = 'asia'
        df.loc[(df['entry_hour'] >= 8) & (df['entry_hour'] < 16), 'session'] = 'europe'
        df.loc[(df['entry_hour'] >= 16) & (df['entry_hour'] < 24), 'session'] = 'us'

        # Hour categories
        df['hour_category'] = pd.cut(
            df['entry_hour'],
            bins=[-1, 6, 12, 18, 24],
            labels=['night', 'morning', 'afternoon', 'evening']
        )

        # Weekend
        df['is_weekend'] = (df['entry_day_of_week'] >= 5).astype(int)

        return df

    def _add_frequency_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Trade frequency features"""

        # Sort by time
        df_sorted = df.sort_values('entry_time')

        # Time between trades
        df['time_since_last_trade_mins'] = df_sorted['entry_time'].diff().dt.total_seconds() / 60
        df['time_to_next_trade_mins'] = -df_sorted['entry_time'].diff(-1).dt.total_seconds() / 60

        # Trade velocity (trades per hour, rolling)
        df['trades_per_hour'] = 60 / df['time_since_last_trade_mins']

        # Frequency regime
        df['frequency_regime'] = pd.cut(
            df['time_since_last_trade_mins'],
            bins=[0, 5, 30, 120, 10000],
            labels=['hft', 'scalping', 'intraday', 'swing']
        )

        return df

    def _add_sizing_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Position sizing features"""

        if 'size' in df.columns:
            # Size statistics
            df['size_percentile'] = df['size'].rank(pct=True) * 100
            df['size_vs_median'] = df['size'] / df['size'].median()
            df['size_zscore'] = (df['size'] - df['size'].mean()) / df['size'].std()

            # Size regime
            size_median = df['size'].median()
            df['size_regime'] = pd.cut(
                df['size'],
                bins=[0, size_median * 0.5, size_median * 1.5, df['size'].max() * 2],
                labels=['small', 'normal', 'large']
            )

            # Adaptive sizing (correlation with volatility)
            if 'atr_pct' in df.columns:
                # Check if sizing is inversely correlated with volatility
                corr = df[['size', 'atr_pct']].corr().iloc[0, 1]
                df['size_atr_correlation'] = corr

        return df

    def _add_performance_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Trade performance features"""

        # Win/Loss
        df['is_winner'] = (df['pnl'] > 0).astype(int)

        # Holding time
        df['holding_time_hours'] = df['holding_time_mins'] / 60
        df['holding_regime'] = pd.cut(
            df['holding_time_mins'],
            bins=[0, 5, 15, 60, 240, 10000],
            labels=['ultra_fast', 'scalp', 'short', 'medium', 'long']
        )

        # Return metrics
        if 'pnl' in df.columns and 'entry_price' in df.columns and 'size' in df.columns:
            df['return_pct'] = (df['pnl'] / (df['entry_price'] * df['size'])) * 100
            df['return_per_hour'] = df['return_pct'] / (df['holding_time_mins'] / 60 + 0.001)

        return df

    def _add_risk_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """Risk and R-multiple features"""

        if 'mfe' in df.columns and 'mae' in df.columns:
            # MFE/MAE in dollars and percentages
            df['mfe_pct'] = (df['mfe'] / df['entry_price']) * 100
            df['mae_pct'] = (df['mae'] / df['entry_price']) * 100

            # Efficiency (how much of MFE was captured)
            df['capture_efficiency'] = abs(df['pnl']) / (abs(df['mfe']) + 0.0001)

            # R-multiples
            mae_abs = df['mae'].abs()
            df['r_multiple'] = df['pnl'] / (mae_abs + 0.0001)
            df['potential_r'] = df['mfe'] / (mae_abs + 0.0001)

            # Stop loss estimate (median MAE)
            median_mae_pct = df['mae_pct'].abs().median()
            df['estimated_stop_pct'] = median_mae_pct

            # Risk/Reward at entry (using MFE as potential reward)
            df['risk_reward_ratio'] = abs(df['mfe']) / (abs(df['mae']) + 0.0001)

        return df

    def _categorize_features(self, df: pd.DataFrame, original_df: pd.DataFrame):
        """Categorize features into numeric and categorical"""

        # All new features
        self.feature_names = [col for col in df.columns if col not in original_df.columns]

        # Numeric features
        self.numeric_features = [
            col for col in self.feature_names
            if df[col].dtype in [np.float64, np.int64, np.float32, np.int32]
        ]

        # Categorical features
        self.categorical_features = [
            col for col in self.feature_names
            if col not in self.numeric_features
        ]

    def get_feature_importance_data(self, df: pd.DataFrame) -> Dict:
        """Prepare data for ML analysis"""

        # Only numeric features for ML
        available_features = [col for col in self.numeric_features if col in df.columns]

        # Remove target variables and identifiers
        exclude = ['is_winner', 'pnl', 'return_pct', 'r_multiple', 'date']
        X_cols = [col for col in available_features if col not in exclude]

        # Drop rows with NaN in features
        X = df[X_cols].replace([np.inf, -np.inf], np.nan).dropna()
        y = df.loc[X.index, 'is_winner']

        return {
            'X': X,
            'y': y,
            'feature_names': X_cols,
            'all_features': self.feature_names
        }

    def get_feature_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        """Get statistical summary of all features"""

        summary_data = []

        for col in self.numeric_features:
            if col in df.columns:
                summary_data.append({
                    'feature': col,
                    'mean': df[col].mean(),
                    'median': df[col].median(),
                    'std': df[col].std(),
                    'min': df[col].min(),
                    'max': df[col].max(),
                    'missing_pct': (df[col].isna().sum() / len(df)) * 100
                })

        return pd.DataFrame(summary_data)
