"""
Unit tests for indicator calculations
"""

import unittest
import pandas as pd
import numpy as np
from engine.indicators import Indicators


class TestIndicators(unittest.TestCase):
    """Test indicator calculations"""

    def setUp(self):
        """Set up test data"""
        # Create sample data
        np.random.seed(42)
        dates = pd.date_range('2024-01-01', periods=100, freq='1h')
        self.df = pd.DataFrame({
            'timestamp': dates,
            'open': 100 + np.random.randn(100).cumsum(),
            'high': 102 + np.random.randn(100).cumsum(),
            'low': 98 + np.random.randn(100).cumsum(),
            'close': 100 + np.random.randn(100).cumsum(),
            'volume': 1000 + np.random.randint(0, 100, 100)
        })

    def test_sma(self):
        """Test Simple Moving Average"""
        sma_20 = Indicators.sma(self.df['close'], 20)

        # Check length
        self.assertEqual(len(sma_20), len(self.df))

        # Check first values are NaN
        self.assertTrue(pd.isna(sma_20.iloc[0]))

        # Check value at position 20 (should be average of first 20 values)
        expected = self.df['close'].iloc[:20].mean()
        self.assertAlmostEqual(sma_20.iloc[19], expected, places=5)

    def test_ema(self):
        """Test Exponential Moving Average"""
        ema_20 = Indicators.ema(self.df['close'], 20)

        # Check length
        self.assertEqual(len(ema_20), len(self.df))

        # EMA should not be NaN after first value
        self.assertFalse(pd.isna(ema_20.iloc[-1]))

    def test_rsi(self):
        """Test RSI calculation"""
        rsi = Indicators.rsi(self.df['close'], 14)

        # Check length
        self.assertEqual(len(rsi), len(self.df))

        # RSI should be between 0 and 100
        valid_rsi = rsi.dropna()
        self.assertTrue((valid_rsi >= 0).all() and (valid_rsi <= 100).all())

    def test_atr(self):
        """Test Average True Range"""
        atr = Indicators.atr(self.df['high'], self.df['low'], self.df['close'], 14)

        # Check length
        self.assertEqual(len(atr), len(self.df))

        # ATR should be positive
        valid_atr = atr.dropna()
        self.assertTrue((valid_atr >= 0).all())

    def test_true_range(self):
        """Test True Range calculation"""
        tr = Indicators.true_range(self.df['high'], self.df['low'], self.df['close'])

        # Check length
        self.assertEqual(len(tr), len(self.df))

        # TR should be positive
        valid_tr = tr.dropna()
        self.assertTrue((valid_tr >= 0).all())

    def test_bollinger_bands(self):
        """Test Bollinger Bands"""
        middle, upper, lower = Indicators.bollinger_bands(self.df['close'], 20, 2.0)

        # Check lengths
        self.assertEqual(len(middle), len(self.df))
        self.assertEqual(len(upper), len(self.df))
        self.assertEqual(len(lower), len(self.df))

        # Upper should be > middle > lower (where not NaN)
        for i in range(20, len(self.df)):
            self.assertGreater(upper.iloc[i], middle.iloc[i])
            self.assertGreater(middle.iloc[i], lower.iloc[i])

    def test_macd(self):
        """Test MACD"""
        macd_line, signal_line, histogram = Indicators.macd(self.df['close'])

        # Check lengths
        self.assertEqual(len(macd_line), len(self.df))
        self.assertEqual(len(signal_line), len(self.df))
        self.assertEqual(len(histogram), len(self.df))

        # Histogram should equal macd - signal
        for i in range(30, len(self.df)):
            expected_hist = macd_line.iloc[i] - signal_line.iloc[i]
            self.assertAlmostEqual(histogram.iloc[i], expected_hist, places=5)


if __name__ == '__main__':
    unittest.main()
