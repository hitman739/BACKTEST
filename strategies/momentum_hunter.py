"""
Momentum Hunter Strategy

Explosive breakout trading strategy targeting 3-6% weekly returns.

Core Logic:
- Volume breakouts (volume > 2x average)
- ADX trend strength filter (ADX > 30)
- Price breakout above recent high
- Wide targets (2-4%)
- Moderate win rate (45-50% target)

Best for: 15m timeframe, explosive altcoins
Trade frequency: 30-40 per week
"""

from typing import Optional
import pandas as pd
import numpy as np

from engine.strategy import Strategy, TradeSignal, PositionState
from engine.indicators import Indicators


class MomentumHunterStrategy(Strategy):
    """Aggressive breakout trading with momentum confirmation"""

    def __init__(self):
        super().__init__()
        self.name = "Momentum Hunter"

        # Momentum detection
        self.volume_breakout = 2.0  # 2x average volume
        self.volume_period = 20

        self.min_adx = 30  # Strong trend required
        self.adx_period = 14

        self.lookback_high = 20  # Breakout above 20-candle high
        self.breakout_margin = 0.002  # Must break by 0.2%

        # Risk management (wider for breakouts)
        self.stop_atr_multiplier = 1.5  # Stop at 1.5 ATR
        self.target_rr = 3.0  # 1:3 risk/reward
        self.trailing_atr = 1.0  # Trail at 1 ATR

        # Position management
        self.scale_out_1 = 0.015  # Take 30% at +1.5%
        self.scale_out_2 = 0.025  # Take 30% at +2.5%
        # Let 40% run to full target

    def initialize(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add required indicators"""
        # Volume
        data['volume_ma'] = Indicators.volume_ma(data['volume'], self.volume_period)
        data['volume_ratio'] = data['volume'] / data['volume_ma']

        # ADX for trend strength
        data['adx'] = Indicators.adx(data['high'], data['low'], data['close'], self.adx_period)

        # ATR for stops
        data['atr'] = Indicators.atr(data['high'], data['low'], data['close'], 14)

        # Rolling high/low
        data['high_20'] = data['high'].rolling(window=self.lookback_high).max()
        data['low_20'] = data['low'].rolling(window=self.lookback_high).min()

        # EMA for trend direction
        data['ema_20'] = Indicators.ema(data['close'], 20)

        return data

    def generate_signal(
        self,
        data: pd.DataFrame,
        idx: int,
        position: Optional[PositionState] = None
    ) -> TradeSignal:
        """Generate trading signals"""

        if position is None:
            # Look for breakout entry
            signal = self._check_entry(data, idx)
            if signal:
                return signal

        else:
            # Manage position
            signal = self._check_exit(data, idx, position)
            if signal:
                return signal

        return TradeSignal.HOLD

    def _check_entry(self, data: pd.DataFrame, idx: int) -> Optional[TradeSignal]:
        """Check for momentum breakout"""
        if idx < self.lookback_high:
            return None

        current = data.iloc[idx]
        prev = data.iloc[idx - 1]

        # Get values
        close = current['close']
        high = current['high']
        volume_ratio = current['volume_ratio']
        adx = current['adx']
        high_20 = prev['high_20']  # Previous high (not including current)
        ema_20 = current['ema_20']
        atr = current['atr']

        # Filter: Strong trend required
        if adx < self.min_adx:
            return None

        # Filter: Volume breakout
        if volume_ratio < self.volume_breakout:
            return None

        # Long setup: Breakout above recent high + uptrend
        if close > ema_20:  # Uptrend
            breakout_level = high_20 * (1 + self.breakout_margin)
            if high >= breakout_level:
                # Confirmation: close near high (strong candle)
                if close >= high * 0.95:
                    return TradeSignal.LONG

        # Short setup: Breakdown below recent low + downtrend
        # (Disabled for now - focus on longs in crypto)
        # if close < ema_20:  # Downtrend
        #     low_20 = prev['low_20']
        #     breakdown_level = low_20 * (1 - self.breakout_margin)
        #     if current['low'] <= breakdown_level:
        #         if close <= current['low'] * 1.05:
        #             return TradeSignal.SHORT

        return None

    def _check_exit(
        self,
        data: pd.DataFrame,
        idx: int,
        position: PositionState
    ) -> Optional[TradeSignal]:
        """Manage open position with trailing stop"""
        current = data.iloc[idx]
        current_price = current['close']
        atr = current['atr']

        if position.direction == 'long':
            # Calculate P&L
            pnl_pct = (current_price - position.entry_price) / position.entry_price

            # Stop loss (fixed at entry)
            stop_distance = position.entry_atr * self.stop_atr_multiplier
            stop_price = position.entry_price - stop_distance

            if current_price <= stop_price:
                return TradeSignal.CLOSE

            # Scale out at milestones
            if not hasattr(position, 'scaled_out_1'):
                if pnl_pct >= self.scale_out_1:
                    position.scaled_out_1 = True
                    # In real implementation, would close 30% here
                    # For backtest, we track but don't partial close

            if not hasattr(position, 'scaled_out_2'):
                if pnl_pct >= self.scale_out_2:
                    position.scaled_out_2 = True
                    # Would close another 30% here

            # Trailing stop for remaining position
            if pnl_pct >= self.scale_out_1:  # Once in profit
                trailing_stop = current_price - (atr * self.trailing_atr)

                if not hasattr(position, 'highest_price'):
                    position.highest_price = current_price

                position.highest_price = max(position.highest_price, current_price)
                trailing_stop = position.highest_price - (atr * self.trailing_atr)

                if current_price <= trailing_stop:
                    return TradeSignal.CLOSE

            # Full target
            target_pct = (stop_distance / position.entry_price) * self.target_rr
            if pnl_pct >= target_pct:
                return TradeSignal.CLOSE

        elif position.direction == 'short':
            # Similar logic for shorts (if enabled)
            pnl_pct = (position.entry_price - current_price) / position.entry_price
            stop_distance = position.entry_atr * self.stop_atr_multiplier
            stop_price = position.entry_price + stop_distance

            if current_price >= stop_price:
                return TradeSignal.CLOSE

            if pnl_pct >= self.scale_out_1:
                if not hasattr(position, 'lowest_price'):
                    position.lowest_price = current_price

                position.lowest_price = min(position.lowest_price, current_price)
                trailing_stop = position.lowest_price + (atr * self.trailing_atr)

                if current_price >= trailing_stop:
                    return TradeSignal.CLOSE

            target_pct = (stop_distance / position.entry_price) * self.target_rr
            if pnl_pct >= target_pct:
                return TradeSignal.CLOSE

        return None

    def calculate_position_size(
        self,
        balance: float,
        current_price: float,
        atr: float
    ) -> float:
        """Calculate position size (1.5% risk per trade - more aggressive)"""
        risk_per_trade = balance * 0.015  # 1.5% risk
        stop_distance = atr * self.stop_atr_multiplier
        position_size = risk_per_trade / stop_distance

        # Max 30% of balance per trade
        max_size = (balance * 0.30) / current_price
        position_size = min(position_size, max_size)

        return position_size

    def get_stop_loss(
        self,
        entry_price: float,
        direction: str,
        atr: float
    ) -> float:
        """Calculate stop loss price"""
        stop_distance = atr * self.stop_atr_multiplier

        if direction == 'long':
            return entry_price - stop_distance
        else:  # short
            return entry_price + stop_distance

    def get_take_profit(
        self,
        entry_price: float,
        direction: str,
        atr: float
    ) -> float:
        """Calculate take profit price"""
        stop_distance = atr * self.stop_atr_multiplier
        target_distance = stop_distance * self.target_rr

        if direction == 'long':
            return entry_price + target_distance
        else:  # short
            return entry_price - target_distance
