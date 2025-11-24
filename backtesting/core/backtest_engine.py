"""
Professional Backtesting Engine with Event-Driven Architecture
Author: Trading Pro System
Version: 3.0
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from collections import deque
import json
import pickle

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrderType(Enum):
    """Order types"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"
    TRAILING_STOP = "TRAILING_STOP"


class OrderSide(Enum):
    """Order sides"""
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(Enum):
    """Order status"""
    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIAL = "PARTIAL"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class PositionStatus(Enum):
    """Position status"""
    OPEN = "OPEN"
    CLOSED = "CLOSED"


@dataclass
class Order:
    """Order representation"""
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: str = "GTC"  # GTC, IOC, FOK, DAY
    timestamp: datetime = field(default_factory=datetime.now)
    status: OrderStatus = OrderStatus.PENDING
    filled_price: Optional[float] = None
    filled_quantity: float = 0
    commission: float = 0
    slippage: float = 0
    metadata: Dict = field(default_factory=dict)


@dataclass
class Position:
    """Position representation"""
    position_id: str
    symbol: str
    side: str
    entry_price: float
    quantity: float
    entry_time: datetime
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    status: PositionStatus = PositionStatus.OPEN
    pnl: float = 0
    commission: float = 0
    metadata: Dict = field(default_factory=dict)


@dataclass
class Trade:
    """Completed trade record"""
    trade_id: str
    symbol: str
    side: str
    entry_price: float
    exit_price: float
    quantity: float
    entry_time: datetime
    exit_time: datetime
    pnl: float
    pnl_percentage: float
    commission: float
    slippage: float
    duration: timedelta
    metadata: Dict = field(default_factory=dict)


@dataclass
class BacktestConfig:
    """Backtesting configuration"""
    initial_capital: float = 10000
    commission_rate: float = 0.001  # 0.1%
    slippage_rate: float = 0.0005  # 0.05%
    leverage: float = 1.0
    margin_call_level: float = 0.3  # 30% drawdown
    position_sizing: str = "fixed"  # fixed, kelly, risk_parity
    max_positions: int = 10
    risk_per_trade: float = 0.02  # 2% risk per trade
    use_stops: bool = True
    use_take_profits: bool = True
    allow_shorting: bool = True
    rebalance_frequency: Optional[str] = None  # daily, weekly, monthly
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    data_frequency: str = "1d"  # 1m, 5m, 15m, 1h, 1d
    benchmark_symbol: Optional[str] = "SPY"


@dataclass
class BacktestResult:
    """Comprehensive backtest results"""
    # Performance metrics
    total_return: float = 0
    annual_return: float = 0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0
    avg_win: float = 0
    avg_loss: float = 0
    largest_win: float = 0
    largest_loss: float = 0
    profit_factor: float = 0
    expectancy: float = 0

    # Risk metrics
    max_drawdown: float = 0
    max_drawdown_duration: int = 0
    sharpe_ratio: float = 0
    sortino_ratio: float = 0
    calmar_ratio: float = 0
    omega_ratio: float = 0
    ulcer_index: float = 0
    var_95: float = 0
    cvar_95: float = 0

    # Trading metrics
    avg_trade_duration: float = 0
    max_consecutive_wins: int = 0
    max_consecutive_losses: int = 0
    recovery_factor: float = 0
    payoff_ratio: float = 0
    avg_bars_in_trade: float = 0

    # Portfolio metrics
    final_capital: float = 0
    peak_capital: float = 0
    lowest_capital: float = 0
    total_commission: float = 0
    total_slippage: float = 0
    turnover: float = 0

    # Time series data
    equity_curve: pd.Series = field(default_factory=pd.Series)
    drawdown_curve: pd.Series = field(default_factory=pd.Series)
    returns: pd.Series = field(default_factory=pd.Series)
    positions_over_time: pd.DataFrame = field(default_factory=pd.DataFrame)

    # Trade log
    trades: List[Trade] = field(default_factory=list)
    orders: List[Order] = field(default_factory=list)

    # Metadata
    config: BacktestConfig = field(default_factory=BacktestConfig)
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime = field(default_factory=datetime.now)
    runtime_seconds: float = 0


class BacktestEngine:
    """
    Professional event-driven backtesting engine
    """

    def __init__(self, config: BacktestConfig = None):
        """
        Initialize backtesting engine

        Args:
            config: Backtesting configuration
        """
        self.config = config or BacktestConfig()
        self.reset()

    def reset(self):
        """Reset the backtesting engine to initial state"""
        self.capital = self.config.initial_capital
        self.cash = self.config.initial_capital
        self.positions = {}
        self.closed_positions = []
        self.orders = deque()
        self.filled_orders = []
        self.trades = []
        self.equity_curve = []
        self.current_time = None
        self.current_prices = {}
        self.position_counter = 0
        self.order_counter = 0
        self.trade_counter = 0
        self.metrics_history = []

    def run(self, data: pd.DataFrame, strategy: Callable,
            progress_callback: Optional[Callable] = None) -> BacktestResult:
        """
        Run backtest on historical data

        Args:
            data: Historical OHLCV data with MultiIndex (datetime, symbol) or single symbol
            strategy: Strategy function that generates signals
            progress_callback: Optional callback for progress updates

        Returns:
            BacktestResult with comprehensive metrics
        """
        start_time = datetime.now()
        self.reset()

        # Prepare data
        if not isinstance(data.index, pd.MultiIndex):
            # Single symbol data
            data = data.sort_index()
            symbols = ['default']
        else:
            # Multi-symbol data
            data = data.sort_index()
            symbols = data.index.get_level_values(1).unique()

        # Apply date filtering if specified
        if self.config.start_date:
            data = data[data.index >= self.config.start_date]
        if self.config.end_date:
            data = data[data.index <= self.config.end_date]

        total_bars = len(data.index.get_level_values(0).unique()) if isinstance(
            data.index, pd.MultiIndex) else len(data)

        # Main backtesting loop
        for i, (timestamp, bar_data) in enumerate(self._iterate_bars(data)):
            self.current_time = timestamp

            # Update current prices
            self._update_prices(bar_data)

            # Update positions with current prices
            self._update_positions()

            # Check margin requirements
            if self._check_margin_call():
                self._close_all_positions("Margin call")
                break

            # Process pending orders
            self._process_orders(bar_data)

            # Generate signals from strategy
            signals = strategy(
                bar_data,
                self.positions,
                self.capital,
                self.current_time
            )

            # Create orders from signals
            if signals:
                self._create_orders_from_signals(signals)

            # Update equity curve
            self._update_equity()

            # Progress callback
            if progress_callback and i % 100 == 0:
                progress = (i + 1) / total_bars
                progress_callback(progress, self.capital)

            # Risk management checks
            self._apply_risk_management()

        # Close remaining positions
        self._close_all_positions("Backtest ended")

        # Calculate final metrics
        result = self._calculate_results()
        result.start_time = start_time
        result.end_time = datetime.now()
        result.runtime_seconds = (result.end_time - start_time).total_seconds()

        return result

    def _iterate_bars(self, data: pd.DataFrame):
        """
        Iterate through data bars

        Yields:
            Tuple of (timestamp, bar_data)
        """
        if isinstance(data.index, pd.MultiIndex):
            # Multi-symbol data
            timestamps = data.index.get_level_values(0).unique()
            for timestamp in timestamps:
                bar_data = data.xs(timestamp, level=0)
                yield timestamp, bar_data
        else:
            # Single symbol data
            for timestamp, row in data.iterrows():
                yield timestamp, row.to_frame().T

    def _update_prices(self, bar_data):
        """Update current prices from bar data"""
        if isinstance(bar_data, pd.DataFrame):
            for symbol in bar_data.index:
                self.current_prices[symbol] = bar_data.loc[symbol, 'close']
        else:
            self.current_prices['default'] = bar_data['close'].iloc[0]

    def _update_positions(self):
        """Update position values with current prices"""
        for position_id, position in self.positions.items():
            if position.symbol in self.current_prices:
                current_price = self.current_prices[position.symbol]

                # Calculate unrealized P&L
                if position.side == "BUY":
                    position.pnl = (current_price - position.entry_price) * position.quantity
                else:  # SELL
                    position.pnl = (position.entry_price - current_price) * position.quantity

                # Check stop loss
                if position.stop_loss:
                    if (position.side == "BUY" and current_price <= position.stop_loss) or \
                       (position.side == "SELL" and current_price >= position.stop_loss):
                        self._close_position(position_id, current_price, "Stop loss hit")

                # Check take profit
                if position.take_profit:
                    if (position.side == "BUY" and current_price >= position.take_profit) or \
                       (position.side == "SELL" and current_price <= position.take_profit):
                        self._close_position(position_id, current_price, "Take profit hit")

    def _check_margin_call(self) -> bool:
        """Check if margin call level is reached"""
        current_equity = self._calculate_equity()
        drawdown = (self.config.initial_capital - current_equity) / self.config.initial_capital

        return drawdown >= self.config.margin_call_level

    def _process_orders(self, bar_data):
        """Process pending orders"""
        filled_orders = []

        for order in list(self.orders):
            if order.status != OrderStatus.PENDING:
                continue

            # Get current bar for order symbol
            if isinstance(bar_data, pd.DataFrame) and order.symbol in bar_data.index:
                bar = bar_data.loc[order.symbol]
            elif not isinstance(bar_data, pd.DataFrame):
                bar = bar_data.iloc[0]
            else:
                continue

            filled = False
            fill_price = 0

            # Check if order can be filled
            if order.order_type == OrderType.MARKET:
                # Market order - fill at open
                fill_price = bar['open'] if 'open' in bar else bar['close']
                filled = True

            elif order.order_type == OrderType.LIMIT:
                # Limit order
                if order.side == OrderSide.BUY and bar['low'] <= order.price:
                    fill_price = min(order.price, bar['open'])
                    filled = True
                elif order.side == OrderSide.SELL and bar['high'] >= order.price:
                    fill_price = max(order.price, bar['open'])
                    filled = True

            elif order.order_type == OrderType.STOP:
                # Stop order
                if order.side == OrderSide.BUY and bar['high'] >= order.stop_price:
                    fill_price = max(order.stop_price, bar['open'])
                    filled = True
                elif order.side == OrderSide.SELL and bar['low'] <= order.stop_price:
                    fill_price = min(order.stop_price, bar['open'])
                    filled = True

            if filled:
                # Apply slippage
                slippage = fill_price * self.config.slippage_rate
                if order.side == OrderSide.BUY:
                    fill_price += slippage
                else:
                    fill_price -= slippage

                # Calculate commission
                commission = abs(fill_price * order.quantity * self.config.commission_rate)

                # Update order
                order.status = OrderStatus.FILLED
                order.filled_price = fill_price
                order.filled_quantity = order.quantity
                order.commission = commission
                order.slippage = slippage

                # Update cash
                if order.side == OrderSide.BUY:
                    self.cash -= (fill_price * order.quantity + commission)
                else:
                    self.cash += (fill_price * order.quantity - commission)

                # Create or update position
                self._update_position_from_order(order)

                filled_orders.append(order)
                self.filled_orders.append(order)

        # Remove filled orders from queue
        for order in filled_orders:
            self.orders.remove(order)

    def _create_orders_from_signals(self, signals: List[Dict]):
        """Create orders from strategy signals"""
        for signal in signals:
            # Validate signal
            if not self._validate_signal(signal):
                continue

            # Check position limits
            if len(self.positions) >= self.config.max_positions:
                logger.warning(f"Maximum positions ({self.config.max_positions}) reached")
                continue

            # Calculate position size
            position_size = self._calculate_position_size(signal)

            if position_size <= 0:
                continue

            # Create order
            order = Order(
                order_id=f"ORDER_{self.order_counter}",
                symbol=signal.get('symbol', 'default'),
                side=OrderSide[signal['side'].upper()],
                order_type=OrderType[signal.get('order_type', 'MARKET').upper()],
                quantity=position_size,
                price=signal.get('price'),
                stop_price=signal.get('stop_price'),
                metadata=signal.get('metadata', {})
            )

            self.orders.append(order)
            self.order_counter += 1

    def _validate_signal(self, signal: Dict) -> bool:
        """Validate signal format"""
        required_fields = ['side']
        for field in required_fields:
            if field not in signal:
                logger.warning(f"Signal missing required field: {field}")
                return False

        # Check side
        if signal['side'].upper() not in ['BUY', 'SELL']:
            logger.warning(f"Invalid signal side: {signal['side']}")
            return False

        # Check shorting permission
        if signal['side'].upper() == 'SELL' and not self.config.allow_shorting:
            return False

        return True

    def _calculate_position_size(self, signal: Dict) -> float:
        """Calculate position size based on configuration"""
        if self.config.position_sizing == "fixed":
            # Fixed position size
            risk_amount = self.capital * self.config.risk_per_trade
            if 'stop_loss' in signal and signal['stop_loss']:
                # Calculate based on stop loss
                entry_price = signal.get('price', self.current_prices.get(
                    signal.get('symbol', 'default'), 0))
                if entry_price > 0:
                    risk_per_unit = abs(entry_price - signal['stop_loss'])
                    if risk_per_unit > 0:
                        return risk_amount / risk_per_unit
            return risk_amount / self.current_prices.get(signal.get('symbol', 'default'), 1)

        elif self.config.position_sizing == "kelly":
            # Kelly criterion (simplified)
            win_rate = signal.get('win_rate', 0.5)
            avg_win = signal.get('avg_win', 0.02)
            avg_loss = signal.get('avg_loss', 0.01)

            if avg_loss > 0:
                kelly = (win_rate * avg_win - (1 - win_rate) * avg_loss) / avg_win
                kelly = max(0, min(kelly, 0.25))  # Cap at 25%
                return self.capital * kelly / self.current_prices.get(
                    signal.get('symbol', 'default'), 1)

        return 0

    def _update_position_from_order(self, order: Order):
        """Update or create position from filled order"""
        # Check if we're adding to existing position
        existing_position = None
        for pos_id, pos in self.positions.items():
            if pos.symbol == order.symbol and pos.side == order.side.value:
                existing_position = pos
                break

        if existing_position:
            # Add to existing position (averaging)
            total_quantity = existing_position.quantity + order.filled_quantity
            existing_position.entry_price = (
                (existing_position.entry_price * existing_position.quantity +
                 order.filled_price * order.filled_quantity) / total_quantity
            )
            existing_position.quantity = total_quantity
            existing_position.commission += order.commission
        else:
            # Create new position
            position = Position(
                position_id=f"POS_{self.position_counter}",
                symbol=order.symbol,
                side=order.side.value,
                entry_price=order.filled_price,
                quantity=order.filled_quantity,
                entry_time=self.current_time,
                commission=order.commission,
                stop_loss=order.metadata.get('stop_loss'),
                take_profit=order.metadata.get('take_profit'),
                metadata=order.metadata
            )

            self.positions[position.position_id] = position
            self.position_counter += 1

    def _close_position(self, position_id: str, exit_price: float, reason: str = ""):
        """Close a position"""
        if position_id not in self.positions:
            return

        position = self.positions[position_id]

        # Apply slippage
        slippage = exit_price * self.config.slippage_rate
        if position.side == "BUY":
            exit_price -= slippage
        else:
            exit_price += slippage

        # Calculate commission
        commission = abs(exit_price * position.quantity * self.config.commission_rate)

        # Calculate P&L
        if position.side == "BUY":
            pnl = (exit_price - position.entry_price) * position.quantity
        else:
            pnl = (position.entry_price - exit_price) * position.quantity

        pnl -= (position.commission + commission)

        # Update position
        position.exit_price = exit_price
        position.exit_time = self.current_time
        position.status = PositionStatus.CLOSED
        position.pnl = pnl
        position.commission += commission

        # Update cash
        if position.side == "BUY":
            self.cash += exit_price * position.quantity - commission
        else:
            self.cash -= exit_price * position.quantity + commission

        # Create trade record
        trade = Trade(
            trade_id=f"TRADE_{self.trade_counter}",
            symbol=position.symbol,
            side=position.side,
            entry_price=position.entry_price,
            exit_price=exit_price,
            quantity=position.quantity,
            entry_time=position.entry_time,
            exit_time=self.current_time,
            pnl=pnl,
            pnl_percentage=pnl / (position.entry_price * position.quantity) * 100,
            commission=position.commission + commission,
            slippage=slippage * position.quantity,
            duration=self.current_time - position.entry_time if self.current_time else timedelta(0),
            metadata={'reason': reason}
        )

        self.trades.append(trade)
        self.trade_counter += 1

        # Move to closed positions
        self.closed_positions.append(position)
        del self.positions[position_id]

    def _close_all_positions(self, reason: str = ""):
        """Close all open positions"""
        for position_id in list(self.positions.keys()):
            if self.positions[position_id].symbol in self.current_prices:
                exit_price = self.current_prices[self.positions[position_id].symbol]
                self._close_position(position_id, exit_price, reason)

    def _calculate_equity(self) -> float:
        """Calculate current equity (cash + open positions value)"""
        equity = self.cash

        for position in self.positions.values():
            if position.symbol in self.current_prices:
                current_price = self.current_prices[position.symbol]
                if position.side == "BUY":
                    equity += current_price * position.quantity
                else:
                    # For short positions
                    equity += (2 * position.entry_price - current_price) * position.quantity

        return equity

    def _update_equity(self):
        """Update equity curve"""
        equity = self._calculate_equity()
        self.equity_curve.append({
            'timestamp': self.current_time,
            'equity': equity,
            'cash': self.cash,
            'positions_value': equity - self.cash,
            'num_positions': len(self.positions)
        })

    def _apply_risk_management(self):
        """Apply risk management rules"""
        equity = self._calculate_equity()

        # Check drawdown
        peak = max([e['equity'] for e in self.equity_curve]) if self.equity_curve else self.config.initial_capital
        drawdown = (peak - equity) / peak

        # Stop trading if drawdown exceeds limit
        if drawdown > 0.2:  # 20% drawdown
            logger.warning(f"High drawdown detected: {drawdown:.2%}")
            # Could implement position reduction or stop trading

        # Check position concentration
        for position in self.positions.values():
            position_value = abs(position.quantity * self.current_prices.get(position.symbol, 0))
            concentration = position_value / equity

            if concentration > 0.3:  # 30% in single position
                logger.warning(f"High concentration in {position.symbol}: {concentration:.2%}")

    def _calculate_results(self) -> BacktestResult:
        """Calculate comprehensive backtest results"""
        result = BacktestResult(config=self.config)

        if not self.trades:
            logger.warning("No trades executed during backtest")
            return result

        # Convert equity curve to DataFrame
        equity_df = pd.DataFrame(self.equity_curve)
        equity_df.set_index('timestamp', inplace=True)

        # Calculate returns
        equity_series = equity_df['equity']
        returns = equity_series.pct_change().dropna()

        # Performance metrics
        result.total_return = (equity_series.iloc[-1] - self.config.initial_capital) / self.config.initial_capital
        result.final_capital = equity_series.iloc[-1]
        result.peak_capital = equity_series.max()
        result.lowest_capital = equity_series.min()

        # Annualized return
        days = (equity_df.index[-1] - equity_df.index[0]).days
        if days > 0:
            result.annual_return = (1 + result.total_return) ** (365 / days) - 1

        # Trade statistics
        result.total_trades = len(self.trades)
        winning_trades = [t for t in self.trades if t.pnl > 0]
        losing_trades = [t for t in self.trades if t.pnl <= 0]

        result.winning_trades = len(winning_trades)
        result.losing_trades = len(losing_trades)
        result.win_rate = result.winning_trades / result.total_trades if result.total_trades > 0 else 0

        if winning_trades:
            result.avg_win = np.mean([t.pnl for t in winning_trades])
            result.largest_win = max([t.pnl for t in winning_trades])

        if losing_trades:
            result.avg_loss = np.mean([t.pnl for t in losing_trades])
            result.largest_loss = min([t.pnl for t in losing_trades])

        # Profit factor
        if result.avg_loss != 0 and result.losing_trades > 0:
            total_wins = result.winning_trades * result.avg_win
            total_losses = abs(result.losing_trades * result.avg_loss)
            result.profit_factor = total_wins / total_losses if total_losses > 0 else 0

        # Expectancy
        result.expectancy = (result.win_rate * result.avg_win) - ((1 - result.win_rate) * abs(result.avg_loss))

        # Risk metrics
        result.max_drawdown = self._calculate_max_drawdown(equity_series)
        result.sharpe_ratio = self._calculate_sharpe_ratio(returns)
        result.sortino_ratio = self._calculate_sortino_ratio(returns)
        result.calmar_ratio = result.annual_return / abs(result.max_drawdown) if result.max_drawdown != 0 else 0

        # VaR and CVaR
        result.var_95 = np.percentile(returns, 5) if len(returns) > 0 else 0
        result.cvar_95 = returns[returns <= result.var_95].mean() if len(returns[returns <= result.var_95]) > 0 else 0

        # Trading metrics
        if self.trades:
            durations = [t.duration.total_seconds() / 3600 for t in self.trades]  # in hours
            result.avg_trade_duration = np.mean(durations)

            # Consecutive wins/losses
            result.max_consecutive_wins = self._max_consecutive(self.trades, True)
            result.max_consecutive_losses = self._max_consecutive(self.trades, False)

        # Commission and slippage
        result.total_commission = sum([t.commission for t in self.trades])
        result.total_slippage = sum([t.slippage for t in self.trades])

        # Time series data
        result.equity_curve = equity_series
        result.drawdown_curve = self._calculate_drawdown_curve(equity_series)
        result.returns = returns

        # Trade log
        result.trades = self.trades
        result.orders = self.filled_orders

        return result

    def _calculate_max_drawdown(self, equity_series: pd.Series) -> float:
        """Calculate maximum drawdown"""
        cumulative = (1 + equity_series.pct_change()).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return abs(drawdown.min()) if len(drawdown) > 0 else 0

    def _calculate_drawdown_curve(self, equity_series: pd.Series) -> pd.Series:
        """Calculate drawdown curve"""
        cumulative = (1 + equity_series.pct_change()).cumprod()
        running_max = cumulative.expanding().max()
        drawdown = (cumulative - running_max) / running_max
        return drawdown

    def _calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio"""
        if len(returns) < 30:
            return 0

        excess_returns = returns - risk_free_rate / 252  # Daily risk-free rate
        if returns.std() > 0:
            return np.sqrt(252) * excess_returns.mean() / returns.std()
        return 0

    def _calculate_sortino_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calculate Sortino ratio"""
        if len(returns) < 30:
            return 0

        excess_returns = returns - risk_free_rate / 252
        downside_returns = returns[returns < 0]

        if len(downside_returns) > 0 and downside_returns.std() > 0:
            return np.sqrt(252) * excess_returns.mean() / downside_returns.std()
        return 0

    def _max_consecutive(self, trades: List[Trade], wins: bool) -> int:
        """Calculate maximum consecutive wins or losses"""
        max_consecutive = 0
        current_consecutive = 0

        for trade in trades:
            if (wins and trade.pnl > 0) or (not wins and trade.pnl <= 0):
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0

        return max_consecutive

    def save_results(self, result: BacktestResult, filepath: str):
        """Save backtest results to file"""
        with open(filepath, 'wb') as f:
            pickle.dump(result, f)
        logger.info(f"Results saved to {filepath}")

    def load_results(self, filepath: str) -> BacktestResult:
        """Load backtest results from file"""
        with open(filepath, 'rb') as f:
            result = pickle.load(f)
        logger.info(f"Results loaded from {filepath}")
        return result


# Example usage
if __name__ == "__main__":
    # Example strategy function
    def simple_moving_average_strategy(bar_data, positions, capital, timestamp):
        """Simple MA crossover strategy"""
        signals = []

        # Get close price
        if isinstance(bar_data, pd.DataFrame):
            close = bar_data['close'].iloc[0]
        else:
            close = bar_data['close']

        # Simple logic (would use indicators in real strategy)
        import random
        if random.random() > 0.95 and not positions:  # 5% chance to buy if no positions
            signals.append({
                'side': 'BUY',
                'order_type': 'MARKET',
                'stop_loss': close * 0.98,  # 2% stop loss
                'take_profit': close * 1.03,  # 3% take profit
                'metadata': {'strategy': 'MA_Crossover'}
            })
        elif positions and random.random() > 0.95:  # 5% chance to close
            signals.append({
                'side': 'SELL',
                'order_type': 'MARKET',
                'metadata': {'strategy': 'MA_Crossover', 'reason': 'Exit signal'}
            })

        return signals

    # Create sample data
    dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='D')
    sample_data = pd.DataFrame({
        'open': 100 + np.random.randn(len(dates)) * 2,
        'high': 102 + np.random.randn(len(dates)) * 2,
        'low': 98 + np.random.randn(len(dates)) * 2,
        'close': 100 + np.random.randn(len(dates)).cumsum() * 0.5,
        'volume': 1000000 + np.random.randint(-100000, 100000, len(dates))
    }, index=dates)

    # Configure backtest
    config = BacktestConfig(
        initial_capital=10000,
        commission_rate=0.001,
        slippage_rate=0.0005,
        risk_per_trade=0.02,
        max_positions=3
    )

    # Run backtest
    engine = BacktestEngine(config)
    result = engine.run(sample_data, simple_moving_average_strategy)

    # Print results
    print("\n" + "="*50)
    print("BACKTEST RESULTS")
    print("="*50)
    print(f"Total Return: {result.total_return:.2%}")
    print(f"Annual Return: {result.annual_return:.2%}")
    print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
    print(f"Max Drawdown: {result.max_drawdown:.2%}")
    print(f"Win Rate: {result.win_rate:.2%}")
    print(f"Profit Factor: {result.profit_factor:.2f}")
    print(f"Total Trades: {result.total_trades}")
    print(f"Final Capital: ${result.final_capital:.2f}")