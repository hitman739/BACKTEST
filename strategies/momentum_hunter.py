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

from typing import List
import pandas as pd
from engine.strategy import BaseStrategy, StrategyContext, StrategyState
from engine.orders import Order, OrderType, OrderSide
from engine.indicators import Indicators


class MomentumHunterStrategy(BaseStrategy):
    """Aggressive breakout trading with momentum confirmation"""

    def __init__(self, config: dict = None):
        if config is None:
            config = {
                'name': 'Momentum Hunter',

                # Momentum detection
                'volume_breakout': 2.0,  # 2x volume
                'volume_period': 20,
                'min_adx': 30,  # Strong trend
                'adx_period': 14,
                'lookback_high': 20,  # 20-period high
                'breakout_margin': 0.002,  # 0.2%

                # Risk management (wider for breakouts)
                'stop_atr_multiplier': 1.5,
                'target_rr': 3.0,  # 1:3 RR
                'trailing_atr': 1.0,

                # Position management
                'scale_out_1': 0.015,  # +1.5%
                'scale_out_2': 0.025,  # +2.5%

                'risk_pct': 1.5,  # 1.5% risk (aggressive)
            }

        super().__init__(config)

        self.volume_breakout = config['volume_breakout']
        self.volume_period = config['volume_period']
        self.min_adx = config['min_adx']
        self.adx_period = config['adx_period']
        self.lookback_high = config['lookback_high']
        self.breakout_margin = config['breakout_margin']
        self.stop_atr_multiplier = config['stop_atr_multiplier']
        self.target_rr = config['target_rr']
        self.trailing_atr = config['trailing_atr']
        self.scale_out_1 = config['scale_out_1']
        self.scale_out_2 = config['scale_out_2']
        self.risk_pct = config['risk_pct']

    def initialize(self, context: StrategyContext) -> pd.DataFrame:
        """Add required indicators"""
        df = context.data.copy()

        # Volume
        df['volume_ma'] = Indicators.volume_ma(df['volume'], self.volume_period)
        df['volume_ratio'] = df['volume'] / df['volume_ma']

        # ADX for trend strength
        df['adx'] = Indicators.adx(df['high'], df['low'], df['close'], self.adx_period)

        # ATR for stops
        df['atr'] = Indicators.atr(df['high'], df['low'], df['close'], 14)

        # Rolling high/low
        df['high_20'] = df['high'].rolling(window=self.lookback_high).max()
        df['low_20'] = df['low'].rolling(window=self.lookback_high).min()

        # EMA for trend direction
        df['ema_20'] = Indicators.ema(df['close'], 20)

        return df

    def on_bar(self, bar: pd.Series, bar_index: int, state: StrategyState, context: StrategyContext) -> List[Order]:
        """Entry logic - breakout detection"""
        if bar_index < self.lookback_high or state.position_size != 0:
            return []

        data = context.data.iloc[:bar_index+1]

        # Get values
        close = bar['close']
        high = bar['high']
        volume_ratio = data['volume_ratio'].iloc[bar_index]
        adx = data['adx'].iloc[bar_index]
        high_20 = data['high_20'].iloc[bar_index-1]  # Previous high
        ema_20 = data['ema_20'].iloc[bar_index]

        # Filters
        if adx < self.min_adx:
            return []
        if volume_ratio < self.volume_breakout:
            return []

        # Long setup: Breakout above recent high + uptrend
        if close > ema_20:  # Uptrend
            breakout_level = high_20 * (1 + self.breakout_margin)
            if high >= breakout_level:
                # Strong candle confirmation
                if close >= high * 0.95:
                    return self._enter_long(bar, bar_index, state, context, data)

        return []

    def on_exit(self, bar: pd.Series, bar_index: int, state: StrategyState, context: StrategyContext) -> List[Order]:
        """Exit logic - trailing stop management"""
        if state.position_size == 0 or not state.entry_price or not state.stop_loss:
            return []

        orders = []
        current_price = bar['close']
        data = context.data.iloc[:bar_index+1]
        atr = data['atr'].iloc[bar_index]

        if state.position_size > 0:  # Long position
            entry_atr = state.custom_data.get('entry_atr', atr)
            pnl_pct = (current_price - state.entry_price) / state.entry_price

            # Stop loss
            if current_price <= state.stop_loss:
                orders.append(Order(
                    order_id=f'sl_{bar_index}',
                    symbol=context.symbol,
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=abs(state.position_size),
                    reduce_only=True,
                    tags={'exit_reason': 'STOP_LOSS'}
                ))

            # Trailing stop after first milestone
            elif pnl_pct >= self.scale_out_1:
                if 'highest_price' not in state.custom_data:
                    state.custom_data['highest_price'] = current_price

                state.custom_data['highest_price'] = max(state.custom_data['highest_price'], current_price)
                trailing_stop = state.custom_data['highest_price'] - (atr * self.trailing_atr)

                if current_price <= trailing_stop:
                    orders.append(Order(
                        order_id=f'trail_{bar_index}',
                        symbol=context.symbol,
                        side=OrderSide.SELL,
                        order_type=OrderType.MARKET,
                        quantity=abs(state.position_size),
                        reduce_only=True,
                        tags={'exit_reason': 'TRAILING_STOP'}
                    ))

            # Full target
            stop_distance = abs(state.entry_price - state.stop_loss)
            target_pct = (stop_distance / state.entry_price) * self.target_rr
            if pnl_pct >= target_pct:
                orders.append(Order(
                    order_id=f'tp_{bar_index}',
                    symbol=context.symbol,
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=abs(state.position_size),
                    reduce_only=True,
                    tags={'exit_reason': 'TAKE_PROFIT'}
                ))

        return orders

    def _enter_long(self, bar: pd.Series, bar_index: int, state: StrategyState, context: StrategyContext, data: pd.DataFrame) -> List[Order]:
        """Enter long position"""
        entry_price = bar['close']
        atr = data['atr'].iloc[bar_index]

        # Calculate position size (1.5% risk) WITH LEVERAGE
        risk_amount = context.account_equity * (self.risk_pct / 100)
        stop_distance = atr * self.stop_atr_multiplier
        position_size = (risk_amount / stop_distance) * context.leverage  # 🔥 LEVERAGE APPLIED

        # Max 30% of balance WITH LEVERAGE
        max_size = (context.account_equity * 0.30 * context.leverage) / entry_price
        position_size = min(position_size, max_size)

        # Set stops
        state.stop_loss = entry_price - stop_distance
        target_distance = stop_distance * self.target_rr
        state.take_profit = entry_price + target_distance
        state.entry_price = entry_price
        state.custom_data['entry_atr'] = atr

        return [Order(
            order_id=f'breakout_long_{bar_index}',
            symbol=context.symbol,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=position_size,
            tags={'strategy': 'momentum_hunter', 'setup': 'volume_breakout'}
        )]
