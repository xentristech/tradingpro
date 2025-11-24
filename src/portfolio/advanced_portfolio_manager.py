"""
Advanced Portfolio Management System with Risk Parity and Dynamic Allocation
Author: Trading Pro System
Version: 3.0
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from abc import ABC, abstractmethod
import scipy.optimize as sco
from scipy.stats import norm
import warnings
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AllocationMethod(Enum):
    """Portfolio allocation methods"""
    EQUAL_WEIGHT = "equal_weight"
    MARKET_CAP = "market_cap"
    RISK_PARITY = "risk_parity"
    MEAN_VARIANCE = "mean_variance"
    BLACK_LITTERMAN = "black_litterman"
    HIERARCHICAL_RISK_PARITY = "hrp"
    MINIMUM_VARIANCE = "minimum_variance"
    MAXIMUM_DIVERSIFICATION = "max_diversification"


class RebalanceFrequency(Enum):
    """Rebalancing frequency options"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    THRESHOLD = "threshold"  # Rebalance when drift exceeds threshold


@dataclass
class AssetInfo:
    """Information about an asset in the portfolio"""
    symbol: str
    asset_class: str
    sector: Optional[str] = None
    country: Optional[str] = None
    currency: str = "USD"
    current_price: float = 0.0
    market_cap: Optional[float] = None
    beta: Optional[float] = None
    volatility: Optional[float] = None
    correlation_spy: Optional[float] = None


@dataclass
class PortfolioConstraints:
    """Portfolio construction constraints"""
    min_weight: float = 0.0  # Minimum weight per asset
    max_weight: float = 1.0  # Maximum weight per asset
    max_sector_weight: float = 0.3  # Maximum weight per sector
    max_country_weight: float = 0.5  # Maximum weight per country
    min_assets: int = 2  # Minimum number of assets
    max_assets: int = 50  # Maximum number of assets
    max_turnover: float = 0.5  # Maximum turnover per rebalance
    leverage_limit: float = 1.0  # Maximum leverage
    long_only: bool = True  # Long-only constraint
    risk_budget: Dict[str, float] = field(default_factory=dict)  # Risk budget by asset class


@dataclass
class PortfolioMetrics:
    """Portfolio performance and risk metrics"""
    # Returns
    total_return: float = 0.0
    annual_return: float = 0.0
    excess_return: float = 0.0

    # Risk
    volatility: float = 0.0
    downside_deviation: float = 0.0
    max_drawdown: float = 0.0
    var_95: float = 0.0
    cvar_95: float = 0.0

    # Risk-adjusted
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    information_ratio: float = 0.0

    # Diversification
    effective_assets: float = 0.0
    concentration_index: float = 0.0
    diversification_ratio: float = 0.0

    # Tracking
    tracking_error: float = 0.0
    beta: float = 0.0
    alpha: float = 0.0

    # Portfolio specific
    turnover: float = 0.0
    transaction_costs: float = 0.0
    current_leverage: float = 1.0


class PortfolioOptimizer(ABC):
    """Base class for portfolio optimization methods"""

    @abstractmethod
    def optimize(self, expected_returns: pd.Series, covariance_matrix: pd.DataFrame,
                 constraints: PortfolioConstraints, **kwargs) -> pd.Series:
        """
        Optimize portfolio weights

        Args:
            expected_returns: Expected returns for each asset
            covariance_matrix: Covariance matrix
            constraints: Portfolio constraints

        Returns:
            Optimal weights as pandas Series
        """
        pass


class EqualWeightOptimizer(PortfolioOptimizer):
    """Equal weight allocation"""

    def optimize(self, expected_returns: pd.Series, covariance_matrix: pd.DataFrame,
                 constraints: PortfolioConstraints, **kwargs) -> pd.Series:
        """Equal weight optimization"""
        n_assets = len(expected_returns)
        weights = pd.Series(1.0 / n_assets, index=expected_returns.index)
        return weights


class RiskParityOptimizer(PortfolioOptimizer):
    """Risk parity optimization - equal risk contribution"""

    def optimize(self, expected_returns: pd.Series, covariance_matrix: pd.DataFrame,
                 constraints: PortfolioConstraints, **kwargs) -> pd.Series:
        """Risk parity optimization"""

        def risk_budget_objective(weights, covariance_matrix):
            """Objective function for risk parity"""
            weights = np.array(weights)
            portfolio_vol = np.sqrt(np.dot(weights, np.dot(covariance_matrix, weights)))

            # Risk contributions
            marginal_contrib = np.dot(covariance_matrix, weights) / portfolio_vol
            contrib = weights * marginal_contrib

            # Target equal risk contribution
            target_contrib = portfolio_vol / len(weights)

            # Sum of squared deviations
            return np.sum((contrib - target_contrib) ** 2)

        n_assets = len(expected_returns)
        cov_matrix = covariance_matrix.values

        # Initial guess - equal weights
        x0 = np.array([1.0 / n_assets] * n_assets)

        # Constraints
        constraints_list = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0}  # Weights sum to 1
        ]

        # Bounds
        bounds = [(constraints.min_weight, constraints.max_weight) for _ in range(n_assets)]

        # Optimize
        result = sco.minimize(
            risk_budget_objective,
            x0,
            args=(cov_matrix,),
            method='SLSQP',
            bounds=bounds,
            constraints=constraints_list,
            options={'maxiter': 1000}
        )

        if result.success:
            weights = pd.Series(result.x, index=expected_returns.index)
        else:
            logger.warning("Risk parity optimization failed, using equal weights")
            weights = pd.Series(1.0 / n_assets, index=expected_returns.index)

        return weights


class MeanVarianceOptimizer(PortfolioOptimizer):
    """Mean-variance optimization (Markowitz)"""

    def optimize(self, expected_returns: pd.Series, covariance_matrix: pd.DataFrame,
                 constraints: PortfolioConstraints, **kwargs) -> pd.Series:
        """Mean-variance optimization"""

        target_return = kwargs.get('target_return', expected_returns.mean())
        risk_aversion = kwargs.get('risk_aversion', 1.0)

        def objective(weights, expected_returns, covariance_matrix, risk_aversion):
            """Utility function: return - risk_aversion * variance"""
            weights = np.array(weights)
            returns = np.dot(weights, expected_returns)
            variance = np.dot(weights, np.dot(covariance_matrix, weights))
            return -(returns - risk_aversion * variance)

        n_assets = len(expected_returns)
        cov_matrix = covariance_matrix.values
        exp_returns = expected_returns.values

        # Initial guess
        x0 = np.array([1.0 / n_assets] * n_assets)

        # Constraints
        constraints_list = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0}  # Weights sum to 1
        ]

        # Optional return constraint
        if target_return is not None:
            constraints_list.append({
                'type': 'eq',
                'fun': lambda x: np.dot(x, exp_returns) - target_return
            })

        # Bounds
        bounds = [(constraints.min_weight, constraints.max_weight) for _ in range(n_assets)]

        # Optimize
        result = sco.minimize(
            objective,
            x0,
            args=(exp_returns, cov_matrix, risk_aversion),
            method='SLSQP',
            bounds=bounds,
            constraints=constraints_list,
            options={'maxiter': 1000}
        )

        if result.success:
            weights = pd.Series(result.x, index=expected_returns.index)
        else:
            logger.warning("Mean-variance optimization failed, using equal weights")
            weights = pd.Series(1.0 / n_assets, index=expected_returns.index)

        return weights


class MinimumVarianceOptimizer(PortfolioOptimizer):
    """Minimum variance optimization"""

    def optimize(self, expected_returns: pd.Series, covariance_matrix: pd.DataFrame,
                 constraints: PortfolioConstraints, **kwargs) -> pd.Series:
        """Minimum variance optimization"""

        def objective(weights, covariance_matrix):
            """Portfolio variance"""
            weights = np.array(weights)
            return np.dot(weights, np.dot(covariance_matrix, weights))

        n_assets = len(expected_returns)
        cov_matrix = covariance_matrix.values

        # Initial guess
        x0 = np.array([1.0 / n_assets] * n_assets)

        # Constraints
        constraints_list = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - 1.0}  # Weights sum to 1
        ]

        # Bounds
        bounds = [(constraints.min_weight, constraints.max_weight) for _ in range(n_assets)]

        # Optimize
        result = sco.minimize(
            objective,
            x0,
            args=(cov_matrix,),
            method='SLSQP',
            bounds=bounds,
            constraints=constraints_list,
            options={'maxiter': 1000}
        )

        if result.success:
            weights = pd.Series(result.x, index=expected_returns.index)
        else:
            logger.warning("Minimum variance optimization failed, using equal weights")
            weights = pd.Series(1.0 / n_assets, index=expected_returns.index)

        return weights


class HierarchicalRiskParityOptimizer(PortfolioOptimizer):
    """Hierarchical Risk Parity (HRP) optimization"""

    def optimize(self, expected_returns: pd.Series, covariance_matrix: pd.DataFrame,
                 constraints: PortfolioConstraints, **kwargs) -> pd.Series:
        """HRP optimization using Lopez de Prado's method"""

        def getIVP(cov, **kargs):
            """Compute the inverse-variance portfolio"""
            ivp = 1. / np.diag(cov)
            ivp /= ivp.sum()
            return ivp

        def getClusterVar(cov, cItems):
            """Compute variance per cluster"""
            cov_ = cov.loc[cItems, cItems]  # matrix slice
            w_ = getIVP(cov_).reshape(-1, 1)
            cVar = np.dot(w_.T, np.dot(cov_, w_))[0, 0]
            return cVar

        def getQuasiDiag(link):
            """Sort clustered items by distance"""
            link = link.astype(int)
            sortIx = pd.Series([link[-1, 0], link[-1, 1]])
            numItems = link[-1, 3]  # number of original items
            while sortIx.max() >= numItems:
                sortIx.index = range(0, sortIx.shape[0] * 2, 2)  # make space
                df0 = sortIx[sortIx >= numItems]  # find clusters
                i = df0.index
                j = df0.values - numItems
                sortIx.loc[i] = link[j, 0]  # item 1
                df0 = pd.Series(link[j, 1], index=i + 1)
                sortIx = sortIx.append(df0)  # item 2
                sortIx = sortIx.sort_index()  # re-sort
                sortIx.index = range(sortIx.shape[0])  # re-index
            return sortIx.tolist()

        def getRecBipart(cov, sortIx):
            """Compute HRP alloc"""
            w = pd.Series(1, index=sortIx)
            cItems = [sortIx]  # initialize all items in one cluster
            while len(cItems) > 0:
                cItems = [i[j:k] for i in cItems for j, k in
                          ((0, len(i) // 2), (len(i) // 2, len(i))) if len(i) > 1]  # bi-section
                for i in range(0, len(cItems), 2):  # parse in pairs
                    cItems0 = cItems[i]  # cluster 1
                    cItems1 = cItems[i + 1]  # cluster 2
                    cVar0 = getClusterVar(cov, cItems0)
                    cVar1 = getClusterVar(cov, cItems1)
                    alpha = 1 - cVar0 / (cVar0 + cVar1)
                    w[cItems0] *= alpha  # weight 1
                    w[cItems1] *= 1 - alpha  # weight 2
            return w

        try:
            from scipy.cluster.hierarchy import linkage
            from scipy.spatial.distance import squareform

            # Compute distance matrix
            corr = covariance_matrix.div(
                np.outer(np.sqrt(np.diag(covariance_matrix)),
                         np.sqrt(np.diag(covariance_matrix))))
            dist = ((1 - corr) / 2.) ** .5
            dist = dist.fillna(0)

            # Hierarchical clustering
            link = linkage(squareform(dist.values), 'single')

            # Get quasi-diagonal matrix
            sortIx = getQuasiDiag(link)
            sortIx = corr.index[sortIx].tolist()

            # Recursive bisection
            hrp_weights = getRecBipart(covariance_matrix, sortIx)
            hrp_weights = hrp_weights.reindex(expected_returns.index)

            return hrp_weights

        except ImportError:
            logger.warning("Scipy clustering not available, using risk parity")
            rp_optimizer = RiskParityOptimizer()
            return rp_optimizer.optimize(expected_returns, covariance_matrix, constraints)
        except Exception as e:
            logger.warning(f"HRP optimization failed: {e}, using equal weights")
            return pd.Series(1.0 / len(expected_returns), index=expected_returns.index)


class AdvancedPortfolioManager:
    """
    Advanced portfolio management system with multiple optimization methods
    """

    def __init__(self, initial_capital: float = 100000,
                 rebalance_frequency: RebalanceFrequency = RebalanceFrequency.MONTHLY,
                 constraints: PortfolioConstraints = None):
        """
        Initialize portfolio manager

        Args:
            initial_capital: Initial portfolio value
            rebalance_frequency: How often to rebalance
            constraints: Portfolio constraints
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.rebalance_frequency = rebalance_frequency
        self.constraints = constraints or PortfolioConstraints()

        # Portfolio state
        self.assets = {}  # symbol -> AssetInfo
        self.current_weights = pd.Series(dtype=float)
        self.target_weights = pd.Series(dtype=float)
        self.positions = {}  # symbol -> quantity
        self.last_rebalance = None
        self.rebalance_threshold = 0.05  # 5% drift threshold

        # Historical data
        self.price_history = pd.DataFrame()
        self.weight_history = pd.DataFrame()
        self.return_history = pd.Series(dtype=float)
        self.metrics_history = []

        # Optimizers
        self.optimizers = {
            AllocationMethod.EQUAL_WEIGHT: EqualWeightOptimizer(),
            AllocationMethod.RISK_PARITY: RiskParityOptimizer(),
            AllocationMethod.MEAN_VARIANCE: MeanVarianceOptimizer(),
            AllocationMethod.MINIMUM_VARIANCE: MinimumVarianceOptimizer(),
            AllocationMethod.HIERARCHICAL_RISK_PARITY: HierarchicalRiskParityOptimizer()
        }

        # Risk free rate (annualized)
        self.risk_free_rate = 0.02

    def add_asset(self, asset_info: AssetInfo):
        """Add an asset to the universe"""
        self.assets[asset_info.symbol] = asset_info
        logger.info(f"Added asset: {asset_info.symbol} ({asset_info.asset_class})")

    def remove_asset(self, symbol: str):
        """Remove an asset from the universe"""
        if symbol in self.assets:
            del self.assets[symbol]
            logger.info(f"Removed asset: {symbol}")

    def update_prices(self, prices: Dict[str, float], timestamp: datetime = None):
        """
        Update asset prices

        Args:
            prices: Dictionary of symbol -> price
            timestamp: Price timestamp (defaults to now)
        """
        if timestamp is None:
            timestamp = datetime.now()

        # Update asset prices
        for symbol, price in prices.items():
            if symbol in self.assets:
                self.assets[symbol].current_price = price

        # Store price history
        price_row = pd.Series(prices, name=timestamp)
        if self.price_history.empty:
            self.price_history = pd.DataFrame([price_row])
        else:
            self.price_history = pd.concat([self.price_history, price_row.to_frame().T])

        # Update current portfolio value
        self._update_portfolio_value()

        # Check if rebalancing is needed
        if self._should_rebalance():
            self.rebalance()

    def calculate_expected_returns(self, method: str = 'historical',
                                   lookback_days: int = 252) -> pd.Series:
        """
        Calculate expected returns for each asset

        Args:
            method: Method to calculate returns ('historical', 'capm', 'exponential')
            lookback_days: Lookback period in days

        Returns:
            Expected returns as pandas Series
        """
        if self.price_history.empty or len(self.price_history) < 2:
            # Default expected returns if no history
            return pd.Series(0.001, index=list(self.assets.keys()))

        # Get recent price data
        recent_prices = self.price_history.tail(lookback_days)
        returns = recent_prices.pct_change().dropna()

        if method == 'historical':
            # Simple historical mean
            expected_returns = returns.mean() * 252  # Annualized

        elif method == 'exponential':
            # Exponentially weighted returns
            alpha = 2 / (lookback_days + 1)
            weights = [(1 - alpha) ** i for i in range(len(returns))]
            weights.reverse()
            weights = np.array(weights)
            weights /= weights.sum()

            expected_returns = pd.Series(
                [np.average(returns[col], weights=weights) * 252 for col in returns.columns],
                index=returns.columns
            )

        elif method == 'capm':
            # CAPM-based expected returns
            market_returns = returns.mean(axis=1)  # Equal-weighted market proxy
            expected_returns = pd.Series(index=returns.columns, dtype=float)

            for symbol in returns.columns:
                if symbol in self.assets and self.assets[symbol].beta is not None:
                    beta = self.assets[symbol].beta
                    market_premium = market_returns.mean() * 252 - self.risk_free_rate
                    expected_returns[symbol] = self.risk_free_rate + beta * market_premium
                else:
                    expected_returns[symbol] = returns[symbol].mean() * 252

        else:
            raise ValueError(f"Unknown expected returns method: {method}")

        return expected_returns.fillna(0.001)

    def calculate_covariance_matrix(self, method: str = 'sample',
                                    lookback_days: int = 252) -> pd.DataFrame:
        """
        Calculate covariance matrix

        Args:
            method: Method to calculate covariance ('sample', 'exponential', 'shrinkage')
            lookback_days: Lookback period in days

        Returns:
            Covariance matrix as pandas DataFrame
        """
        if self.price_history.empty or len(self.price_history) < 2:
            # Default covariance matrix
            n_assets = len(self.assets)
            symbols = list(self.assets.keys())
            default_var = 0.04  # 20% annual volatility
            default_corr = 0.3  # 30% correlation

            cov_matrix = pd.DataFrame(
                default_var * (default_corr + (1 - default_corr) * np.eye(n_assets)),
                index=symbols,
                columns=symbols
            )
            return cov_matrix

        # Get recent price data
        recent_prices = self.price_history.tail(lookback_days)
        returns = recent_prices.pct_change().dropna()

        if method == 'sample':
            # Sample covariance matrix
            cov_matrix = returns.cov() * 252  # Annualized

        elif method == 'exponential':
            # Exponentially weighted covariance
            alpha = 2 / (lookback_days + 1)
            cov_matrix = returns.ewm(alpha=alpha).cov().iloc[-len(returns.columns):] * 252

        elif method == 'shrinkage':
            # Ledoit-Wolf shrinkage estimator
            sample_cov = returns.cov() * 252
            n_assets = len(sample_cov)

            # Shrinkage target (diagonal matrix with average variance)
            avg_var = np.trace(sample_cov) / n_assets
            target = avg_var * np.eye(n_assets)
            target = pd.DataFrame(target, index=sample_cov.index, columns=sample_cov.columns)

            # Shrinkage intensity (simplified)
            shrinkage = 0.2  # 20% shrinkage
            cov_matrix = (1 - shrinkage) * sample_cov + shrinkage * target

        else:
            raise ValueError(f"Unknown covariance method: {method}")

        return cov_matrix.fillna(0.04)

    def optimize_portfolio(self, method: AllocationMethod = AllocationMethod.RISK_PARITY,
                          **kwargs) -> pd.Series:
        """
        Optimize portfolio weights

        Args:
            method: Optimization method
            **kwargs: Additional arguments for optimizer

        Returns:
            Optimal weights as pandas Series
        """
        if not self.assets:
            return pd.Series(dtype=float)

        # Calculate expected returns and covariance
        expected_returns = self.calculate_expected_returns()
        covariance_matrix = self.calculate_covariance_matrix()

        # Ensure we have data for all assets
        symbols = list(self.assets.keys())
        expected_returns = expected_returns.reindex(symbols, fill_value=0.001)
        covariance_matrix = covariance_matrix.reindex(symbols).reindex(symbols, axis=1).fillna(0.04)

        # Get optimizer
        if method not in self.optimizers:
            logger.warning(f"Unknown optimization method: {method}, using equal weight")
            method = AllocationMethod.EQUAL_WEIGHT

        optimizer = self.optimizers[method]

        # Optimize
        try:
            weights = optimizer.optimize(expected_returns, covariance_matrix, self.constraints, **kwargs)
            weights = weights.reindex(symbols, fill_value=0.0)

            # Apply constraints
            weights = self._apply_constraints(weights)

            logger.info(f"Portfolio optimized using {method.value}")
            return weights

        except Exception as e:
            logger.error(f"Portfolio optimization failed: {e}")
            # Fallback to equal weights
            return pd.Series(1.0 / len(symbols), index=symbols)

    def _apply_constraints(self, weights: pd.Series) -> pd.Series:
        """Apply portfolio constraints to weights"""

        # Clip weights to bounds
        weights = weights.clip(self.constraints.min_weight, self.constraints.max_weight)

        # Normalize to sum to 1
        weights = weights / weights.sum()

        # Asset class constraints
        if self.constraints.risk_budget:
            weights = self._apply_risk_budget(weights)

        # Sector constraints
        weights = self._apply_sector_constraints(weights)

        return weights

    def _apply_risk_budget(self, weights: pd.Series) -> pd.Series:
        """Apply risk budget constraints"""
        # This is a simplified implementation
        # In practice, you'd optimize subject to risk budget constraints
        return weights

    def _apply_sector_constraints(self, weights: pd.Series) -> pd.Series:
        """Apply sector concentration constraints"""
        # Group by sector and check constraints
        sector_weights = {}
        for symbol, weight in weights.items():
            if symbol in self.assets:
                sector = self.assets[symbol].sector or 'Other'
                sector_weights[sector] = sector_weights.get(sector, 0) + weight

        # If any sector exceeds limit, proportionally reduce
        for sector, sector_weight in sector_weights.items():
            if sector_weight > self.constraints.max_sector_weight:
                # Get assets in this sector
                sector_assets = [s for s, a in self.assets.items() if a.sector == sector]
                reduction_factor = self.constraints.max_sector_weight / sector_weight

                # Reduce weights proportionally
                for symbol in sector_assets:
                    if symbol in weights:
                        weights[symbol] *= reduction_factor

        # Renormalize
        weights = weights / weights.sum()
        return weights

    def rebalance(self, method: AllocationMethod = AllocationMethod.RISK_PARITY):
        """
        Rebalance the portfolio

        Args:
            method: Optimization method for rebalancing
        """
        logger.info("Starting portfolio rebalance")

        # Calculate new target weights
        new_weights = self.optimize_portfolio(method)

        if new_weights.empty:
            logger.warning("No weights calculated, skipping rebalance")
            return

        # Calculate turnover
        if not self.current_weights.empty:
            turnover = (new_weights - self.current_weights).abs().sum() / 2
            logger.info(f"Portfolio turnover: {turnover:.2%}")

            # Check turnover constraint
            if turnover > self.constraints.max_turnover:
                logger.warning(f"Turnover {turnover:.2%} exceeds limit {self.constraints.max_turnover:.2%}")
                # Could implement turnover minimization here

        # Update weights
        self.target_weights = new_weights
        self.current_weights = new_weights.copy()
        self.last_rebalance = datetime.now()

        # Calculate new positions
        self._calculate_positions()

        # Store weight history
        weight_row = pd.Series(new_weights, name=datetime.now())
        if self.weight_history.empty:
            self.weight_history = pd.DataFrame([weight_row])
        else:
            self.weight_history = pd.concat([self.weight_history, weight_row.to_frame().T])

        logger.info("Portfolio rebalanced successfully")

    def _calculate_positions(self):
        """Calculate position sizes based on target weights"""
        total_value = self.current_capital

        for symbol, weight in self.target_weights.items():
            if symbol in self.assets and weight > 0:
                target_value = total_value * weight
                current_price = self.assets[symbol].current_price

                if current_price > 0:
                    position_size = target_value / current_price
                    self.positions[symbol] = position_size

    def _update_portfolio_value(self):
        """Update current portfolio value based on positions and prices"""
        total_value = 0

        for symbol, quantity in self.positions.items():
            if symbol in self.assets:
                current_price = self.assets[symbol].current_price
                total_value += quantity * current_price

        if total_value > 0:
            # Update current weights
            new_weights = pd.Series(dtype=float)
            for symbol, quantity in self.positions.items():
                if symbol in self.assets:
                    current_price = self.assets[symbol].current_price
                    position_value = quantity * current_price
                    new_weights[symbol] = position_value / total_value

            self.current_weights = new_weights
            self.current_capital = total_value

    def _should_rebalance(self) -> bool:
        """Determine if portfolio should be rebalanced"""
        if self.last_rebalance is None:
            return True

        if self.rebalance_frequency == RebalanceFrequency.THRESHOLD:
            # Check weight drift
            if not self.current_weights.empty and not self.target_weights.empty:
                max_drift = (self.current_weights - self.target_weights).abs().max()
                return max_drift > self.rebalance_threshold

        elif self.rebalance_frequency == RebalanceFrequency.DAILY:
            return (datetime.now() - self.last_rebalance).days >= 1

        elif self.rebalance_frequency == RebalanceFrequency.WEEKLY:
            return (datetime.now() - self.last_rebalance).days >= 7

        elif self.rebalance_frequency == RebalanceFrequency.MONTHLY:
            return (datetime.now() - self.last_rebalance).days >= 30

        elif self.rebalance_frequency == RebalanceFrequency.QUARTERLY:
            return (datetime.now() - self.last_rebalance).days >= 90

        return False

    def calculate_metrics(self, benchmark_returns: Optional[pd.Series] = None) -> PortfolioMetrics:
        """
        Calculate comprehensive portfolio metrics

        Args:
            benchmark_returns: Benchmark returns for comparison

        Returns:
            PortfolioMetrics object
        """
        metrics = PortfolioMetrics()

        if self.return_history.empty or len(self.return_history) < 2:
            return metrics

        returns = self.return_history.dropna()

        # Basic return metrics
        total_periods = len(returns)
        total_return_ratio = (1 + returns).prod()
        metrics.total_return = total_return_ratio - 1

        if total_periods > 0:
            periods_per_year = 252  # Assuming daily returns
            metrics.annual_return = total_return_ratio ** (periods_per_year / total_periods) - 1

        # Risk metrics
        metrics.volatility = returns.std() * np.sqrt(252)  # Annualized

        # Downside metrics
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 0:
            metrics.downside_deviation = downside_returns.std() * np.sqrt(252)

        # Drawdown
        cumulative = (1 + returns).cumprod()
        rolling_max = cumulative.expanding().max()
        drawdown = (cumulative - rolling_max) / rolling_max
        metrics.max_drawdown = abs(drawdown.min())

        # VaR and CVaR
        metrics.var_95 = np.percentile(returns, 5)
        tail_losses = returns[returns <= metrics.var_95]
        if len(tail_losses) > 0:
            metrics.cvar_95 = tail_losses.mean()

        # Risk-adjusted metrics
        excess_returns = returns - self.risk_free_rate / 252
        if metrics.volatility > 0:
            metrics.sharpe_ratio = excess_returns.mean() * np.sqrt(252) / metrics.volatility

        if metrics.downside_deviation > 0:
            metrics.sortino_ratio = excess_returns.mean() * np.sqrt(252) / metrics.downside_deviation

        if metrics.max_drawdown > 0:
            metrics.calmar_ratio = metrics.annual_return / metrics.max_drawdown

        # Diversification metrics
        if not self.current_weights.empty:
            weights = self.current_weights.fillna(0)
            metrics.effective_assets = 1 / (weights ** 2).sum()  # Inverse Herfindahl index
            metrics.concentration_index = (weights ** 2).sum()

        # Benchmark comparison
        if benchmark_returns is not None and len(benchmark_returns) > 0:
            # Align returns
            aligned_returns = returns.reindex(benchmark_returns.index).dropna()
            aligned_benchmark = benchmark_returns.reindex(returns.index).dropna()

            if len(aligned_returns) > 0 and len(aligned_benchmark) > 0:
                # Beta and alpha
                covariance = np.cov(aligned_returns, aligned_benchmark)[0, 1]
                benchmark_var = aligned_benchmark.var()

                if benchmark_var > 0:
                    metrics.beta = covariance / benchmark_var
                    metrics.alpha = (aligned_returns.mean() - metrics.beta * aligned_benchmark.mean()) * 252

                # Tracking error
                tracking_diff = aligned_returns - aligned_benchmark
                metrics.tracking_error = tracking_diff.std() * np.sqrt(252)

                # Information ratio
                if metrics.tracking_error > 0:
                    metrics.information_ratio = tracking_diff.mean() * np.sqrt(252) / metrics.tracking_error

        return metrics

    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get comprehensive portfolio summary"""
        metrics = self.calculate_metrics()

        summary = {
            'portfolio_value': self.current_capital,
            'total_return': metrics.total_return,
            'annual_return': metrics.annual_return,
            'volatility': metrics.volatility,
            'sharpe_ratio': metrics.sharpe_ratio,
            'max_drawdown': metrics.max_drawdown,
            'num_assets': len([w for w in self.current_weights if w > 0.001]),
            'effective_assets': metrics.effective_assets,
            'last_rebalance': self.last_rebalance,
            'current_weights': self.current_weights.to_dict(),
            'largest_position': self.current_weights.max() if not self.current_weights.empty else 0,
            'asset_allocation': self._get_asset_allocation()
        }

        return summary

    def _get_asset_allocation(self) -> Dict[str, float]:
        """Get allocation by asset class"""
        allocation = {}

        for symbol, weight in self.current_weights.items():
            if symbol in self.assets:
                asset_class = self.assets[symbol].asset_class
                allocation[asset_class] = allocation.get(asset_class, 0) + weight

        return allocation

    def export_data(self, filepath: str):
        """Export portfolio data to file"""
        data = {
            'summary': self.get_portfolio_summary(),
            'price_history': self.price_history.to_dict(),
            'weight_history': self.weight_history.to_dict(),
            'return_history': self.return_history.to_dict(),
            'assets': {symbol: {
                'asset_class': asset.asset_class,
                'sector': asset.sector,
                'current_price': asset.current_price
            } for symbol, asset in self.assets.items()}
        }

        import json
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        logger.info(f"Portfolio data exported to {filepath}")


# Example usage
if __name__ == "__main__":
    # Initialize portfolio manager
    portfolio = AdvancedPortfolioManager(
        initial_capital=100000,
        rebalance_frequency=RebalanceFrequency.MONTHLY
    )

    # Add assets
    assets = [
        AssetInfo('SPY', 'Equity', 'Technology', 'US', current_price=450),
        AssetInfo('QQQ', 'Equity', 'Technology', 'US', current_price=380),
        AssetInfo('TLT', 'Bond', 'Government', 'US', current_price=95),
        AssetInfo('GLD', 'Commodity', 'Precious Metals', 'US', current_price=180),
        AssetInfo('VEA', 'Equity', 'Developed Markets', 'Global', current_price=52)
    ]

    for asset in assets:
        portfolio.add_asset(asset)

    # Simulate price updates over time
    dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='D')

    for date in dates:
        # Generate random price movements
        price_changes = {
            'SPY': np.random.normal(0.0005, 0.02),
            'QQQ': np.random.normal(0.0008, 0.025),
            'TLT': np.random.normal(0.0002, 0.015),
            'GLD': np.random.normal(0.0003, 0.018),
            'VEA': np.random.normal(0.0004, 0.022)
        }

        # Update prices
        new_prices = {}
        for symbol in price_changes:
            old_price = portfolio.assets[symbol].current_price
            new_price = old_price * (1 + price_changes[symbol])
            new_prices[symbol] = new_price

        portfolio.update_prices(new_prices, date)

        # Calculate returns
        if len(portfolio.price_history) > 1:
            latest_returns = portfolio.price_history.pct_change().iloc[-1]
            portfolio_return = (portfolio.current_weights * latest_returns).sum()
            portfolio.return_history.loc[date] = portfolio_return

    # Final rebalance with different methods
    print("\n" + "="*50)
    print("PORTFOLIO OPTIMIZATION COMPARISON")
    print("="*50)

    methods = [
        AllocationMethod.EQUAL_WEIGHT,
        AllocationMethod.RISK_PARITY,
        AllocationMethod.MINIMUM_VARIANCE,
        AllocationMethod.MEAN_VARIANCE
    ]

    for method in methods:
        weights = portfolio.optimize_portfolio(method)
        print(f"\n{method.value.upper()} ALLOCATION:")
        for symbol, weight in weights.items():
            print(f"  {symbol}: {weight:.2%}")

    # Get portfolio summary
    print("\n" + "="*50)
    print("PORTFOLIO SUMMARY")
    print("="*50)

    summary = portfolio.get_portfolio_summary()
    print(f"Portfolio Value: ${summary['portfolio_value']:,.0f}")
    print(f"Total Return: {summary['total_return']:.2%}")
    print(f"Annual Return: {summary['annual_return']:.2%}")
    print(f"Volatility: {summary['volatility']:.2%}")
    print(f"Sharpe Ratio: {summary['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {summary['max_drawdown']:.2%}")
    print(f"Effective Assets: {summary['effective_assets']:.1f}")

    print(f"\nAsset Allocation:")
    for asset_class, allocation in summary['asset_allocation'].items():
        print(f"  {asset_class}: {allocation:.2%}")

    print(f"\nCurrent Weights:")
    for symbol, weight in summary['current_weights'].items():
        print(f"  {symbol}: {weight:.2%}")