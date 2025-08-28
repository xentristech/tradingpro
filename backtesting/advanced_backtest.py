"""
Professional Backtesting Engine for Algorithmic Trading
Includes slippage, commission, and realistic execution modeling
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"

class OrderSide(Enum):
    BUY = "buy"
    SELL = "sell"

@dataclass
class Order:
    """Order representation"""
    timestamp: datetime
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    order_id: Optional[str] = None
    
@dataclass
class Trade:
    """Executed trade representation"""
    timestamp: datetime
    symbol: str
    side: OrderSide
    quantity: float
    price: float
    commission: float
    slippage: float
    order_id: str
    trade_id: str
    
@dataclass
class Position:
    """Position tracking"""
    symbol: str
    quantity: float
    avg_price: float
    current_price: float
    unrealized_pnl: float
    realized_pnl: float
    
@dataclass
class BacktestResults:
    """Comprehensive backtest results"""
    # Performance metrics
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    
    # Risk metrics
    max_drawdown: float
    max_drawdown_duration: int
    var_95: float
    cvar_95: float
    
    # Trading metrics
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    expectancy: float
    
    # Additional metrics
    trades: List[Trade] = field(default_factory=list)
    equity_curve: pd.Series = field(default_factory=pd.Series)
    drawdown_series: pd.Series = field(default_factory=pd.Series)
    monthly_returns: pd.Series = field(default_factory=pd.Series)
    
class BacktestEngine:
    """
    Professional backtesting engine with realistic execution modeling
    """
    
    def __init__(self,
                 initial_capital: float = 10000,
                 commission_rate: float = 0.001,  # 0.1%
                 slippage_model: str = 'percentage',  # 'percentage', 'fixed', 'dynamic'
                 slippage_value: float = 0.0005,  # 0.05%
                 leverage: float = 1.0):
        """
        Initialize backtesting engine
        
        Args:
            initial_capital: Starting capital
            commission_rate: Commission per trade (percentage)
            slippage_model: Type of slippage model
            slippage_value: Slippage amount
            leverage: Maximum leverage allowed
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage_model = slippage_model
        self.slippage_value = slippage_value
        self.leverage = leverage
        
        # State tracking
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.orders: List[Order] = []
        self.equity_curve: List[Tuple[datetime, float]] = []
        self.trade_id_counter = 0
        
    def calculate_slippage(self, 
                          price: float, 
                          side: OrderSide,
                          volume: Optional[float] = None,
                          volatility: Optional[float] = None) -> float:
        """
        Calculate realistic slippage based on model
        """
        if self.slippage_model == 'percentage':
            slippage = price * self.slippage_value
        elif self.slippage_model == 'fixed':
            slippage = self.slippage_value
        elif self.slippage_model == 'dynamic':
            # Dynamic slippage based on volume and volatility
            base_slippage = price * self.slippage_value
            
            if volume:
                # Higher volume = higher slippage
                volume_factor = 1 + (volume / 1000000) * 0.1  # Adjust based on volume
                base_slippage *= volume_factor
                
            if volatility:
                # Higher volatility = higher slippage
                vol_factor = 1 + volatility * 2
                base_slippage *= vol_factor
                
            slippage = base_slippage
        else:
            slippage = 0
            
        # Apply slippage direction
        if side == OrderSide.BUY:
            return slippage  # Pay more when buying
        else:
            return -slippage  # Receive less when selling
    
    def calculate_commission(self, quantity: float, price: float) -> float:
        """Calculate trading commission"""
        return quantity * price * self.commission_rate
    
    def execute_order(self, 
                     order: Order,
                     current_price: float,
                     current_time: datetime,
                     volume: Optional[float] = None,
                     volatility: Optional[float] = None) -> Optional[Trade]:
        """
        Execute an order with realistic fills
        """
        # Check if order should be executed
        if order.order_type == OrderType.LIMIT:
            if order.side == OrderSide.BUY and current_price > order.price:
                return None  # Don't fill buy limit above limit price
            elif order.side == OrderSide.SELL and current_price < order.price:
                return None  # Don't fill sell limit below limit price
                
        elif order.order_type == OrderType.STOP:
            if order.side == OrderSide.BUY and current_price < order.stop_price:
                return None  # Don't fill buy stop below stop price
            elif order.side == OrderSide.SELL and current_price > order.stop_price:
                return None  # Don't fill sell stop above stop price
        
        # Calculate execution price with slippage
        slippage = self.calculate_slippage(current_price, order.side, volume, volatility)
        execution_price = current_price + slippage
        
        # Calculate commission
        commission = self.calculate_commission(order.quantity, execution_price)
        
        # Check if we have enough capital
        required_capital = order.quantity * execution_price + commission
        if order.side == OrderSide.BUY and required_capital > self.current_capital * self.leverage:
            logger.warning(f"Insufficient capital for order: required={required_capital}, available={self.current_capital * self.leverage}")
            return None
        
        # Create trade
        self.trade_id_counter += 1
        trade = Trade(
            timestamp=current_time,
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=execution_price,
            commission=commission,
            slippage=slippage,
            order_id=order.order_id or str(self.trade_id_counter),
            trade_id=str(self.trade_id_counter)
        )
        
        # Update position
        self._update_position(trade)
        
        # Update capital
        if trade.side == OrderSide.BUY:
            self.current_capital -= (trade.quantity * trade.price + trade.commission)
        else:
            self.current_capital += (trade.quantity * trade.price - trade.commission)
        
        # Record trade
        self.trades.append(trade)
        
        return trade
    
    def _update_position(self, trade: Trade):
        """Update or create position based on trade"""
        if trade.symbol not in self.positions:
            # New position
            self.positions[trade.symbol] = Position(
                symbol=trade.symbol,
                quantity=trade.quantity if trade.side == OrderSide.BUY else -trade.quantity,
                avg_price=trade.price,
                current_price=trade.price,
                unrealized_pnl=0,
                realized_pnl=-trade.commission
            )
        else:
            position = self.positions[trade.symbol]
            
            if trade.side == OrderSide.BUY:
                # Adding to position
                new_quantity = position.quantity + trade.quantity
                if new_quantity != 0:
                    position.avg_price = (position.avg_price * position.quantity + 
                                         trade.price * trade.quantity) / new_quantity
                position.quantity = new_quantity
            else:
                # Reducing position
                position.quantity -= trade.quantity
                
                # Calculate realized PnL
                if position.quantity < 0:
                    # Position flipped
                    position.realized_pnl += (trade.price - position.avg_price) * trade.quantity
                    position.avg_price = trade.price
                elif position.quantity == 0:
                    # Position closed
                    position.realized_pnl += (trade.price - position.avg_price) * trade.quantity
                    del self.positions[trade.symbol]
                else:
                    # Partial close
                    position.realized_pnl += (trade.price - position.avg_price) * trade.quantity
            
            # Subtract commission from realized PnL
            position.realized_pnl -= trade.commission
    
    def update_prices(self, prices: Dict[str, float], timestamp: datetime):
        """Update current prices and calculate unrealized PnL"""
        total_equity = self.current_capital
        
        for symbol, position in self.positions.items():
            if symbol in prices:
                position.current_price = prices[symbol]
                position.unrealized_pnl = (position.current_price - position.avg_price) * position.quantity
                total_equity += position.unrealized_pnl
        
        self.equity_curve.append((timestamp, total_equity))
    
    def print_results(self, results: BacktestResults):
        """Print formatted backtest results"""
        print("\n" + "=" * 60)
        print(" BACKTEST RESULTS")
        print("=" * 60)
        
        print("\n📊 PERFORMANCE METRICS:")
        print(f"   Total Return:       {results.total_return:+.2%}")
        print(f"   Annualized Return:  {results.annualized_return:+.2%}")
        print(f"   Sharpe Ratio:       {results.sharpe_ratio:.2f}")
        print(f"   Sortino Ratio:      {results.sortino_ratio:.2f}")
        print(f"   Calmar Ratio:       {results.calmar_ratio:.2f}")
        
        print("\n📉 RISK METRICS:")
        print(f"   Max Drawdown:       {results.max_drawdown:.2%}")
        print(f"   Max DD Duration:    {results.max_drawdown_duration} days")
        print(f"   VaR (95%):         {results.var_95:.2%}")
        print(f"   CVaR (95%):        {results.cvar_95:.2%}")
        
        print("\n📈 TRADING METRICS:")
        print(f"   Total Trades:       {results.total_trades}")
        print(f"   Win Rate:          {results.win_rate:.1%}")
        print(f"   Avg Win:           ${results.avg_win:.2f}")
        print(f"   Avg Loss:          ${results.avg_loss:.2f}")
        print(f"   Profit Factor:      {results.profit_factor:.2f}")
        print(f"   Expectancy:        ${results.expectancy:.2f}")
        
        print("\n" + "=" * 60)
