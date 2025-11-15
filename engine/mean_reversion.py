"""
Mean Reversion Engine - Distance-based DCA with Regime Filters

Core concept:
- Define a dynamic "mean" (VWAP, MIDRANGE, etc.)
- Enter positions when price deviates too far from mean
- Add layers (DCA) as price moves further away
- Exit when price reverts to mean or basket reaches target PnL
- Strong regime filters to avoid bad market conditions
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
import pandas as pd
import numpy as np
from datetime import datetime, time
import uuid

from engine.strategy import BaseStrategy, StrategyContext, StrategyState
from engine.orders import Order, OrderType, OrderSide
from engine.indicators import Indicators


class MeanType(Enum):
    """Types of mean calculation"""
    VWAP = "vwap"  # Volume-weighted average price
    MIDRANGE = "midrange"  # Mid of high/low over lookback
    SMA = "sma"  # Simple moving average
    EMA = "ema"  # Exponential moving average


@dataclass
class Layer:
    """Represents a single DCA layer"""
    entry_price: float
    size: float
    timestamp: pd.Timestamp
    distance_pct: float  # Distance from mean when entered


@dataclass
class Basket:
    """Represents a basket of layers in one direction"""
    side: str  # 'long' or 'short'
    layers: List[Layer] = field(default_factory=list)

    @property
    def total_size(self) -> float:
        """Total position size across all layers"""
        return sum(layer.size for layer in self.layers)

    @property
    def avg_entry_price(self) -> float:
        """Volume-weighted average entry price"""
        if not self.layers:
            return 0.0
        total_notional = sum(layer.entry_price * layer.size for layer in self.layers)
        return total_notional / self.total_size if self.total_size > 0 else 0.0

    @property
    def num_layers(self) -> int:
        """Number of active layers"""
        return len(self.layers)

    def calc_pnl(self, current_price: float) -> float:
        """Calculate unrealized PnL for the basket"""
        if not self.layers:
            return 0.0

        if self.side == 'long':
            return (current_price - self.avg_entry_price) * self.total_size
        else:  # short
            return (self.avg_entry_price - current_price) * self.total_size

    def calc_pnl_pct(self, current_price: float, equity: float) -> float:
        """Calculate PnL as % of account equity"""
        pnl = self.calc_pnl(current_price)
        return (pnl / equity * 100) if equity > 0 else 0.0

    def calc_pnl_pct_from_entry(self, current_price: float) -> float:
        """Calculate PnL as % from average entry price (for stop loss logic)"""
        if not self.layers or self.avg_entry_price == 0:
            return 0.0

        if self.side == 'long':
            return ((current_price - self.avg_entry_price) / self.avg_entry_price) * 100
        else:  # short
            return ((self.avg_entry_price - current_price) / self.avg_entry_price) * 100


@dataclass
class MeanReversionState(StrategyState):
    """Extended state for mean reversion with DCA"""
    long_basket: Basket = field(default_factory=lambda: Basket(side='long'))
    short_basket: Basket = field(default_factory=lambda: Basket(side='short'))
    last_layer_time: Dict[str, pd.Timestamp] = field(default_factory=dict)
    daily_loss: float = 0.0
    current_date: Optional[str] = None
    blocked_sides: Dict[str, pd.Timestamp] = field(default_factory=dict)  # Cooldowns
    total_trades: int = 0
    winning_trades: int = 0


class MeanReversionEngine(BaseStrategy):
    """
    Generic mean reversion engine with distance-based DCA entries
    """

    def __init__(self, config: Dict):
        super().__init__(config)

        # Mean calculation settings
        self.mean_type = MeanType(config.get('mean_type', 'midrange'))
        self.mean_lookback = config.get('mean_lookback', 240)
        self.session_start_hour = config.get('session_start_hour', 0)  # For VWAP reset

        # Entry thresholds (as % distance from mean)
        self.long_thresholds = config.get('long_thresholds', [-1.5, -2.5])
        self.short_thresholds = config.get('short_thresholds', [1.5, 2.5])
        self.max_layers_long = config.get('max_layers_long', 2)
        self.max_layers_short = config.get('max_layers_short', 2)
        self.min_time_between_layers = config.get('min_time_between_layers', 5)  # minutes

        # Position sizing
        self.total_risk_cap_long = config.get('total_risk_cap_long', 1.0)  # % of equity
        self.total_risk_cap_short = config.get('total_risk_cap_short', 1.0)
        self.layer_multipliers = config.get('layer_multipliers', [1.0, 1.0, 1.0])

        # Exit settings
        self.mean_reentry_band = config.get('mean_reentry_band', 0.5)  # % from mean to exit
        self.target_pnl_pct = config.get('target_pnl_pct', 1.0)  # % of equity
        self.max_hold_bars = config.get('max_hold_bars', None)  # Optional time stop
        self.hard_stop_distance = config.get('hard_stop_distance', None)  # e.g., -4% or +4%

        # Regime filters
        self.min_atr_ratio = config.get('min_atr_ratio', 0.8)
        self.max_atr_ratio = config.get('max_atr_ratio', 2.0)
        self.min_vol_ratio = config.get('min_vol_ratio', 0.8)
        self.max_vol_ratio = config.get('max_vol_ratio', 2.5)
        self.min_daily_range_pct = config.get('min_daily_range_pct', None)  # Optional

        # Session filters (UTC hours)
        self.trading_hours = config.get('trading_hours', None)  # [(8, 20)] for London+NY

        # Global risk controls
        self.max_account_dd = config.get('max_account_dd', 20.0)  # %
        self.max_daily_loss = config.get('max_daily_loss', 5.0)  # %
        self.one_side_only = config.get('one_side_only', True)

        # Cooldown after hard stop
        self.cooldown_hours = config.get('cooldown_hours', 4)

    def get_initial_state(self) -> MeanReversionState:
        """Return initial state for this strategy type"""
        return MeanReversionState()

    def initialize(self, context: StrategyContext) -> pd.DataFrame:
        """Initialize indicators"""
        df = context.data.copy()

        # Add required indicators
        df['atr_14'] = Indicators.atr(df['high'], df['low'], df['close'], 14)
        df['atr_200'] = Indicators.atr(df['high'], df['low'], df['close'], 200)
        df['atr_ratio'] = df['atr_14'] / df['atr_200']

        # Volume ratio
        df['volume_ma_20'] = df['volume'].rolling(20).mean()
        df['vol_ratio'] = df['volume'] / df['volume_ma_20']

        # Calculate mean based on type
        df['mean_price'] = self._calculate_mean(df)

        # Distance from mean
        df['distance_pct'] = ((df['close'] - df['mean_price']) / df['mean_price'] * 100)

        # Daily range (for regime filter)
        df['date'] = pd.to_datetime(df['timestamp']).dt.date
        daily_high = df.groupby('date')['high'].transform('max')
        daily_low = df.groupby('date')['low'].transform('min')
        daily_open = df.groupby('date')['open'].transform('first')
        df['daily_range_pct'] = ((daily_high - daily_low) / daily_open * 100)

        # UTC hour
        df['hour'] = pd.to_datetime(df['timestamp']).dt.hour

        return df

    def _calculate_mean(self, df: pd.DataFrame) -> pd.Series:
        """Calculate mean price based on configured type"""
        if self.mean_type == MeanType.MIDRANGE:
            # Rolling mid of high/low
            rolling_high = df['high'].rolling(self.mean_lookback).max()
            rolling_low = df['low'].rolling(self.mean_lookback).min()
            return (rolling_high + rolling_low) / 2

        elif self.mean_type == MeanType.VWAP:
            # Rolling VWAP
            typical_price = (df['high'] + df['low'] + df['close']) / 3
            return self._rolling_vwap(typical_price, df['volume'], self.mean_lookback)

        elif self.mean_type == MeanType.SMA:
            return df['close'].rolling(self.mean_lookback).mean()

        elif self.mean_type == MeanType.EMA:
            return df['close'].ewm(span=self.mean_lookback, adjust=False).mean()

        else:
            # Default to MIDRANGE
            rolling_high = df['high'].rolling(self.mean_lookback).max()
            rolling_low = df['low'].rolling(self.mean_lookback).min()
            return (rolling_high + rolling_low) / 2

    def _rolling_vwap(self, typical_price: pd.Series, volume: pd.Series, window: int) -> pd.Series:
        """Calculate rolling VWAP"""
        tp_vol = typical_price * volume
        rolling_tp_vol = tp_vol.rolling(window).sum()
        rolling_vol = volume.rolling(window).sum()
        return rolling_tp_vol / rolling_vol

    def on_bar(
        self,
        bar: pd.Series,
        bar_index: int,
        state: MeanReversionState,
        context: StrategyContext
    ) -> List[Order]:
        """Check for new entries"""
        orders = []

        # Check global risk limits
        if not self._check_global_limits(bar, state, context):
            return []

        # Check regime filters
        if not self._check_regime_filters(bar):
            return []

        # Check session filters
        if not self._check_session_filters(bar):
            return []

        # Get current distance from mean
        distance_pct = bar.get('distance_pct')
        current_price = bar['close']
        mean_price = bar.get('mean_price')

        # Skip if distance_pct or mean_price is NaN (indicators still initializing)
        if pd.isna(distance_pct) or pd.isna(mean_price):
            return []

        # Check for long entries (price below mean)
        if distance_pct < 0 and not self._is_side_blocked('long', bar, state):
            if self.one_side_only and state.short_basket.num_layers > 0:
                pass  # Skip if short basket active
            else:
                long_orders = self._check_layer_entries(
                    distance_pct, current_price, mean_price, 'long',
                    bar, state, context
                )
                orders.extend(long_orders)

        # Check for short entries (price above mean)
        if distance_pct > 0 and not self._is_side_blocked('short', bar, state):
            if self.one_side_only and state.long_basket.num_layers > 0:
                pass  # Skip if long basket active
            else:
                short_orders = self._check_layer_entries(
                    distance_pct, current_price, mean_price, 'short',
                    bar, state, context
                )
                orders.extend(short_orders)

        # Update state
        state.current_bar_index = bar_index

        return orders

    def _check_layer_entries(
        self,
        distance_pct: float,
        current_price: float,
        mean_price: float,
        side: str,
        bar: pd.Series,
        state: MeanReversionState,
        context: StrategyContext
    ) -> List[Order]:
        """Check if we should add a new layer"""
        orders = []

        basket = state.long_basket if side == 'long' else state.short_basket
        thresholds = self.long_thresholds if side == 'long' else self.short_thresholds
        max_layers = self.max_layers_long if side == 'long' else self.max_layers_short

        # Check if we've hit max layers
        if basket.num_layers >= max_layers:
            return []

        # Check time since last layer
        last_time = state.last_layer_time.get(side)
        if last_time is not None:
            time_diff = (bar['timestamp'] - last_time).total_seconds() / 60
            if time_diff < self.min_time_between_layers:
                return []

        # Determine which layer to add based on distance
        abs_distance = abs(distance_pct)
        current_layer = basket.num_layers

        # Check if distance exceeds the threshold for next layer
        if current_layer < len(thresholds):
            threshold = abs(thresholds[current_layer])
            if abs_distance >= threshold:
                # Calculate position size for this layer
                size = self._calculate_layer_size(
                    current_layer, side, mean_price, current_price, context
                )

                if size > 0:
                    # Create order
                    order_side = OrderSide.BUY if side == 'long' else OrderSide.SELL
                    order = Order(
                        order_id=str(uuid.uuid4()),
                        symbol=context.symbol,
                        side=order_side,
                        order_type=OrderType.MARKET,
                        quantity=size
                    )
                    orders.append(order)

                    # Track layer in basket
                    layer = Layer(
                        entry_price=current_price,
                        size=size,
                        timestamp=bar['timestamp'],
                        distance_pct=distance_pct
                    )
                    basket.layers.append(layer)

                    # Update last layer time
                    state.last_layer_time[side] = bar['timestamp']

        return orders

    def _calculate_layer_size(
        self,
        layer_index: int,
        side: str,
        mean_price: float,
        entry_price: float,
        context: StrategyContext
    ) -> float:
        """Calculate position size for a layer"""
        # Get risk cap and multiplier
        risk_cap = self.total_risk_cap_long if side == 'long' else self.total_risk_cap_short
        multiplier = self.layer_multipliers[layer_index] if layer_index < len(self.layer_multipliers) else 1.0

        # Calculate risk amount for this layer
        total_layers = self.max_layers_long if side == 'long' else self.max_layers_short
        base_risk_per_layer = risk_cap / sum(self.layer_multipliers[:total_layers])
        layer_risk_pct = base_risk_per_layer * multiplier
        layer_risk_amount = context.account_equity * (layer_risk_pct / 100)

        # Use distance to mean as "virtual stop loss"
        distance = abs(entry_price - mean_price)
        if distance == 0:
            return 0.0

        # Size based on risk
        # NOTE: Do NOT apply leverage here - backtester applies it automatically
        size = layer_risk_amount / distance

        return size

    def on_exit(
        self,
        bar: pd.Series,
        bar_index: int,
        state: MeanReversionState,
        context: StrategyContext
    ) -> List[Order]:
        """Check exit conditions for baskets"""
        orders = []

        current_price = bar['close']
        distance_pct = bar.get('distance_pct')

        # Skip if distance_pct is NaN
        if pd.isna(distance_pct):
            return []

        # Check long basket exits
        if state.long_basket.num_layers > 0:
            if self._should_exit_basket(state.long_basket, distance_pct, current_price, bar, state, context):
                # Close all long layers
                total_size = state.long_basket.total_size
                if total_size > 0:
                    orders.append(Order(
                        order_id=str(uuid.uuid4()),
                        symbol=context.symbol,
                        side=OrderSide.SELL,
                        order_type=OrderType.MARKET,
                        quantity=total_size
                    ))

                    # Track performance
                    pnl = state.long_basket.calc_pnl(current_price)
                    state.total_trades += 1
                    if pnl > 0:
                        state.winning_trades += 1

                    # Clear basket
                    state.long_basket.layers.clear()

        # Check short basket exits
        if state.short_basket.num_layers > 0:
            if self._should_exit_basket(state.short_basket, distance_pct, current_price, bar, state, context):
                # Close all short layers
                total_size = state.short_basket.total_size
                if total_size > 0:
                    orders.append(Order(
                        order_id=str(uuid.uuid4()),
                        symbol=context.symbol,
                        side=OrderSide.BUY,
                        order_type=OrderType.MARKET,
                        quantity=total_size
                    ))

                    # Track performance
                    pnl = state.short_basket.calc_pnl(current_price)
                    state.total_trades += 1
                    if pnl > 0:
                        state.winning_trades += 1

                    # Clear basket
                    state.short_basket.layers.clear()

        return orders

    def _should_exit_basket(
        self,
        basket: Basket,
        distance_pct: float,
        current_price: float,
        bar: pd.Series,
        state: MeanReversionState,
        context: StrategyContext
    ) -> bool:
        """Determine if basket should be exited"""
        if basket.num_layers == 0:
            return False

        # Exit condition 1: Price reverted to mean
        abs_distance = abs(distance_pct)
        if abs_distance <= self.mean_reentry_band:
            return True

        # Exit condition 2: Target PnL reached
        pnl_pct = basket.calc_pnl_pct(current_price, context.account_equity)
        if pnl_pct >= self.target_pnl_pct:
            return True

        # Exit condition 3: Hard stop (based on basket PnL from entry, not distance from mean)
        if self.hard_stop_distance is not None:
            basket_pnl_pct = basket.calc_pnl_pct_from_entry(current_price)
            if basket_pnl_pct <= -abs(self.hard_stop_distance):
                # Activate cooldown
                state.blocked_sides[basket.side] = bar['timestamp']
                return True

        # Exit condition 4: Max hold time
        if self.max_hold_bars is not None and basket.layers:
            oldest_layer = basket.layers[0]
            bars_held = (bar['timestamp'] - oldest_layer.timestamp).total_seconds() / 60
            # Convert to bars (assumes 1m timeframe, adjust if needed)
            if bars_held / 1 >= self.max_hold_bars:
                return True

        return False

    def _check_regime_filters(self, bar: pd.Series) -> bool:
        """Check if market regime is favorable"""
        # ATR ratio filter
        atr_ratio = bar.get('atr_ratio')
        if pd.notna(atr_ratio):  # Only check if value exists
            if atr_ratio < self.min_atr_ratio or atr_ratio > self.max_atr_ratio:
                return False

        # Volume ratio filter
        vol_ratio = bar.get('vol_ratio')
        if pd.notna(vol_ratio):  # Only check if value exists
            if vol_ratio < self.min_vol_ratio or vol_ratio > self.max_vol_ratio:
                return False

        # Daily range filter
        if self.min_daily_range_pct is not None:
            daily_range = bar.get('daily_range_pct', 0)
            if pd.notna(daily_range) and daily_range < self.min_daily_range_pct:
                return False

        return True

    def _check_session_filters(self, bar: pd.Series) -> bool:
        """Check if current time is within trading hours"""
        if self.trading_hours is None:
            return True

        hour = bar.get('hour', 0)
        for start_hour, end_hour in self.trading_hours:
            if start_hour <= hour < end_hour:
                return True

        return False

    def _check_global_limits(
        self,
        bar: pd.Series,
        state: MeanReversionState,
        context: StrategyContext
    ) -> bool:
        """Check global risk limits"""
        # Check daily loss limit
        current_date = str(bar.get('date'))
        if current_date != state.current_date:
            # New day, reset
            state.daily_loss = 0.0
            state.current_date = current_date

        daily_loss_pct = (state.daily_loss / context.account_equity * 100)
        if daily_loss_pct >= self.max_daily_loss:
            return False

        # TODO: Check max account drawdown (requires tracking equity high)

        return True

    def _is_side_blocked(self, side: str, bar: pd.Series, state: MeanReversionState) -> bool:
        """Check if side is in cooldown after hard stop"""
        if side not in state.blocked_sides:
            return False

        blocked_time = state.blocked_sides[side]
        hours_elapsed = (bar['timestamp'] - blocked_time).total_seconds() / 3600

        if hours_elapsed >= self.cooldown_hours:
            # Cooldown expired
            del state.blocked_sides[side]
            return False

        return True
