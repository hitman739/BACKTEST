"""
Support Resistance Bounce (SRB) Strategy

Concept: Trade bounces off key levels
- Identifies support/resistance using pivot points
- Enters on wick rejections at these levels
- Tight stops, quick profits

Author: Claude (Original Strategy)
"""

from typing import List
import pandas as pd
import numpy as np
from engine.strategy import BaseStrategy, StrategyContext, StrategyState
from engine.orders import Order, OrderType, OrderSide
from engine.indicators import Indicators


class SRBStrategy(BaseStrategy):
    """Support Resistance Bounce"""

    def __init__(self, config: dict = None):
        if config is None:
            config = {
                'name': 'Support Resistance Bounce',

                # Pivot detection
                'pivot_lookback': 10,  # Look for pivots in last 10 candles
                'pivot_tolerance': 0.002,  # 0.2% tolerance for level match
                'min_touches': 2,  # Need at least 2 touches to establish level

                # Rejection criteria
                'min_wick_ratio': 0.5,  # Wick >= 50% of candle range
                'max_body_ratio': 0.4,  # Small body (<40% of range)

                # Volume
                'min_volume_mult': 1.3,

                # Trend filter
                'ema_period': 50,
                'only_with_trend': True,  # Only bounce with trend

                # Risk management
                'stop_beyond_wick': 0.3,  # Stop 0.3 ATR beyond wick
                'tp1_r': 2.0,
                'tp2_r': 3.5,
                'tp_partial': 0.5,

                'risk_pct': 1.0,
            }

        super().__init__(config)

        self.pivot_lookback = config['pivot_lookback']
        self.pivot_tolerance = config['pivot_tolerance']
        self.min_touches = config['min_touches']
        self.min_wick_ratio = config['min_wick_ratio']
        self.max_body_ratio = config['max_body_ratio']
        self.min_volume_mult = config['min_volume_mult']
        self.ema_period = config['ema_period']
        self.only_with_trend = config['only_with_trend']
        self.stop_beyond_wick = config['stop_beyond_wick']
        self.tp1_r = config['tp1_r']
        self.tp2_r = config['tp2_r']
        self.tp_partial = config['tp_partial']
        self.risk_pct = config['risk_pct']

    def initialize(self, context: StrategyContext) -> pd.DataFrame:
        df = context.data.copy()

        # ATR
        df['atr'] = Indicators.atr(df['high'], df['low'], df['close'], 14)

        # EMA for trend
        df['ema'] = Indicators.ema(df['close'], self.ema_period)

        # Volume
        df['volume_ma'] = df['volume'].rolling(20).mean()

        # Candle characteristics
        df['candle_range'] = df['high'] - df['low']
        df['candle_body'] = abs(df['close'] - df['open'])
        df['upper_wick'] = df['high'] - df[['open', 'close']].max(axis=1)
        df['lower_wick'] = df[['open', 'close']].min(axis=1) - df['low']

        return df

    def on_bar(self, bar: pd.Series, bar_index: int, state: StrategyState, context: StrategyContext) -> List[Order]:
        if bar_index < self.pivot_lookback + 50 or state.position_size != 0:
            return []

        data = context.data.iloc[:bar_index+1]

        # Check for support bounce (LONG)
        if self._check_support_bounce(data, bar_index):
            return self._enter_long(bar, bar_index, state, context, data)

        # Check for resistance bounce (SHORT)
        if self._check_resistance_bounce(data, bar_index):
            return self._enter_short(bar, bar_index, state, context, data)

        return []

    def on_exit(self, bar: pd.Series, bar_index: int, state: StrategyState, context: StrategyContext) -> List[Order]:
        if state.position_size == 0 or not state.entry_price or not state.stop_loss:
            return []

        orders = []
        current_price = bar['close']
        risk = abs(state.entry_price - state.stop_loss)

        tp1_hit = state.custom_data.get('tp1_hit', False)
        tp2_hit = state.custom_data.get('tp2_hit', False)
        position_side = 'long' if state.position_size > 0 else 'short'

        if position_side == 'long':
            pnl_r = (current_price - state.entry_price) / risk if risk > 0 else 0

            if not tp1_hit and pnl_r >= self.tp1_r:
                orders.append(Order(
                    order_id=f'tp1_{bar_index}',
                    symbol=context.symbol,
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=abs(state.position_size) * self.tp_partial,
                    reduce_only=True,
                    tags={'exit_reason': f'TP1_{self.tp1_r}R'}
                ))
                state.custom_data['tp1_hit'] = True

            if not tp2_hit and pnl_r >= self.tp2_r:
                orders.append(Order(
                    order_id=f'tp2_{bar_index}',
                    symbol=context.symbol,
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=abs(state.position_size),
                    reduce_only=True,
                    tags={'exit_reason': f'TP2_{self.tp2_r}R'}
                ))
                state.custom_data['tp2_hit'] = True

            if current_price <= state.stop_loss:
                orders.append(Order(
                    order_id=f'sl_{bar_index}',
                    symbol=context.symbol,
                    side=OrderSide.SELL,
                    order_type=OrderType.MARKET,
                    quantity=abs(state.position_size),
                    reduce_only=True,
                    tags={'exit_reason': 'stop_loss'}
                ))

        else:  # short
            pnl_r = (state.entry_price - current_price) / risk if risk > 0 else 0

            if not tp1_hit and pnl_r >= self.tp1_r:
                orders.append(Order(
                    order_id=f'tp1_{bar_index}',
                    symbol=context.symbol,
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    quantity=abs(state.position_size) * self.tp_partial,
                    reduce_only=True,
                    tags={'exit_reason': f'TP1_{self.tp1_r}R'}
                ))
                state.custom_data['tp1_hit'] = True

            if not tp2_hit and pnl_r >= self.tp2_r:
                orders.append(Order(
                    order_id=f'tp2_{bar_index}',
                    symbol=context.symbol,
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    quantity=abs(state.position_size),
                    reduce_only=True,
                    tags={'exit_reason': f'TP2_{self.tp2_r}R'}
                ))
                state.custom_data['tp2_hit'] = True

            if current_price >= state.stop_loss:
                orders.append(Order(
                    order_id=f'sl_{bar_index}',
                    symbol=context.symbol,
                    side=OrderSide.BUY,
                    order_type=OrderType.MARKET,
                    quantity=abs(state.position_size),
                    reduce_only=True,
                    tags={'exit_reason': 'stop_loss'}
                ))

        return orders

    def _find_support_levels(self, data, idx):
        """Find support levels from recent pivot lows"""

        lookback_data = data.iloc[max(0, idx - self.pivot_lookback):idx]
        lows = lookback_data['low'].values

        # Find local lows (pivots)
        levels = []
        for i in range(2, len(lows) - 2):
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
               lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                levels.append(lows[i])

        # Group similar levels
        if not levels:
            return []

        clustered_levels = []
        levels = sorted(levels)

        current_cluster = [levels[0]]
        for level in levels[1:]:
            if abs(level - current_cluster[0]) / current_cluster[0] < self.pivot_tolerance:
                current_cluster.append(level)
            else:
                if len(current_cluster) >= self.min_touches:
                    clustered_levels.append(np.mean(current_cluster))
                current_cluster = [level]

        if len(current_cluster) >= self.min_touches:
            clustered_levels.append(np.mean(current_cluster))

        return clustered_levels

    def _find_resistance_levels(self, data, idx):
        """Find resistance levels from recent pivot highs"""

        lookback_data = data.iloc[max(0, idx - self.pivot_lookback):idx]
        highs = lookback_data['high'].values

        # Find local highs (pivots)
        levels = []
        for i in range(2, len(highs) - 2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
               highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                levels.append(highs[i])

        # Group similar levels
        if not levels:
            return []

        clustered_levels = []
        levels = sorted(levels, reverse=True)

        current_cluster = [levels[0]]
        for level in levels[1:]:
            if abs(level - current_cluster[0]) / current_cluster[0] < self.pivot_tolerance:
                current_cluster.append(level)
            else:
                if len(current_cluster) >= self.min_touches:
                    clustered_levels.append(np.mean(current_cluster))
                current_cluster = [level]

        if len(current_cluster) >= self.min_touches:
            clustered_levels.append(np.mean(current_cluster))

        return clustered_levels

    def _check_support_bounce(self, data, idx):
        """Check for bounce off support"""

        candle = data.iloc[idx]

        # 1. Find support levels
        support_levels = self._find_support_levels(data, idx)
        if not support_levels:
            return False

        # 2. Check if current candle tested support
        tested_support = False
        for level in support_levels:
            distance = abs(candle['low'] - level) / level
            if distance < self.pivot_tolerance:
                tested_support = True
                break

        if not tested_support:
            return False

        # 3. Strong lower wick (rejection)
        if candle['candle_range'] == 0:
            return False

        lower_wick_ratio = candle['lower_wick'] / candle['candle_range']
        if lower_wick_ratio < self.min_wick_ratio:
            return False

        # 4. Small body
        body_ratio = candle['candle_body'] / candle['candle_range']
        if body_ratio > self.max_body_ratio:
            return False

        # 5. Close above support
        if candle['close'] <= min(support_levels):
            return False

        # 6. Volume
        vol_ratio = candle['volume'] / candle['volume_ma']
        if vol_ratio < self.min_volume_mult:
            return False

        # 7. Trend filter (if enabled)
        if self.only_with_trend:
            if candle['close'] < candle['ema']:
                return False

        return True

    def _check_resistance_bounce(self, data, idx):
        """Check for bounce off resistance"""

        candle = data.iloc[idx]

        # 1. Find resistance levels
        resistance_levels = self._find_resistance_levels(data, idx)
        if not resistance_levels:
            return False

        # 2. Check if current candle tested resistance
        tested_resistance = False
        for level in resistance_levels:
            distance = abs(candle['high'] - level) / level
            if distance < self.pivot_tolerance:
                tested_resistance = True
                break

        if not tested_resistance:
            return False

        # 3. Strong upper wick (rejection)
        if candle['candle_range'] == 0:
            return False

        upper_wick_ratio = candle['upper_wick'] / candle['candle_range']
        if upper_wick_ratio < self.min_wick_ratio:
            return False

        # 4. Small body
        body_ratio = candle['candle_body'] / candle['candle_range']
        if body_ratio > self.max_body_ratio:
            return False

        # 5. Close below resistance
        if candle['close'] >= max(resistance_levels):
            return False

        # 6. Volume
        vol_ratio = candle['volume'] / candle['volume_ma']
        if vol_ratio < self.min_volume_mult:
            return False

        # 7. Trend filter (if enabled)
        if self.only_with_trend:
            if candle['close'] > candle['ema']:
                return False

        return True

    def _enter_long(self, bar, bar_index, state, context, data):
        entry_price = bar['close']
        atr = data['atr'].iloc[bar_index]

        # Tight stop below wick
        stop_loss = bar['low'] - (atr * self.stop_beyond_wick)

        risk = entry_price - stop_loss
        if risk <= 0:
            return []

        account_risk = context.account_equity * (self.risk_pct / 100)
        position_size = account_risk / risk

        state.stop_loss = stop_loss
        state.custom_data['tp1_hit'] = False
        state.custom_data['tp2_hit'] = False

        return [Order(
            order_id=f'long_{bar_index}',
            symbol=context.symbol,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=position_size,
            tags={'setup': 'SRB_LONG', 'stop_loss': stop_loss}
        )]

    def _enter_short(self, bar, bar_index, state, context, data):
        entry_price = bar['close']
        atr = data['atr'].iloc[bar_index]

        # Tight stop above wick
        stop_loss = bar['high'] + (atr * self.stop_beyond_wick)

        risk = stop_loss - entry_price
        if risk <= 0:
            return []

        account_risk = context.account_equity * (self.risk_pct / 100)
        position_size = account_risk / risk

        state.stop_loss = stop_loss
        state.custom_data['tp1_hit'] = False
        state.custom_data['tp2_hit'] = False

        return [Order(
            order_id=f'short_{bar_index}',
            symbol=context.symbol,
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=position_size,
            tags={'setup': 'SRB_SHORT', 'stop_loss': stop_loss}
        )]
