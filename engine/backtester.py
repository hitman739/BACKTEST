"""
Main Backtesting Engine

Orchestrates the entire backtest process:
- Loads data
- Initializes strategy
- Runs simulation loop
- Executes orders
- Tracks positions and PnL
- Generates reports
"""

import pandas as pd
from typing import Dict, Optional
from datetime import datetime
import logging

from engine.data_loader import load_data
from engine.strategy import BaseStrategy, StrategyContext, StrategyState, load_strategy_from_file
from engine.orders import ExecutionEngine, OrderStatus
from engine.account import Account
from engine.metrics import calculate_metrics, format_metrics_table
from engine.reporter import generate_report

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Backtester:
    """
    Main backtesting engine
    """

    def __init__(
        self,
        strategy: BaseStrategy,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str,
        initial_balance: float = 10000,
        leverage: float = 1.0,
        maker_fee: float = 0.0002,
        taker_fee: float = 0.0004,
        slippage_bps: float = 2.0,
        funding_rate: float = 0.0001,
        data_dir: str = "./data/binance",
        use_cache: bool = True
    ):
        """
        Initialize backtester

        Args:
            strategy: Strategy instance
            symbol: Trading symbol (e.g., 'BTCUSDT')
            timeframe: Timeframe (e.g., '5m')
            start_date: Start date 'YYYY-MM-DD'
            end_date: End date 'YYYY-MM-DD'
            initial_balance: Starting balance
            leverage: Leverage to use
            maker_fee: Maker fee rate
            taker_fee: Taker fee rate
            slippage_bps: Slippage in basis points
            funding_rate: Funding rate per 8 hours
            data_dir: Directory for data cache
            use_cache: Whether to use cached data
        """
        self.strategy = strategy
        self.symbol = symbol
        self.timeframe = timeframe
        self.start_date = start_date
        self.end_date = end_date
        self.initial_balance = initial_balance
        self.leverage = leverage
        self.maker_fee = maker_fee
        self.taker_fee = taker_fee
        self.slippage_bps = slippage_bps
        self.funding_rate = funding_rate
        self.data_dir = data_dir
        self.use_cache = use_cache

        # Initialize components
        self.execution_engine = ExecutionEngine(
            maker_fee=maker_fee,
            taker_fee=taker_fee,
            slippage_bps=slippage_bps,
            enable_partial_fills=False  # Disable for deterministic results
        )

        self.account = Account(
            initial_balance=initial_balance,
            leverage=leverage,
            funding_rate=funding_rate
        )

        self.data: Optional[pd.DataFrame] = None
        self.state = StrategyState()

    def load_data(self) -> pd.DataFrame:
        """Load historical data"""
        logger.info(f"Loading data for {self.symbol} {self.timeframe} from {self.start_date} to {self.end_date}")

        df = load_data(
            symbol=self.symbol,
            timeframe=self.timeframe,
            start_date=self.start_date,
            end_date=self.end_date,
            data_dir=self.data_dir,
            use_cache=self.use_cache
        )

        logger.info(f"Loaded {len(df)} candles")
        return df

    def initialize_strategy(self, data: pd.DataFrame) -> pd.DataFrame:
        """Initialize strategy and compute indicators"""
        logger.info("Initializing strategy and computing indicators")

        context = StrategyContext(
            symbol=self.symbol,
            timeframe=self.timeframe,
            leverage=self.leverage,
            account_equity=self.initial_balance,
            position_size=0.0,
            data=data
        )

        # Strategy adds its indicators
        data_with_indicators = self.strategy.initialize(context)

        logger.info(f"Strategy initialized: {self.strategy.name}")
        return data_with_indicators

    def run(self) -> Dict:
        """
        Run the backtest

        Returns:
            Dictionary with metrics and results
        """
        # Load data
        self.data = self.load_data()

        # Initialize strategy
        self.data = self.initialize_strategy(self.data)

        # Create strategy context
        context = StrategyContext(
            symbol=self.symbol,
            timeframe=self.timeframe,
            leverage=self.leverage,
            account_equity=self.account.equity,
            position_size=self.account.position_size,
            data=self.data
        )

        logger.info("Starting backtest simulation")
        logger.info("=" * 60)

        # Simulation loop
        funding_counter = 0
        funding_interval_bars = 96  # 8 hours in 5m bars (adjust based on timeframe)

        for idx in range(len(self.data)):
            bar = self.data.iloc[idx]
            bar_dict = {
                'timestamp': bar['timestamp'],
                'open': bar['open'],
                'high': bar['high'],
                'low': bar['low'],
                'close': bar['close'],
                'volume': bar['volume']
            }

            # Update context
            context.account_equity = self.account.equity
            context.position_size = self.account.position_size

            # Update state
            self.state.position_size = self.account.position_size
            self.state.current_bar_index = idx

            # Check for exits first if in position
            if self.account.position_size != 0:
                exit_orders = self.strategy.on_exit(bar, idx, self.state, context)

                for order in exit_orders:
                    executed_order = self.execution_engine.execute_order(
                        order,
                        bar_dict,
                        self.account.position_size
                    )

                    if executed_order.is_filled:
                        # Close position
                        tags = executed_order.tags.copy()
                        tags['duration_bars'] = idx - self.state.entry_bar_index

                        # Calculate initial risk for R-multiple
                        if self.state.entry_price and self.state.stop_loss:
                            initial_risk = abs(self.state.entry_price - self.state.stop_loss) * abs(self.account.position_size)
                            tags['initial_risk'] = initial_risk

                        self.account.close_position(
                            exit_price=executed_order.filled_price,
                            fee=executed_order.fee,
                            timestamp=bar_dict['timestamp'],
                            tags=tags
                        )

                        # Reset state
                        self.state.position_size = 0.0
                        self.state.entry_price = None
                        self.state.stop_loss = None
                        self.state.take_profit = None

            # Check for entry signals if flat
            if self.account.position_size == 0:
                entry_orders = self.strategy.on_bar(bar, idx, self.state, context)

                for order in entry_orders:
                    executed_order = self.execution_engine.execute_order(
                        order,
                        bar_dict,
                        self.account.position_size
                    )

                    if executed_order.is_filled:
                        # Open position with leverage applied to size
                        # With 10x leverage, position size is 10x larger
                        leveraged_size = executed_order.filled_quantity * self.leverage

                        self.account.open_position(
                            symbol=self.symbol,
                            side='buy' if executed_order.side.value == 'buy' else 'sell',
                            size=leveraged_size,  # Size multiplied by leverage
                            entry_price=executed_order.filled_price,
                            leverage=self.leverage,
                            fee=executed_order.fee,
                            timestamp=bar_dict['timestamp']
                        )

                        # Update state
                        self.state.position_size = self.account.position_size
                        self.state.entry_price = executed_order.filled_price
                        self.state.entry_bar_index = idx

            # Update position with current price
            self.account.update_position(bar['close'], bar['timestamp'])

            # Apply funding periodically
            funding_counter += 1
            if funding_counter >= funding_interval_bars:
                self.account.apply_funding(bar['close'])
                funding_counter = 0

            # Check for liquidation
            if self.account.check_liquidation(bar['close']):
                logger.warning(f"Position liquidated at bar {idx}")
                self.state.position_size = 0.0
                self.state.entry_price = None
                self.state.stop_loss = None
                self.state.take_profit = None

        # Close any remaining position
        if self.account.position_size != 0:
            final_bar = self.data.iloc[-1]
            self.account.close_position(
                exit_price=final_bar['close'],
                fee=abs(self.account.position_size) * final_bar['close'] * self.taker_fee,
                timestamp=final_bar['timestamp'],
                tags={'exit_reason': 'end_of_backtest'}
            )

        logger.info("=" * 60)
        logger.info("Backtest complete")

        # Calculate metrics
        trades_df = self.account.get_trades_df()
        equity_curve_df = self.account.get_equity_curve_df()

        metrics = calculate_metrics(
            trades_df,
            equity_curve_df,
            self.initial_balance
        )

        # Return results
        results = {
            'metrics': metrics,
            'trades': trades_df,
            'equity_curve': equity_curve_df,
            'config': self.get_config()
        }

        return results

    def get_config(self) -> Dict:
        """Get full configuration"""
        return {
            'strategy': {
                'name': self.strategy.name,
                'config': self.strategy.config
            },
            'backtest': {
                'symbol': self.symbol,
                'timeframe': self.timeframe,
                'start_date': self.start_date,
                'end_date': self.end_date,
                'initial_balance': self.initial_balance,
                'leverage': self.leverage,
                'maker_fee': self.maker_fee,
                'taker_fee': self.taker_fee,
                'slippage_bps': self.slippage_bps,
                'funding_rate': self.funding_rate
            }
        }


def run_backtest(
    strategy_path: str,
    symbol: str,
    timeframe: str,
    start_date: str,
    end_date: str,
    initial_balance: float = 10000,
    leverage: float = 1.0,
    maker_fee: float = 0.0002,
    taker_fee: float = 0.0004,
    slippage_bps: float = 2.0,
    report_name: Optional[str] = None,
    data_dir: str = "./data/binance",
    report_dir: str = "./reports"
) -> Dict:
    """
    Convenience function to run a complete backtest

    Args:
        strategy_path: Path to strategy file (YAML/JSON or Python)
        symbol: Trading symbol
        timeframe: Timeframe
        start_date: Start date
        end_date: End date
        initial_balance: Starting balance
        leverage: Leverage
        maker_fee: Maker fee rate
        taker_fee: Taker fee rate
        slippage_bps: Slippage in basis points
        report_name: Optional report name (default: timestamp-based)
        data_dir: Data directory
        report_dir: Report directory

    Returns:
        Results dictionary with metrics
    """
    # Load strategy
    strategy = load_strategy_from_file(strategy_path)

    # Create backtester
    backtester = Backtester(
        strategy=strategy,
        symbol=symbol,
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        initial_balance=initial_balance,
        leverage=leverage,
        maker_fee=maker_fee,
        taker_fee=taker_fee,
        slippage_bps=slippage_bps,
        data_dir=data_dir
    )

    # Run backtest
    results = backtester.run()

    # Generate report
    if report_name is None:
        report_name = f"{symbol}_{timeframe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    generate_report(
        run_id=report_name,
        metrics=results['metrics'],
        config=results['config'],
        trades_df=results['trades'],
        equity_curve_df=results['equity_curve'],
        report_dir=report_dir
    )

    # Print metrics
    print("\n" + "=" * 60)
    print("BACKTEST RESULTS")
    print("=" * 60)
    print(format_metrics_table(results['metrics']))
    print("=" * 60)

    return results
