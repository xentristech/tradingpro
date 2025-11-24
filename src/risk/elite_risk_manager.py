#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ELITE RISK MANAGER - GESTIÓN PROFESIONAL DE RIESGO
===================================================
Sistema avanzado de gestión de riesgo con Kelly Criterion y VAR
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
import json
import os
from scipy import stats
from scipy.optimize import minimize
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

@dataclass
class RiskMetrics:
    """Métricas de riesgo avanzadas"""
    var_95: float  # Value at Risk 95%
    var_99: float  # Value at Risk 99%
    cvar: float  # Conditional Value at Risk
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    max_drawdown: float
    current_drawdown: float
    win_rate: float
    profit_factor: float
    recovery_factor: float
    kelly_fraction: float
    optimal_position_size: float
    risk_score: float  # 0-100
    market_regime: str  # 'bull', 'bear', 'sideways', 'volatile'
    
@dataclass
class PositionSizing:
    """Cálculo de tamaño de posición óptimo"""
    base_size: float
    kelly_size: float
    var_adjusted_size: float
    volatility_adjusted_size: float
    correlation_adjusted_size: float
    final_size: float
    max_size: float
    min_size: float
    leverage: float

class EliteRiskManager:
    """
    Sistema profesional de gestión de riesgo con:
    - Kelly Criterion para sizing óptimo
    - Value at Risk (VaR) y CVaR
    - Gestión de correlaciones
    - Ajuste dinámico por régimen de mercado
    - Machine Learning para predicción de riesgo
    """
    
    def __init__(self, 
                 initial_capital: float = 10000,
                 max_risk_per_trade: float = 0.02,
                 max_portfolio_risk: float = 0.06,
                 max_correlation: float = 0.7,
                 use_kelly: bool = True):
        
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.max_risk_per_trade = max_risk_per_trade
        self.max_portfolio_risk = max_portfolio_risk
        self.max_correlation = max_correlation
        self.use_kelly = use_kelly
        
        # Estado del portfolio
        self.open_positions = []
        self.trade_history = []
        self.daily_returns = []
        self.equity_curve = [initial_capital]
        
        # Parámetros de Kelly
        self.kelly_fraction = 0.25  # Kelly conservador (25% del Kelly completo)
        self.min_kelly = 0.01
        self.max_kelly = 0.25
        
        # Régimen de mercado
        self.market_regime = 'normal'
        self.volatility_regime = 'normal'
        
        # Matriz de correlación
        self.correlation_matrix = {}
        self.position_correlations = {}
        
        # Métricas de performance
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.consecutive_losses = 0
        self.max_consecutive_losses = 0
        
        # Límites de riesgo
        self.daily_loss_limit = initial_capital * 0.05
        self.weekly_loss_limit = initial_capital * 0.10
        self.monthly_loss_limit = initial_capital * 0.15
        
        # Tracking de pérdidas
        self.daily_pnl = 0
        self.weekly_pnl = 0
        self.monthly_pnl = 0
        
        logger.info(f"Elite Risk Manager initialized with ${initial_capital}")
    
    def calculate_kelly_criterion(self, 
                                 win_rate: float,
                                 avg_win: float,
                                 avg_loss: float) -> float:
        """
        Calcula el Kelly Criterion para determinar el tamaño óptimo de posición
        f* = (p * b - q) / b
        donde:
        - p = probabilidad de ganar
        - q = probabilidad de perder (1-p)
        - b = ratio win/loss
        """
        if avg_loss == 0 or win_rate == 0:
            return self.min_kelly
        
        p = win_rate
        q = 1 - win_rate
        b = abs(avg_win / avg_loss)
        
        kelly_full = (p * b - q) / b
        
        # Aplicar Kelly conservador
        kelly_fraction = kelly_full * self.kelly_fraction
        
        # Limitar entre min y max
        kelly_fraction = max(self.min_kelly, min(self.max_kelly, kelly_fraction))
        
        return kelly_fraction
    
    def calculate_var(self, 
                     returns: List[float],
                     confidence_level: float = 0.95,
                     time_horizon: int = 1) -> Tuple[float, float]:
        """
        Calcula Value at Risk usando método paramétrico y histórico
        """
        if not returns or len(returns) < 20:
            return 0, 0
        
        returns_array = np.array(returns)
        
        # Método paramétrico (asumiendo distribución normal)
        mean = np.mean(returns_array)
        std = np.std(returns_array)
        
        # Z-score para nivel de confianza
        z_score = stats.norm.ppf(1 - confidence_level)
        var_parametric = mean + z_score * std * np.sqrt(time_horizon)
        
        # Método histórico
        var_historical = np.percentile(returns_array, (1 - confidence_level) * 100)
        
        # Usar el más conservador
        var = min(var_parametric, var_historical)
        
        # Calcular CVaR (Expected Shortfall)
        cvar = returns_array[returns_array <= var].mean() if len(returns_array[returns_array <= var]) > 0 else var
        
        return abs(var), abs(cvar)
    
    def calculate_position_size(self,
                               symbol: str,
                               entry_price: float,
                               stop_loss: float,
                               confidence: float,
                               volatility: float,
                               correlation_with_portfolio: float = 0) -> PositionSizing:
        """
        Calcula el tamaño óptimo de posición usando múltiples métodos
        """
        # 1. Tamaño base (% de riesgo fijo)
        risk_amount = self.current_capital * self.max_risk_per_trade
        price_risk = abs(entry_price - stop_loss)
        # Calcular tamaño en unidades monetarias, no lotes
        base_size = risk_amount / price_risk if price_risk > 0 else 100
        # Convertir a lotes (asumiendo 100,000 unidades por lote para Forex)
        if 'USD' in symbol:
            base_size = base_size / 100000  # Para forex
        else:
            base_size = base_size / entry_price  # Para otros activos
        
        # 2. Kelly sizing
        kelly_size = base_size
        if self.use_kelly and len(self.trade_history) >= 10:
            recent_trades = self.trade_history[-50:]
            wins = [t['pnl'] for t in recent_trades if t['pnl'] > 0]
            losses = [t['pnl'] for t in recent_trades if t['pnl'] <= 0]
            
            if wins and losses:
                win_rate = len(wins) / len(recent_trades)
                avg_win = np.mean(wins)
                avg_loss = abs(np.mean(losses))
                
                kelly_fraction = self.calculate_kelly_criterion(win_rate, avg_win, avg_loss)
                kelly_size = base_size * (kelly_fraction / self.max_risk_per_trade)
        
        # 3. VaR adjusted sizing
        var_size = base_size
        if len(self.daily_returns) >= 20:
            var_95, cvar = self.calculate_var(self.daily_returns, 0.95)
            var_adjustment = max(0.5, 1 - abs(var_95))
            var_size = base_size * var_adjustment
        
        # 4. Volatility adjusted sizing
        # Reducir tamaño en alta volatilidad
        vol_adjustment = max(0.3, 1 - (volatility / 100))
        volatility_size = base_size * vol_adjustment
        
        # 5. Correlation adjusted sizing
        # Reducir si hay alta correlación con posiciones existentes
        corr_adjustment = max(0.5, 1 - abs(correlation_with_portfolio))
        correlation_size = base_size * corr_adjustment
        
        # 6. Ajuste por confianza
        confidence_adjustment = 0.5 + (confidence / 200)  # 0.5 a 1.0
        
        # Calcular tamaño final (promedio ponderado)
        weights = {
            'base': 0.2,
            'kelly': 0.25 if self.use_kelly else 0,
            'var': 0.15,
            'volatility': 0.2,
            'correlation': 0.1,
            'confidence': 0.1
        }
        
        # Normalizar pesos
        total_weight = sum(weights.values())
        weights = {k: v/total_weight for k, v in weights.items()}
        
        final_size = (
            base_size * weights['base'] +
            kelly_size * weights['kelly'] +
            var_size * weights['var'] +
            volatility_size * weights['volatility'] +
            correlation_size * weights['correlation']
        ) * confidence_adjustment
        
        # Aplicar límites según régimen de mercado
        if self.market_regime == 'bear':
            final_size *= 0.7
        elif self.market_regime == 'volatile':
            final_size *= 0.5
        elif self.market_regime == 'bull':
            final_size *= 1.1
        
        # Límites absolutos
        min_size = 0.01
        max_size = 5.0  # Max 5 lotes
        final_size = max(min_size, min(max_size, final_size))
        
        # Calcular leverage efectivo
        position_value = final_size * entry_price
        leverage = position_value / self.current_capital
        
        return PositionSizing(
            base_size=round(base_size, 2),
            kelly_size=round(kelly_size, 2),
            var_adjusted_size=round(var_size, 2),
            volatility_adjusted_size=round(volatility_size, 2),
            correlation_adjusted_size=round(correlation_size, 2),
            final_size=round(final_size, 2),
            max_size=round(max_size, 2),
            min_size=min_size,
            leverage=round(leverage, 2)
        )
    
    def check_risk_limits(self) -> Dict[str, Any]:
        """
        Verifica todos los límites de riesgo
        """
        checks = {
            'can_trade': True,
            'warnings': [],
            'blocks': []
        }
        
        # Check daily loss limit
        if abs(self.daily_pnl) > self.daily_loss_limit:
            checks['can_trade'] = False
            checks['blocks'].append(f"Daily loss limit exceeded: ${abs(self.daily_pnl):.2f}")
        
        # Check weekly loss limit
        if abs(self.weekly_pnl) > self.weekly_loss_limit:
            checks['can_trade'] = False
            checks['blocks'].append(f"Weekly loss limit exceeded: ${abs(self.weekly_pnl):.2f}")
        
        # Check consecutive losses
        if self.consecutive_losses >= 3:
            checks['warnings'].append(f"Consecutive losses: {self.consecutive_losses}")
            if self.consecutive_losses >= 5:
                checks['can_trade'] = False
                checks['blocks'].append("Max consecutive losses reached")
        
        # Check drawdown
        current_drawdown = self.calculate_drawdown()
        if current_drawdown > 0.10:
            checks['warnings'].append(f"High drawdown: {current_drawdown:.2%}")
            if current_drawdown > 0.15:
                checks['can_trade'] = False
                checks['blocks'].append(f"Max drawdown exceeded: {current_drawdown:.2%}")
        
        # Check portfolio concentration
        if len(self.open_positions) >= 5:
            checks['warnings'].append("High number of open positions")
            if len(self.open_positions) >= 7:
                checks['can_trade'] = False
                checks['blocks'].append("Max positions reached")
        
        # Check margin/leverage
        total_exposure = sum(p['size'] * p['entry_price'] for p in self.open_positions)
        leverage = total_exposure / self.current_capital if self.current_capital > 0 else 0
        
        if leverage > 2:
            checks['warnings'].append(f"High leverage: {leverage:.2f}x")
            if leverage > 3:
                checks['can_trade'] = False
                checks['blocks'].append(f"Max leverage exceeded: {leverage:.2f}x")
        
        return checks
    
    def calculate_portfolio_correlation(self, 
                                       symbol: str,
                                       new_position_direction: str) -> float:
        """
        Calcula la correlación de una nueva posición con el portfolio existente
        """
        if not self.open_positions:
            return 0
        
        # Simplificación: usar correlaciones predefinidas
        correlations = {
            ('XAUUSD', 'EURUSD'): -0.3,
            ('XAUUSD', 'GBPUSD'): -0.2,
            ('XAUUSD', 'BTCUSD'): 0.4,
            ('EURUSD', 'GBPUSD'): 0.7,
            ('EURUSD', 'USDJPY'): -0.5,
            ('BTCUSD', 'ETHUSD'): 0.8
        }
        
        total_correlation = 0
        for position in self.open_positions:
            pair = tuple(sorted([symbol, position['symbol']]))
            corr = correlations.get(pair, 0)
            
            # Ajustar por dirección
            if position['direction'] != new_position_direction:
                corr *= -1
            
            total_correlation += abs(corr)
        
        # Normalizar
        return min(1.0, total_correlation / len(self.open_positions))
    
    def calculate_drawdown(self) -> float:
        """Calcula el drawdown actual"""
        if not self.equity_curve:
            return 0
        
        peak = max(self.equity_curve)
        current = self.current_capital
        drawdown = (peak - current) / peak if peak > 0 else 0
        
        return drawdown
    
    def update_market_regime(self, 
                            volatility: float,
                            trend_strength: float,
                            volume_ratio: float):
        """
        Actualiza el régimen de mercado basado en indicadores
        """
        # Determinar régimen de volatilidad
        if volatility > 50:
            self.volatility_regime = 'high'
        elif volatility < 20:
            self.volatility_regime = 'low'
        else:
            self.volatility_regime = 'normal'
        
        # Determinar régimen de mercado
        if trend_strength > 30 and volume_ratio > 1.5:
            self.market_regime = 'bull' if trend_strength > 0 else 'bear'
        elif volatility > 40:
            self.market_regime = 'volatile'
        else:
            self.market_regime = 'sideways'
        
        logger.info(f"Market regime updated: {self.market_regime} (vol: {self.volatility_regime})")
    
    def calculate_risk_metrics(self) -> RiskMetrics:
        """
        Calcula todas las métricas de riesgo del portfolio
        """
        if len(self.trade_history) < 10:
            return RiskMetrics(
                var_95=0, var_99=0, cvar=0,
                sharpe_ratio=0, sortino_ratio=0, calmar_ratio=0,
                max_drawdown=0, current_drawdown=0,
                win_rate=0, profit_factor=0, recovery_factor=0,
                kelly_fraction=self.min_kelly,
                optimal_position_size=0.01,
                risk_score=50,
                market_regime=self.market_regime
            )
        
        # Calcular returns
        returns = [t['pnl_pct'] for t in self.trade_history]
        positive_returns = [r for r in returns if r > 0]
        negative_returns = [r for r in returns if r < 0]
        
        # VaR y CVaR
        var_95, cvar_95 = self.calculate_var(returns, 0.95)
        var_99, cvar_99 = self.calculate_var(returns, 0.99)
        
        # Sharpe Ratio
        if len(returns) > 0:
            avg_return = np.mean(returns)
            std_return = np.std(returns)
            sharpe_ratio = (avg_return / std_return) * np.sqrt(252) if std_return > 0 else 0
        else:
            sharpe_ratio = 0
        
        # Sortino Ratio
        if negative_returns:
            downside_std = np.std(negative_returns)
            sortino_ratio = (avg_return / downside_std) * np.sqrt(252) if downside_std > 0 else 0
        else:
            sortino_ratio = sharpe_ratio
        
        # Calmar Ratio
        max_dd = self.calculate_max_drawdown()
        calmar_ratio = (avg_return * 252) / max_dd if max_dd > 0 else 0
        
        # Win Rate y Profit Factor
        win_rate = len(positive_returns) / len(returns) if returns else 0
        
        if positive_returns and negative_returns:
            profit_factor = sum(positive_returns) / abs(sum(negative_returns))
        else:
            profit_factor = 1
        
        # Recovery Factor
        total_profit = self.current_capital - self.initial_capital
        recovery_factor = total_profit / max_dd if max_dd > 0 else 0
        
        # Kelly Fraction
        if positive_returns and negative_returns:
            avg_win = np.mean(positive_returns)
            avg_loss = abs(np.mean(negative_returns))
            kelly_fraction = self.calculate_kelly_criterion(win_rate, avg_win, avg_loss)
        else:
            kelly_fraction = self.min_kelly
        
        # Risk Score (0-100, donde 0 es máximo riesgo)
        risk_score = self.calculate_risk_score(
            var_95, sharpe_ratio, max_dd, win_rate, self.consecutive_losses
        )
        
        return RiskMetrics(
            var_95=var_95,
            var_99=var_99,
            cvar=cvar_95,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            max_drawdown=max_dd,
            current_drawdown=self.calculate_drawdown(),
            win_rate=win_rate,
            profit_factor=profit_factor,
            recovery_factor=recovery_factor,
            kelly_fraction=kelly_fraction,
            optimal_position_size=kelly_fraction * self.current_capital,
            risk_score=risk_score,
            market_regime=self.market_regime
        )
    
    def calculate_max_drawdown(self) -> float:
        """Calcula el máximo drawdown histórico"""
        if len(self.equity_curve) < 2:
            return 0
        
        peak = self.equity_curve[0]
        max_dd = 0
        
        for value in self.equity_curve[1:]:
            if value > peak:
                peak = value
            else:
                dd = (peak - value) / peak
                max_dd = max(max_dd, dd)
        
        return max_dd
    
    def calculate_risk_score(self,
                            var: float,
                            sharpe: float,
                            max_dd: float,
                            win_rate: float,
                            consecutive_losses: int) -> float:
        """
        Calcula un score de riesgo de 0-100
        100 = Riesgo muy bajo, 0 = Riesgo muy alto
        """
        score = 50  # Base
        
        # Ajustar por VaR (±20 puntos)
        if var < 0.02:
            score += 20
        elif var < 0.05:
            score += 10
        elif var > 0.10:
            score -= 10
        elif var > 0.15:
            score -= 20
        
        # Ajustar por Sharpe (±15 puntos)
        if sharpe > 2:
            score += 15
        elif sharpe > 1:
            score += 7
        elif sharpe < 0:
            score -= 7
        elif sharpe < -1:
            score -= 15
        
        # Ajustar por Drawdown (±15 puntos)
        if max_dd < 0.05:
            score += 15
        elif max_dd < 0.10:
            score += 7
        elif max_dd > 0.20:
            score -= 7
        elif max_dd > 0.30:
            score -= 15
        
        # Ajustar por Win Rate (±10 puntos)
        if win_rate > 0.60:
            score += 10
        elif win_rate > 0.50:
            score += 5
        elif win_rate < 0.40:
            score -= 5
        elif win_rate < 0.30:
            score -= 10
        
        # Ajustar por consecutive losses (±10 puntos)
        if consecutive_losses == 0:
            score += 10
        elif consecutive_losses < 3:
            score += 5
        elif consecutive_losses > 5:
            score -= 10
        
        # Limitar entre 0 y 100
        return max(0, min(100, score))
    
    def generate_risk_report(self) -> str:
        """Genera un reporte completo de riesgo"""
        metrics = self.calculate_risk_metrics()
        risk_checks = self.check_risk_limits()
        
        report = f"""
ELITE RISK MANAGEMENT REPORT
=============================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

PORTFOLIO STATUS:
-----------------
Current Capital: ${self.current_capital:,.2f}
Initial Capital: ${self.initial_capital:,.2f}
Total P&L: ${self.current_capital - self.initial_capital:,.2f}
ROI: {((self.current_capital / self.initial_capital - 1) * 100):.2f}%

RISK METRICS:
-------------
VaR (95%): {metrics.var_95:.2%}
VaR (99%): {metrics.var_99:.2%}
CVaR: {metrics.cvar:.2%}
Max Drawdown: {metrics.max_drawdown:.2%}
Current Drawdown: {metrics.current_drawdown:.2%}

PERFORMANCE METRICS:
-------------------
Sharpe Ratio: {metrics.sharpe_ratio:.2f}
Sortino Ratio: {metrics.sortino_ratio:.2f}
Calmar Ratio: {metrics.calmar_ratio:.2f}
Win Rate: {metrics.win_rate:.2%}
Profit Factor: {metrics.profit_factor:.2f}
Recovery Factor: {metrics.recovery_factor:.2f}

POSITION SIZING:
---------------
Kelly Fraction: {metrics.kelly_fraction:.2%}
Optimal Position Size: ${metrics.optimal_position_size:.2f}

MARKET CONDITIONS:
-----------------
Market Regime: {metrics.market_regime}
Volatility Regime: {self.volatility_regime}
Risk Score: {metrics.risk_score}/100

RISK LIMITS STATUS:
------------------
Can Trade: {risk_checks['can_trade']}
Open Positions: {len(self.open_positions)}
Consecutive Losses: {self.consecutive_losses}

WARNINGS:
{chr(10).join('- ' + w for w in risk_checks['warnings']) if risk_checks['warnings'] else 'None'}

BLOCKS:
{chr(10).join('- ' + b for b in risk_checks['blocks']) if risk_checks['blocks'] else 'None'}
"""
        
        return report
    
    def save_state(self, filepath: str = 'data/risk_state.json'):
        """Guarda el estado del risk manager"""
        state = {
            'timestamp': datetime.now().isoformat(),
            'current_capital': self.current_capital,
            'open_positions': self.open_positions,
            'trade_history': self.trade_history[-100:],  # Últimos 100 trades
            'equity_curve': self.equity_curve[-1000:],  # Últimos 1000 puntos
            'market_regime': self.market_regime,
            'volatility_regime': self.volatility_regime,
            'consecutive_losses': self.consecutive_losses,
            'daily_pnl': self.daily_pnl,
            'weekly_pnl': self.weekly_pnl,
            'monthly_pnl': self.monthly_pnl
        }
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2, default=str)
        
        logger.info(f"Risk state saved to {filepath}")
    
    def load_state(self, filepath: str = 'data/risk_state.json'):
        """Carga el estado del risk manager"""
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                state = json.load(f)
            
            self.current_capital = state.get('current_capital', self.initial_capital)
            self.open_positions = state.get('open_positions', [])
            self.trade_history = state.get('trade_history', [])
            self.equity_curve = state.get('equity_curve', [self.initial_capital])
            self.market_regime = state.get('market_regime', 'normal')
            self.volatility_regime = state.get('volatility_regime', 'normal')
            self.consecutive_losses = state.get('consecutive_losses', 0)
            self.daily_pnl = state.get('daily_pnl', 0)
            self.weekly_pnl = state.get('weekly_pnl', 0)
            self.monthly_pnl = state.get('monthly_pnl', 0)
            
            logger.info(f"Risk state loaded from {filepath}")
        else:
            logger.warning(f"Risk state file not found: {filepath}")