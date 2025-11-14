"""
Scalper Pro Strategy

High-frequency mean reversion scalping strategy targeting 2-4% weekly returns.

Core Logic:
- RSI oversold/overbought entries (RSI < 30 buy, > 70 sell)
- Volume confirmation (volume > 1.5x average)
- Tight stops (0.5-0.8%)
- Quick profit targets (0.8-1.2%)
- High win rate (65-70% target)

Best for: 5m timeframe, volatile altcoins
Trade frequency: 50-80 per week
"""

from typing import Optional
import pandas as pd
import numpy as np

from engine.strategy import Strategy, TradeSignal, PositionState
from engine.indicators import Indicators


class ScalperProStrategy(Strategy):
    """Mean reversion scalping with tight risk management"""

    def __init__(self):
        super().__init__()
        self.name = "Scalper Pro"

        # Configuration
        self.rsi_period = 14
        self.rsi_oversold = 30
        self.rsi_overbought = 70
        self.rsi_exit = 50  # Exit when RSI returns to neutral

        self.volume_multiplier = 1.5  # Volume must be 1.5x average
        self.volume_period = 20

        # Risk management (aggressive for scalping)
        self.stop_loss_pct = 0.007  # 0.7% stop
        self.take_profit_pct = 0.010  # 1.0% target (1.43:1 RR)
        self.breakeven_pct = 0.004  # Move to BE at 0.4%

        # Additional filters
        self.min_candle_size = 0.002  # Min 0.2% candle range
        self.max_spread_pct = 0.001  # Max 0.1% spread

    def initialize(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add required indicators"""
        # RSI
        data['rsi'] = Indicators.rsi(data['close'], self.rsi_period)

        # Volume
        data['volume_ma'] = Indicators.volume_ma(data['volume'], self.volume_period)
        data['volume_ratio'] = data['volume'] / data['volume_ma']

        # ATR for context
        data['atr'] = Indicators.atr(data['high'], data['low'], data['close'], 14)

        # Candle metrics
        data['candle_range'] = (data['high'] - data['low']) / data['low']
        data['spread'] = (data['high'] - data['low']) / data['close']

        return data

    def generate_signal(
        self,
        data: pd.DataFrame,
        idx: int,
        position: Optional[PositionState] = None
    ) -> TradeSignal:
        """Generate trading signals"""

        if position is None:
            # Look for entry
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
        """Check for scalping entry"""
        current = data.iloc[idx]
        prev = data.iloc[idx - 1] if idx > 0 else None

        if prev is None:
            return None

        # Get values
        rsi = current['rsi']
        volume_ratio = current['volume_ratio']
        candle_range = current['candle_range']
        spread = current['spread']

        # Filter: minimum candle size
        if candle_range < self.min_candle_size:
            return None

        # Filter: spread not too wide
        if spread > self.max_spread_pct:
            return None

        # Long setup: RSI oversold + volume confirmation
        if rsi < self.rsi_oversold and volume_ratio > self.volume_multiplier:
            # Additional confirmation: price bouncing up
            if current['close'] > current['open']:
                return TradeSignal.LONG

        # Short setup: RSI overbought + volume confirmation
        if rsi > self.rsi_overbought and volume_ratio > self.volume_multiplier:
            # Additional confirmation: price rejecting
            if current['close'] < current['open']:
                return TradeSignal.SHORT

        return None

    def _check_exit(
        self,
        data: pd.DataFrame,
        idx: int,
        position: PositionState
    ) -> Optional[TradeSignal]:
        """Manage open position"""
        current = data.iloc[idx]
        current_price = current['close']
        rsi = current['rsi']

        if position.direction == 'long':
            # Calculate P&L
            pnl_pct = (current_price - position.entry_price) / position.entry_price

            # Stop loss
            if pnl_pct <= -self.stop_loss_pct:
                return TradeSignal.CLOSE

            # Move to breakeven at +0.4%
            if pnl_pct >= self.breakeven_pct:
                if not hasattr(position, 'breakeven_moved'):
                    position.breakeven_moved = True

            # Take profit at +1%
            if pnl_pct >= self.take_profit_pct:
                return TradeSignal.CLOSE

            # Exit if RSI returns to neutral/overbought
            if rsi >= self.rsi_exit:
                return TradeSignal.CLOSE

        elif position.direction == 'short':
            # Calculate P&L
            pnl_pct = (position.entry_price - current_price) / position.entry_price

            # Stop loss
            if pnl_pct <= -self.stop_loss_pct:
                return TradeSignal.CLOSE

            # Move to breakeven
            if pnl_pct >= self.breakeven_pct:
                if not hasattr(position, 'breakeven_moved'):
                    position.breakeven_moved = True

            # Take profit
            if pnl_pct >= self.take_profit_pct:
                return TradeSignal.CLOSE

            # Exit if RSI returns to neutral/oversold
            if rsi <= self.rsi_exit:
                return TradeSignal.CLOSE

        return None

    def calculate_position_size(
        self,
        balance: float,
        current_price: float,
        atr: float
    ) -> float:
        """Calculate position size (1% risk per trade)"""
        risk_per_trade = balance * 0.01  # 1% risk
        stop_distance = current_price * self.stop_loss_pct
        position_size = risk_per_trade / stop_distance

        # Max 20% of balance per trade (leverage consideration)
        max_size = (balance * 0.20) / current_price
        position_size = min(position_size, max_size)

        return position_size

    def get_stop_loss(
        self,
        entry_price: float,
        direction: str,
        atr: float
    ) -> float:
        """Calculate stop loss price"""
        if direction == 'long':
            return entry_price * (1 - self.stop_loss_pct)
        else:  # short
            return entry_price * (1 + self.stop_loss_pct)

    def get_take_profit(
        self,
        entry_price: float,
        direction: str,
        atr: float
    ) -> float:
        """Calculate take profit price"""
        if direction == 'long':
            return entry_price * (1 + self.take_profit_pct)
        else:  # short
            return entry_price * (1 - self.take_profit_pct)
