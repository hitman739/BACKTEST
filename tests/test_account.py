"""
Unit tests for account and position management
"""

import unittest
from datetime import datetime
from engine.account import Account, Position, PositionSide


class TestAccount(unittest.TestCase):
    """Test account management"""

    def setUp(self):
        """Set up test account"""
        self.account = Account(
            initial_balance=10000,
            leverage=5.0,
            maintenance_margin_rate=0.004
        )

    def test_initial_state(self):
        """Test initial account state"""
        self.assertEqual(self.account.balance, 10000)
        self.assertEqual(self.account.equity, 10000)
        self.assertEqual(self.account.position_size, 0)
        self.assertIsNone(self.account.position)

    def test_open_long_position(self):
        """Test opening a long position"""
        self.account.open_position(
            symbol='BTCUSDT',
            side='buy',
            size=1.0,
            entry_price=100.0,
            leverage=5.0,
            fee=0.04,  # 0.04% of 100 = 0.04
            timestamp=datetime.now()
        )

        # Check position
        self.assertIsNotNone(self.account.position)
        self.assertEqual(self.account.position.size, 1.0)
        self.assertEqual(self.account.position.entry_price, 100.0)
        self.assertEqual(self.account.position.leverage, 5.0)

        # Check balance (should have fee deducted)
        self.assertLess(self.account.balance, 10000)

    def test_unrealized_pnl_long(self):
        """Test unrealized PnL calculation for long position"""
        self.account.open_position(
            symbol='BTCUSDT',
            side='buy',
            size=1.0,
            entry_price=100.0,
            leverage=5.0,
            fee=0.04,
            timestamp=datetime.now()
        )

        # Price goes up to 110
        self.account.update_position(110.0, datetime.now())

        # Unrealized PnL should be (110 - 100) * 1.0 = 10
        self.assertEqual(self.account.position.unrealized_pnl, 10.0)

        # Equity should be balance + unrealized PnL
        expected_equity = self.account.balance + 10.0
        self.assertAlmostEqual(self.account.equity, expected_equity, places=2)

    def test_unrealized_pnl_short(self):
        """Test unrealized PnL calculation for short position"""
        self.account.open_position(
            symbol='BTCUSDT',
            side='sell',
            size=1.0,
            entry_price=100.0,
            leverage=5.0,
            fee=0.04,
            timestamp=datetime.now()
        )

        # Price goes down to 90
        self.account.update_position(90.0, datetime.now())

        # Unrealized PnL should be (100 - 90) * 1.0 = 10
        self.assertEqual(self.account.position.unrealized_pnl, 10.0)

    def test_close_position(self):
        """Test closing a position"""
        # Open position
        self.account.open_position(
            symbol='BTCUSDT',
            side='buy',
            size=1.0,
            entry_price=100.0,
            leverage=5.0,
            fee=0.04,
            timestamp=datetime.now()
        )

        initial_balance = self.account.balance

        # Close at profit
        trade = self.account.close_position(
            exit_price=110.0,
            fee=0.044,  # 0.04% of 110
            timestamp=datetime.now()
        )

        # Should have a trade
        self.assertIsNotNone(trade)
        self.assertEqual(trade.pnl, 10.0)  # (110 - 100) * 1.0

        # Position should be closed
        self.assertIsNone(self.account.position)
        self.assertEqual(self.account.position_size, 0)

        # Balance should reflect PnL minus fees
        expected_balance = initial_balance + 10.0 - 0.044
        self.assertAlmostEqual(self.account.balance, expected_balance, places=2)

    def test_margin_calculation(self):
        """Test margin calculation"""
        self.account.open_position(
            symbol='BTCUSDT',
            side='buy',
            size=1.0,
            entry_price=100.0,
            leverage=5.0,
            fee=0.04,
            timestamp=datetime.now()
        )

        # Margin used = notional / leverage = 100 / 5 = 20
        self.assertEqual(self.account.margin_used, 20.0)

        # Available balance = equity - margin used
        available = self.account.available_balance
        expected_available = self.account.equity - 20.0
        self.assertAlmostEqual(available, expected_available, places=2)

    def test_liquidation_price(self):
        """Test liquidation price calculation"""
        self.account.open_position(
            symbol='BTCUSDT',
            side='buy',
            size=1.0,
            entry_price=100.0,
            leverage=5.0,
            fee=0.04,
            timestamp=datetime.now()
        )

        liq_price = self.account.position.calculate_liquidation_price(0.004)

        # For long with 5x leverage, liquidation should be below entry
        self.assertLess(liq_price, 100.0)

        # Should be roughly at entry * (1 - 1/5 + 0.004)
        expected_approx = 100.0 * (1 - 0.2 + 0.004)
        self.assertAlmostEqual(liq_price, expected_approx, places=1)


class TestDrawdown(unittest.TestCase):
    """Test drawdown calculation"""

    def test_drawdown_tracking(self):
        """Test drawdown calculation"""
        account = Account(initial_balance=10000)

        # Initial peak should be initial balance
        self.assertEqual(account.peak_equity, 10000)
        self.assertEqual(account.current_drawdown, 0)

        # Simulate winning trade
        account.balance = 11000
        account.update_position(100.0, datetime.now())

        # Peak should update
        self.assertEqual(account.peak_equity, 11000)
        self.assertEqual(account.current_drawdown, 0)

        # Simulate losing trade
        account.balance = 10500
        account.update_position(100.0, datetime.now())

        # Should have drawdown
        expected_dd = (11000 - 10500) / 11000
        self.assertAlmostEqual(account.current_drawdown, expected_dd, places=4)


if __name__ == '__main__':
    unittest.main()
