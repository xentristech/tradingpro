#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DIARIO DE TRADING INTELIGENTE - ALGO TRADER V3
==============================================
Sistema completo de registro de operaciones con métricas avanzadas
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from dataclasses import dataclass, asdict
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Trade:
    """Estructura de datos para cada trade"""
    ticket: int
    symbol: str
    trade_type: str  # BUY/SELL
    volume: float
    entry_price: float
    exit_price: Optional[float]
    sl_price: Optional[float]
    tp_price: Optional[float]
    entry_time: str
    exit_time: Optional[str]
    profit_usd: Optional[float]
    profit_pips: Optional[float]
    profit_percent: Optional[float]
    commission: float
    swap: float
    magic: int
    comment: str
    strategy: str  # AI_Hybrid, Multi_TF, etc
    confidence: float  # Confianza de la señal
    indicators: Dict[str, float]  # RSI, MACD, etc al momento de entrada
    ai_analysis: Optional[str]  # Análisis de IA si aplica
    result: Optional[str]  # WIN/LOSS/BREAKEVEN
    tags: List[str]  # Tags para categorización
    
    def to_dict(self):
        return asdict(self)

class TradingJournal:
    """Diario de trading con métricas avanzadas y análisis"""
    
    def __init__(self, journal_path: str = "data/trading_journal.json"):
        self.journal_path = Path(journal_path)
        self.journal_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Cargar historial existente
        self.trades: List[Trade] = []
        self.balance_history: List[Dict] = []
        self.equity_history: List[Dict] = []
        self.metrics_cache: Dict = {}
        
        self.load_journal()
        
    def load_journal(self):
        """Carga el diario desde el archivo"""
        if self.journal_path.exists():
            try:
                with open(self.journal_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Cargar trades
                for trade_dict in data.get('trades', []):
                    self.trades.append(Trade(**trade_dict))
                    
                # Cargar historial de balance y equity
                self.balance_history = data.get('balance_history', [])
                self.equity_history = data.get('equity_history', [])
                self.metrics_cache = data.get('metrics', {})
                
                logger.info(f"Diario cargado: {len(self.trades)} trades")
            except Exception as e:
                logger.error(f"Error cargando diario: {e}")
                
    def save_journal(self):
        """Guarda el diario en el archivo"""
        try:
            data = {
                'trades': [trade.to_dict() for trade in self.trades],
                'balance_history': self.balance_history,
                'equity_history': self.equity_history,
                'metrics': self.metrics_cache,
                'last_update': datetime.now().isoformat()
            }
            
            with open(self.journal_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Diario guardado: {len(self.trades)} trades")
        except Exception as e:
            logger.error(f"Error guardando diario: {e}")
            
    def add_trade(self, trade_data: Dict) -> Trade:
        """Añade un nuevo trade al diario"""
        # Crear objeto Trade
        trade = Trade(
            ticket=trade_data.get('ticket'),
            symbol=trade_data.get('symbol'),
            trade_type=trade_data.get('type'),
            volume=trade_data.get('volume'),
            entry_price=trade_data.get('entry_price'),
            exit_price=trade_data.get('exit_price'),
            sl_price=trade_data.get('sl_price'),
            tp_price=trade_data.get('tp_price'),
            entry_time=trade_data.get('entry_time', datetime.now().isoformat()),
            exit_time=trade_data.get('exit_time'),
            profit_usd=trade_data.get('profit_usd'),
            profit_pips=trade_data.get('profit_pips'),
            profit_percent=trade_data.get('profit_percent'),
            commission=trade_data.get('commission', 0),
            swap=trade_data.get('swap', 0),
            magic=trade_data.get('magic', 0),
            comment=trade_data.get('comment', ''),
            strategy=trade_data.get('strategy', 'Manual'),
            confidence=trade_data.get('confidence', 0),
            indicators=trade_data.get('indicators', {}),
            ai_analysis=trade_data.get('ai_analysis'),
            result=self._determine_result(trade_data),
            tags=trade_data.get('tags', [])
        )
        
        self.trades.append(trade)
        self.save_journal()
        
        logger.info(f"Trade añadido: {trade.symbol} {trade.trade_type} #{trade.ticket}")
        return trade
        
    def update_trade(self, ticket: int, update_data: Dict):
        """Actualiza un trade existente"""
        for trade in self.trades:
            if trade.ticket == ticket:
                for key, value in update_data.items():
                    if hasattr(trade, key):
                        setattr(trade, key, value)
                        
                # Actualizar resultado si se cerró
                if trade.exit_price and not trade.result:
                    trade.result = self._determine_result(asdict(trade))
                    
                self.save_journal()
                logger.info(f"Trade actualizado: #{ticket}")
                return trade
                
        logger.warning(f"Trade no encontrado: #{ticket}")
        return None
        
    def _determine_result(self, trade_data: Dict) -> str:
        """Determina el resultado del trade"""
        profit = trade_data.get('profit_usd', 0)
        if profit > 0:
            return 'WIN'
        elif profit < 0:
            return 'LOSS'
        else:
            return 'BREAKEVEN'
            
    def add_balance_snapshot(self, balance: float, equity: float):
        """Añade un snapshot del balance y equity"""
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'balance': balance,
            'equity': equity,
            'floating_pnl': equity - balance
        }
        
        self.balance_history.append(snapshot)
        self.equity_history.append({
            'timestamp': snapshot['timestamp'],
            'value': equity
        })
        
        # Mantener solo últimos 1000 registros
        if len(self.balance_history) > 1000:
            self.balance_history = self.balance_history[-1000:]
        if len(self.equity_history) > 1000:
            self.equity_history = self.equity_history[-1000:]
            
        self.save_journal()
        
    def calculate_metrics(self, period_days: int = 30) -> Dict:
        """Calcula métricas de rendimiento"""
        # Filtrar trades del período
        cutoff_date = datetime.now() - timedelta(days=period_days)
        recent_trades = [
            t for t in self.trades 
            if t.exit_time and datetime.fromisoformat(t.exit_time) >= cutoff_date
        ]
        
        if not recent_trades:
            return self._empty_metrics()
            
        # Convertir a DataFrame para cálculos
        df = pd.DataFrame([t.to_dict() for t in recent_trades])
        
        metrics = {}
        
        # Métricas básicas
        metrics['total_trades'] = len(recent_trades)
        metrics['winning_trades'] = len([t for t in recent_trades if t.result == 'WIN'])
        metrics['losing_trades'] = len([t for t in recent_trades if t.result == 'LOSS'])
        metrics['win_rate'] = metrics['winning_trades'] / metrics['total_trades'] if metrics['total_trades'] > 0 else 0
        
        # PnL
        metrics['gross_profit'] = df[df['profit_usd'] > 0]['profit_usd'].sum()
        metrics['gross_loss'] = abs(df[df['profit_usd'] < 0]['profit_usd'].sum())
        metrics['net_profit'] = metrics['gross_profit'] - metrics['gross_loss']
        metrics['profit_factor'] = metrics['gross_profit'] / metrics['gross_loss'] if metrics['gross_loss'] > 0 else 0
        
        # Promedio de ganancia/pérdida
        wins = df[df['profit_usd'] > 0]['profit_usd']
        losses = df[df['profit_usd'] < 0]['profit_usd']
        
        metrics['avg_win'] = wins.mean() if len(wins) > 0 else 0
        metrics['avg_loss'] = abs(losses.mean()) if len(losses) > 0 else 0
        metrics['avg_rr'] = metrics['avg_win'] / metrics['avg_loss'] if metrics['avg_loss'] > 0 else 0
        
        # Sharpe Ratio (asumiendo retornos diarios)
        if len(df) > 1:
            returns = df.groupby(pd.to_datetime(df['exit_time']).dt.date)['profit_usd'].sum()
            if len(returns) > 1:
                metrics['sharpe_ratio'] = self._calculate_sharpe_ratio(returns)
                metrics['sortino_ratio'] = self._calculate_sortino_ratio(returns)
            else:
                metrics['sharpe_ratio'] = 0
                metrics['sortino_ratio'] = 0
        else:
            metrics['sharpe_ratio'] = 0
            metrics['sortino_ratio'] = 0
            
        # Maximum Drawdown
        metrics['max_drawdown'] = self._calculate_max_drawdown()
        metrics['max_drawdown_percent'] = self._calculate_max_drawdown_percent()
        
        # Value at Risk (VaR) - 95% confidence
        if len(df) > 0:
            metrics['var_95'] = np.percentile(df['profit_usd'], 5)
        else:
            metrics['var_95'] = 0
            
        # Calmar Ratio
        if metrics['max_drawdown_percent'] > 0:
            annual_return = (metrics['net_profit'] / period_days) * 365
            metrics['calmar_ratio'] = annual_return / abs(metrics['max_drawdown_percent'])
        else:
            metrics['calmar_ratio'] = 0
            
        # Expectancy
        if metrics['total_trades'] > 0:
            metrics['expectancy'] = (
                (metrics['win_rate'] * metrics['avg_win']) - 
                ((1 - metrics['win_rate']) * metrics['avg_loss'])
            )
        else:
            metrics['expectancy'] = 0
            
        # Recovery Factor
        if metrics['max_drawdown'] != 0:
            metrics['recovery_factor'] = metrics['net_profit'] / abs(metrics['max_drawdown'])
        else:
            metrics['recovery_factor'] = 0
            
        # Estadísticas por símbolo
        metrics['by_symbol'] = self._calculate_symbol_metrics(df)
        
        # Estadísticas por estrategia
        metrics['by_strategy'] = self._calculate_strategy_metrics(df)
        
        # Guardar en cache
        self.metrics_cache = metrics
        self.save_journal()
        
        return metrics
        
    def _calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calcula el Sharpe Ratio"""
        if len(returns) < 2:
            return 0
            
        daily_rf = risk_free_rate / 252  # Tasa libre de riesgo diaria
        excess_returns = returns - daily_rf
        
        if excess_returns.std() == 0:
            return 0
            
        sharpe = np.sqrt(252) * (excess_returns.mean() / excess_returns.std())
        return round(sharpe, 2)
        
    def _calculate_sortino_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """Calcula el Sortino Ratio (solo considera volatilidad negativa)"""
        if len(returns) < 2:
            return 0
            
        daily_rf = risk_free_rate / 252
        excess_returns = returns - daily_rf
        
        # Solo considerar retornos negativos para el denominador
        downside_returns = excess_returns[excess_returns < 0]
        
        if len(downside_returns) == 0 or downside_returns.std() == 0:
            return 0
            
        sortino = np.sqrt(252) * (excess_returns.mean() / downside_returns.std())
        return round(sortino, 2)
        
    def _calculate_max_drawdown(self) -> float:
        """Calcula el drawdown máximo en USD"""
        if not self.equity_history:
            return 0
            
        equity_values = [e['value'] for e in self.equity_history]
        peak = equity_values[0]
        max_dd = 0
        
        for value in equity_values:
            if value > peak:
                peak = value
            dd = peak - value
            if dd > max_dd:
                max_dd = dd
                
        return round(max_dd, 2)
        
    def _calculate_max_drawdown_percent(self) -> float:
        """Calcula el drawdown máximo en porcentaje"""
        if not self.equity_history:
            return 0
            
        equity_values = [e['value'] for e in self.equity_history]
        peak = equity_values[0]
        max_dd_pct = 0
        
        for value in equity_values:
            if value > peak:
                peak = value
            if peak > 0:
                dd_pct = ((peak - value) / peak) * 100
                if dd_pct > max_dd_pct:
                    max_dd_pct = dd_pct
                    
        return round(max_dd_pct, 2)
        
    def _calculate_symbol_metrics(self, df: pd.DataFrame) -> Dict:
        """Calcula métricas por símbolo"""
        symbol_metrics = {}
        
        for symbol in df['symbol'].unique():
            symbol_df = df[df['symbol'] == symbol]
            
            symbol_metrics[symbol] = {
                'trades': len(symbol_df),
                'profit': symbol_df['profit_usd'].sum(),
                'win_rate': len(symbol_df[symbol_df['result'] == 'WIN']) / len(symbol_df) if len(symbol_df) > 0 else 0,
                'avg_profit': symbol_df['profit_usd'].mean()
            }
            
        return symbol_metrics
        
    def _calculate_strategy_metrics(self, df: pd.DataFrame) -> Dict:
        """Calcula métricas por estrategia"""
        strategy_metrics = {}
        
        for strategy in df['strategy'].unique():
            strategy_df = df[df['strategy'] == strategy]
            
            strategy_metrics[strategy] = {
                'trades': len(strategy_df),
                'profit': strategy_df['profit_usd'].sum(),
                'win_rate': len(strategy_df[strategy_df['result'] == 'WIN']) / len(strategy_df) if len(strategy_df) > 0 else 0,
                'avg_confidence': strategy_df['confidence'].mean()
            }
            
        return strategy_metrics
        
    def _empty_metrics(self) -> Dict:
        """Retorna métricas vacías"""
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0,
            'gross_profit': 0,
            'gross_loss': 0,
            'net_profit': 0,
            'profit_factor': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'avg_rr': 0,
            'sharpe_ratio': 0,
            'sortino_ratio': 0,
            'max_drawdown': 0,
            'max_drawdown_percent': 0,
            'var_95': 0,
            'calmar_ratio': 0,
            'expectancy': 0,
            'recovery_factor': 0,
            'by_symbol': {},
            'by_strategy': {}
        }
        
    def export_to_csv(self, filepath: str = None):
        """Exporta el diario a CSV"""
        if not filepath:
            filepath = f"data/trading_journal_{datetime.now().strftime('%Y%m%d')}.csv"
            
        df = pd.DataFrame([t.to_dict() for t in self.trades])
        df.to_csv(filepath, index=False, encoding='utf-8')
        logger.info(f"Diario exportado a: {filepath}")
        
    def get_daily_report(self) -> Dict:
        """Genera reporte diario"""
        today = datetime.now().date()
        today_trades = [
            t for t in self.trades
            if t.exit_time and datetime.fromisoformat(t.exit_time).date() == today
        ]
        
        report = {
            'date': today.isoformat(),
            'trades': len(today_trades),
            'profit': sum(t.profit_usd for t in today_trades if t.profit_usd),
            'winning_trades': len([t for t in today_trades if t.result == 'WIN']),
            'losing_trades': len([t for t in today_trades if t.result == 'LOSS']),
            'symbols_traded': list(set(t.symbol for t in today_trades)),
            'best_trade': max((t.profit_usd for t in today_trades if t.profit_usd), default=0),
            'worst_trade': min((t.profit_usd for t in today_trades if t.profit_usd), default=0),
            'current_metrics': self.calculate_metrics(period_days=1)
        }
        
        return report
        
    def analyze_patterns(self) -> Dict:
        """Analiza patrones en el historial de trades"""
        if len(self.trades) < 10:
            return {'message': 'Insuficientes trades para análisis'}
            
        patterns = {}
        
        # Análisis por hora del día
        hour_performance = {}
        for trade in self.trades:
            if trade.entry_time:
                hour = datetime.fromisoformat(trade.entry_time).hour
                if hour not in hour_performance:
                    hour_performance[hour] = {'trades': 0, 'profit': 0}
                hour_performance[hour]['trades'] += 1
                if trade.profit_usd:
                    hour_performance[hour]['profit'] += trade.profit_usd
                    
        patterns['best_hours'] = sorted(
            hour_performance.items(),
            key=lambda x: x[1]['profit'],
            reverse=True
        )[:3]
        
        # Análisis por día de la semana
        day_performance = {}
        for trade in self.trades:
            if trade.entry_time:
                day = datetime.fromisoformat(trade.entry_time).strftime('%A')
                if day not in day_performance:
                    day_performance[day] = {'trades': 0, 'profit': 0}
                day_performance[day]['trades'] += 1
                if trade.profit_usd:
                    day_performance[day]['profit'] += trade.profit_usd
                    
        patterns['best_days'] = sorted(
            day_performance.items(),
            key=lambda x: x[1]['profit'],
            reverse=True
        )[:3]
        
        # Análisis de rachas
        current_streak = 0
        max_win_streak = 0
        max_loss_streak = 0
        current_loss_streak = 0
        
        for trade in self.trades:
            if trade.result == 'WIN':
                current_streak += 1
                current_loss_streak = 0
                max_win_streak = max(max_win_streak, current_streak)
            elif trade.result == 'LOSS':
                current_streak = 0
                current_loss_streak += 1
                max_loss_streak = max(max_loss_streak, current_loss_streak)
                
        patterns['max_win_streak'] = max_win_streak
        patterns['max_loss_streak'] = max_loss_streak
        patterns['current_streak'] = current_streak if current_streak > 0 else -current_loss_streak
        
        return patterns


# Singleton para acceso global
_journal_instance = None

def get_journal() -> TradingJournal:
    """Obtiene la instancia singleton del diario"""
    global _journal_instance
    if _journal_instance is None:
        _journal_instance = TradingJournal()
    return _journal_instance


if __name__ == "__main__":
    # Test del diario
    journal = get_journal()
    
    # Ejemplo de añadir un trade
    test_trade = {
        'ticket': 12345,
        'symbol': 'XAUUSD',
        'type': 'BUY',
        'volume': 0.01,
        'entry_price': 2650.50,
        'exit_price': 2655.00,
        'sl_price': 2648.00,
        'tp_price': 2655.00,
        'profit_usd': 45.0,
        'profit_pips': 45,
        'profit_percent': 0.17,
        'strategy': 'AI_Hybrid',
        'confidence': 0.85,
        'indicators': {
            'RSI': 65,
            'MACD': 0.5,
            'ATR': 2.5
        }
    }
    
    # journal.add_trade(test_trade)
    
    # Calcular métricas
    metrics = journal.calculate_metrics()
    print("\nMétricas de rendimiento (últimos 30 días):")
    print(json.dumps(metrics, indent=2))
    
    # Analizar patrones
    patterns = journal.analyze_patterns()
    print("\nPatrones detectados:")
    print(json.dumps(patterns, indent=2))
    
    # Reporte diario
    daily = journal.get_daily_report()
    print("\nReporte del día:")
    print(json.dumps(daily, indent=2))