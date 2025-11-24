#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
LOGGER DE HISTORIAL DE TRADES - ALGO TRADER V3
===============================================
Sistema completo de logging para backtesting y análisis
"""

import os
import csv
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import pandas as pd

class TradeHistoryLogger:
    """
    Logger completo para historial de trades y ajustes del Director
    Guarda datos para backtesting y análisis posterior
    """
    
    def __init__(self, base_path: str = "data"):
        """
        Inicializa el logger de historial
        Args:
            base_path: Directorio base para logs
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        
        # Archivos de historial
        self.trades_file = self.base_path / "trades_history.csv"
        self.adjustments_file = self.base_path / "tp_adjustments.csv"
        self.signals_file = self.base_path / "signals_history.csv"
        self.performance_file = self.base_path / "performance_log.json"
        
        # Configurar logger
        self.logger = logging.getLogger(__name__)
        
        # Inicializar archivos CSV
        self.init_csv_files()
    
    def init_csv_files(self):
        """Inicializa los archivos CSV con headers"""
        # Trades history
        if not self.trades_file.exists():
            trades_headers = [
                'timestamp', 'ticket', 'symbol', 'type', 'volume', 'entry_price', 
                'exit_price', 'exit_reason', 'sl', 'tp', 'profit_usd', 'profit_pips',
                'duration_seconds', 'strategy', 'ai_confidence', 'market_conditions'
            ]
            self.write_csv_header(self.trades_file, trades_headers)
        
        # TP Adjustments
        if not self.adjustments_file.exists():
            adjustments_headers = [
                'timestamp', 'ticket', 'symbol', 'adjustment_type', 'old_tp', 'new_tp',
                'reason', 'ai_analysis', 'rsi', 'rvol', 'institutional_score',
                'current_price', 'profit_before', 'profit_after'
            ]
            self.write_csv_header(self.adjustments_file, adjustments_headers)
        
        # Signals history  
        if not self.signals_file.exists():
            signals_headers = [
                'timestamp', 'symbol', 'signal_type', 'entry_price', 'sl', 'tp',
                'confidence', 'strategy', 'market_data', 'executed', 'ticket'
            ]
            self.write_csv_header(self.signals_file, signals_headers)
    
    def write_csv_header(self, file_path: Path, headers: List[str]):
        """Escribe header en archivo CSV"""
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
    
    def log_trade_closed(self, trade_data: Dict[str, Any]):
        """
        Registra un trade cerrado (TP o SL)
        
        Args:
            trade_data: Diccionario con información del trade
            {
                'ticket': int,
                'symbol': str,
                'type': 'BUY'/'SELL',
                'volume': float,
                'entry_price': float,
                'exit_price': float,
                'exit_reason': 'TP'/'SL'/'MANUAL',
                'sl': float,
                'tp': float,
                'profit_usd': float,
                'duration_seconds': int,
                'strategy': str,
                'ai_confidence': float,
                'market_conditions': dict
            }
        """
        try:
            # Calcular profit en pips
            if trade_data['type'] == 'BUY':
                profit_pips = (trade_data['exit_price'] - trade_data['entry_price'])
            else:
                profit_pips = (trade_data['entry_price'] - trade_data['exit_price'])
            
            # Para forex, convertir a pips reales
            if any(pair in trade_data['symbol'] for pair in ['USD', 'EUR', 'GBP']):
                if 'JPY' in trade_data['symbol']:
                    profit_pips *= 100  # JPY pairs
                else:
                    profit_pips *= 10000  # Major pairs
            
            row = [
                datetime.now().isoformat(),
                trade_data.get('ticket', ''),
                trade_data.get('symbol', ''),
                trade_data.get('type', ''),
                trade_data.get('volume', 0),
                trade_data.get('entry_price', 0),
                trade_data.get('exit_price', 0),
                trade_data.get('exit_reason', 'UNKNOWN'),
                trade_data.get('sl', 0),
                trade_data.get('tp', 0),
                trade_data.get('profit_usd', 0),
                round(profit_pips, 2),
                trade_data.get('duration_seconds', 0),
                trade_data.get('strategy', ''),
                trade_data.get('ai_confidence', 0),
                json.dumps(trade_data.get('market_conditions', {}))
            ]
            
            self.append_to_csv(self.trades_file, row)
            self.logger.info(f"Trade cerrado registrado: {trade_data['ticket']} - {trade_data['exit_reason']} - ${trade_data.get('profit_usd', 0):.2f}")
            
        except Exception as e:
            self.logger.error(f"Error registrando trade cerrado: {e}")
    
    def log_tp_adjustment(self, adjustment_data: Dict[str, Any]):
        """
        Registra un ajuste de TP del Director
        
        Args:
            adjustment_data: Información del ajuste
            {
                'ticket': int,
                'symbol': str,
                'adjustment_type': 'EXTENSION'/'REDUCTION',
                'old_tp': float,
                'new_tp': float,
                'reason': str,
                'ai_analysis': str,
                'market_analysis': dict,
                'current_price': float,
                'profit_before': float,
                'profit_after': float
            }
        """
        try:
            market_data = adjustment_data.get('market_analysis', {})
            volume_data = market_data.get('volume', {})
            momentum_data = market_data.get('momentum', {})
            
            row = [
                datetime.now().isoformat(),
                adjustment_data.get('ticket', ''),
                adjustment_data.get('symbol', ''),
                adjustment_data.get('adjustment_type', ''),
                adjustment_data.get('old_tp', 0),
                adjustment_data.get('new_tp', 0),
                adjustment_data.get('reason', ''),
                adjustment_data.get('ai_analysis', ''),
                momentum_data.get('rsi', 0),
                volume_data.get('rvol', 1),
                volume_data.get('institutional_score', 0),
                adjustment_data.get('current_price', 0),
                adjustment_data.get('profit_before', 0),
                adjustment_data.get('profit_after', 0)
            ]
            
            self.append_to_csv(self.adjustments_file, row)
            self.logger.info(f"Ajuste TP registrado: {adjustment_data['ticket']} - {adjustment_data['adjustment_type']}")
            
        except Exception as e:
            self.logger.error(f"Error registrando ajuste TP: {e}")
    
    def log_signal_generated(self, signal_data: Dict[str, Any]):
        """
        Registra una señal generada
        
        Args:
            signal_data: Información de la señal
        """
        try:
            row = [
                datetime.now().isoformat(),
                signal_data.get('symbol', ''),
                signal_data.get('type', ''),
                signal_data.get('price', 0),
                signal_data.get('sl', 0),
                signal_data.get('tp', 0),
                signal_data.get('strength', 0),
                signal_data.get('strategy', ''),
                json.dumps(signal_data.get('market_data', {})),
                signal_data.get('executed', False),
                signal_data.get('ticket', '')
            ]
            
            self.append_to_csv(self.signals_file, row)
            
        except Exception as e:
            self.logger.error(f"Error registrando señal: {e}")
    
    def append_to_csv(self, file_path: Path, row: List):
        """Agrega una fila a un archivo CSV"""
        with open(file_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(row)
    
    def get_trades_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        Obtiene resumen de trades de los últimos días
        
        Args:
            days: Número de días hacia atrás
            
        Returns:
            Diccionario con estadísticas
        """
        try:
            if not self.trades_file.exists():
                return {"error": "No hay historial de trades"}
            
            df = pd.read_csv(self.trades_file)
            if df.empty:
                return {"message": "No hay trades registrados"}
            
            # Filtrar por días
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            cutoff_date = datetime.now() - pd.Timedelta(days=days)
            recent_trades = df[df['timestamp'] >= cutoff_date]
            
            if recent_trades.empty:
                return {"message": f"No hay trades en los últimos {days} días"}
            
            # Calcular estadísticas
            total_trades = len(recent_trades)
            winning_trades = len(recent_trades[recent_trades['profit_usd'] > 0])
            losing_trades = len(recent_trades[recent_trades['profit_usd'] < 0])
            
            total_profit = recent_trades['profit_usd'].sum()
            avg_profit = recent_trades['profit_usd'].mean()
            max_profit = recent_trades['profit_usd'].max()
            max_loss = recent_trades['profit_usd'].min()
            
            win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
            
            # Estadísticas por exit reason
            tp_trades = len(recent_trades[recent_trades['exit_reason'] == 'TP'])
            sl_trades = len(recent_trades[recent_trades['exit_reason'] == 'SL'])
            
            return {
                "period_days": days,
                "total_trades": total_trades,
                "winning_trades": winning_trades,
                "losing_trades": losing_trades,
                "win_rate": round(win_rate, 2),
                "total_profit": round(total_profit, 2),
                "avg_profit_per_trade": round(avg_profit, 2),
                "max_profit": round(max_profit, 2),
                "max_loss": round(max_loss, 2),
                "tp_exits": tp_trades,
                "sl_exits": sl_trades,
                "manual_exits": total_trades - tp_trades - sl_trades
            }
            
        except Exception as e:
            self.logger.error(f"Error calculando resumen: {e}")
            return {"error": str(e)}
    
    def get_adjustments_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        Obtiene resumen de ajustes TP de los últimos días
        """
        try:
            if not self.adjustments_file.exists():
                return {"message": "No hay ajustes registrados"}
            
            df = pd.read_csv(self.adjustments_file)
            if df.empty:
                return {"message": "No hay ajustes registrados"}
            
            # Filtrar por días
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            cutoff_date = datetime.now() - pd.Timedelta(days=days)
            recent_adjustments = df[df['timestamp'] >= cutoff_date]
            
            if recent_adjustments.empty:
                return {"message": f"No hay ajustes en los últimos {days} días"}
            
            total_adjustments = len(recent_adjustments)
            extensions = len(recent_adjustments[recent_adjustments['adjustment_type'] == 'EXTENSION'])
            reductions = len(recent_adjustments[recent_adjustments['adjustment_type'] == 'REDUCTION'])
            
            avg_rsi = recent_adjustments['rsi'].mean()
            avg_rvol = recent_adjustments['rvol'].mean()
            avg_institutional_score = recent_adjustments['institutional_score'].mean()
            
            return {
                "period_days": days,
                "total_adjustments": total_adjustments,
                "extensions": extensions,
                "reductions": reductions,
                "avg_rsi_at_adjustment": round(avg_rsi, 2),
                "avg_rvol_at_adjustment": round(avg_rvol, 2),
                "avg_institutional_score": round(avg_institutional_score, 2)
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def export_for_backtesting(self, output_file: str = None) -> str:
        """
        Exporta datos en formato optimizado para backtesting
        
        Returns:
            Path del archivo exportado
        """
        if not output_file:
            output_file = f"backtest_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        try:
            # Combinar datos de trades y ajustes
            trades_df = pd.read_csv(self.trades_file) if self.trades_file.exists() else pd.DataFrame()
            adjustments_df = pd.read_csv(self.adjustments_file) if self.adjustments_file.exists() else pd.DataFrame()
            
            # Crear dataset completo para backtesting
            backtest_data = []
            
            for _, trade in trades_df.iterrows():
                # Buscar ajustes para este trade
                trade_adjustments = adjustments_df[adjustments_df['ticket'] == trade['ticket']]
                
                backtest_record = {
                    'timestamp': trade['timestamp'],
                    'ticket': trade['ticket'],
                    'symbol': trade['symbol'],
                    'type': trade['type'],
                    'entry_price': trade['entry_price'],
                    'exit_price': trade['exit_price'],
                    'exit_reason': trade['exit_reason'],
                    'final_profit': trade['profit_usd'],
                    'total_adjustments': len(trade_adjustments),
                    'extensions': len(trade_adjustments[trade_adjustments['adjustment_type'] == 'EXTENSION']),
                    'reductions': len(trade_adjustments[trade_adjustments['adjustment_type'] == 'REDUCTION']),
                    'original_tp': trade.get('tp', 0),
                    'final_tp': trade_adjustments['new_tp'].iloc[-1] if not trade_adjustments.empty else trade.get('tp', 0)
                }
                backtest_data.append(backtest_record)
            
            # Guardar archivo
            backtest_df = pd.DataFrame(backtest_data)
            output_path = self.base_path / output_file
            backtest_df.to_csv(output_path, index=False)
            
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"Error exportando para backtesting: {e}")
            return ""

# Instancia global
trade_logger = TradeHistoryLogger()

# Funciones de conveniencia
def log_trade_closed(**kwargs):
    """Registra un trade cerrado"""
    trade_logger.log_trade_closed(kwargs)

def log_tp_adjustment(**kwargs):
    """Registra un ajuste de TP"""
    trade_logger.log_tp_adjustment(kwargs)

def log_signal_generated(**kwargs):
    """Registra una señal generada"""
    trade_logger.log_signal_generated(kwargs)

def get_trading_summary(days=7):
    """Obtiene resumen de trading"""
    return trade_logger.get_trades_summary(days)

def get_director_summary(days=7):
    """Obtiene resumen del Director"""
    return trade_logger.get_adjustments_summary(days)

if __name__ == "__main__":
    # Test del sistema
    logger = TradeHistoryLogger()
    
    # Ejemplo de trade cerrado
    logger.log_trade_closed({
        'ticket': 123456,
        'symbol': 'EURUSD',
        'type': 'BUY',
        'volume': 0.1,
        'entry_price': 1.1000,
        'exit_price': 1.1050,
        'exit_reason': 'TP',
        'profit_usd': 50.0,
        'strategy': 'AI_Hybrid'
    })
    
    # Ejemplo de ajuste TP
    logger.log_tp_adjustment({
        'ticket': 123456,
        'symbol': 'EURUSD',
        'adjustment_type': 'EXTENSION',
        'old_tp': 1.1030,
        'new_tp': 1.1050,
        'reason': 'Volumen institucional detectado',
        'current_price': 1.1020
    })
    
    print("Resumen trading:", logger.get_trades_summary())
    print("Resumen ajustes:", logger.get_adjustments_summary())