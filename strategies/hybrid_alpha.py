"""
Hybrid Alpha Strategy

Balanced hybrid strategy combining mean reversion + momentum targeting 3-5% weekly.

Core Logic:
- Mean reversion base: RSI divergence + oversold/overbought
- Momentum overlay: Volume + ADX confirmation
- Multi-target exits: Quick scalps + trend rides
- Adaptive stops based on market conditions
- Balanced win rate (55-60% target)

Best for: 15m timeframe, volatile altcoins
Trade frequency: 40-50 per week
"""

from typing import Optional
import pandas as pd
import numpy as np

from engine.strategy import Strategy, TradeSignal, PositionState
from engine.indicators import Indicators


class HybridAlphaStrategy(Strategy):
    """Hybrid mean reversion + momentum strategy"""

    def __init__(self):
        super().__init__()
        self.name = "Hybrid Alpha"

        # Indicators
        self.rsi_period = 14
        self.rsi_oversold = 35  # Slightly less extreme than pure scalping
        self.rsi_overbought = 65

        self.adx_period = 14
        self.min_adx = 20  # Lower than pure momentum (accept weaker trends)

        self.volume_period = 20
        self.min_volume_ratio = 1.3  # Lower than pure breakout

        # EMAs for trend context
        self.ema_fast = 9
        self.ema_slow = 21

        # Risk management (balanced)
        self.base_stop_pct = 0.008  # 0.8% base stop
        self.quick_target_pct = 0.012  # 1.2% quick target
        self.momentum_target_pct = 0.025  # 2.5% momentum target

        # Position management
        self.take_quick = 0.5  # Take 50% at quick target
        self.trail_remainder = True  # Trail remaining 50%

    def initialize(self, data: pd.DataFrame) -> pd.DataFrame:
        """Add required indicators"""
        # RSI
        data['rsi'] = Indicators.rsi(data['close'], self.rsi_period)

        # ADX
        data['adx'] = Indicators.adx(data['high'], data['low'], data['close'], self.adx_period)

        # Volume
        data['volume_ma'] = Indicators.volume_ma(data['volume'], self.volume_period)
        data['volume_ratio'] = data['volume'] / data['volume_ma']

        # EMAs
        data['ema_fast'] = Indicators.ema(data['close'], self.ema_fast)
        data['ema_slow'] = Indicators.ema(data['close'], self.ema_slow)

        # ATR
        data['atr'] = Indicators.atr(data['high'], data['low'], data['close'], 14)

        # Bollinger Bands for mean reversion context
        bb_middle, bb_upper, bb_lower = Indicators.bollinger_bands(data['close'], 20, 2.0)
        data['bb_upper'] = bb_upper
        data['bb_lower'] = bb_lower
        data['bb_middle'] = bb_middle

        return data

    def generate_signal(
        self,
        data: pd.DataFrame,
        idx: int,
        position: Optional[PositionState] = None
    ) -> TradeSignal:
        """Generate trading signals"""

        if position is None:
            # Check both mean reversion and momentum setups
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
        """Check for hybrid entry (mean reversion OR momentum)"""
        if idx < 2:
            return None

        current = data.iloc[idx]
        prev = data.iloc[idx - 1]

        # Get values
        rsi = current['rsi']
        adx = current['adx']
        volume_ratio = current['volume_ratio']
        ema_fast = current['ema_fast']
        ema_slow = current['ema_slow']
        close = current['close']
        bb_lower = current['bb_lower']
        bb_upper = current['bb_upper']

        # Setup Type 1: Mean Reversion (high probability, quick profit)
        # RSI oversold + at BB lower + volume confirmation
        if rsi < self.rsi_oversold and volume_ratio > self.min_volume_ratio:
            if close <= bb_lower * 1.01:  # Near or below lower BB
                # Confirmation: price bouncing
                if current['close'] > current['open']:
                    return TradeSignal.LONG

        # Setup Type 2: Momentum Continuation (lower probability, big profit)
        # Strong trend + volume + breakout
        if adx > self.min_adx and volume_ratio > self.min_volume_ratio * 1.2:
            # Uptrend: EMA fast above slow
            if ema_fast > ema_slow * 1.002:  # At least 0.2% separation
                # Price above both EMAs
                if close > ema_fast:
                    # Recent pullback to EMA (buy the dip in uptrend)
                    if prev['low'] <= ema_fast * 1.005:
                        return TradeSignal.LONG

        # Setup Type 3: Hybrid (best of both)
        # RSI oversold BUT in uptrend (pullback buy)
        if rsi < self.rsi_oversold + 5 and volume_ratio > self.min_volume_ratio:
            if ema_fast > ema_slow:  # Uptrend
                if adx > self.min_adx - 5:  # Decent trend strength
                    if current['close'] > current['open']:  # Bullish candle
                        return TradeSignal.LONG

        # Short setups (optional - crypto is more long-biased)
        # Disabled for now

        return None

    def _check_exit(
        self,
        data: pd.DataFrame,
        idx: int,
        position: PositionState
    ) -> Optional[TradeSignal]:
        """Adaptive exit based on entry type"""
        current = data.iloc[idx]
        current_price = current['close']
        rsi = current['rsi']
        atr = current['atr']
        ema_fast = current['ema_fast']
        ema_slow = current['ema_slow']

        if position.direction == 'long':
            # Calculate P&L
            pnl_pct = (current_price - position.entry_price) / position.entry_price

            # Base stop loss (tight)
            if pnl_pct <= -self.base_stop_pct:
                return TradeSignal.CLOSE

            # Detect entry type based on position metadata
            if not hasattr(position, 'entry_type'):
                # Determine retroactively based on entry conditions
                if position.entry_rsi < self.rsi_oversold:
                    position.entry_type = 'mean_reversion'
                else:
                    position.entry_type = 'momentum'

            # Mean reversion exits: Quick profit
            if position.entry_type == 'mean_reversion':
                # Take profit at quick target
                if pnl_pct >= self.quick_target_pct:
                    return TradeSignal.CLOSE

                # Exit if RSI back to neutral
                if rsi >= 50:
                    if pnl_pct > 0:  # Only if profitable
                        return TradeSignal.CLOSE

            # Momentum exits: Let it run
            elif position.entry_type == 'momentum':
                # Quick target (take 50% - tracked but not executed in backtest)
                if not hasattr(position, 'hit_quick_target'):
                    if pnl_pct >= self.quick_target_pct:
                        position.hit_quick_target = True

                # Trailing stop after quick target
                if hasattr(position, 'hit_quick_target'):
                    if not hasattr(position, 'highest_price'):
                        position.highest_price = current_price

                    position.highest_price = max(position.highest_price, current_price)
                    trail_distance = atr * 1.5
                    trailing_stop = position.highest_price - trail_distance

                    if current_price <= trailing_stop:
                        return TradeSignal.CLOSE

                # Full momentum target
                if pnl_pct >= self.momentum_target_pct:
                    return TradeSignal.CLOSE

                # Exit if trend breaks
                if ema_fast < ema_slow:
                    if pnl_pct > 0:  # Only if profitable
                        return TradeSignal.CLOSE

            # Universal exits
            # Breakeven move at +0.5%
            if pnl_pct >= 0.005:
                if not hasattr(position, 'breakeven_moved'):
                    position.breakeven_moved = True
                    # Would move stop to entry here

        elif position.direction == 'short':
            # Similar logic for shorts
            pnl_pct = (position.entry_price - current_price) / position.entry_price

            if pnl_pct <= -self.base_stop_pct:
                return TradeSignal.CLOSE

            if pnl_pct >= self.quick_target_pct:
                return TradeSignal.CLOSE

        return None

    def calculate_position_size(
        self,
        balance: float,
        current_price: float,
        atr: float
    ) -> float:
        """Calculate position size (1.2% risk per trade)"""
        risk_per_trade = balance * 0.012  # 1.2% risk (balanced)
        stop_distance = current_price * self.base_stop_pct
        position_size = risk_per_trade / stop_distance

        # Max 25% of balance per trade
        max_size = (balance * 0.25) / current_price
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
            return entry_price * (1 - self.base_stop_pct)
        else:  # short
            return entry_price * (1 + self.base_stop_pct)

    def get_take_profit(
        self,
        entry_price: float,
        direction: str,
        atr: float
    ) -> float:
        """Calculate take profit price (quick target)"""
        if direction == 'long':
            return entry_price * (1 + self.quick_target_pct)
        else:  # short
            return entry_price * (1 - self.quick_target_pct)
