"""
Sistema de Gestión de Riesgo Adaptativo
Ajusta automáticamente según las condiciones del mercado
Author: XentrisTech
Version: 2.0
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import logging
import json
import os

logger = logging.getLogger(__name__)

@dataclass
class RiskParameters:
    """Parámetros de riesgo dinámicos"""
    position_size: float
    stop_loss: float
    take_profit: float
    max_drawdown: float
    risk_per_trade: float
    confidence_level: float
    risk_reward_ratio: float
    entry_price: float
    
    def to_dict(self) -> Dict:
        """Convierte a diccionario"""
        return {
            'position_size': self.position_size,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'max_drawdown': self.max_drawdown,
            'risk_per_trade': self.risk_per_trade,
            'confidence_level': self.confidence_level,
            'risk_reward_ratio': self.risk_reward_ratio,
            'entry_price': self.entry_price
        }

@dataclass
class TradeResult:
    """Resultado de una operación"""
    symbol: str
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    position_size: float
    direction: str  # 'buy' o 'sell'
    pnl: float
    pnl_pct: float
    balance_after: float
    
    def to_dict(self) -> Dict:
        return {
            'symbol': self.symbol,
            'entry_time': self.entry_time.isoformat(),
            'exit_time': self.exit_time.isoformat(),
            'entry_price': self.entry_price,
            'exit_price': self.exit_price,
            'position_size': self.position_size,
            'direction': self.direction,
            'pnl': self.pnl,
            'pnl_pct': self.pnl_pct,
            'balance_after': self.balance_after
        }

class AdaptiveRiskManager:
    """
    Gestor de riesgo que se adapta a las condiciones del mercado
    """
    
    def __init__(self, 
                 account_balance: float,
                 base_risk_pct: float = 0.01,
                 max_risk_pct: float = 0.03,
                 max_positions: int = 3,
                 data_file: str = 'data/risk_history.json'):
        
        self.initial_balance = account_balance
        self.account_balance = account_balance
        self.base_risk_pct = base_risk_pct
        self.max_risk_pct = max_risk_pct
        self.max_positions = max_positions
        self.data_file = data_file
        
        # Estado actual
        self.open_positions = []
        self.trade_history = []
        
        # Métricas de performance
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = 0
        self.max_drawdown = 0
        self.current_drawdown = 0
        self.peak_balance = account_balance
        
        # Parámetros adaptativos
        self.volatility_multiplier = 1.0
        self.win_rate = 0.5
        self.avg_win_loss_ratio = 1.0
        self.confidence_multiplier = 1.0
        
        # Cargar historial si existe
        self._load_history()
        
    def calculate_dynamic_position_size(self,
                                       entry_price: float,
                                       stop_loss: float,
                                       market_conditions: Dict[str, any],
                                       symbol: str = 'BTCUSD') -> RiskParameters:
        """
        Calcula el tamaño de posición dinámico basado en:
        - Volatilidad actual
        - Win rate histórico
        - Drawdown actual
        - Condiciones del mercado
        - Correlación con posiciones abiertas
        """
        
        # Validar inputs
        if entry_price <= 0 or stop_loss <= 0:
            logger.error(f"Precios inválidos: entry={entry_price}, stop={stop_loss}")
            return self._get_default_parameters(entry_price)
        
        # 1. Calcular riesgo base ajustado
        risk_adjustments = []
        
        # Ajuste por volatilidad
        volatility_adjustment = self._adjust_for_volatility(market_conditions)
        risk_adjustments.append(('Volatilidad', volatility_adjustment))
        
        # Ajuste por performance
        performance_adjustment = self._adjust_for_performance()
        risk_adjustments.append(('Performance', performance_adjustment))
        
        # Ajuste por drawdown
        drawdown_adjustment = self._adjust_for_drawdown()
        risk_adjustments.append(('Drawdown', drawdown_adjustment))
        
        # Ajuste por condiciones del mercado
        market_adjustment = self._adjust_for_market_conditions(market_conditions)
        risk_adjustments.append(('Mercado', market_adjustment))
        
        # Ajuste por correlación con posiciones abiertas
        correlation_adjustment = self._adjust_for_correlation(symbol)
        risk_adjustments.append(('Correlación', correlation_adjustment))
        
        # Calcular riesgo final
        total_adjustment = 1.0
        for name, adj in risk_adjustments:
            total_adjustment *= adj
            logger.debug(f"Ajuste {name}: {adj:.2f}")
        
        final_risk_pct = self.base_risk_pct * total_adjustment
        
        # Aplicar límites
        final_risk_pct = max(self.base_risk_pct * 0.5, min(final_risk_pct, self.max_risk_pct))
        
        # Calcular tamaño de posición
        risk_amount = self.account_balance * final_risk_pct
        stop_distance = abs(entry_price - stop_loss)
        
        if stop_distance == 0:
            logger.warning("Stop distance es 0, usando 1% default")
            stop_distance = entry_price * 0.01
        
        # Tamaño de posición en unidades del activo
        position_size = risk_amount / stop_distance
        
        # Ajustar por número de posiciones abiertas
        if len(self.open_positions) >= self.max_positions:
            logger.warning(f"Máximo de posiciones alcanzado ({self.max_positions})")
            position_size = 0
        elif len(self.open_positions) > 0:
            # Reducir tamaño si hay múltiples posiciones
            position_size *= (1 - len(self.open_positions) * 0.15)
        
        # Calcular take profit dinámico
        risk_reward_ratio = self._calculate_dynamic_risk_reward(market_conditions)
        
        # Determinar dirección
        is_long = entry_price > stop_loss
        
        if is_long:
            take_profit = entry_price + (stop_distance * risk_reward_ratio)
        else:
            take_profit = entry_price - (stop_distance * risk_reward_ratio)
        
        # Calcular nivel de confianza
        confidence = self._calculate_confidence_level(market_conditions)
        
        # Logging
        logger.info(f"""
        Cálculo de Riesgo Dinámico:
        - Riesgo Base: {self.base_risk_pct:.2%}
        - Ajuste Total: {total_adjustment:.2f}
        - Riesgo Final: {final_risk_pct:.2%}
        - Tamaño Posición: {position_size:.8f}
        - R:R Ratio: 1:{risk_reward_ratio:.1f}
        - Confianza: {confidence:.1f}%
        """)
        
        return RiskParameters(
            position_size=round(position_size, 8),
            stop_loss=stop_loss,
            take_profit=take_profit,
            max_drawdown=self.account_balance * 0.1,
            risk_per_trade=final_risk_pct,
            confidence_level=confidence,
            risk_reward_ratio=risk_reward_ratio,
            entry_price=entry_price
        )
    
    def _adjust_for_volatility(self, market_conditions: Dict) -> float:
        """
        Ajusta el riesgo basado en la volatilidad
        Mayor volatilidad = Menor tamaño de posición
        """
        current_atr = market_conditions.get('atr', 0)
        avg_atr = market_conditions.get('avg_atr', current_atr)
        
        if avg_atr == 0 or current_atr == 0:
            return 1.0
        
        volatility_ratio = current_atr / avg_atr
        
        # Tabla de ajustes por volatilidad
        if volatility_ratio > 2.0:  # Volatilidad extrema
            return 0.3
        elif volatility_ratio > 1.5:  # Alta volatilidad
            return 0.5
        elif volatility_ratio > 1.2:
            return 0.7
        elif volatility_ratio > 1.0:
            return 0.85
        elif volatility_ratio < 0.8:  # Baja volatilidad
            return 1.2
        elif volatility_ratio < 0.6:  # Muy baja volatilidad
            return 1.3
        else:
            return 1.0
    
    def _adjust_for_performance(self) -> float:
        """
        Ajusta basado en el performance histórico usando Kelly Criterion
        """
        if self.total_trades < 10:
            return 1.0  # No hay suficiente historial
        
        # Calcular métricas de los últimos 20 trades
        recent_trades = self.trade_history[-20:] if len(self.trade_history) >= 20 else self.trade_history
        
        wins = sum(1 for t in recent_trades if t.pnl > 0)
        losses = sum(1 for t in recent_trades if t.pnl < 0)
        
        if wins + losses == 0:
            return 1.0
        
        win_rate = wins / (wins + losses)
        
        # Calcular ratio promedio ganancia/pérdida
        winning_trades = [t.pnl for t in recent_trades if t.pnl > 0]
        losing_trades = [abs(t.pnl) for t in recent_trades if t.pnl < 0]
        
        if not winning_trades or not losing_trades:
            return 1.0
        
        avg_win = np.mean(winning_trades)
        avg_loss = np.mean(losing_trades)
        
        if avg_loss == 0:
            return 1.2  # Solo ganancias
        
        win_loss_ratio = avg_win / avg_loss
        
        # Kelly Criterion: f = (p * b - q) / b
        # donde p = probabilidad de ganar, q = probabilidad de perder, b = ratio ganancia/pérdida
        kelly_pct = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio
        
        # Aplicar Kelly conservador (25% del Kelly completo)
        kelly_pct = max(0, min(kelly_pct * 0.25, 0.25))
        
        # Convertir a multiplicador
        if kelly_pct > 0.15:
            return 1.3
        elif kelly_pct > 0.10:
            return 1.2
        elif kelly_pct > 0.05:
            return 1.1
        elif kelly_pct < 0.02:
            return 0.7
        else:
            return 1.0
    
    def _adjust_for_drawdown(self) -> float:
        """
        Reduce el riesgo durante drawdowns
        """
        # Calcular drawdown actual
        self.current_drawdown = (self.peak_balance - self.account_balance) / self.peak_balance if self.peak_balance > 0 else 0
        
        # Tabla de ajustes por drawdown
        if self.current_drawdown > 0.15:  # Más del 15% de drawdown
            return 0.3
        elif self.current_drawdown > 0.10:  # Más del 10%
            return 0.4
        elif self.current_drawdown > 0.07:  # Más del 7%
            return 0.5
        elif self.current_drawdown > 0.05:  # Más del 5%
            return 0.7
        elif self.current_drawdown > 0.03:  # Más del 3%
            return 0.85
        else:
            # Sin drawdown significativo
            if self.account_balance > self.peak_balance * 1.1:  # En profits
                return 1.1
            else:
                return 1.0
    
    def _adjust_for_market_conditions(self, market_conditions: Dict) -> float:
        """
        Ajusta basado en las condiciones específicas del mercado
        """
        adjustment = 1.0
        
        # RSI extremo
        rsi = market_conditions.get('rsi', 50)
        if rsi > 85 or rsi < 15:
            adjustment *= 0.5  # Reducir mucho en extremos
        elif rsi > 75 or rsi < 25:
            adjustment *= 0.7  # Reducir en sobrecompra/sobreventa
        elif 45 <= rsi <= 55:
            adjustment *= 1.1  # Aumentar ligeramente en zona neutral
        
        # Alineación de timeframes
        alignment = market_conditions.get('timeframe_alignment', 50)
        if alignment > 80:  # Alta alineación
            adjustment *= 1.3
        elif alignment > 70:
            adjustment *= 1.15
        elif alignment < 30:  # Baja alineación
            adjustment *= 0.7
        elif alignment < 40:
            adjustment *= 0.85
        
        # Calidad de la señal
        signal_quality = market_conditions.get('signal_quality', 50)
        if signal_quality > 80:
            adjustment *= 1.2
        elif signal_quality > 70:
            adjustment *= 1.1
        elif signal_quality < 30:
            adjustment *= 0.7
        
        # Proximidad a niveles clave
        distance_to_resistance = market_conditions.get('distance_to_resistance_pct', 100)
        distance_to_support = market_conditions.get('distance_to_support_pct', 100)
        
        if distance_to_resistance < 0.5:  # Muy cerca de resistencia
            adjustment *= 0.8
        if distance_to_support < 0.5:  # Muy cerca de soporte  
            adjustment *= 0.9
        
        # Confirmación de volumen
        if market_conditions.get('volume_confirmation', False):
            adjustment *= 1.1
        
        # Divergencias detectadas
        if market_conditions.get('divergence_detected', False):
            adjustment *= 0.6  # Reducir significativamente con divergencias
        
        # Sesión de trading
        session = market_conditions.get('trading_session', 'UNKNOWN')
        session_multipliers = {
            'NEWYORK': 1.1,   # Mejor liquidez
            'LONDON': 1.05,
            'OVERLAP': 1.15,  # Londres + NY
            'ASIA': 0.95,
            'UNKNOWN': 1.0
        }
        adjustment *= session_multipliers.get(session, 1.0)
        
        return adjustment
    
    def _adjust_for_correlation(self, symbol: str) -> float:
        """
        Ajusta por correlación con posiciones abiertas
        """
        if not self.open_positions:
            return 1.0
        
        # Contar posiciones del mismo símbolo
        same_symbol = sum(1 for p in self.open_positions if p.get('symbol') == symbol)
        
        if same_symbol >= 2:
            return 0.5  # Ya hay 2 posiciones del mismo activo
        elif same_symbol == 1:
            return 0.75  # Ya hay 1 posición
        
        # Verificar direcciones
        long_positions = sum(1 for p in self.open_positions if p.get('direction') == 'buy')
        short_positions = sum(1 for p in self.open_positions if p.get('direction') == 'sell')
        
        # Si hay posiciones en ambas direcciones, reducir riesgo
        if long_positions > 0 and short_positions > 0:
            return 0.8
        
        return 1.0
    
    def _calculate_dynamic_risk_reward(self, market_conditions: Dict) -> float:
        """
        Calcula ratio risk/reward dinámico basado en condiciones
        """
        base_rr = 2.0  # Base 1:2
        
        # Ajustar por volatilidad
        volatility_percentile = market_conditions.get('volatility_percentile', 50)
        if volatility_percentile > 80:  # Alta volatilidad
            base_rr = 2.5  # Buscar mayor reward
        elif volatility_percentile > 65:
            base_rr = 2.2
        elif volatility_percentile < 20:  # Baja volatilidad
            base_rr = 1.5  # Ser más conservador
        elif volatility_percentile < 35:
            base_rr = 1.7
        
        # Ajustar por tendencia
        trend_strength = market_conditions.get('trend_strength', 0)
        if abs(trend_strength) > 80:  # Tendencia muy fuerte
            base_rr = 3.0  # Dejar correr ganancias
        elif abs(trend_strength) > 65:
            base_rr *= 1.2
        elif abs(trend_strength) < 30:  # Tendencia débil
            base_rr *= 0.9
        
        # Ajustar por win rate histórico
        if self.win_rate > 0.65:  # Alto win rate
            base_rr *= 0.9  # Puede aceptar menor R:R
        elif self.win_rate < 0.35:  # Bajo win rate
            base_rr *= 1.3  # Necesita mayor R:R
        
        # Límites
        return max(1.2, min(base_rr, 4.0))
    
    def _calculate_confidence_level(self, market_conditions: Dict) -> float:
        """
        Calcula nivel de confianza de la operación
        """
        confidence = 50  # Base
        
        # Factores positivos
        if market_conditions.get('timeframe_alignment', 0) > 70:
            confidence += 15
        elif market_conditions.get('timeframe_alignment', 0) > 60:
            confidence += 10
        
        if market_conditions.get('volume_confirmation', False):
            confidence += 10
        
        if market_conditions.get('pattern_confirmation', False):
            confidence += 15
        
        if market_conditions.get('trend_quality', 0) > 70:
            confidence += 10
        
        # RSI en zona favorable
        rsi = market_conditions.get('rsi', 50)
        if 40 <= rsi <= 60:  # Zona neutral
            confidence += 5
        
        # Múltiples confirmaciones técnicas
        confirmations = market_conditions.get('technical_confirmations', 0)
        confidence += min(15, confirmations * 5)
        
        # Factores negativos
        if market_conditions.get('divergence_detected', False):
            confidence -= 20
        
        if market_conditions.get('volatility_spike', False):
            confidence -= 15
        
        if market_conditions.get('resistance_nearby', False):
            confidence -= 10
        
        if market_conditions.get('support_broken', False):
            confidence -= 15
        
        # Drawdown actual
        if self.current_drawdown > 0.05:
            confidence -= 10
        elif self.current_drawdown > 0.10:
            confidence -= 20
        
        return min(100, max(0, confidence))
    
    def add_position(self, position: Dict):
        """
        Añade una posición abierta
        """
        self.open_positions.append(position)
        logger.info(f"Posición añadida: {position.get('symbol')} - Total abiertas: {len(self.open_positions)}")
    
    def close_position(self, position_id: str, exit_price: float, exit_time: datetime):
        """
        Cierra una posición y actualiza métricas
        """
        position = None
        for i, p in enumerate(self.open_positions):
            if p.get('id') == position_id:
                position = self.open_positions.pop(i)
                break
        
        if not position:
            logger.warning(f"Posición {position_id} no encontrada")
            return None
        
        # Calcular PnL
        if position['direction'] == 'buy':
            pnl = (exit_price - position['entry_price']) * position['position_size']
        else:
            pnl = (position['entry_price'] - exit_price) * position['position_size']
        
        pnl_pct = pnl / (position['entry_price'] * position['position_size']) * 100
        
        # Actualizar balance
        self.account_balance += pnl
        
        # Crear resultado
        result = TradeResult(
            symbol=position['symbol'],
            entry_time=position['entry_time'],
            exit_time=exit_time,
            entry_price=position['entry_price'],
            exit_price=exit_price,
            position_size=position['position_size'],
            direction=position['direction'],
            pnl=pnl,
            pnl_pct=pnl_pct,
            balance_after=self.account_balance
        )
        
        # Actualizar historial y métricas
        self.update_trade_history(result)
        
        logger.info(f"""
        Posición Cerrada:
        - Símbolo: {result.symbol}
        - PnL: ${pnl:.2f} ({pnl_pct:.2f}%)
        - Balance: ${self.account_balance:.2f}
        """)
        
        return result
    
    def update_trade_history(self, trade_result: TradeResult):
        """
        Actualiza el historial de trades y métricas
        """
        self.trade_history.append(trade_result)
        self.total_trades += 1
        
        if trade_result.pnl > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1
        
        self.total_pnl += trade_result.pnl
        
        # Actualizar peak balance y drawdown
        if self.account_balance > self.peak_balance:
            self.peak_balance = self.account_balance
        
        self.current_drawdown = (self.peak_balance - self.account_balance) / self.peak_balance if self.peak_balance > 0 else 0
        self.max_drawdown = max(self.max_drawdown, self.current_drawdown)
        
        # Actualizar métricas adaptativas
        if self.total_trades >= 10:
            self.win_rate = self.winning_trades / self.total_trades
            
            # Calcular ratio promedio
            recent = self.trade_history[-20:] if len(self.trade_history) >= 20 else self.trade_history
            wins = [t.pnl for t in recent if t.pnl > 0]
            losses = [abs(t.pnl) for t in recent if t.pnl < 0]
            
            if wins and losses:
                self.avg_win_loss_ratio = np.mean(wins) / np.mean(losses)
        
        # Guardar historial
        self._save_history()
    
    def _get_default_parameters(self, entry_price: float) -> RiskParameters:
        """
        Retorna parámetros por defecto en caso de error
        """
        return RiskParameters(
            position_size=0,
            stop_loss=entry_price * 0.98,
            take_profit=entry_price * 1.02,
            max_drawdown=self.account_balance * 0.1,
            risk_per_trade=self.base_risk_pct,
            confidence_level=0,
            risk_reward_ratio=1.0,
            entry_price=entry_price
        )
    
    def get_risk_metrics(self) -> Dict[str, any]:
        """
        Obtiene métricas de riesgo actuales
        """
        sharpe_ratio = self._calculate_sharpe_ratio()
        max_consecutive_losses = self._calculate_max_consecutive_losses()
        
        return {
            'account_balance': self.account_balance,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'win_rate': self.win_rate,
            'avg_win_loss_ratio': self.avg_win_loss_ratio,
            'total_pnl': self.total_pnl,
            'total_return': (self.account_balance - self.initial_balance) / self.initial_balance * 100,
            'current_drawdown': self.current_drawdown * 100,
            'max_drawdown': self.max_drawdown * 100,
            'sharpe_ratio': sharpe_ratio,
            'max_consecutive_losses': max_consecutive_losses,
            'open_positions': len(self.open_positions),
            'peak_balance': self.peak_balance
        }
    
    def _calculate_sharpe_ratio(self) -> float:
        """
        Calcula el Sharpe Ratio
        """
        if len(self.trade_history) < 2:
            return 0
        
        returns = [t.pnl_pct for t in self.trade_history]
        
        if not returns:
            return 0
        
        avg_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0:
            return 0
        
        # Asumiendo tasa libre de riesgo del 2% anual
        risk_free_rate = 0.02 / 252  # Diario
        
        sharpe = (avg_return - risk_free_rate) / std_return * np.sqrt(252)
        
        return round(sharpe, 2)
    
    def _calculate_max_consecutive_losses(self) -> int:
        """
        Calcula el máximo número de pérdidas consecutivas
        """
        if not self.trade_history:
            return 0
        
        max_losses = 0
        current_losses = 0
        
        for trade in self.trade_history:
            if trade.pnl < 0:
                current_losses += 1
                max_losses = max(max_losses, current_losses)
            else:
                current_losses = 0
        
        return max_losses
    
    def _save_history(self):
        """
        Guarda el historial en archivo
        """
        try:
            data = {
                'metrics': self.get_risk_metrics(),
                'trade_history': [t.to_dict() for t in self.trade_history[-100:]],  # Últimos 100 trades
                'timestamp': datetime.now().isoformat()
            }
            
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error guardando historial: {e}")
    
    def _load_history(self):
        """
        Carga el historial desde archivo
        """
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                
                # Restaurar métricas
                metrics = data.get('metrics', {})
                self.total_trades = metrics.get('total_trades', 0)
                self.winning_trades = metrics.get('winning_trades', 0)
                self.losing_trades = metrics.get('losing_trades', 0)
                self.win_rate = metrics.get('win_rate', 0.5)
                self.avg_win_loss_ratio = metrics.get('avg_win_loss_ratio', 1.0)
                self.total_pnl = metrics.get('total_pnl', 0)
                self.max_drawdown = metrics.get('max_drawdown', 0) / 100
                self.peak_balance = metrics.get('peak_balance', self.account_balance)
                
                # Restaurar historial de trades
                trade_dicts = data.get('trade_history', [])
                self.trade_history = []
                
                for td in trade_dicts:
                    try:
                        trade = TradeResult(
                            symbol=td['symbol'],
                            entry_time=datetime.fromisoformat(td['entry_time']),
                            exit_time=datetime.fromisoformat(td['exit_time']),
                            entry_price=td['entry_price'],
                            exit_price=td['exit_price'],
                            position_size=td['position_size'],
                            direction=td['direction'],
                            pnl=td['pnl'],
                            pnl_pct=td['pnl_pct'],
                            balance_after=td['balance_after']
                        )
                        self.trade_history.append(trade)
                    except:
                        pass
                
                logger.info(f"Historial cargado: {self.total_trades} trades")
                
        except Exception as e:
            logger.warning(f"No se pudo cargar historial: {e}")
