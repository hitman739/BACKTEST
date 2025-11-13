"""
Order Types and Execution Simulation

Supports:
- Market orders
- Limit orders (with post-only and reduce-only options)
- Stop orders
- Slippage modeling
- Partial fills
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime


class OrderType(Enum):
    """Order type enumeration"""
    MARKET = "market"
    LIMIT = "limit"
    STOP_MARKET = "stop_market"
    STOP_LIMIT = "stop_limit"


class OrderSide(Enum):
    """Order side enumeration"""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Order status enumeration"""
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class Order:
    """
    Represents a trading order
    """
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    post_only: bool = False
    reduce_only: bool = False
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    filled_price: Optional[float] = None
    fee: float = 0.0
    timestamp: Optional[datetime] = None
    fill_timestamp: Optional[datetime] = None
    tags: dict = field(default_factory=dict)

    def __post_init__(self):
        # Convert string enums if needed
        if isinstance(self.side, str):
            self.side = OrderSide(self.side)
        if isinstance(self.order_type, str):
            self.order_type = OrderType(self.order_type)
        if isinstance(self.status, str):
            self.status = OrderStatus(self.status)

    @property
    def is_filled(self) -> bool:
        """Check if order is completely filled"""
        return self.status == OrderStatus.FILLED

    @property
    def is_pending(self) -> bool:
        """Check if order is still pending"""
        return self.status in [OrderStatus.PENDING, OrderStatus.PARTIALLY_FILLED]

    @property
    def remaining_quantity(self) -> float:
        """Get remaining quantity to be filled"""
        return self.quantity - self.filled_quantity


class ExecutionEngine:
    """
    Simulates order execution with realistic market mechanics
    """

    def __init__(
        self,
        maker_fee: float = 0.0002,
        taker_fee: float = 0.0004,
        slippage_bps: float = 2.0,
        enable_partial_fills: bool = False
    ):
        """
        Initialize execution engine

        Args:
            maker_fee: Maker fee rate (default: 0.02%)
            taker_fee: Taker fee rate (default: 0.04%)
            slippage_bps: Slippage in basis points for market orders
            enable_partial_fills: Whether to simulate partial fills
        """
        self.maker_fee = maker_fee
        self.taker_fee = taker_fee
        self.slippage_bps = slippage_bps
        self.enable_partial_fills = enable_partial_fills

    def calculate_slippage(
        self,
        price: float,
        side: OrderSide,
        volume: float,
        bar_volume: float
    ) -> float:
        """
        Calculate slippage based on order size and market conditions

        Args:
            price: Base price
            side: Order side
            volume: Order volume
            bar_volume: Bar volume for impact estimation

        Returns:
            Adjusted price after slippage
        """
        # Base slippage
        base_slippage = price * (self.slippage_bps / 10000)

        # Volume impact (larger orders get worse prices)
        if bar_volume > 0:
            volume_impact = (volume / bar_volume) * price * 0.001
        else:
            volume_impact = 0

        total_slippage = base_slippage + volume_impact

        # Apply slippage direction
        if side == OrderSide.BUY:
            return price + total_slippage
        else:
            return price - total_slippage

    def execute_market_order(
        self,
        order: Order,
        bar: dict,
        current_position_size: float = 0.0
    ) -> Order:
        """
        Execute a market order

        Args:
            order: Order to execute
            bar: Current bar data (open, high, low, close, volume)
            current_position_size: Current position size (for reduce-only check)

        Returns:
            Updated order with execution details
        """
        # Check reduce-only constraint
        if order.reduce_only:
            if current_position_size == 0:
                order.status = OrderStatus.REJECTED
                return order

            # Reduce-only orders can only close positions
            if order.side == OrderSide.BUY and current_position_size >= 0:
                order.status = OrderStatus.REJECTED
                return order
            if order.side == OrderSide.SELL and current_position_size <= 0:
                order.status = OrderStatus.REJECTED
                return order

            # Limit quantity to position size
            max_quantity = abs(current_position_size)
            order.quantity = min(order.quantity, max_quantity)

        # Use close price as base for market orders
        base_price = bar['close']

        # Calculate slippage
        execution_price = self.calculate_slippage(
            base_price,
            order.side,
            order.quantity,
            bar.get('volume', 1000000)
        )

        # Partial fills simulation
        if self.enable_partial_fills:
            # Simulate 70-100% fill on market orders
            fill_ratio = 0.7 + (0.3 * (bar.get('volume', 0) / 1000000))
            fill_ratio = min(1.0, fill_ratio)
            filled_qty = order.quantity * fill_ratio
        else:
            filled_qty = order.quantity

        # Calculate fees (market orders pay taker fees)
        notional = filled_qty * execution_price
        fee = notional * self.taker_fee

        # Update order
        order.filled_quantity = filled_qty
        order.filled_price = execution_price
        order.fee = fee
        order.fill_timestamp = bar.get('timestamp')

        if filled_qty >= order.quantity:
            order.status = OrderStatus.FILLED
        else:
            order.status = OrderStatus.PARTIALLY_FILLED

        return order

    def execute_limit_order(
        self,
        order: Order,
        bar: dict,
        current_position_size: float = 0.0
    ) -> Order:
        """
        Execute a limit order if price is reached

        Args:
            order: Limit order to check
            bar: Current bar data
            current_position_size: Current position size

        Returns:
            Updated order
        """
        if order.price is None:
            order.status = OrderStatus.REJECTED
            return order

        # Check reduce-only constraint
        if order.reduce_only:
            if current_position_size == 0:
                order.status = OrderStatus.REJECTED
                return order

            if order.side == OrderSide.BUY and current_position_size >= 0:
                order.status = OrderStatus.REJECTED
                return order
            if order.side == OrderSide.SELL and current_position_size <= 0:
                order.status = OrderStatus.REJECTED
                return order

            max_quantity = abs(current_position_size)
            order.quantity = min(order.quantity, max_quantity)

        # Check if limit price was reached
        filled = False

        if order.side == OrderSide.BUY:
            # Buy limit: execute if price went below limit
            if bar['low'] <= order.price:
                filled = True
                execution_price = order.price
        else:
            # Sell limit: execute if price went above limit
            if bar['high'] >= order.price:
                filled = True
                execution_price = order.price

        if not filled:
            return order

        # Post-only check: reject if would have taken liquidity
        if order.post_only:
            # Simple check: if limit price would execute immediately, reject
            if order.side == OrderSide.BUY and order.price >= bar['close']:
                order.status = OrderStatus.REJECTED
                return order
            if order.side == OrderSide.SELL and order.price <= bar['close']:
                order.status = OrderStatus.REJECTED
                return order

        # Partial fills for limit orders
        if self.enable_partial_fills:
            fill_ratio = 0.8 + (0.2 * (bar.get('volume', 0) / 1000000))
            fill_ratio = min(1.0, fill_ratio)
            filled_qty = order.quantity * fill_ratio
        else:
            filled_qty = order.quantity

        # Calculate fees (limit orders pay maker fees if post-only, else taker)
        fee_rate = self.maker_fee if order.post_only else self.taker_fee
        notional = filled_qty * execution_price
        fee = notional * fee_rate

        # Update order
        order.filled_quantity = filled_qty
        order.filled_price = execution_price
        order.fee = fee
        order.fill_timestamp = bar.get('timestamp')

        if filled_qty >= order.quantity:
            order.status = OrderStatus.FILLED
        else:
            order.status = OrderStatus.PARTIALLY_FILLED

        return order

    def execute_stop_order(
        self,
        order: Order,
        bar: dict,
        current_position_size: float = 0.0
    ) -> Order:
        """
        Execute a stop order if stop price is reached

        Args:
            order: Stop order
            bar: Current bar
            current_position_size: Current position size

        Returns:
            Updated order
        """
        if order.stop_price is None:
            order.status = OrderStatus.REJECTED
            return order

        # Check if stop was triggered
        triggered = False

        if order.side == OrderSide.BUY:
            # Buy stop: trigger if price went above stop
            if bar['high'] >= order.stop_price:
                triggered = True
        else:
            # Sell stop: trigger if price went below stop
            if bar['low'] <= order.stop_price:
                triggered = True

        if not triggered:
            return order

        # Convert to market or limit order
        if order.order_type == OrderType.STOP_MARKET:
            order.order_type = OrderType.MARKET
            return self.execute_market_order(order, bar, current_position_size)
        elif order.order_type == OrderType.STOP_LIMIT and order.price is not None:
            order.order_type = OrderType.LIMIT
            return self.execute_limit_order(order, bar, current_position_size)

        return order

    def execute_order(
        self,
        order: Order,
        bar: dict,
        current_position_size: float = 0.0
    ) -> Order:
        """
        Execute an order based on its type

        Args:
            order: Order to execute
            bar: Current bar data
            current_position_size: Current position size

        Returns:
            Updated order
        """
        if order.order_type == OrderType.MARKET:
            return self.execute_market_order(order, bar, current_position_size)

        elif order.order_type == OrderType.LIMIT:
            return self.execute_limit_order(order, bar, current_position_size)

        elif order.order_type in [OrderType.STOP_MARKET, OrderType.STOP_LIMIT]:
            return self.execute_stop_order(order, bar, current_position_size)

        else:
            order.status = OrderStatus.REJECTED
            return order
