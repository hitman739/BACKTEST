"""
Hybrid Alpha Strategy

Balanced hybrid strategy combining mean reversion + momentum targeting 3-5% weekly.

Core Logic:
- Mean reversion base: RSI oversold/overbought
- Momentum overlay: Volume + ADX confirmation
- Multi-target exits: Quick scalps + trend rides
- Adaptive stops based on market conditions
- Balanced win rate (55-60% target)

Best for: 15m timeframe, volatile altcoins
Trade frequency: 40-50 per week
"""

from typing import List
import pandas as pd
from engine.strategy import BaseStrategy, StrategyContext, StrategyState
from engine.orders import Order, OrderType, OrderSide
from engine.indicators import Indicators


class HybridAlphaStrategy(BaseStrategy):
    """Hybrid mean reversion + momentum strategy"""

    def __init__(self, config: dict = None):
        if config is None:
            config = {
                'name': 'Hybrid Alpha',

                # Indicators
                'rsi_period': 14,
                'rsi_oversold': 35,  # Less extreme than pure scalping
                'rsi_overbought': 65,
                'adx_period': 14,
                'min_adx': 20,  # Lower than pure momentum
                'volume_period': 20,
                'min_volume_mult': 1.3,
                'ema_fast': 9,
                'ema_slow': 21,

                # Risk management (balanced)
                'base_stop_pct': 0.008,  # 0.8%
                'quick_target_pct': 0.012,  # 1.2%
                'momentum_target_pct': 0.025,  # 2.5%
                'breakeven_pct': 0.005,  # 0.5%

                'risk_pct': 1.2,  # 1.2% risk (balanced)
            }

        super().__init__(config)

        self.rsi_period = config['rsi_period']
        self.rsi_oversold = config['rsi_oversold']
        self.rsi_overbought = config['rsi_overbought']
        self.adx_period = config['adx_period']
        self.min_adx = config['min_adx']
        self.volume_period = config['volume_period']
        self.min_volume_mult = config['min_volume_mult']
        self.ema_fast = config['ema_fast']
        self.ema_slow = config['ema_slow']
        self.base_stop_pct = config['base_stop_pct']
        self.quick_target_pct = config['quick_target_pct']
        self.momentum_target_pct = config['momentum_target_pct']
        self.breakeven_pct = config['breakeven_pct']
        self.risk_pct = config['risk_pct']

    def initialize(self, context: StrategyContext) -> pd.DataFrame:
        """Add required indicators"""
        df = context.data.copy()

        # RSI
        df['rsi'] = Indicators.rsi(df['close'], self.rsi_period)

        # ADX
        df['adx'] = Indicators.adx(df['high'], df['low'], df['close'], self.adx_period)

        # Volume
        df['volume_ma'] = Indicators.volume_ma(df['volume'], self.volume_period)
        df['volume_ratio'] = df['volume'] / df['volume_ma']

        # EMAs
        df['ema_fast'] = Indicators.ema(df['close'], self.ema_fast)
        df['ema_slow'] = Indicators.ema(df['close'], self.ema_slow)

        # ATR
        df['atr'] = Indicators.atr(df['high'], df['low'], df['close'], 14)

        # Bollinger Bands
        bb_middle, bb_upper, bb_lower = Indicators.bollinger_bands(df['close'], 20, 2.0)
        df['bb_upper'] = bb_upper
        df['bb_lower'] = bb_lower
        df['bb_middle'] = bb_middle

        return df

    def on_bar(self, bar: pd.Series, bar_index: int, state: StrategyState, context: StrategyContext) -> List[Order]:
        """Entry logic - hybrid setups"""
        if bar_index < max(self.rsi_period, self.ema_slow) or state.position_size != 0:
            return []

        data = context.data.iloc[:bar_index+1]

        # Get values
        rsi = data['rsi'].iloc[bar_index]
        adx = data['adx'].iloc[bar_index]
        volume_ratio = data['volume_ratio'].iloc[bar_index]
        ema_fast = data['ema_fast'].iloc[bar_index]
        ema_slow = data['ema_slow'].iloc[bar_index]
        close = bar['close']
        bb_lower = data['bb_lower'].iloc[bar_index]

        # Setup Type 1: Mean Reversion (RSI oversold + BB)
        if rsi < self.rsi_oversold and volume_ratio > self.min_volume_mult:
            if close <= bb_lower * 1.01:  # Near lower BB
                if bar['close'] > bar['open']:  # Bullish candle
                    return self._enter_long(bar, bar_index, state, context, data, 'mean_reversion')

        # Setup Type 2: Momentum Continuation
        if adx > self.min_adx and volume_ratio > self.min_volume_mult * 1.2:
            if ema_fast > ema_slow * 1.002:  # 0.2% separation
                if close > ema_fast:
                    # Pullback buy
                    prev_low = data['low'].iloc[bar_index-1]
                    if prev_low <= ema_fast * 1.005:
                        return self._enter_long(bar, bar_index, state, context, data, 'momentum')

        # Setup Type 3: Hybrid (RSI + trend)
        if rsi < self.rsi_oversold + 5 and volume_ratio > self.min_volume_mult:
            if ema_fast > ema_slow:  # Uptrend
                if adx > self.min_adx - 5:  # Decent trend
                    if bar['close'] > bar['open']:  # Bullish
                        return self._enter_long(bar, bar_index, state, context, data, 'hybrid')

        return []

    def on_exit(self, bar: pd.Series, bar_index: int, state: StrategyState, context: StrategyContext) -> List[Order]:
        """Adaptive exit based on entry type"""
        if state.position_size == 0 or not state.entry_price:
            return []

        orders = []
        current_price = bar['close']
        data = context.data.iloc[:bar_index+1]
        rsi = data['rsi'].iloc[bar_index]
        atr = data['atr'].iloc[bar_index]
        ema_fast = data['ema_fast'].iloc[bar_index]
        ema_slow = data['ema_slow'].iloc[bar_index]

        if state.position_size > 0:  # Long position
            pnl_pct = (current_price - state.entry_price) / state.entry_price
            entry_type = state.custom_data.get('entry_type', 'mean_reversion')

            # Base stop loss
            if pnl_pct <= -self.base_stop_pct:
                orders.append(Order(
                    order_id=f'sl_{bar_index}',
                    symbol=context.symbol,
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=abs(state.position_size),
                    reduce_only=True,
                    tags={'exit_reason': 'STOP_LOSS'}
                ))

            # Mean reversion exits: Quick profit
            elif entry_type == 'mean_reversion':
                if pnl_pct >= self.quick_target_pct:
                    orders.append(Order(
                        order_id=f'tp_{bar_index}',
                        symbol=context.symbol,
                        side=OrderSide.SELL,
                        order_type=OrderType.MARKET,
                        quantity=abs(state.position_size),
                        reduce_only=True,
                        tags={'exit_reason': 'QUICK_PROFIT'}
                    ))
                elif rsi >= 50 and pnl_pct > 0:
                    orders.append(Order(
                        order_id=f'rsi_{bar_index}',
                        symbol=context.symbol,
                        side=OrderSide.SELL,
                        order_type=OrderType.MARKET,
                        quantity=abs(state.position_size),
                        reduce_only=True,
                        tags={'exit_reason': 'RSI_NEUTRAL'}
                    ))

            # Momentum exits: Let it run with trailing
            elif entry_type in ['momentum', 'hybrid']:
                # Quick target
                if pnl_pct >= self.quick_target_pct:
                    state.custom_data['hit_quick_target'] = True

                # Trailing stop
                if state.custom_data.get('hit_quick_target', False):
                    if 'highest_price' not in state.custom_data:
                        state.custom_data['highest_price'] = current_price

                    state.custom_data['highest_price'] = max(state.custom_data['highest_price'], current_price)
                    trail_distance = atr * 1.5
                    trailing_stop = state.custom_data['highest_price'] - trail_distance

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

                # Full momentum target
                if pnl_pct >= self.momentum_target_pct:
                    orders.append(Order(
                        order_id=f'tp_mom_{bar_index}',
                        symbol=context.symbol,
                        side=OrderSide.SELL,
                        order_type=OrderType.MARKET,
                        quantity=abs(state.position_size),
                        reduce_only=True,
                        tags={'exit_reason': 'MOMENTUM_TARGET'}
                    ))

                # Exit if trend breaks
                if ema_fast < ema_slow and pnl_pct > 0:
                    orders.append(Order(
                        order_id=f'trend_{bar_index}',
                        symbol=context.symbol,
                        side=OrderSide.SELL,
                        order_type=OrderType.MARKET,
                        quantity=abs(state.position_size),
                        reduce_only=True,
                        tags={'exit_reason': 'TREND_BREAK'}
                    ))

        return orders

    def _enter_long(self, bar: pd.Series, bar_index: int, state: StrategyState, context: StrategyContext, data: pd.DataFrame, entry_type: str) -> List[Order]:
        """Enter long position"""
        entry_price = bar['close']

        # Calculate position size (1.2% risk) WITH LEVERAGE
        risk_amount = context.account_equity * (self.risk_pct / 100)
        stop_distance = entry_price * self.base_stop_pct
        position_size = (risk_amount / stop_distance) * context.leverage  # 🔥 LEVERAGE APPLIED

        # Max 25% of balance WITH LEVERAGE
        max_size = (context.account_equity * 0.25 * context.leverage) / entry_price
        position_size = min(position_size, max_size)

        # Set stops
        state.stop_loss = entry_price * (1 - self.base_stop_pct)
        state.take_profit = entry_price * (1 + self.quick_target_pct)
        state.entry_price = entry_price
        state.custom_data['entry_type'] = entry_type
        state.custom_data['entry_rsi'] = data['rsi'].iloc[bar_index]

        return [Order(
            order_id=f'hybrid_long_{bar_index}',
            symbol=context.symbol,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=position_size,
            tags={'strategy': 'hybrid_alpha', 'setup': entry_type}
        )]
