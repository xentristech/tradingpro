"""
Advanced Risk Management System
Implements Kelly Criterion, VaR, Portfolio Correlation, and Dynamic Position Sizing
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@dataclass
class RiskMetrics:
    """Container for risk metrics"""
    position_size: float
    risk_amount: float
    var_95: float
    max_drawdown: float
    sharpe_ratio: float
    kelly_fraction: float
    correlation_adjustment: float

class AdvancedRiskManager:
    """
    Professional risk management system for algorithmic trading
    """
    
    def __init__(self, 
                 initial_capital: float = 10000,
                 max_risk_per_trade: float = 0.02,
                 max_portfolio_risk: float = 0.06,
                 confidence_factor: float = 0.25):
        """
        Initialize risk manager
        
        Args:
            initial_capital: Starting capital
            max_risk_per_trade: Maximum risk per trade (2%)
            max_portfolio_risk: Maximum portfolio risk (6%)
            confidence_factor: Kelly criterion confidence factor (0.25 = 25% of Kelly)
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.max_risk_per_trade = max_risk_per_trade
        self.max_portfolio_risk = max_portfolio_risk
        self.confidence_factor = confidence_factor
        self.trade_history = []
        self.open_positions = []
        
    def calculate_position_size_kelly(self, 
                                     win_rate: float, 
                                     avg_win: float, 
                                     avg_loss: float,
                                     stop_loss_distance: float,
                                     current_price: float) -> float:
        """
        Calculate optimal position size using Kelly Criterion
        
        Kelly Formula: f = (p*b - q) / b
        where:
            f = fraction of capital to bet
            p = probability of winning
            b = odds (win/loss ratio)
            q = probability of losing (1-p)
        """
        if avg_loss == 0 or win_rate <= 0 or win_rate >= 1:
            return 0.0
            
        # Calculate Kelly fraction
        odds = avg_win / avg_loss
        q = 1 - win_rate
        kelly_fraction = (win_rate * odds - q) / odds
        
        # Apply confidence factor (never use full Kelly)
        adjusted_kelly = kelly_fraction * self.confidence_factor
        
        # Cap at maximum risk per trade
        adjusted_kelly = min(adjusted_kelly, self.max_risk_per_trade)
        
        # Calculate position size in units
        if stop_loss_distance > 0:
            risk_amount = self.current_capital * adjusted_kelly
            position_size = risk_amount / stop_loss_distance
            
            # Convert to lots (assuming 1 lot = 1 unit for crypto)
            return round(position_size, 8)
        
        return 0.0
    
    def calculate_var(self, 
                     returns: List[float], 
                     confidence_level: float = 0.95,
                     holding_period: int = 1) -> float:
        """
        Calculate Value at Risk (VaR)
        
        VaR answers: What is the maximum loss over a given time period
        with a confidence level?
        """
        if not returns:
            return 0.0
            
        returns_array = np.array(returns)
        
        # Calculate VaR using historical method
        var_percentile = (1 - confidence_level) * 100
        var = np.percentile(returns_array, var_percentile)
        
        # Adjust for holding period (square root of time)
        var_adjusted = var * np.sqrt(holding_period)
        
        return abs(var_adjusted) * self.current_capital
    
    def calculate_correlation_adjustment(self, 
                                       new_symbol: str, 
                                       existing_positions: List[Dict]) -> float:
        """
        Adjust position size based on correlation with existing positions
        
        High correlation = reduce position size
        Low/negative correlation = maintain or increase position size
        """
        if not existing_positions:
            return 1.0
            
        # Simplified correlation matrix (in production, use actual price data)
        correlation_matrix = {
            ('BTCUSD', 'ETHUSD'): 0.85,
            ('BTCUSD', 'EURUSD'): -0.3,
            ('ETHUSD', 'EURUSD'): -0.25,
            # Add more pairs as needed
        }
        
        total_correlation = 0
        for position in existing_positions:
            pair = tuple(sorted([new_symbol, position['symbol']]))
            correlation = correlation_matrix.get(pair, 0.5)  # Default moderate correlation
            total_correlation += abs(correlation)
        
        # Adjustment factor: lower position size for high correlation
        if existing_positions:
            avg_correlation = total_correlation / len(existing_positions)
            adjustment = 1 / (1 + avg_correlation)
        else:
            adjustment = 1.0
            
        return adjustment
    
    def calculate_dynamic_stop_loss(self, 
                                   atr: float, 
                                   support_level: float,
                                   current_price: float,
                                   direction: str = 'BUY') -> float:
        """
        Calculate dynamic stop loss based on ATR and support/resistance
        """
        # ATR-based stop (2.5x ATR is common)
        atr_stop_distance = atr * 2.5
        
        if direction == 'BUY':
            atr_stop = current_price - atr_stop_distance
            # Use the higher of ATR stop or support level
            stop_loss = max(atr_stop, support_level * 0.99)  # 1% below support
        else:  # SELL
            atr_stop = current_price + atr_stop_distance
            # Use the lower of ATR stop or resistance level
            stop_loss = min(atr_stop, support_level * 1.01)  # 1% above resistance
            
        return stop_loss
    
    def calculate_position_metrics(self,
                                  symbol: str,
                                  entry_price: float,
                                  stop_loss: float,
                                  take_profit: float,
                                  win_rate: float = 0.6,
                                  historical_returns: List[float] = None) -> RiskMetrics:
        """
        Calculate comprehensive risk metrics for a position
        """
        # Calculate basic position size
        stop_loss_distance = abs(entry_price - stop_loss)
        take_profit_distance = abs(take_profit - entry_price)
        
        # Risk-reward ratio
        risk_reward_ratio = take_profit_distance / stop_loss_distance if stop_loss_distance > 0 else 0
        
        # Kelly position size
        avg_win = take_profit_distance
        avg_loss = stop_loss_distance
        kelly_size = self.calculate_position_size_kelly(
            win_rate, avg_win, avg_loss, stop_loss_distance, entry_price
        )
        
        # Correlation adjustment
        correlation_adj = self.calculate_correlation_adjustment(symbol, self.open_positions)
        
        # Final position size
        adjusted_size = kelly_size * correlation_adj
        
        # Risk amount
        risk_amount = adjusted_size * stop_loss_distance
        
        # VaR calculation
        var_95 = self.calculate_var(historical_returns or []) if historical_returns else 0
        
        # Maximum drawdown
        max_dd = self.calculate_max_drawdown(historical_returns or [])
        
        # Sharpe ratio
        sharpe = self.calculate_sharpe_ratio(historical_returns or [])
        
        return RiskMetrics(
            position_size=adjusted_size,
            risk_amount=risk_amount,
            var_95=var_95,
            max_drawdown=max_dd,
            sharpe_ratio=sharpe,
            kelly_fraction=kelly_size / self.current_capital if self.current_capital > 0 else 0,
            correlation_adjustment=correlation_adj
        )
    
    def calculate_max_drawdown(self, returns: List[float]) -> float:
        """Calculate maximum drawdown from returns series"""
        if not returns:
            return 0.0
            
        cumulative = np.cumprod(1 + np.array(returns))
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        return abs(np.min(drawdown))
    
    def calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio"""
        if not returns or len(returns) < 2:
            return 0.0
            
        returns_array = np.array(returns)
        excess_returns = returns_array - risk_free_rate/252  # Daily risk-free rate
        
        if np.std(excess_returns) == 0:
            return 0.0
            
        return np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
    
    def should_take_trade(self, risk_metrics: RiskMetrics) -> Tuple[bool, str]:
        """
        Determine if trade should be taken based on risk metrics
        
        Returns:
            (should_trade, reason)
        """
        # Check portfolio risk
        total_risk = sum(pos.get('risk', 0) for pos in self.open_positions)
        total_risk += risk_metrics.risk_amount
        
        if total_risk > self.current_capital * self.max_portfolio_risk:
            return False, f"Portfolio risk exceeded: {total_risk/self.current_capital:.1%}"
        
        # Check individual position risk
        if risk_metrics.risk_amount > self.current_capital * self.max_risk_per_trade:
            return False, f"Position risk too high: {risk_metrics.risk_amount/self.current_capital:.1%}"
        
        # Check Sharpe ratio (minimum 1.0)
        if risk_metrics.sharpe_ratio < 1.0:
            return False, f"Sharpe ratio too low: {risk_metrics.sharpe_ratio:.2f}"
        
        # Check Kelly fraction (must be positive)
        if risk_metrics.kelly_fraction <= 0:
            return False, "Negative Kelly fraction - negative edge"
        
        # Check VaR
        if risk_metrics.var_95 > self.current_capital * 0.05:
            return False, f"VaR too high: ${risk_metrics.var_95:.2f}"
        
        return True, "Risk parameters acceptable"
    
    def update_capital(self, pnl: float):
        """Update current capital with P&L"""
        self.current_capital += pnl
        logger.info(f"Capital updated: ${self.current_capital:.2f} (PnL: ${pnl:+.2f})")
    
    def add_trade_to_history(self, trade: Dict):
        """Add completed trade to history"""
        self.trade_history.append(trade)
        
    def get_current_stats(self) -> Dict:
        """Get current risk statistics"""
        if not self.trade_history:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'profit_factor': 0,
                'current_drawdown': 0,
                'max_drawdown': 0
            }
        
        wins = [t['pnl'] for t in self.trade_history if t['pnl'] > 0]
        losses = [t['pnl'] for t in self.trade_history if t['pnl'] < 0]
        
        win_rate = len(wins) / len(self.trade_history) if self.trade_history else 0
        avg_win = np.mean(wins) if wins else 0
        avg_loss = abs(np.mean(losses)) if losses else 0
        
        profit_factor = (sum(wins) / abs(sum(losses))) if losses else 0
        
        # Calculate current drawdown
        peak_capital = self.initial_capital
        for trade in self.trade_history:
            peak_capital = max(peak_capital, self.initial_capital + sum(t['pnl'] for t in self.trade_history[:self.trade_history.index(trade)+1]))
        
        current_drawdown = (peak_capital - self.current_capital) / peak_capital if peak_capital > 0 else 0
        
        return {
            'total_trades': len(self.trade_history),
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'current_drawdown': current_drawdown,
            'max_drawdown': self.calculate_max_drawdown([t['pnl']/self.initial_capital for t in self.trade_history])
        }
