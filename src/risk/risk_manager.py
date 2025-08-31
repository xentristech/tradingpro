"""
Risk Manager - Gestor Avanzado de Riesgo
Implementa gestión de riesgo profesional con múltiples técnicas
Version: 3.0.0
"""
import logging
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class RiskMetrics:
    """Métricas de riesgo del portfolio"""
    current_risk: float          # Riesgo actual en %
    max_risk: float              # Riesgo máximo permitido
    open_positions: int          # Número de posiciones abiertas
    total_exposure: float        # Exposición total en $
    daily_loss: float           # Pérdida del día
    max_daily_loss: float       # Máxima pérdida diaria permitida
    consecutive_losses: int      # Pérdidas consecutivas
    sharpe_ratio: float         # Ratio de Sharpe
    max_drawdown: float         # Drawdown máximo
    win_rate: float            # Tasa de acierto
    risk_reward_ratio: float    # Ratio riesgo/beneficio

class RiskManager:
    """
    Gestor profesional de riesgo para trading algorítmico
    Implementa: Kelly Criterion, VaR, Position Sizing, Risk Limits
    """
    
    def __init__(self,
                 initial_capital: float = 10000,
                 risk_per_trade: float = 0.01,
                 max_risk: float = 0.06,
                 max_drawdown: float = 0.20):
        """
        Inicializa el gestor de riesgo
        Args:
            initial_capital: Capital inicial
            risk_per_trade: Riesgo por operación (1% = 0.01)
            max_risk: Riesgo máximo total
            max_drawdown: Drawdown máximo permitido
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.risk_per_trade = risk_per_trade
        self.max_risk = max_risk
        self.max_drawdown = max_drawdown
        
        # Límites de riesgo
        self.max_daily_loss = 0.05  # 5% pérdida diaria máxima
        self.max_consecutive_losses = 5
        self.max_positions = 3
        self.correlation_threshold = 0.7
        
        # Estado del portfolio
        self.open_positions = []
        self.closed_positions = []
        self.daily_pnl = 0.0
        self.consecutive_losses = 0
        self.last_trade_date = None
        
        # Métricas históricas
        self.equity_curve = [initial_capital]
        self.returns = []
        
        # Archivo de persistencia
        self.state_file = Path('storage/risk_state.json')
        self.load_state()
        
        logger.info(f"RiskManager inicializado - Capital: ${initial_capital:.2f}, Risk/Trade: {risk_per_trade*100:.1f}%")
    
    def evaluate_trade(self,
                       symbol: str,
                       signal_strength: str,
                       current_positions: int = 0,
                       max_positions: int = 1) -> Dict:
        """
        Evalúa si se puede abrir una nueva operación
        Args:
            symbol: Símbolo a operar
            signal_strength: Fuerza de la señal
            current_positions: Posiciones actuales
            max_positions: Máximo de posiciones permitidas
        Returns:
            Dict con evaluación de riesgo
        """
        assessment = {
            'trade_allowed': False,
            'reason': '',
            'risk_score': 0.0,
            'position_size': 0.0,
            'max_loss': 0.0
        }
        
        # Verificar límites básicos
        if current_positions >= max_positions:
            assessment['reason'] = f"Máximo de posiciones alcanzado ({max_positions})"
            return assessment
        
        # Verificar drawdown
        current_drawdown = self._calculate_drawdown()
        if current_drawdown > self.max_drawdown:
            assessment['reason'] = f"Drawdown excedido: {current_drawdown:.1%} > {self.max_drawdown:.1%}"
            return assessment
        
        # Verificar pérdida diaria
        if abs(self.daily_pnl) > self.current_capital * self.max_daily_loss:
            assessment['reason'] = f"Límite diario alcanzado: ${self.daily_pnl:.2f}"
            return assessment
        
        # Verificar rachas de pérdidas
        if self.consecutive_losses >= self.max_consecutive_losses:
            assessment['reason'] = f"Racha de {self.consecutive_losses} pérdidas consecutivas"
            return assessment
        
        # Calcular riesgo dinámico basado en performance
        dynamic_risk = self._calculate_dynamic_risk(signal_strength)
        
        # Calcular tamaño de posición
        position_size = self._calculate_position_size_kelly(
            win_rate=self._get_win_rate(),
            avg_win=self._get_avg_win(),
            avg_loss=self._get_avg_loss()
        )
        
        # Verificar correlación con posiciones existentes
        if self.open_positions:
            correlation_risk = self._check_correlation_risk(symbol)
            if correlation_risk > self.correlation_threshold:
                position_size *= 0.5  # Reducir tamaño si hay alta correlación
        
        # Evaluación final
        risk_score = self._calculate_risk_score(
            signal_strength=signal_strength,
            market_conditions=self._assess_market_conditions(),
            portfolio_heat=current_positions / max_positions
        )
        
        if risk_score > 0.3:  # Umbral mínimo de confianza
            assessment['trade_allowed'] = True
            assessment['reason'] = 'Condiciones de riesgo aceptables'
            assessment['risk_score'] = risk_score
            assessment['position_size'] = position_size
            assessment['max_loss'] = self.current_capital * dynamic_risk
        else:
            assessment['reason'] = f'Score de riesgo insuficiente: {risk_score:.2f}'
        
        return assessment
    
    def calculate_position_size(self,
                              symbol: str,
                              stop_loss_pips: float,
                              account_balance: Optional[float] = None) -> float:
        """
        Calcula el tamaño de posición basado en riesgo fijo
        Args:
            symbol: Símbolo a operar
            stop_loss_pips: Stop loss en pips
            account_balance: Balance de cuenta (None = usar actual)
        Returns:
            Tamaño de posición en lotes
        """
        if account_balance is None:
            account_balance = self.current_capital
        
        # Riesgo en dinero
        risk_amount = account_balance * self.risk_per_trade
        
        # Valor del pip (simplificado, debería obtenerse del broker)
        pip_value = 10  # USD por pip para 1 lote estándar
        
        # Calcular lotes
        if stop_loss_pips > 0:
            lots = risk_amount / (stop_loss_pips * pip_value)
        else:
            lots = 0.01  # Mínimo
        
        # Aplicar límites
        lots = max(0.01, min(lots, 2.0))  # Entre 0.01 y 2.0 lotes
        
        return round(lots, 2)
    
    def _calculate_position_size_kelly(self,
                                      win_rate: float,
                                      avg_win: float,
                                      avg_loss: float) -> float:
        """
        Calcula tamaño óptimo usando Kelly Criterion
        Kelly % = (p * b - q) / b
        donde:
            p = probabilidad de ganar
            q = probabilidad de perder (1-p)
            b = ratio ganancia/pérdida
        """
        if avg_loss == 0 or win_rate == 0:
            return 0.01  # Tamaño mínimo
        
        p = win_rate
        q = 1 - win_rate
        b = abs(avg_win / avg_loss) if avg_loss != 0 else 1
        
        # Kelly completo
        kelly_pct = (p * b - q) / b if b > 0 else 0
        
        # Aplicar fracción de Kelly (25% para ser conservador)
        kelly_fraction = 0.25
        position_pct = kelly_pct * kelly_fraction
        
        # Limitar entre 0.5% y 3%
        position_pct = max(0.005, min(position_pct, 0.03))
        
        # Convertir a lotes (simplificado)
        position_size = position_pct * 100  # Asumiendo 1% = 1 lote
        
        return round(position_size, 2)
    
    def _calculate_dynamic_risk(self, signal_strength: str) -> float:
        """
        Calcula riesgo dinámico basado en condiciones
        Args:
            signal_strength: Fuerza de la señal
        Returns:
            Porcentaje de riesgo ajustado
        """
        base_risk = self.risk_per_trade
        
        # Ajustar por performance reciente
        if self.consecutive_losses > 2:
            base_risk *= 0.5  # Reducir riesgo en mala racha
        elif self._get_win_rate() > 0.6 and len(self.returns) > 10:
            base_risk *= 1.2  # Aumentar ligeramente en buena racha
        
        # Ajustar por fuerza de señal
        signal_multipliers = {
            'strong': 1.2,
            'moderate': 1.0,
            'weak': 0.7,
            'neutral': 0.0
        }
        
        signal_mult = signal_multipliers.get(signal_strength, 0.8)
        adjusted_risk = base_risk * signal_mult
        
        # Ajustar por volatilidad del mercado
        market_vol = self._get_market_volatility()
        if market_vol > 0.03:  # Alta volatilidad (>3%)
            adjusted_risk *= 0.8
        elif market_vol < 0.01:  # Baja volatilidad (<1%)
            adjusted_risk *= 1.1
        
        # Limitar riesgo final
        return max(0.005, min(adjusted_risk, self.max_risk))
    
    def _calculate_drawdown(self) -> float:
        """
        Calcula el drawdown actual
        Returns:
            Drawdown como porcentaje
        """
        if not self.equity_curve:
            return 0.0
        
        peak = max(self.equity_curve)
        current = self.current_capital
        
        if peak > 0:
            drawdown = (peak - current) / peak
            return max(0, drawdown)
        
        return 0.0
    
    def _get_win_rate(self) -> float:
        """
        Calcula la tasa de acierto histórica
        Returns:
            Win rate entre 0 y 1
        """
        if not self.closed_positions:
            return 0.5  # Default 50%
        
        wins = sum(1 for p in self.closed_positions if p.get('pnl', 0) > 0)
        total = len(self.closed_positions)
        
        return wins / total if total > 0 else 0.5
    
    def _get_avg_win(self) -> float:
        """
        Calcula la ganancia promedio
        Returns:
            Ganancia promedio en $
        """
        wins = [p['pnl'] for p in self.closed_positions if p.get('pnl', 0) > 0]
        return np.mean(wins) if wins else 100
    
    def _get_avg_loss(self) -> float:
        """
        Calcula la pérdida promedio
        Returns:
            Pérdida promedio en $ (valor positivo)
        """
        losses = [abs(p['pnl']) for p in self.closed_positions if p.get('pnl', 0) < 0]
        return np.mean(losses) if losses else 50
    
    def _check_correlation_risk(self, symbol: str) -> float:
        """
        Verifica correlación con posiciones existentes
        Args:
            symbol: Nuevo símbolo a evaluar
        Returns:
            Score de correlación (0 a 1)
        """
        # Simplificado: considera todos los cripto altamente correlacionados
        crypto_symbols = ['BTC', 'ETH', 'SOL', 'BNB']
        
        for position in self.open_positions:
            pos_symbol = position.get('symbol', '')
            
            # Si ambos son cripto, alta correlación
            if any(c in symbol for c in crypto_symbols) and any(c in pos_symbol for c in crypto_symbols):
                return 0.8
        
        return 0.2  # Baja correlación por defecto
    
    def _assess_market_conditions(self) -> str:
        """
        Evalúa las condiciones generales del mercado
        Returns:
            'favorable', 'neutral', o 'adverse'
        """
        # Implementación simplificada
        # En producción, esto analizaría VIX, correlaciones, etc.
        
        volatility = self._get_market_volatility()
        
        if volatility < 0.015:
            return 'favorable'
        elif volatility < 0.025:
            return 'neutral'
        else:
            return 'adverse'
    
    def _get_market_volatility(self) -> float:
        """
        Obtiene volatilidad del mercado
        Returns:
            Volatilidad estimada
        """
        # Implementación simplificada
        # En producción, calcularía volatilidad real de los datos
        return 0.02  # 2% volatilidad por defecto
    
    def _calculate_risk_score(self,
                             signal_strength: str,
                             market_conditions: str,
                             portfolio_heat: float) -> float:
        """
        Calcula score de riesgo consolidado
        Args:
            signal_strength: Fuerza de señal
            market_conditions: Condiciones del mercado
            portfolio_heat: Uso del portfolio (0 a 1)
        Returns:
            Score de riesgo (0 a 1)
        """
        # Puntajes base
        signal_scores = {
            'buy': 0.6,
            'sell': 0.6,
            'strong': 0.8,
            'moderate': 0.5,
            'weak': 0.3,
            'neutral': 0.0
        }
        
        market_scores = {
            'favorable': 0.8,
            'neutral': 0.5,
            'adverse': 0.2
        }
        
        signal_score = signal_scores.get(signal_strength, 0.4)
        market_score = market_scores.get(market_conditions, 0.5)
        portfolio_score = 1.0 - (portfolio_heat * 0.5)  # Penalizar portfolios muy cargados
        
        # Score ponderado
        final_score = (signal_score * 0.5 + 
                      market_score * 0.3 + 
                      portfolio_score * 0.2)
        
        return min(1.0, max(0.0, final_score))
    
    def update_position(self, position: Dict):
        """
        Actualiza una posición
        Args:
            position: Datos de la posición
        """
        # Buscar y actualizar posición existente
        for i, pos in enumerate(self.open_positions):
            if pos.get('id') == position.get('id'):
                self.open_positions[i] = position
                return
        
        # Si no existe, agregarla
        self.open_positions.append(position)
    
    def close_position(self, position_id: str, pnl: float):
        """
        Cierra una posición y actualiza métricas
        Args:
            position_id: ID de la posición
            pnl: Ganancia/pérdida
        """
        # Mover de abiertas a cerradas
        position = None
        for i, pos in enumerate(self.open_positions):
            if pos.get('id') == position_id:
                position = self.open_positions.pop(i)
                break
        
        if position:
            position['pnl'] = pnl
            position['close_time'] = datetime.now().isoformat()
            self.closed_positions.append(position)
            
            # Actualizar capital
            self.current_capital += pnl
            self.equity_curve.append(self.current_capital)
            
            # Actualizar métricas
            self.daily_pnl += pnl
            
            if pnl < 0:
                self.consecutive_losses += 1
            else:
                self.consecutive_losses = 0
            
            # Calcular retorno
            if self.current_capital > 0:
                return_pct = pnl / self.current_capital
                self.returns.append(return_pct)
            
            logger.info(f"Position {position_id} closed - PnL: ${pnl:.2f}")
    
    def get_risk_metrics(self) -> RiskMetrics:
        """
        Obtiene métricas actuales de riesgo
        Returns:
            RiskMetrics con todas las métricas
        """
        total_exposure = sum(p.get('size', 0) * p.get('price', 0) 
                           for p in self.open_positions)
        
        current_risk = total_exposure / self.current_capital if self.current_capital > 0 else 0
        
        # Calcular Sharpe Ratio
        if len(self.returns) > 1:
            returns_array = np.array(self.returns)
            sharpe = np.mean(returns_array) / np.std(returns_array) * np.sqrt(252) if np.std(returns_array) > 0 else 0
        else:
            sharpe = 0
        
        # Calcular risk/reward ratio
        avg_win = self._get_avg_win()
        avg_loss = self._get_avg_loss()
        risk_reward = avg_win / avg_loss if avg_loss > 0 else 1
        
        return RiskMetrics(
            current_risk=current_risk,
            max_risk=self.max_risk,
            open_positions=len(self.open_positions),
            total_exposure=total_exposure,
            daily_loss=self.daily_pnl,
            max_daily_loss=self.current_capital * self.max_daily_loss,
            consecutive_losses=self.consecutive_losses,
            sharpe_ratio=sharpe,
            max_drawdown=self._calculate_drawdown(),
            win_rate=self._get_win_rate(),
            risk_reward_ratio=risk_reward
        )
    
    def reset_daily_metrics(self):
        """Resetea métricas diarias"""
        self.daily_pnl = 0.0
        self.last_trade_date = datetime.now().date()
        logger.info("Métricas diarias reseteadas")
    
    def save_state(self):
        """Guarda el estado actual en archivo"""
        state = {
            'current_capital': self.current_capital,
            'open_positions': self.open_positions,
            'closed_positions': self.closed_positions[-100:],  # Últimas 100
            'equity_curve': self.equity_curve[-1000:],  # Últimos 1000 puntos
            'returns': self.returns[-500:],  # Últimos 500 retornos
            'consecutive_losses': self.consecutive_losses,
            'daily_pnl': self.daily_pnl,
            'last_trade_date': self.last_trade_date.isoformat() if self.last_trade_date else None
        }
        
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
            logger.debug("Estado guardado")
        except Exception as e:
            logger.error(f"Error guardando estado: {e}")
    
    def load_state(self):
        """Carga el estado desde archivo"""
        if not self.state_file.exists():
            return
        
        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)
            
            self.current_capital = state.get('current_capital', self.initial_capital)
            self.open_positions = state.get('open_positions', [])
            self.closed_positions = state.get('closed_positions', [])
            self.equity_curve = state.get('equity_curve', [self.initial_capital])
            self.returns = state.get('returns', [])
            self.consecutive_losses = state.get('consecutive_losses', 0)
            self.daily_pnl = state.get('daily_pnl', 0)
            
            last_date = state.get('last_trade_date')
            if last_date:
                self.last_trade_date = datetime.fromisoformat(last_date).date()
            
            logger.info("Estado cargado desde archivo")
            
        except Exception as e:
            logger.error(f"Error cargando estado: {e}")

# Testing
if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Crear risk manager
    rm = RiskManager(
        initial_capital=10000,
        risk_per_trade=0.01,
        max_risk=0.06,
        max_drawdown=0.20
    )
    
    # Simular evaluación de trade
    print("\n📊 EVALUACIÓN DE RIESGO:")
    assessment = rm.evaluate_trade(
        symbol='BTCUSD',
        signal_strength='strong',
        current_positions=0,
        max_positions=3
    )
    
    print(f"Trade permitido: {assessment['trade_allowed']}")
    print(f"Razón: {assessment['reason']}")
    print(f"Score de riesgo: {assessment['risk_score']:.2f}")
    print(f"Tamaño posición: {assessment['position_size']:.2f} lotes")
    print(f"Pérdida máxima: ${assessment['max_loss']:.2f}")
    
    # Obtener métricas
    print("\n📈 MÉTRICAS DE RIESGO:")
    metrics = rm.get_risk_metrics()
    print(f"Riesgo actual: {metrics.current_risk:.1%}")
    print(f"Posiciones abiertas: {metrics.open_positions}")
    print(f"Win rate: {metrics.win_rate:.1%}")
    print(f"Sharpe ratio: {metrics.sharpe_ratio:.2f}")
    print(f"Max drawdown: {metrics.max_drawdown:.1%}")
    print(f"Risk/Reward: {metrics.risk_reward_ratio:.2f}")
    
    # Guardar estado
    rm.save_state()
    print("\n✅ Estado guardado")
