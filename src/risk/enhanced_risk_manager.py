"""
Enhanced Risk Management System with Kelly Criterion and Advanced Position Sizing
Author: Trading Pro System
Version: 3.0
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    """Risk levels for position sizing"""
    CONSERVATIVE = 0.25  # 25% of Kelly
    MODERATE = 0.5      # 50% of Kelly
    AGGRESSIVE = 0.75   # 75% of Kelly
    FULL = 1.0         # Full Kelly (not recommended)


@dataclass
class TradeStats:
    """Trade statistics for calculations"""
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    win_rate: float
    profit_factor: float
    sharpe_ratio: float
    max_drawdown: float
    current_drawdown: float


@dataclass
class PositionSizeResult:
    """Result of position sizing calculation"""
    position_size: float
    risk_amount: float
    kelly_fraction: float
    adjusted_kelly: float
    confidence_level: float
    risk_reward_ratio: float
    expected_value: float
    max_position_allowed: float
    reasoning: str


class EnhancedRiskManager:
    """
    Advanced Risk Management System with multiple position sizing methods
    """

    def __init__(self, account_balance: float, max_risk_per_trade: float = 0.02):
        """
        Initialize Enhanced Risk Manager

        Args:
            account_balance: Current account balance
            max_risk_per_trade: Maximum risk per trade (default 2%)
        """
        self.account_balance = account_balance
        self.max_risk_per_trade = max_risk_per_trade
        self.trade_history = []
        self.current_positions = {}
        self.risk_level = RiskLevel.CONSERVATIVE
        self.correlation_matrix = None
        self.var_confidence = 0.95
        self.lookback_period = 252  # Trading days for calculations

    def calculate_kelly_criterion(self, win_rate: float, avg_win: float,
                                 avg_loss: float, apply_safety: bool = True) -> float:
        """
        Calculate optimal position size using Kelly Criterion

        Kelly Formula: f = (p * b - q) / b
        where:
            f = fraction of capital to wager
            p = probability of winning
            b = ratio of win to loss (odds)
            q = probability of losing (1 - p)

        Args:
            win_rate: Historical win rate (0-1)
            avg_win: Average winning trade amount
            avg_loss: Average losing trade amount
            apply_safety: Apply safety factor (recommended)

        Returns:
            Optimal Kelly fraction
        """
        if avg_loss == 0 or avg_win == 0:
            logger.warning("Cannot calculate Kelly with zero avg_win or avg_loss")
            return 0.0

        # Calculate Kelly fraction
        p = win_rate
        q = 1 - win_rate
        b = abs(avg_win / avg_loss)  # Ratio of average win to average loss

        kelly = (p * b - q) / b

        # Apply safety constraints
        if apply_safety:
            # Never use more than 25% Kelly (industry standard)
            kelly = min(kelly, 0.25)

            # Apply risk level adjustment
            kelly *= self.risk_level.value

            # Further reduce if drawdown is high
            if hasattr(self, 'current_drawdown') and self.current_drawdown > 0.1:
                drawdown_adjustment = 1 - (self.current_drawdown / 0.3)  # Reduce linearly
                kelly *= max(drawdown_adjustment, 0.5)

        # Ensure Kelly is not negative (would indicate negative edge)
        kelly = max(kelly, 0.0)

        # Cap at maximum risk per trade
        kelly = min(kelly, self.max_risk_per_trade)

        logger.info(f"Kelly Criterion calculated: {kelly:.4f} (win_rate: {win_rate:.2%}, b: {b:.2f})")

        return kelly

    def calculate_position_size(self, signal: Dict, method: str = 'kelly') -> PositionSizeResult:
        """
        Calculate position size using specified method

        Args:
            signal: Trading signal dictionary with entry, stop_loss, take_profit
            method: Position sizing method ('kelly', 'fixed', 'volatility', 'optimal_f')

        Returns:
            PositionSizeResult with detailed sizing information
        """
        entry_price = signal.get('entry_price', 0)
        stop_loss = signal.get('stop_loss', 0)
        take_profit = signal.get('take_profit', 0)

        if entry_price == 0 or stop_loss == 0:
            return PositionSizeResult(
                position_size=0,
                risk_amount=0,
                kelly_fraction=0,
                adjusted_kelly=0,
                confidence_level=0,
                risk_reward_ratio=0,
                expected_value=0,
                max_position_allowed=0,
                reasoning="Invalid signal parameters"
            )

        # Calculate risk and reward
        risk_per_unit = abs(entry_price - stop_loss)
        reward_per_unit = abs(take_profit - entry_price) if take_profit else risk_per_unit * 2
        risk_reward_ratio = reward_per_unit / risk_per_unit if risk_per_unit > 0 else 0

        # Get trade statistics
        trade_stats = self._calculate_trade_statistics()

        # Calculate position size based on method
        if method == 'kelly':
            kelly_fraction = self.calculate_kelly_criterion(
                win_rate=trade_stats.win_rate,
                avg_win=trade_stats.avg_win,
                avg_loss=abs(trade_stats.avg_loss)
            )
            risk_amount = self.account_balance * kelly_fraction

        elif method == 'fixed':
            kelly_fraction = self.max_risk_per_trade
            risk_amount = self.account_balance * self.max_risk_per_trade

        elif method == 'volatility':
            volatility = signal.get('volatility', 0.02)
            kelly_fraction = min(0.02 / volatility, self.max_risk_per_trade)
            risk_amount = self.account_balance * kelly_fraction

        elif method == 'optimal_f':
            kelly_fraction = self._calculate_optimal_f()
            risk_amount = self.account_balance * kelly_fraction

        else:
            raise ValueError(f"Unknown position sizing method: {method}")

        # Calculate actual position size
        position_size = risk_amount / risk_per_unit if risk_per_unit > 0 else 0

        # Apply portfolio heat check
        position_size = self._apply_portfolio_heat_limit(position_size, risk_amount)

        # Calculate expected value
        expected_value = (
            trade_stats.win_rate * reward_per_unit * position_size -
            (1 - trade_stats.win_rate) * risk_per_unit * position_size
        )

        # Determine confidence level based on trade statistics
        confidence_level = self._calculate_confidence_level(trade_stats, signal)

        # Apply confidence adjustment
        if confidence_level < 0.6:
            position_size *= 0.5
            reasoning = "Low confidence - position reduced by 50%"
        elif confidence_level < 0.7:
            position_size *= 0.75
            reasoning = "Medium confidence - position reduced by 25%"
        else:
            reasoning = f"High confidence - using {method} method"

        return PositionSizeResult(
            position_size=round(position_size, 8),
            risk_amount=risk_amount,
            kelly_fraction=kelly_fraction,
            adjusted_kelly=kelly_fraction * self.risk_level.value,
            confidence_level=confidence_level,
            risk_reward_ratio=risk_reward_ratio,
            expected_value=expected_value,
            max_position_allowed=self.account_balance * self.max_risk_per_trade / risk_per_unit,
            reasoning=reasoning
        )

    def calculate_var(self, portfolio_returns: pd.Series, confidence: float = 0.95) -> float:
        """
        Calculate Value at Risk (VaR)

        Args:
            portfolio_returns: Historical portfolio returns
            confidence: Confidence level (default 95%)

        Returns:
            VaR amount
        """
        if len(portfolio_returns) < 30:
            return self.account_balance * 0.02  # Default 2% if insufficient data

        # Calculate percentile (historical VaR)
        var_percentile = np.percentile(portfolio_returns, (1 - confidence) * 100)

        # Convert to dollar amount
        var_amount = abs(var_percentile * self.account_balance)

        logger.info(f"VaR at {confidence:.0%} confidence: ${var_amount:.2f}")

        return var_amount

    def calculate_cvar(self, portfolio_returns: pd.Series, confidence: float = 0.95) -> float:
        """
        Calculate Conditional Value at Risk (CVaR) - Expected Shortfall

        Args:
            portfolio_returns: Historical portfolio returns
            confidence: Confidence level

        Returns:
            CVaR amount
        """
        var = self.calculate_var(portfolio_returns, confidence)
        var_threshold = np.percentile(portfolio_returns, (1 - confidence) * 100)

        # Get returns worse than VaR
        tail_losses = portfolio_returns[portfolio_returns <= var_threshold]

        if len(tail_losses) == 0:
            return var

        # Calculate expected shortfall
        cvar = abs(tail_losses.mean() * self.account_balance)

        logger.info(f"CVaR at {confidence:.0%} confidence: ${cvar:.2f}")

        return cvar

    def calculate_portfolio_correlation(self, positions: Dict) -> pd.DataFrame:
        """
        Calculate correlation matrix for current positions

        Args:
            positions: Dictionary of current positions

        Returns:
            Correlation matrix
        """
        if len(positions) < 2:
            return pd.DataFrame()

        # Extract returns for each position
        returns_data = {}
        for symbol, position in positions.items():
            if 'returns' in position:
                returns_data[symbol] = position['returns']

        if not returns_data:
            return pd.DataFrame()

        # Create DataFrame and calculate correlation
        df = pd.DataFrame(returns_data)
        correlation_matrix = df.corr()

        self.correlation_matrix = correlation_matrix

        return correlation_matrix

    def apply_correlation_adjustment(self, position_size: float, symbol: str,
                                    correlation_threshold: float = 0.7) -> float:
        """
        Adjust position size based on correlation with existing positions

        Args:
            position_size: Initial position size
            symbol: Symbol to trade
            correlation_threshold: Threshold for high correlation

        Returns:
            Adjusted position size
        """
        if self.correlation_matrix is None or symbol not in self.correlation_matrix.columns:
            return position_size

        # Check correlation with existing positions
        high_correlations = []
        for existing_symbol in self.current_positions.keys():
            if existing_symbol != symbol and existing_symbol in self.correlation_matrix.columns:
                correlation = abs(self.correlation_matrix.loc[symbol, existing_symbol])
                if correlation > correlation_threshold:
                    high_correlations.append(correlation)

        if high_correlations:
            # Reduce position size based on number of correlated positions
            avg_correlation = np.mean(high_correlations)
            reduction_factor = 1 - (avg_correlation - correlation_threshold) / (1 - correlation_threshold)
            reduction_factor = max(reduction_factor, 0.5)  # At least 50% of original

            adjusted_size = position_size * reduction_factor

            logger.info(f"Position reduced by {(1-reduction_factor)*100:.1f}% due to correlation")

            return adjusted_size

        return position_size

    def calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """
        Calculate Sharpe ratio

        Args:
            returns: Series of returns
            risk_free_rate: Annual risk-free rate

        Returns:
            Sharpe ratio
        """
        if len(returns) < 30:
            return 0.0

        # Annualize returns and volatility
        mean_return = returns.mean() * 252
        volatility = returns.std() * np.sqrt(252)

        if volatility == 0:
            return 0.0

        sharpe = (mean_return - risk_free_rate) / volatility

        return sharpe

    def calculate_sortino_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02,
                               target_return: float = 0) -> float:
        """
        Calculate Sortino ratio (focuses on downside volatility)

        Args:
            returns: Series of returns
            risk_free_rate: Annual risk-free rate
            target_return: Target return threshold

        Returns:
            Sortino ratio
        """
        if len(returns) < 30:
            return 0.0

        # Calculate downside returns
        downside_returns = returns[returns < target_return]

        if len(downside_returns) == 0:
            return float('inf')  # No downside risk

        # Annualize
        mean_return = returns.mean() * 252
        downside_deviation = downside_returns.std() * np.sqrt(252)

        if downside_deviation == 0:
            return 0.0

        sortino = (mean_return - risk_free_rate) / downside_deviation

        return sortino

    def calculate_calmar_ratio(self, returns: pd.Series, max_drawdown: float = None) -> float:
        """
        Calculate Calmar ratio (return / max drawdown)

        Args:
            returns: Series of returns
            max_drawdown: Maximum drawdown (if None, will calculate)

        Returns:
            Calmar ratio
        """
        if len(returns) < 30:
            return 0.0

        # Annualized return
        annual_return = returns.mean() * 252

        # Calculate max drawdown if not provided
        if max_drawdown is None:
            cumulative = (1 + returns).cumprod()
            running_max = cumulative.expanding().max()
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = abs(drawdown.min())

        if max_drawdown == 0:
            return float('inf')

        calmar = annual_return / max_drawdown

        return calmar

    def _calculate_trade_statistics(self) -> TradeStats:
        """
        Calculate comprehensive trade statistics

        Returns:
            TradeStats object with all statistics
        """
        if not self.trade_history:
            # Return default stats if no history
            return TradeStats(
                total_trades=0,
                winning_trades=0,
                losing_trades=0,
                avg_win=0.01,
                avg_loss=0.01,
                largest_win=0,
                largest_loss=0,
                win_rate=0.5,
                profit_factor=1.0,
                sharpe_ratio=0,
                max_drawdown=0,
                current_drawdown=0
            )

        # Calculate statistics from trade history
        df = pd.DataFrame(self.trade_history)

        winning_trades = df[df['pnl'] > 0]
        losing_trades = df[df['pnl'] <= 0]

        stats = TradeStats(
            total_trades=len(df),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            avg_win=winning_trades['pnl'].mean() if len(winning_trades) > 0 else 0.01,
            avg_loss=abs(losing_trades['pnl'].mean()) if len(losing_trades) > 0 else 0.01,
            largest_win=winning_trades['pnl'].max() if len(winning_trades) > 0 else 0,
            largest_loss=abs(losing_trades['pnl'].min()) if len(losing_trades) > 0 else 0,
            win_rate=len(winning_trades) / len(df) if len(df) > 0 else 0.5,
            profit_factor=1.0,
            sharpe_ratio=0,
            max_drawdown=0,
            current_drawdown=0
        )

        # Calculate profit factor
        if stats.losing_trades > 0 and stats.avg_loss > 0:
            total_wins = stats.winning_trades * stats.avg_win
            total_losses = stats.losing_trades * stats.avg_loss
            stats.profit_factor = total_wins / total_losses if total_losses > 0 else 1.0

        # Calculate Sharpe ratio if we have returns
        if 'returns' in df.columns:
            stats.sharpe_ratio = self.calculate_sharpe_ratio(df['returns'])

        # Calculate drawdown
        if 'cumulative_pnl' in df.columns:
            running_max = df['cumulative_pnl'].expanding().max()
            drawdown = (df['cumulative_pnl'] - running_max) / running_max
            stats.max_drawdown = abs(drawdown.min())
            stats.current_drawdown = abs(drawdown.iloc[-1])

        return stats

    def _calculate_optimal_f(self) -> float:
        """
        Calculate Optimal f using Ralph Vince's method

        Returns:
            Optimal fraction to risk
        """
        if len(self.trade_history) < 30:
            return self.max_risk_per_trade * 0.5

        # Extract P&L from trade history
        pnls = [trade['pnl'] for trade in self.trade_history]

        # Find the largest loss
        largest_loss = abs(min(pnls))

        if largest_loss == 0:
            return self.max_risk_per_trade * 0.5

        # Test different f values
        best_f = 0
        best_twi = 0

        for f in np.arange(0.01, 0.5, 0.01):
            twi = 1.0  # Terminal Wealth Index

            for pnl in pnls:
                hpp = pnl / largest_loss  # Holding Period Return
                twi *= (1 + f * hpp)

                if twi <= 0:
                    break

            if twi > best_twi:
                best_twi = twi
                best_f = f

        # Apply safety factor
        optimal_f = best_f * 0.25  # Use 25% of optimal f

        return min(optimal_f, self.max_risk_per_trade)

    def _apply_portfolio_heat_limit(self, position_size: float, risk_amount: float) -> float:
        """
        Apply portfolio heat limit to prevent overexposure

        Args:
            position_size: Calculated position size
            risk_amount: Risk amount for the position

        Returns:
            Adjusted position size
        """
        # Calculate current portfolio heat
        current_heat = sum(pos.get('risk_amount', 0) for pos in self.current_positions.values())

        # Maximum portfolio heat (e.g., 6% of account)
        max_heat = self.account_balance * 0.06

        # Check if adding this position would exceed heat limit
        if current_heat + risk_amount > max_heat:
            # Reduce position size proportionally
            available_heat = max(max_heat - current_heat, 0)
            reduction_factor = available_heat / risk_amount if risk_amount > 0 else 0

            adjusted_size = position_size * reduction_factor

            logger.info(f"Position reduced by {(1-reduction_factor)*100:.1f}% due to portfolio heat limit")

            return adjusted_size

        return position_size

    def _calculate_confidence_level(self, trade_stats: TradeStats, signal: Dict) -> float:
        """
        Calculate confidence level for a signal

        Args:
            trade_stats: Trade statistics
            signal: Trading signal

        Returns:
            Confidence level (0-1)
        """
        confidence_factors = []

        # Win rate factor
        if trade_stats.win_rate > 0.6:
            confidence_factors.append(1.0)
        elif trade_stats.win_rate > 0.5:
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.6)

        # Profit factor
        if trade_stats.profit_factor > 1.5:
            confidence_factors.append(1.0)
        elif trade_stats.profit_factor > 1.2:
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.6)

        # Risk-reward ratio
        risk_reward = signal.get('risk_reward_ratio', 1.0)
        if risk_reward > 2.0:
            confidence_factors.append(1.0)
        elif risk_reward > 1.5:
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.6)

        # Signal strength (if provided)
        signal_strength = signal.get('strength', 0.7)
        confidence_factors.append(signal_strength)

        # ML confidence (if provided)
        if 'ml_confidence' in signal:
            confidence_factors.append(signal['ml_confidence'])

        # Calculate weighted average
        confidence = np.mean(confidence_factors)

        return confidence

    def add_trade(self, trade: Dict) -> None:
        """
        Add a trade to history for statistics calculation

        Args:
            trade: Trade dictionary with pnl, symbol, entry, exit, etc.
        """
        self.trade_history.append(trade)

        # Keep only recent trades (e.g., last 100)
        if len(self.trade_history) > 100:
            self.trade_history = self.trade_history[-100:]

    def update_position(self, symbol: str, position: Dict) -> None:
        """
        Update current position

        Args:
            symbol: Symbol identifier
            position: Position details
        """
        self.current_positions[symbol] = position

    def remove_position(self, symbol: str) -> None:
        """
        Remove position from tracking

        Args:
            symbol: Symbol identifier
        """
        if symbol in self.current_positions:
            del self.current_positions[symbol]

    def get_risk_metrics(self) -> Dict:
        """
        Get comprehensive risk metrics

        Returns:
            Dictionary of risk metrics
        """
        stats = self._calculate_trade_statistics()

        # Calculate portfolio returns if available
        returns = pd.Series([t.get('returns', 0) for t in self.trade_history if 'returns' in t])

        metrics = {
            'kelly_fraction': self.calculate_kelly_criterion(
                stats.win_rate, stats.avg_win, stats.avg_loss
            ),
            'current_heat': sum(pos.get('risk_amount', 0) for pos in self.current_positions.values()),
            'max_heat': self.account_balance * 0.06,
            'sharpe_ratio': stats.sharpe_ratio,
            'sortino_ratio': self.calculate_sortino_ratio(returns) if len(returns) > 30 else 0,
            'calmar_ratio': self.calculate_calmar_ratio(returns) if len(returns) > 30 else 0,
            'profit_factor': stats.profit_factor,
            'win_rate': stats.win_rate,
            'max_drawdown': stats.max_drawdown,
            'current_drawdown': stats.current_drawdown,
            'var_95': self.calculate_var(returns) if len(returns) > 30 else 0,
            'cvar_95': self.calculate_cvar(returns) if len(returns) > 30 else 0,
            'positions_count': len(self.current_positions),
            'risk_level': self.risk_level.name,
            'account_balance': self.account_balance
        }

        return metrics

    def set_risk_level(self, level: str) -> None:
        """
        Set risk level for position sizing

        Args:
            level: Risk level ('CONSERVATIVE', 'MODERATE', 'AGGRESSIVE', 'FULL')
        """
        try:
            self.risk_level = RiskLevel[level.upper()]
            logger.info(f"Risk level set to {self.risk_level.name}")
        except KeyError:
            logger.error(f"Invalid risk level: {level}")

    def should_stop_trading(self) -> Tuple[bool, str]:
        """
        Determine if trading should be stopped based on risk metrics

        Returns:
            Tuple of (should_stop, reason)
        """
        stats = self._calculate_trade_statistics()

        # Check max drawdown
        if stats.max_drawdown > 0.2:  # 20% drawdown
            return True, f"Maximum drawdown exceeded: {stats.max_drawdown:.1%}"

        # Check current drawdown
        if stats.current_drawdown > 0.15:  # 15% current drawdown
            return True, f"Current drawdown too high: {stats.current_drawdown:.1%}"

        # Check losing streak
        if stats.total_trades > 0:
            recent_trades = self.trade_history[-10:] if len(self.trade_history) >= 10 else self.trade_history
            recent_losses = sum(1 for t in recent_trades if t.get('pnl', 0) < 0)
            if recent_losses >= 7:  # 7 out of 10 losses
                return True, f"Losing streak detected: {recent_losses}/10 losses"

        # Check portfolio heat
        current_heat = sum(pos.get('risk_amount', 0) for pos in self.current_positions.values())
        if current_heat > self.account_balance * 0.08:  # 8% heat
            return True, f"Portfolio heat too high: {current_heat/self.account_balance:.1%}"

        return False, "All risk checks passed"


# Example usage and testing
if __name__ == "__main__":
    # Initialize risk manager with $10,000 account
    risk_manager = EnhancedRiskManager(account_balance=10000, max_risk_per_trade=0.02)

    # Set risk level
    risk_manager.set_risk_level('CONSERVATIVE')

    # Add some sample trade history
    sample_trades = [
        {'pnl': 150, 'returns': 0.015},
        {'pnl': -100, 'returns': -0.01},
        {'pnl': 200, 'returns': 0.02},
        {'pnl': -75, 'returns': -0.0075},
        {'pnl': 180, 'returns': 0.018},
    ]

    for trade in sample_trades:
        risk_manager.add_trade(trade)

    # Calculate position size for a signal
    signal = {
        'entry_price': 100,
        'stop_loss': 98,
        'take_profit': 105,
        'volatility': 0.02,
        'strength': 0.75,
        'ml_confidence': 0.82,
        'risk_reward_ratio': 2.5
    }

    # Calculate position size using Kelly Criterion
    result = risk_manager.calculate_position_size(signal, method='kelly')

    print("Position Sizing Result:")
    print(f"Position Size: {result.position_size:.4f}")
    print(f"Risk Amount: ${result.risk_amount:.2f}")
    print(f"Kelly Fraction: {result.kelly_fraction:.4%}")
    print(f"Confidence Level: {result.confidence_level:.2%}")
    print(f"Expected Value: ${result.expected_value:.2f}")
    print(f"Reasoning: {result.reasoning}")

    # Get risk metrics
    metrics = risk_manager.get_risk_metrics()
    print("\nRisk Metrics:")
    for key, value in metrics.items():
        print(f"{key}: {value}")

    # Check if should stop trading
    should_stop, reason = risk_manager.should_stop_trading()
    print(f"\nShould Stop Trading: {should_stop}")
    print(f"Reason: {reason}")