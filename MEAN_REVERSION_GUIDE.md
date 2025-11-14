# Mean Reversion Engine - Complete Guide

## Overview

The Mean Reversion Engine is a professional-grade trading framework designed for crypto futures markets. Unlike traditional indicator-based strategies (RSI, EMA crosses), this engine trades based on **distance from a reference price** (the "mean"), with **layered DCA entries** and **strong regime filters**.

### Philosophy

- **Tolerates drawdown** to capture larger mean reversion wins
- **High win rate** (60-75%) but lower Sharpe ratio (~0.5-1.0)
- **Turns unrealized DD into profit** when price reverts to mean
- **Not a classic indicator bot** - pure price deviation logic
- **Works best in ranging/choppy markets** with clear mean reversion

---

## Architecture

### Core Components

```
engine/mean_reversion.py
├── MeanReversionEngine (Base class)
│   ├── Mean calculation (VWAP, MIDRANGE, SMA, EMA)
│   ├── Distance-based entry logic
│   ├── DCA layer management
│   ├── Basket tracking (long/short baskets)
│   ├── Regime filters (ATR, volume, session)
│   └── Exit logic (reversion, target PnL, hard stops)
│
├── MeanReversionState (Extended state)
│   ├── long_basket: Basket
│   ├── short_basket: Basket
│   ├── last_layer_time: Dict
│   └── blocked_sides: Dict (cooldowns)
│
├── Basket (Position container)
│   ├── layers: List[Layer]
│   ├── avg_entry_price()
│   ├── total_size()
│   └── calc_pnl()
│
└── Layer (Single entry)
    ├── entry_price
    ├── size
    ├── timestamp
    └── distance_pct
```

### Data Flow

1. **Initialization**: Calculate mean price (VWAP/MIDRANGE/etc)
2. **Each Bar**:
   - Calculate distance from mean: `(price - mean) / mean * 100`
   - Check regime filters (ATR, volume, session)
   - Check for layer entries if distance exceeds thresholds
   - Track layers in basket (average entry, total size)
3. **Exit Check**:
   - Exit if price reverts close to mean (±X%)
   - Exit if basket PnL reaches target (e.g., +2.5% equity)
   - Hard stop if distance extends too far (e.g., ±10%)
4. **Position Management**:
   - Each layer adds to position via `account.open_position()`
   - Backtester tracks average entry price automatically
   - Exit closes entire basket in one order

---

## Strategy Variants

### 1. Shallow Revert (Conservative)

**Philosophy**: Capture small, frequent mean reversions with tight risk control.

**Configuration**:
```python
Mean: MIDRANGE (mid of high/low, last 240 candles ≈ 4h)
Entry thresholds:
  - Long: -1.5%, -2.5%
  - Short: +1.5%, +2.5%
Max layers: 2
Total risk: 1% of equity
Layer sizes: [0.4%, 0.6%]
Exit: ±0.5% from mean OR +1.0% PnL
Hard stop: ±4% distance
```

**Expected Performance**:
- Win rate: 65-75%
- Sharpe: 0.8-1.2
- Max DD per basket: 1-2%
- Trades per week: 5-10 (on BTC 1m)

**Best For**: BTC, ETH on 1m and 5m timeframes

---

### 2. Session Revert (Intermediate)

**Philosophy**: Target reversions to session VWAP after aggressive intraday moves.

**Configuration**:
```python
Mean: VWAP (rolling 480 candles ≈ 8h)
Entry thresholds:
  - Long: -3.0%, -5.0%, -7.0%
  - Short: +3.0%, +5.0%, +7.0%
Max layers: 3
Total risk: 2% of equity
Layer sizes: [0.5%, 0.7%, 0.8%]
Exit: ±0.7% from VWAP OR +2.5% PnL
Hard stop: ±10% distance
```

**Regime Filters**:
- Daily range ≥ 2.5% (only trending days)
- Volume ratio: 1.0-3.5
- ATR ratio: 0.5-2.5 (no new layers in crash mode)

**Expected Performance**:
- Win rate: 60-70%
- Sharpe: 0.6-0.9
- Max DD per basket: 2-4%
- Trades per week: 2-5 (selective)

**Best For**: BTC, ETH, SOL on 1m/5m during volatile sessions

---

### 3. Deep Panic Revert (Aggressive)

**Philosophy**: Only trade extreme panic/pump events for massive R-multiples.

**Configuration**:
```python
Mean: MIDRANGE (mid of high/low, last 720 candles ≈ 12h)
Entry thresholds:
  - Long: -5.0%, -8.0%, -11.0%
  - Short: +5.0%, +8.0%, +11.0%
Max layers: 3
Total risk: 3% of equity
Layer sizes: [0.8%, 1.0%, 1.2%]
Exit: ±2.0% from mean OR +4.5% PnL
Hard stop: ±15% distance
Cooldown: 24 hours after hard stop
```

**Regime Filters**:
- Daily range ≥ 5.0% (MUST be extreme event)
- Volume ratio ≥ 1.5 (real volume, not fake)
- No upper ATR limit (trade even in crashes)

**Expected Performance**:
- Win rate: 55-65%
- Sharpe: 0.4-0.7 (tolerates DD)
- Max DD per basket: 5-8%
- Trades per month: 2-8 (very infrequent)
- Average R: 4-6 (massive when it works)

**Best For**: BTC, ETH, SOL during liquidation cascades, flash crashes, major news events

---

## Configuration Reference

### Mean Types

```python
mean_type: 'vwap' | 'midrange' | 'sma' | 'ema'
mean_lookback: int  # Number of candles for calculation

# VWAP: Volume-weighted average price
# - Best for: Session-based mean reversion
# - Resets: No (rolling VWAP over lookback)

# MIDRANGE: Mid of high/low over lookback
# - Best for: Range-bound markets
# - Fast response to price swings

# SMA/EMA: Moving averages
# - Best for: Trend-aware mean reversion
# - Slower to respond
```

### Entry Configuration

```python
long_thresholds: List[float]   # e.g., [-1.5, -2.5, -3.5]
short_thresholds: List[float]  # e.g., [1.5, 2.5, 3.5]
max_layers_long: int
max_layers_short: int
min_time_between_layers: int   # Minutes between layer entries
```

**How it works**:
- When `distance_pct = -1.6%`, enter Layer 1 (threshold -1.5%)
- When `distance_pct = -2.6%`, add Layer 2 (threshold -2.5%)
- Each layer calculates size independently
- Average entry price tracked automatically

### Position Sizing

```python
total_risk_cap_long: float      # % of equity (e.g., 2.0 = 2%)
total_risk_cap_short: float
layer_multipliers: List[float]  # [1.0, 1.2, 1.5] = progressive sizing

# Example:
# total_risk_cap = 2.0%
# layer_multipliers = [0.5, 0.7, 0.8]
# Sum of multipliers = 2.0
# Base risk = 2.0% / 2.0 = 1.0%
# Layer 1: 1.0% * 0.5 = 0.5% equity
# Layer 2: 1.0% * 0.7 = 0.7% equity
# Layer 3: 1.0% * 0.8 = 0.8% equity
# Total: 2.0% equity risk
```

### Exit Configuration

```python
mean_reentry_band: float     # Exit when within ±X% of mean
target_pnl_pct: float        # Exit at +X% of equity PnL
max_hold_bars: Optional[int] # Time-based exit (None = disabled)
hard_stop_distance: float    # Hard cut at ±X% distance
```

**Exit Priority**:
1. **Mean reversion**: Price returns within `mean_reentry_band`
2. **Target PnL**: Basket reaches `target_pnl_pct` profit
3. **Hard stop**: Distance extends beyond `hard_stop_distance`
4. **Time stop**: (Optional) Held for `max_hold_bars`

### Regime Filters

```python
# ATR Filter
min_atr_ratio: float  # ATR(14) / ATR(200) minimum
max_atr_ratio: float  # ATR(14) / ATR(200) maximum

# Volume Filter
min_vol_ratio: float  # Volume / MA(20) minimum
max_vol_ratio: float  # Volume / MA(20) maximum

# Daily Range Filter
min_daily_range_pct: Optional[float]  # (high-low)/open minimum

# Session Filter
trading_hours: Optional[List[Tuple[int, int]]]  # UTC hours
# Example: [(8, 20)] = 08:00-20:00 UTC (London + NY)
```

**Purpose**: Only trade when market conditions are favorable
- Low volatility → no trades (boring)
- Extreme volatility → no new layers (crash mode)
- Dead volume → no trades (fake moves)
- Specific sessions → avoid Asia dead hours

### Global Risk Controls

```python
max_account_dd: float       # Max account drawdown % (circuit breaker)
max_daily_loss: float       # Max daily loss % (daily limit)
one_side_only: bool         # Only long OR short at a time
cooldown_hours: float       # Hours to block side after hard stop
```

---

## Usage

### Quick Start

```bash
# 1. Download 1m data (mean reversion works best on lower timeframes)
python3 download_1m_data.py

# 2. Run comparison of all 3 variants
python3 compare_mean_reversion.py

# 3. Review results
# - Shallow Revert: Highest winrate, lowest DD
# - Session Revert: Balanced
# - Deep Panic: Infrequent, high R
```

### Creating Custom Variants

```python
from engine.mean_reversion import MeanReversionEngine

class MyCustomRevert(MeanReversionEngine):
    def __init__(self):
        config = {
            'name': 'My Custom Mean Reversion',

            # Mean settings
            'mean_type': 'vwap',
            'mean_lookback': 360,  # 6 hours on 1m

            # Entry thresholds
            'long_thresholds': [-2.0, -4.0],
            'short_thresholds': [2.0, 4.0],
            'max_layers_long': 2,
            'max_layers_short': 2,

            # Position sizing
            'total_risk_cap_long': 1.5,
            'total_risk_cap_short': 1.5,
            'layer_multipliers': [0.6, 0.9],

            # Exit settings
            'mean_reentry_band': 0.8,
            'target_pnl_pct': 2.0,
            'hard_stop_distance': 6.0,

            # Regime filters
            'min_atr_ratio': 0.9,
            'max_atr_ratio': 2.2,
            'min_vol_ratio': 1.0,
            'max_vol_ratio': 3.0,
            'min_daily_range_pct': 3.0,

            # Session filters
            'trading_hours': [(8, 20)],  # London + NY

            # Risk controls
            'max_account_dd': 20.0,
            'max_daily_loss': 5.0,
            'one_side_only': True,
            'cooldown_hours': 6,
        }
        super().__init__(config)
```

### Backtesting

```python
from engine.backtester import Backtester
from strategies.shallow_revert import ShallowRevertStrategy

strategy = ShallowRevertStrategy()

backtester = Backtester(
    strategy=strategy,
    symbol='BTCUSDT',
    timeframe='1m',
    start_date='2025-10-01',
    end_date='2025-11-01',
    initial_balance=10000,
    leverage=5.0,  # Conservative for mean reversion
    taker_fee=0.0006,
    slippage_bps=3.0,
    data_dir='./data/binance'
)

results = backtester.run()
```

---

## Performance Analysis

### Key Metrics to Watch

**For Mean Reversion Strategies**:
- **Win Rate**: 60-75% (high is expected)
- **Profit Factor**: 1.5-2.5 (consistent small wins)
- **Max Drawdown**: 5-15% (tolerates DD)
- **Sharpe Ratio**: 0.5-1.2 (lower than momentum)
- **Average R**: 1.5-4.0 (depends on variant)

**Red Flags**:
- Win rate < 50%: Mean not reverting (trending market)
- Profit factor < 1.0: Losses eating profits (bad regime filtering)
- Max DD > 20%: Hard stops not working (distance too large)
- Sharpe < 0.2: DD too large for returns (need tighter stops)

### Comparison: Mean Reversion vs Momentum

| Metric | Mean Reversion | Momentum (Scalper/Hunter) |
|--------|----------------|---------------------------|
| Win Rate | 60-75% | 40-50% |
| Sharpe | 0.5-1.0 | 1.0-2.0 |
| Max DD | 5-15% | 2-8% |
| Avg R | 1.5-4.0 | 2.0-5.0 |
| Best Market | Ranging, choppy | Trending, volatile |
| Entry Logic | Distance from mean | Indicators + volume |
| Exits | Reversion to mean | Trailing stops, targets |

---

## Market Conditions

### Ideal Conditions for Mean Reversion

**✓ Ranging Markets**:
- Price oscillating around a clear mean
- No strong directional bias
- High/low boundaries respected
- VWAP acting as magnet

**✓ Choppy Volatility**:
- ATR elevated but not extreme
- Volume spikes without follow-through
- Failed breakouts reverting to range
- Mean-reversion behavior visible

**✓ Post-Trend Consolidation**:
- After strong move, price consolidates
- Tight range near previous extreme
- Low momentum but decent volume
- VWAP becomes new equilibrium

### Avoid These Conditions

**✗ Strong Trends**:
- Price making higher highs / lower lows
- Mean constantly shifting directionally
- No reversion to previous levels
- DCA layers get run over

**✗ Micro-Chop / Dead Volume**:
- ATR extremely low
- Volume dried up
- Spreads widen, slippage high
- No real moves, just noise

**✗ Crash / Parabolic Pump**:
- One-directional violence
- No intermediate reversions
- Liquidation cascades
- Mean becomes irrelevant

**Note**: Deep Panic Revert is designed FOR crashes, but with very wide stops.

---

## Risk Management

### Position Sizing Guidelines

**Conservative (Shallow Revert)**:
- Total risk: 1-1.5% per side
- Layers: 2-3 max
- Leverage: 3-5x
- For: BTC, ETH, stable pairs

**Moderate (Session Revert)**:
- Total risk: 1.5-2.5% per side
- Layers: 3-4 max
- Leverage: 5-8x
- For: BTC, ETH, SOL, top-tier alts

**Aggressive (Deep Panic)**:
- Total risk: 2.5-4% per side
- Layers: 3-5 max
- Leverage: 8-15x
- For: Extreme events only, BTC/ETH

### Stop Loss Strategy

Mean reversion uses **distance-based hard stops** instead of fixed SL:

```python
# Example: Shallow Revert
long_thresholds = [-1.5, -2.5]
hard_stop_distance = 4.0

# Scenario:
# Enter layer 1 at -1.5% from mean
# Enter layer 2 at -2.5% from mean
# If distance reaches -4.0%, hard stop kicks in
# Total DD: ~2.5% from entry to hard stop
# With 10x leverage: ~25% position loss
# With 1% risk sizing: ~0.25% account loss per layer
```

**Key Points**:
- Hard stop is distance from mean, not entry price
- Each layer has its own entry distance
- Worst case: All layers hit hard stop
- Use `total_risk_cap` to limit max exposure

### Cooldown Mechanism

After hitting a hard stop, the side is **blocked** for `cooldown_hours`:

```python
cooldown_hours = 4  # Shallow Revert
cooldown_hours = 6  # Session Revert
cooldown_hours = 24 # Deep Panic (wait for next event)
```

**Purpose**:
- Prevent revenge trading
- Wait for regime to change
- Avoid catching falling knives in trending markets

---

## Optimization Strategies

### Parameter Tuning

**Entry Thresholds**:
```python
# Tighter thresholds = More trades, smaller DD per basket
long_thresholds = [-1.0, -2.0, -3.0]  # Frequent, small wins

# Wider thresholds = Fewer trades, larger DD, higher R
long_thresholds = [-3.0, -6.0, -9.0]  # Rare, big wins
```

**Mean Lookback**:
```python
# Shorter lookback = Faster response to local swings
mean_lookback = 120  # 2 hours on 1m

# Longer lookback = Smoother mean, slower adaptation
mean_lookback = 720  # 12 hours on 1m
```

**Exit Bands**:
```python
# Tight band = Exit early, lower R, higher WR
mean_reentry_band = 0.3  # Exit at ±0.3% from mean

# Wide band = Hold for larger reversion, lower WR
mean_reentry_band = 1.5  # Exit at ±1.5% from mean
```

### Regime Filter Tuning

**ATR Ratio**:
```python
# Stricter = Only trade normal volatility
min_atr_ratio = 0.9
max_atr_ratio = 1.8

# Looser = Trade wider range of conditions
min_atr_ratio = 0.5
max_atr_ratio = 3.0
```

**Daily Range**:
```python
# Higher threshold = Only volatile days (Session/Deep Panic)
min_daily_range_pct = 3.0

# Lower/None = Trade all days (Shallow Revert)
min_daily_range_pct = None
```

### Walk-Forward Optimization

1. **In-Sample Period**: Optimize on 3 months of data
2. **Out-of-Sample Test**: Validate on next 1 month
3. **Rolling Forward**: Re-optimize every month
4. **Track Drift**: Monitor if parameters need adjustment

**Parameters to Optimize**:
- Entry thresholds (biggest impact)
- Mean lookback (second biggest)
- Exit bands (fine-tuning)
- Layer sizes (risk management)

**Don't Over-Optimize**:
- Regime filters (keep broad)
- Global risk limits (fixed)
- Cooldown hours (behavioral)

---

## Troubleshooting

### Problem: No Trades Generated

**Possible Causes**:
1. Regime filters too strict
2. Mean lookback too short (mean equals price)
3. Entry thresholds too wide (never reached)
4. Session filters blocking all hours

**Solutions**:
- Check `distance_pct` in backtest (is it reaching thresholds?)
- Verify regime filter values (ATR ratio, vol ratio)
- Test without filters first, add incrementally
- Print debug info in `on_bar()` to see why entries skipped

### Problem: Too Many Trades, Low Win Rate

**Possible Causes**:
1. Entry thresholds too tight (chasing noise)
2. Exit band too wide (holding losers)
3. Mean lookback too short (whipsaw)
4. Trending market (mean reversion failing)

**Solutions**:
- Widen entry thresholds (wait for real deviation)
- Tighten exit band (take profit faster)
- Increase mean lookback (smoother mean)
- Add trend filter (don't trade strong trends)

### Problem: Large Drawdowns, Hard Stops Hit

**Possible Causes**:
1. Hard stop distance too wide
2. Layer sizes too aggressive
3. Too many layers accumulating
4. Trending market running over stops

**Solutions**:
- Reduce `hard_stop_distance`
- Reduce `total_risk_cap` per side
- Reduce `max_layers`
- Add trend guard filter

### Problem: Good Backtest, Poor Live Performance

**Possible Causes**:
1. Overfitting to in-sample data
2. Market regime changed
3. Fees/slippage higher in live
4. Partial fills not simulated

**Solutions**:
- Test on multiple time periods
- Use walk-forward validation
- Increase `taker_fee` and `slippage_bps` in backtest
- Test on multiple pairs to validate robustness

---

## Advanced Topics

### Multi-Pair Portfolio

Run multiple mean reversion strategies across different pairs:

```python
# Diversification reduces DD
pairs = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'LINKUSDT']
strategy = ShallowRevertStrategy()

# Allocate capital across pairs
capital_per_pair = 10000 / len(pairs)

# Uncorrelated events → smoother equity curve
# When BTC not reverting, maybe ETH is
```

### Hybrid: Mean Reversion + Momentum

Combine both approaches:
- Use momentum for trend direction
- Use mean reversion for entries within trend
- Example: Uptrend → only take long mean reversions

```python
# Pseudo-code
if ema_fast > ema_slow:  # Uptrend
    # Only enter long on pullbacks to mean
    if distance_pct < -2.0:
        enter_long()
```

### Dynamic Parameter Adjustment

Adapt to changing volatility:

```python
# Adjust entry thresholds based on current ATR
current_atr_ratio = atr_14 / atr_200
if current_atr_ratio > 1.5:
    # High volatility → wider thresholds
    long_thresholds = [-3.0, -6.0]
else:
    # Normal volatility → tighter thresholds
    long_thresholds = [-1.5, -2.5]
```

---

## Best Practices

### DO

✓ Backtest on multiple pairs and time periods
✓ Use walk-forward optimization
✓ Start with conservative variants (Shallow Revert)
✓ Respect regime filters (they save you in bad conditions)
✓ Track basket-level metrics (not just individual trades)
✓ Use lower timeframes (1m, 5m) for mean reversion
✓ Test on both trending and ranging periods
✓ Monitor win rate and profit factor closely

### DON'T

✗ Trade mean reversion in strong trends
✗ Ignore regime filters to force more trades
✗ Use leverage > 10x for mean reversion
✗ Add layers too quickly (respect `min_time_between_layers`)
✗ Over-optimize on one historical period
✗ Expect high Sharpe ratio (mean reversion tolerates DD)
✗ Mix multiple mean types without backtesting
✗ Trade illiquid pairs with mean reversion (slippage kills it)

---

## Conclusion

The Mean Reversion Engine provides a robust framework for trading price deviations with layered entries and strict risk management. The three variants (Shallow, Session, Deep Panic) offer different risk/reward profiles suitable for various market conditions and risk tolerances.

**Key Takeaways**:
- Distance-based entries (no indicators) → clean logic
- DCA layers → average entry, turn DD into wins
- Regime filters → avoid bad conditions
- Basket tracking → manage multiple layers as one position
- High win rate, tolerates DD → different profile than momentum

**Next Steps**:
1. Download 1m data: `python3 download_1m_data.py`
2. Run comparison: `python3 compare_mean_reversion.py`
3. Analyze which variant suits your risk tolerance
4. Customize config for your specific pairs/markets
5. Walk-forward test before live deployment

Good luck trading mean reversion!
