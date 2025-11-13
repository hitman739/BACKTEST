"""
Unit tests for order execution
"""

import unittest
from datetime import datetime
from engine.orders import Order, OrderType, OrderSide, OrderStatus, ExecutionEngine


class TestOrders(unittest.TestCase):
    """Test order execution logic"""

    def setUp(self):
        """Set up test environment"""
        self.engine = ExecutionEngine(
            maker_fee=0.0002,
            taker_fee=0.0004,
            slippage_bps=2.0,
            enable_partial_fills=False
        )

        self.bar = {
            'timestamp': datetime.now(),
            'open': 100.0,
            'high': 102.0,
            'low': 98.0,
            'close': 101.0,
            'volume': 1000000
        }

    def test_market_order_buy(self):
        """Test market buy order execution"""
        order = Order(
            order_id='test_1',
            symbol='BTCUSDT',
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=1.0
        )

        executed = self.engine.execute_market_order(order, self.bar)

        # Should be filled
        self.assertEqual(executed.status, OrderStatus.FILLED)
        self.assertEqual(executed.filled_quantity, 1.0)

        # Should have slippage (price higher than close for buy)
        self.assertGreater(executed.filled_price, self.bar['close'])

        # Should have fee
        self.assertGreater(executed.fee, 0)

    def test_market_order_sell(self):
        """Test market sell order execution"""
        order = Order(
            order_id='test_2',
            symbol='BTCUSDT',
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=1.0
        )

        executed = self.engine.execute_market_order(order, self.bar)

        # Should be filled
        self.assertEqual(executed.status, OrderStatus.FILLED)

        # Should have slippage (price lower than close for sell)
        self.assertLess(executed.filled_price, self.bar['close'])

    def test_limit_order_buy(self):
        """Test limit buy order"""
        # Limit buy at 99 (bar low is 98, so should fill)
        order = Order(
            order_id='test_3',
            symbol='BTCUSDT',
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=1.0,
            price=99.0
        )

        executed = self.engine.execute_limit_order(order, self.bar)

        # Should be filled since bar low (98) <= limit price (99)
        self.assertEqual(executed.status, OrderStatus.FILLED)
        self.assertEqual(executed.filled_price, 99.0)

    def test_limit_order_not_filled(self):
        """Test limit order that doesn't fill"""
        # Limit buy at 95 (bar low is 98, so won't fill)
        order = Order(
            order_id='test_4',
            symbol='BTCUSDT',
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=1.0,
            price=95.0
        )

        executed = self.engine.execute_limit_order(order, self.bar)

        # Should still be pending
        self.assertEqual(executed.status, OrderStatus.PENDING)
        self.assertEqual(executed.filled_quantity, 0.0)

    def test_reduce_only_rejection(self):
        """Test reduce-only order rejection when no position"""
        order = Order(
            order_id='test_5',
            symbol='BTCUSDT',
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=1.0,
            reduce_only=True
        )

        # No position (position_size = 0)
        executed = self.engine.execute_market_order(order, self.bar, current_position_size=0.0)

        # Should be rejected
        self.assertEqual(executed.status, OrderStatus.REJECTED)


class TestPositionSizing(unittest.TestCase):
    """Test position sizing calculations"""

    def test_risk_based_sizing(self):
        """Test position size calculation based on risk"""
        account_equity = 10000
        risk_pct = 0.01  # 1%
        entry_price = 100
        stop_loss = 98

        risk_amount = account_equity * risk_pct  # $100
        price_risk = entry_price - stop_loss  # $2

        position_size = risk_amount / price_risk  # 50 units

        self.assertEqual(position_size, 50.0)

        # Verify PnL if stopped out
        loss = position_size * price_risk
        self.assertAlmostEqual(loss, 100.0, places=2)
        self.assertAlmostEqual(loss / account_equity, 0.01, places=4)


if __name__ == '__main__':
    unittest.main()
