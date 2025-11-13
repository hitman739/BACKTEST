"""
Account and Position Management

Handles:
- Position tracking (size, entry price, leverage)
- PnL calculations (realized and unrealized)
- Margin requirements and liquidation
- Funding rate simulation
- Fee and commission tracking
- Equity curve generation
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum
import pandas as pd


class PositionSide(Enum):
    """Position side"""
    LONG = "long"
    SHORT = "short"
    FLAT = "flat"


@dataclass
class Position:
    """
    Represents an open position
    """
    symbol: str
    side: PositionSide
    size: float  # Contract size (positive for long, negative for short)
    entry_price: float
    leverage: float = 1.0
    unrealized_pnl: float = 0.0
    funding_paid: float = 0.0
    entry_timestamp: Optional[datetime] = None

    @property
    def notional_value(self) -> float:
        """Calculate notional value of position"""
        return abs(self.size) * self.entry_price

    @property
    def margin_used(self) -> float:
        """Calculate margin used"""
        return self.notional_value / self.leverage

    def calculate_unrealized_pnl(self, current_price: float) -> float:
        """
        Calculate unrealized PnL

        Args:
            current_price: Current market price

        Returns:
            Unrealized PnL
        """
        if self.size == 0:
            return 0.0

        if self.size > 0:  # Long position
            self.unrealized_pnl = (current_price - self.entry_price) * self.size
        else:  # Short position
            self.unrealized_pnl = (self.entry_price - current_price) * abs(self.size)

        return self.unrealized_pnl

    def calculate_liquidation_price(self, maintenance_margin_rate: float = 0.004) -> Optional[float]:
        """
        Calculate liquidation price

        Args:
            maintenance_margin_rate: Maintenance margin rate (default: 0.4%)

        Returns:
            Liquidation price or None if no position
        """
        if self.size == 0:
            return None

        # Simplified liquidation formula
        # For long: liq_price = entry_price * (1 - 1/leverage + maintenance_margin_rate)
        # For short: liq_price = entry_price * (1 + 1/leverage - maintenance_margin_rate)

        if self.size > 0:  # Long
            liq_price = self.entry_price * (1 - (1 / self.leverage) + maintenance_margin_rate)
        else:  # Short
            liq_price = self.entry_price * (1 + (1 / self.leverage) - maintenance_margin_rate)

        return liq_price


@dataclass
class Trade:
    """
    Represents a completed trade
    """
    trade_id: int
    symbol: str
    side: str  # 'buy' or 'sell'
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    size: float
    leverage: float
    pnl: float
    pnl_percent: float
    fees: float
    funding: float
    net_pnl: float
    r_multiple: Optional[float] = None  # R-multiple if stop-loss is known
    duration_bars: int = 0
    tags: Dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert trade to dictionary"""
        return {
            'trade_id': self.trade_id,
            'symbol': self.symbol,
            'side': self.side,
            'entry_time': self.entry_time,
            'exit_time': self.exit_time,
            'entry_price': self.entry_price,
            'exit_price': self.exit_price,
            'size': self.size,
            'leverage': self.leverage,
            'pnl': self.pnl,
            'pnl_percent': self.pnl_percent,
            'fees': self.fees,
            'funding': self.funding,
            'net_pnl': self.net_pnl,
            'r_multiple': self.r_multiple,
            'duration_bars': self.duration_bars,
            **self.tags
        }


class Account:
    """
    Manages account balance, positions, and PnL tracking
    """

    def __init__(
        self,
        initial_balance: float,
        leverage: float = 1.0,
        maintenance_margin_rate: float = 0.004,
        funding_rate: float = 0.0001,  # Per 8 hours
        funding_interval_hours: int = 8
    ):
        """
        Initialize account

        Args:
            initial_balance: Starting balance
            leverage: Default leverage
            maintenance_margin_rate: Maintenance margin rate for liquidation
            funding_rate: Funding rate per interval
            funding_interval_hours: Hours between funding payments
        """
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.leverage = leverage
        self.maintenance_margin_rate = maintenance_margin_rate
        self.funding_rate = funding_rate
        self.funding_interval_hours = funding_interval_hours

        self.position: Optional[Position] = None
        self.trades: List[Trade] = []
        self.equity_curve: List[Dict] = []

        # Cumulative tracking
        self.total_fees = 0.0
        self.total_funding = 0.0
        self.realized_pnl = 0.0
        self.peak_equity = initial_balance
        self.current_drawdown = 0.0
        self.max_drawdown = 0.0

        # For trade ID generation
        self._trade_counter = 0

    @property
    def equity(self) -> float:
        """Calculate total equity (balance + unrealized PnL)"""
        unrealized = self.position.unrealized_pnl if self.position else 0.0
        return self.balance + unrealized

    @property
    def margin_used(self) -> float:
        """Get margin currently in use"""
        return self.position.margin_used if self.position else 0.0

    @property
    def available_balance(self) -> float:
        """Calculate available balance for new positions"""
        return self.equity - self.margin_used

    @property
    def position_size(self) -> float:
        """Get current position size (positive for long, negative for short)"""
        return self.position.size if self.position else 0.0

    def open_position(
        self,
        symbol: str,
        side: str,
        size: float,
        entry_price: float,
        leverage: float,
        fee: float,
        timestamp: datetime,
        tags: Optional[dict] = None
    ):
        """
        Open a new position or add to existing

        Args:
            symbol: Trading symbol
            side: 'buy' or 'sell'
            size: Position size
            entry_price: Entry price
            leverage: Leverage used
            fee: Entry fee
            timestamp: Entry timestamp
            tags: Optional metadata tags
        """
        # Deduct fee from balance
        self.balance -= fee
        self.total_fees += fee

        # Determine position size with sign
        position_size = size if side == 'buy' else -size

        if self.position is None or self.position.size == 0:
            # Open new position
            pos_side = PositionSide.LONG if side == 'buy' else PositionSide.SHORT
            self.position = Position(
                symbol=symbol,
                side=pos_side,
                size=position_size,
                entry_price=entry_price,
                leverage=leverage,
                entry_timestamp=timestamp
            )
        else:
            # Adding to existing position or reversing
            new_size = self.position.size + position_size

            if abs(new_size) > abs(self.position.size):
                # Adding to position - recalculate average entry
                old_notional = abs(self.position.size) * self.position.entry_price
                new_notional = abs(position_size) * entry_price
                total_size = abs(self.position.size) + abs(position_size)
                self.position.entry_price = (old_notional + new_notional) / total_size
                self.position.size = new_size
            else:
                # Partial or full close - realize PnL
                self._close_position_partial(position_size, entry_price, fee, timestamp, tags)

    def close_position(
        self,
        exit_price: float,
        fee: float,
        timestamp: datetime,
        size: Optional[float] = None,
        tags: Optional[dict] = None
    ) -> Optional[Trade]:
        """
        Close position (full or partial)

        Args:
            exit_price: Exit price
            fee: Exit fee
            timestamp: Exit timestamp
            size: Size to close (None = full close)
            tags: Optional metadata tags

        Returns:
            Trade object if position was closed
        """
        if self.position is None or self.position.size == 0:
            return None

        # Determine size to close
        if size is None:
            size_to_close = abs(self.position.size)
        else:
            size_to_close = min(size, abs(self.position.size))

        # Calculate PnL
        if self.position.size > 0:  # Long position
            pnl = (exit_price - self.position.entry_price) * size_to_close
            side = 'long'
        else:  # Short position
            pnl = (self.position.entry_price - exit_price) * size_to_close
            side = 'short'

        # Calculate PnL percentage
        notional = size_to_close * self.position.entry_price
        pnl_percent = (pnl / notional) * 100 * self.position.leverage

        # Total fees for this trade
        total_fees = fee  # Entry fee was already deducted

        # Funding costs
        funding = self.position.funding_paid

        # Net PnL
        net_pnl = pnl - fee - funding

        # Update balance
        self.balance += pnl - fee
        self.total_fees += fee
        self.realized_pnl += net_pnl

        # Calculate R-multiple if stop-loss info is in tags
        r_multiple = None
        if tags and 'initial_risk' in tags and tags['initial_risk'] > 0:
            r_multiple = net_pnl / tags['initial_risk']

        # Duration
        duration_bars = tags.get('duration_bars', 0) if tags else 0

        # Create trade record
        self._trade_counter += 1
        trade = Trade(
            trade_id=self._trade_counter,
            symbol=self.position.symbol,
            side=side,
            entry_time=self.position.entry_timestamp,
            exit_time=timestamp,
            entry_price=self.position.entry_price,
            exit_price=exit_price,
            size=size_to_close,
            leverage=self.position.leverage,
            pnl=pnl,
            pnl_percent=pnl_percent,
            fees=total_fees,
            funding=funding,
            net_pnl=net_pnl,
            r_multiple=r_multiple,
            duration_bars=duration_bars,
            tags=tags or {}
        )

        self.trades.append(trade)

        # Update or close position
        if size_to_close >= abs(self.position.size):
            # Full close
            self.position = None
        else:
            # Partial close
            if self.position.size > 0:
                self.position.size -= size_to_close
            else:
                self.position.size += size_to_close

            # Reset funding for remaining position
            self.position.funding_paid = 0.0

        return trade

    def _close_position_partial(
        self,
        size_delta: float,
        price: float,
        fee: float,
        timestamp: datetime,
        tags: Optional[dict]
    ):
        """
        Helper to handle partial closes when opening opposite position

        Args:
            size_delta: Size change (with sign)
            price: Execution price
            fee: Fee paid
            timestamp: Timestamp
            tags: Optional tags
        """
        # This is called when adding to position actually reduces it
        # (e.g., holding long 10, buying -5 = closing 5 long)
        size_to_close = min(abs(size_delta), abs(self.position.size))
        self.close_position(price, fee, timestamp, size_to_close, tags)

    def update_position(self, current_price: float, timestamp: datetime):
        """
        Update position with current price and record equity

        Args:
            current_price: Current market price
            timestamp: Current timestamp
        """
        if self.position:
            self.position.calculate_unrealized_pnl(current_price)

        # Calculate drawdown
        current_equity = self.equity
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity
            self.current_drawdown = 0.0
        else:
            self.current_drawdown = (self.peak_equity - current_equity) / self.peak_equity
            self.max_drawdown = max(self.max_drawdown, self.current_drawdown)

        # Record equity curve point
        self.equity_curve.append({
            'timestamp': timestamp,
            'equity': current_equity,
            'balance': self.balance,
            'unrealized_pnl': self.position.unrealized_pnl if self.position else 0.0,
            'drawdown': self.current_drawdown,
            'position_size': self.position_size
        })

    def apply_funding(self, current_price: float):
        """
        Apply funding rate payment

        Args:
            current_price: Current market price for notional calculation
        """
        if self.position is None or self.position.size == 0:
            return

        notional = abs(self.position.size) * current_price
        funding_payment = notional * self.funding_rate

        # Longs pay funding in typical market, shorts receive
        if self.position.size > 0:
            funding_cost = funding_payment
        else:
            funding_cost = -funding_payment

        self.balance -= funding_cost
        self.total_funding += funding_cost
        if self.position:
            self.position.funding_paid += funding_cost

    def check_liquidation(self, current_price: float) -> bool:
        """
        Check if position should be liquidated

        Args:
            current_price: Current market price

        Returns:
            True if liquidated
        """
        if self.position is None or self.position.size == 0:
            return False

        liq_price = self.position.calculate_liquidation_price(self.maintenance_margin_rate)

        if liq_price is None:
            return False

        # Check if liquidation price was hit
        is_liquidated = False
        if self.position.size > 0 and current_price <= liq_price:
            is_liquidated = True
        elif self.position.size < 0 and current_price >= liq_price:
            is_liquidated = True

        if is_liquidated:
            # Close position at liquidation price with penalty
            liquidation_fee = self.position.margin_used * 0.5  # 50% of margin as penalty
            self.close_position(
                liq_price,
                liquidation_fee,
                datetime.now(),
                tags={'liquidated': True}
            )
            return True

        return False

    def get_equity_curve_df(self) -> pd.DataFrame:
        """Get equity curve as DataFrame"""
        return pd.DataFrame(self.equity_curve)

    def get_trades_df(self) -> pd.DataFrame:
        """Get trades as DataFrame"""
        if not self.trades:
            return pd.DataFrame()
        return pd.DataFrame([t.to_dict() for t in self.trades])
