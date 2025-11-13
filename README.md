# Crypto Futures Backtesting Engine

A professional-grade, modular backtesting engine for cryptocurrency futures trading strategies. Built with institutional-quality simulation, comprehensive metrics, and full flexibility for strategy development.

## Features

### Core Capabilities
- **Data Management**: Automated download and caching of Binance Futures OHLCV data
- **Execution Simulation**: Realistic order execution with configurable slippage, fees, and partial fills
- **Position Management**: Full support for leverage, margin requirements, liquidation, and funding rates
- **Strategy Framework**: Dual interface supporting both declarative (YAML/JSON) and programmatic (Python) strategies
- **Comprehensive Metrics**: 20+ performance metrics including Sharpe, Sortino, Calmar, Win Rate, Profit Factor, R-multiples
- **Professional Reporting**: Automated generation of summary.json, trades.csv, equity_curve.csv, and config snapshots

### Order Types
- Market orders (with slippage)
- Limit orders (maker/taker fees)
- Post-only and reduce-only options
- Stop market and stop limit orders

### Technical Indicators
Built-in library includes:
- Moving Averages: SMA, EMA, WMA
- Momentum: RSI, MACD, Stochastic
- Volatility: ATR, Bollinger Bands, True Range
- Volume: VWAP, Volume MA, OBV
- Price Action: Swing High/Low detection
- Fibonacci retracement levels

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd BACKTEST

# Install dependencies
pip install -r requirements.txt
```

## Quick Start

### Running a Backtest

```bash
python run_backtest.py \
    --strategy strategies/examples/ema_cross.yaml \
    --symbol BTCUSDT \
    --timeframe 5m \
    --from 2024-08-01 \
    --to 2024-09-30 \
    --equity 10000 \
    --leverage 5 \
    --report_name my_first_backtest
```

### Command Line Options

| Option | Required | Description | Default |
|--------|----------|-------------|---------|
| `--strategy` | Yes | Path to strategy file (YAML/JSON/Python) | - |
| `--symbol` | Yes | Trading pair (e.g., BTCUSDT) | - |
| `--timeframe` | Yes | Candle interval (1m, 5m, 15m, 1h, etc.) | - |
| `--from` | Yes | Start date (YYYY-MM-DD) | - |
| `--to` | Yes | End date (YYYY-MM-DD) | - |
| `--equity` | No | Initial balance | 10000 |
| `--leverage` | No | Leverage multiplier | 1.0 |
| `--fees_maker` | No | Maker fee rate | 0.0002 (0.02%) |
| `--fees_taker` | No | Taker fee rate | 0.0004 (0.04%) |
| `--slippage` | No | Slippage in basis points | 2.0 |
| `--report_name` | No | Custom report identifier | Auto-generated |
| `--data_dir` | No | Data cache directory | ./data/binance |
| `--report_dir` | No | Report output directory | ./reports |

## Strategy Development

### Declarative Strategy (YAML/JSON)

Create a strategy using rules and indicators without writing Python code.

**Example: `strategies/examples/ema_cross.yaml`**

```yaml
name: "EMA Crossover Strategy"

indicators:
  ema_fast:
    type: ema
    period: 20
    source: close
  ema_slow:
    type: ema
    period: 50
    source: close
  atr:
    type: atr
    period: 14

entry_conditions:
  long:
    - "ema_fast > ema_slow"
    - "ema_fast[1] <= ema_slow[1]"
  short:
    - "ema_fast < ema_slow"
    - "ema_fast[1] >= ema_slow[1]"

exit_rules:
  stop_loss_atr_multiple: 2.0
  take_profit_atr_multiple: 3.0

risk:
  risk_per_trade_pct: 1.0
  max_equity_per_trade: 0.5
  leverage: 5

filters:
  min_atr: 0
  min_volume: 0
```

### Programmatic Strategy (Python)

For complex strategies requiring custom logic, implement a Python class.

**Example: `strategies/examples/simple_ema_cross.py`**

```python
from typing import List
import pandas as pd
from engine.strategy import BaseStrategy, StrategyContext, StrategyState
from engine.orders import Order, OrderType, OrderSide
from engine.indicators import Indicators


class SimpleEMACross(BaseStrategy):
    """Simple EMA crossover strategy"""

    def __init__(self, config: dict = None):
        if config is None:
            config = {
                'name': 'Simple EMA Crossover',
                'fast_ema': 20,
                'slow_ema': 50,
                'atr_period': 14,
                'stop_loss_atr': 2.0,
                'take_profit_atr': 3.0,
                'risk_pct': 1.0,
                'leverage': 5
            }
        super().__init__(config)
        self.fast_period = config.get('fast_ema', 20)
        self.slow_period = config.get('slow_ema', 50)
        self.atr_period = config.get('atr_period', 14)
        self.stop_atr_mult = config.get('stop_loss_atr', 2.0)
        self.tp_atr_mult = config.get('take_profit_atr', 3.0)

    def initialize(self, context: StrategyContext) -> pd.DataFrame:
        """Add indicators to data"""
        df = context.data.copy()
        df['ema_fast'] = Indicators.ema(df['close'], self.fast_period)
        df['ema_slow'] = Indicators.ema(df['close'], self.slow_period)
        df['atr'] = Indicators.atr(df['high'], df['low'], df['close'], self.atr_period)
        return df

    def on_bar(self, bar: pd.Series, bar_index: int, state: StrategyState,
               context: StrategyContext) -> List[Order]:
        """Entry logic - called on each bar"""
        orders = []

        # Skip if already in position
        if state.position_size != 0 or bar_index < 1:
            return orders

        # Get previous bar for crossover detection
        prev_bar = context.data.iloc[bar_index - 1]

        # Bullish crossover: fast EMA crosses above slow EMA
        if bar['ema_fast'] > bar['ema_slow'] and prev_bar['ema_fast'] <= prev_bar['ema_slow']:
            entry_price = bar['close']
            atr = bar['atr']
            stop_loss = entry_price - (atr * self.stop_atr_mult)

            # Calculate position size based on risk
            risk_amount = context.account_equity * 0.01
            position_size = risk_amount / (entry_price - stop_loss)

            order = Order(
                order_id=f"long_{bar_index}",
                symbol=context.symbol,
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=position_size,
                timestamp=bar['timestamp']
            )
            orders.append(order)

            state.stop_loss = stop_loss
            state.take_profit = entry_price + (atr * self.tp_atr_mult)

        return orders

    def on_exit(self, bar: pd.Series, bar_index: int, state: StrategyState,
                context: StrategyContext) -> List[Order]:
        """Exit logic - manage stops and targets"""
        orders = []

        if state.position_size == 0:
            return orders

        is_long = state.position_size > 0
        current_price = bar['close']

        # Check stop loss
        if state.stop_loss and is_long and current_price <= state.stop_loss:
            order = Order(
                order_id=f"exit_sl_{bar_index}",
                symbol=context.symbol,
                side=OrderSide.SELL,
                order_type=OrderType.MARKET,
                quantity=abs(state.position_size),
                timestamp=bar['timestamp'],
                tags={'exit_reason': 'stop_loss'}
            )
            orders.append(order)

        # Check take profit
        elif state.take_profit and is_long and current_price >= state.take_profit:
            order = Order(
                order_id=f"exit_tp_{bar_index}",
                symbol=context.symbol,
                side=OrderSide.SELL,
                order_type=OrderType.MARKET,
                quantity=abs(state.position_size),
                timestamp=bar['timestamp'],
                tags={'exit_reason': 'take_profit'}
            )
            orders.append(order)

        return orders
```

## Project Structure

```
BACKTEST/
├── engine/
│   ├── __init__.py
│   ├── backtester.py      # Main backtesting engine
│   ├── data_loader.py     # Binance data fetching
│   ├── indicators.py      # Technical indicators
│   ├── orders.py          # Order execution
│   ├── account.py         # Position & PnL tracking
│   ├── strategy.py        # Strategy interfaces
│   ├── metrics.py         # Performance calculations
│   └── reporter.py        # Report generation
├── strategies/
│   └── examples/
│       ├── ema_cross.yaml          # Declarative strategy
│       └── simple_ema_cross.py     # Programmatic strategy
├── data/
│   └── binance/           # Cached market data
├── reports/               # Generated reports
├── tests/                 # Unit tests
├── utils/                 # Utility functions
├── run_backtest.py        # CLI entry point
├── requirements.txt       # Dependencies
└── README.md              # This file
```

## Report Files

Each backtest generates a timestamped directory under `reports/` containing:

### 1. `summary.json`
Complete metrics and configuration:
```json
{
  "run_id": "btcusdt_5m_60d_test",
  "timestamp": "2024-11-13T14:35:22",
  "config": {
    "strategy": {...},
    "backtest": {...}
  },
  "metrics": {
    "total_pnl": 1234.56,
    "win_rate_pct": 55.2,
    "sharpe_ratio": 1.8,
    ...
  }
}
```

### 2. `trades.csv`
Detailed trade log with all fills:
- Entry/exit timestamps and prices
- Position size and leverage
- PnL, fees, funding
- R-multiples
- Exit reasons and tags

### 3. `equity_curve.csv`
Equity progression over time:
- Timestamp
- Equity
- Balance
- Unrealized PnL
- Drawdown
- Position size

### 4. `config_snapshot.json`
Exact configuration used for reproducibility.

## Performance Metrics

The engine calculates 20+ metrics across four categories:

### Return Metrics
- Initial Balance
- Final Equity
- Total PnL
- Total Return %

### Trade Metrics
- Total Trades
- Winning/Losing Trades
- Win Rate %
- Average Trade Duration

### Performance Metrics
- Profit Factor (Gross Wins / Gross Losses)
- Expectancy (Expected $ per trade)
- Average Win/Loss
- Average R-Multiple

### Risk Metrics
- Max Drawdown % and $
- Sharpe Ratio (risk-adjusted return)
- Sortino Ratio (downside risk-adjusted)
- Calmar Ratio (return / max drawdown)

## Testing

Run the unit test suite:

```bash
# Run all tests
python -m unittest discover tests -v

# Run specific test modules
python -m unittest tests.test_indicators -v
python -m unittest tests.test_orders -v
python -m unittest tests.test_account -v
```

Test coverage includes:
- Indicator calculations (SMA, EMA, RSI, ATR, etc.)
- Order execution and slippage
- Position sizing and risk management
- PnL calculations and margin requirements
- Liquidation logic
- Drawdown tracking

## Advanced Features

### Custom Indicators

Add your own indicators to `engine/indicators.py`:

```python
@staticmethod
def custom_indicator(series: pd.Series, period: int) -> pd.Series:
    """Your custom indicator logic"""
    result = # ... your calculation
    return result
```

### Position Sizing Strategies

Implement custom position sizing in your strategy:

```python
def calculate_position_size(self, entry_price, stop_loss, account_equity):
    # Fixed fractional
    risk_per_trade = account_equity * 0.02
    position_size = risk_per_trade / (entry_price - stop_loss)

    # Kelly Criterion
    # win_rate, avg_win, avg_loss = self.get_historical_stats()
    # kelly_pct = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
    # position_size = account_equity * kelly_pct / entry_price

    return position_size
```

### Funding Rate Simulation

Funding is applied automatically every 8 hours (configurable):

```python
account = Account(
    initial_balance=10000,
    leverage=5.0,
    funding_rate=0.0001,        # 0.01% per interval
    funding_interval_hours=8     # Standard for perpetual futures
)
```

## Best Practices

### Strategy Development
1. **Start Simple**: Begin with simple logic to validate the framework
2. **Test Incrementally**: Add complexity gradually, testing each component
3. **Use Stops**: Always implement stop losses to prevent catastrophic losses
4. **Risk Management**: Never risk more than 1-2% per trade
5. **Avoid Overfitting**: Test on out-of-sample data periods

### Performance Analysis
1. **Multiple Timeframes**: Test strategies across different timeframes
2. **Market Regimes**: Backtest through trending, ranging, and volatile periods
3. **Parameter Sensitivity**: Vary parameters to assess robustness
4. **Walk-Forward Analysis**: Use rolling windows for validation
5. **Compare Benchmarks**: Always compare against buy-and-hold

### Common Pitfalls
- **Lookahead Bias**: Ensure indicators only use past data
- **Survivorship Bias**: Consider delisted or failed instruments
- **Transaction Costs**: Always include realistic fees and slippage
- **Leverage Risks**: Understand liquidation levels with high leverage
- **Overfitting**: A strategy perfect on historical data rarely works forward

## Data Sources

The engine supports Binance Futures USDT-M perpetual contracts. Historical data is:
- Downloaded via Binance Futures API
- Cached locally in Parquet format for fast re-runs
- Automatically updated when new date ranges are requested

Available timeframes:
- 1m, 3m, 5m, 15m, 30m
- 1h, 2h, 4h, 6h, 8h, 12h
- 1d, 3d, 1w

## Troubleshooting

### No trades generated
- Check indicator calculations are producing valid values
- Verify entry conditions with print statements
- Ensure sufficient warmup period for indicators
- Confirm position sizing is not zero

### Unrealistic results
- Verify slippage and fees are configured
- Check for lookahead bias in indicator calculations
- Ensure orders execute at realistic prices
- Review partial fills settings

### Memory issues
- Use smaller date ranges
- Reduce data caching
- Clear old report files
- Use lower timeframes sparingly (more data)

## Contributing

Contributions are welcome! Areas for enhancement:
- Additional order types (iceberg, TWAP, etc.)
- More sophisticated execution models
- Options and multi-leg strategies
- Machine learning integration
- Live trading adapter
- Web dashboard for results visualization

## License

[Your license here]

## Disclaimer

**This is for educational and research purposes only.**

Past performance does not guarantee future results. Backtesting has inherent limitations and can never fully replicate live trading conditions. Cryptocurrency trading involves substantial risk of loss. Always conduct thorough due diligence and consider your risk tolerance before trading with real capital.

## Support

For questions, issues, or feature requests, please open an issue on GitHub.

---

Built with precision for serious quantitative traders. Happy backtesting! 🚀
