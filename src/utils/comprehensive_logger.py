#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SISTEMA DE LOGGING COMPLETO
===========================
Logger comprehensivo que registra TODA la actividad del sistema de trading
"""

import os
import json
import csv
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import threading
from dataclasses import dataclass, asdict

@dataclass
class LogEntry:
    """Estructura base para entradas de log"""
    timestamp: str
    timestamp_readable: str
    log_type: str
    level: str
    component: str
    message: str
    data: Dict[str, Any]

class ComprehensiveLogger:
    """Sistema de logging completo para trading algorítmico"""
    
    def __init__(self, base_dir="logs/comprehensive"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Fecha actual para archivos
        self.date_str = datetime.now().strftime('%Y%m%d')
        
        # Archivos de log específicos
        self.files = {
            'signals': self.base_dir / f"signals_{self.date_str}.json",
            'trades': self.base_dir / f"trades_{self.date_str}.json", 
            'risk_management': self.base_dir / f"risk_management_{self.date_str}.json",
            'system_events': self.base_dir / f"system_events_{self.date_str}.json",
            'performance': self.base_dir / f"performance_{self.date_str}.json",
            'errors': self.base_dir / f"errors_{self.date_str}.json",
            'telegram_notifications': self.base_dir / f"telegram_{self.date_str}.json",
            'market_data': self.base_dir / f"market_data_{self.date_str}.json"
        }
        
        # CSV para análisis rápido
        self.csv_files = {
            'daily_summary': self.base_dir / f"daily_summary_{self.date_str}.csv",
            'trades_summary': self.base_dir / f"trades_summary_{self.date_str}.csv",
            'risk_actions': self.base_dir / f"risk_actions_{self.date_str}.csv"
        }
        
        # Inicializar CSVs
        self.init_csv_files()
        
        # Lock para threading
        self.lock = threading.Lock()
        
        # Configurar logging estándar
        self.setup_standard_logging()
        
        # Estadísticas en memoria
        self.stats = {
            'signals_generated': 0,
            'trades_executed': 0,
            'breakeven_applied': 0,
            'trailing_applied': 0,
            'errors_count': 0,
            'notifications_sent': 0,
            'start_time': datetime.now().isoformat()
        }
        
        self.log_system_event('SYSTEM_START', 'Sistema de logging completo iniciado', {'version': '1.0'})
    
    def setup_standard_logging(self):
        """Configurar logging estándar de Python"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # Handler para archivo general
        file_handler = logging.FileHandler(
            self.base_dir / f"system_log_{self.date_str}.log", 
            encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter(log_format))
        
        # Configurar root logger
        logging.basicConfig(
            level=logging.INFO,
            format=log_format,
            handlers=[
                file_handler,
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger('ComprehensiveLogger')
    
    def init_csv_files(self):
        """Inicializar archivos CSV con headers"""
        # Daily summary CSV
        if not self.csv_files['daily_summary'].exists():
            with open(self.csv_files['daily_summary'], 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'signals_generated', 'trades_executed', 
                    'breakeven_applied', 'trailing_applied', 'total_profit',
                    'active_positions', 'errors_count', 'notifications_sent'
                ])
        
        # Trades summary CSV
        if not self.csv_files['trades_summary'].exists():
            with open(self.csv_files['trades_summary'], 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'action', 'symbol', 'ticket', 'type', 
                    'entry_price', 'current_price', 'sl', 'tp', 'profit_usd', 
                    'profit_pips', 'strategy', 'confidence'
                ])
        
        # Risk actions CSV
        if not self.csv_files['risk_actions'].exists():
            with open(self.csv_files['risk_actions'], 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'action_type', 'symbol', 'ticket', 'old_sl', 
                    'new_sl', 'profit_pips', 'mode', 'success', 'reason'
                ])
    
    def _create_log_entry(self, log_type: str, level: str, component: str, 
                         message: str, data: Dict[str, Any] = None) -> LogEntry:
        """Crear entrada de log estructurada"""
        timestamp = datetime.now()
        
        return LogEntry(
            timestamp=timestamp.isoformat(),
            timestamp_readable=timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            log_type=log_type,
            level=level,
            component=component,
            message=message,
            data=data or {}
        )
    
    def _save_to_json(self, file_key: str, entry: LogEntry):
        """Guardar entrada en archivo JSON"""
        try:
            with self.lock:
                # Leer entradas existentes
                entries = []
                if self.files[file_key].exists():
                    with open(self.files[file_key], 'r', encoding='utf-8') as f:
                        try:
                            entries = json.load(f)
                        except json.JSONDecodeError:
                            entries = []
                
                # Agregar nueva entrada
                entries.append(asdict(entry))
                
                # Mantener solo últimas 10000 entradas por archivo
                entries = entries[-10000:]
                
                # Guardar
                with open(self.files[file_key], 'w', encoding='utf-8') as f:
                    json.dump(entries, f, indent=2, ensure_ascii=False)
                    
        except Exception as e:
            self.logger.error(f"Error guardando en {file_key}: {e}")
    
    def log_signal(self, signal_data: Dict[str, Any]):
        """Registrar señal de trading"""
        try:
            entry = self._create_log_entry(
                log_type='SIGNAL',
                level='INFO',
                component='SignalGenerator',
                message=f"Señal generada: {signal_data.get('symbol')} {signal_data.get('signal_type')}",
                data=signal_data
            )
            
            self._save_to_json('signals', entry)
            self.stats['signals_generated'] += 1
            
            # Log a CSV también
            self._log_to_trades_csv('SIGNAL_GENERATED', signal_data)
            
            self.logger.info(f"[SIGNAL] {signal_data.get('symbol')}: {signal_data.get('signal_type')} (Conf: {signal_data.get('confidence', 0):.1f}%)")
            
        except Exception as e:
            self.log_error('SIGNAL_LOGGING_ERROR', e, {'signal_data': signal_data})
    
    def log_trade_execution(self, trade_data: Dict[str, Any]):
        """Registrar ejecución de trade"""
        try:
            entry = self._create_log_entry(
                log_type='TRADE_EXECUTION',
                level='INFO',
                component='TradeExecutor',
                message=f"Trade ejecutado: {trade_data.get('symbol')} #{trade_data.get('ticket')}",
                data=trade_data
            )
            
            self._save_to_json('trades', entry)
            self.stats['trades_executed'] += 1
            
            # Log a CSV
            self._log_to_trades_csv('TRADE_EXECUTED', trade_data)
            
            self.logger.info(f"[TRADE] {trade_data.get('symbol')} #{trade_data.get('ticket')}: {trade_data.get('type')} @ {trade_data.get('price')}")
            
        except Exception as e:
            self.log_error('TRADE_LOGGING_ERROR', e, {'trade_data': trade_data})
    
    def log_risk_action(self, action_type: str, position_data: Dict[str, Any], success: bool = True, reason: str = ""):
        """Registrar acción de risk management"""
        try:
            entry = self._create_log_entry(
                log_type='RISK_MANAGEMENT',
                level='INFO',
                component='RiskManager',
                message=f"{action_type}: {position_data.get('symbol')} #{position_data.get('ticket')}",
                data={
                    'action_type': action_type,
                    'position_data': position_data,
                    'success': success,
                    'reason': reason
                }
            )
            
            self._save_to_json('risk_management', entry)
            
            # Actualizar estadísticas
            if success:
                if action_type == 'BREAKEVEN_APPLIED':
                    self.stats['breakeven_applied'] += 1
                elif action_type == 'TRAILING_APPLIED':
                    self.stats['trailing_applied'] += 1
            
            # Log a CSV
            self._log_to_risk_csv(action_type, position_data, success, reason)
            
            status = "SUCCESS" if success else "FAILED"
            self.logger.info(f"[RISK] {action_type}: {position_data.get('symbol')} #{position_data.get('ticket')} - {status}")
            
        except Exception as e:
            self.log_error('RISK_LOGGING_ERROR', e, {'action_type': action_type, 'position_data': position_data})
    
    def log_telegram_notification(self, notification_type: str, data: Dict[str, Any], success: bool = True):
        """Registrar notificación de Telegram"""
        try:
            entry = self._create_log_entry(
                log_type='TELEGRAM_NOTIFICATION',
                level='INFO',
                component='TelegramNotifier',
                message=f"Notificación {notification_type}: {'Enviada' if success else 'Fallida'}",
                data={
                    'notification_type': notification_type,
                    'data': data,
                    'success': success
                }
            )
            
            self._save_to_json('telegram_notifications', entry)
            
            if success:
                self.stats['notifications_sent'] += 1
            
            self.logger.info(f"[TELEGRAM] {notification_type}: {'OK' if success else 'FAILED'}")
            
        except Exception as e:
            self.log_error('TELEGRAM_LOGGING_ERROR', e, {'notification_type': notification_type})
    
    def log_market_data(self, symbol: str, data: Dict[str, Any]):
        """Registrar datos de mercado"""
        try:
            entry = self._create_log_entry(
                log_type='MARKET_DATA',
                level='DEBUG',
                component='MarketData',
                message=f"Datos de mercado: {symbol}",
                data={
                    'symbol': symbol,
                    'market_data': data
                }
            )
            
            self._save_to_json('market_data', entry)
            
        except Exception as e:
            self.log_error('MARKET_DATA_LOGGING_ERROR', e, {'symbol': symbol, 'data': data})
    
    def log_system_event(self, event_type: str, message: str, data: Dict[str, Any] = None):
        """Registrar evento del sistema"""
        try:
            entry = self._create_log_entry(
                log_type='SYSTEM_EVENT',
                level='INFO',
                component='System',
                message=message,
                data={
                    'event_type': event_type,
                    'details': data or {}
                }
            )
            
            self._save_to_json('system_events', entry)
            self.logger.info(f"[SYSTEM] {event_type}: {message}")
            
        except Exception as e:
            self.log_error('SYSTEM_LOGGING_ERROR', e, {'event_type': event_type, 'message': message})
    
    def log_error(self, error_type: str, error: Exception, context: Dict[str, Any] = None):
        """Registrar error"""
        try:
            entry = self._create_log_entry(
                log_type='ERROR',
                level='ERROR',
                component='System',
                message=f"{error_type}: {str(error)}",
                data={
                    'error_type': error_type,
                    'error_message': str(error),
                    'error_class': error.__class__.__name__,
                    'context': context or {}
                }
            )
            
            self._save_to_json('errors', entry)
            self.stats['errors_count'] += 1
            
            self.logger.error(f"[ERROR] {error_type}: {error}")
            
        except Exception as e:
            # Error logging the error - use basic logging
            self.logger.error(f"Critical error in error logging: {e}")
    
    def log_performance_metrics(self, metrics: Dict[str, Any]):
        """Registrar métricas de rendimiento"""
        try:
            entry = self._create_log_entry(
                log_type='PERFORMANCE',
                level='INFO',
                component='PerformanceMonitor',
                message="Métricas de rendimiento",
                data=metrics
            )
            
            self._save_to_json('performance', entry)
            
            # Log también estadísticas actuales
            current_stats = self.get_current_stats()
            entry.data['current_stats'] = current_stats
            
        except Exception as e:
            self.log_error('PERFORMANCE_LOGGING_ERROR', e, {'metrics': metrics})
    
    def _log_to_trades_csv(self, action: str, data: Dict[str, Any]):
        """Log a CSV de trades"""
        try:
            with open(self.csv_files['trades_summary'], 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    action,
                    data.get('symbol', ''),
                    data.get('ticket', ''),
                    data.get('type', ''),
                    data.get('entry_price', ''),
                    data.get('current_price', ''),
                    data.get('sl', ''),
                    data.get('tp', ''),
                    data.get('profit_usd', ''),
                    data.get('profit_pips', ''),
                    data.get('strategy', ''),
                    data.get('confidence', '')
                ])
        except Exception as e:
            self.logger.error(f"Error logging to trades CSV: {e}")
    
    def _log_to_risk_csv(self, action_type: str, position_data: Dict[str, Any], success: bool, reason: str):
        """Log a CSV de acciones de riesgo"""
        try:
            with open(self.csv_files['risk_actions'], 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    action_type,
                    position_data.get('symbol', ''),
                    position_data.get('ticket', ''),
                    position_data.get('old_sl', ''),
                    position_data.get('new_sl', ''),
                    position_data.get('profit_pips', ''),
                    position_data.get('mode', ''),
                    success,
                    reason
                ])
        except Exception as e:
            self.logger.error(f"Error logging to risk CSV: {e}")
    
    def get_current_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas actuales"""
        current_time = datetime.now()
        start_time = datetime.fromisoformat(self.stats['start_time'])
        uptime_seconds = (current_time - start_time).total_seconds()
        
        return {
            **self.stats,
            'current_time': current_time.isoformat(),
            'uptime_seconds': uptime_seconds,
            'uptime_readable': str(current_time - start_time)
        }
    
    def save_daily_summary(self):
        """Guardar resumen diario"""
        try:
            stats = self.get_current_stats()
            
            with open(self.csv_files['daily_summary'], 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    stats['signals_generated'],
                    stats['trades_executed'],
                    stats['breakeven_applied'],
                    stats['trailing_applied'],
                    0,  # total_profit - se puede calcular después
                    0,  # active_positions - se puede obtener de MT5
                    stats['errors_count'],
                    stats['notifications_sent']
                ])
        except Exception as e:
            self.log_error('DAILY_SUMMARY_ERROR', e)
    
    def create_daily_report(self) -> str:
        """Crear reporte diario completo"""
        try:
            stats = self.get_current_stats()
            
            report = f"""
REPORTE DIARIO COMPLETO - {datetime.now().strftime('%Y-%m-%d')}
================================================================

ESTADÍSTICAS GENERALES:
- Tiempo de actividad: {stats['uptime_readable']}
- Señales generadas: {stats['signals_generated']}
- Trades ejecutados: {stats['trades_executed']}
- Breakeven aplicados: {stats['breakeven_applied']}
- Trailing aplicados: {stats['trailing_applied']}
- Errores registrados: {stats['errors_count']}
- Notificaciones enviadas: {stats['notifications_sent']}

ARCHIVOS DE LOG GENERADOS:
"""
            
            for file_type, file_path in self.files.items():
                if file_path.exists():
                    size_kb = file_path.stat().st_size / 1024
                    report += f"- {file_type}: {file_path.name} ({size_kb:.1f} KB)\n"
            
            report += f"""

ARCHIVOS CSV PARA ANÁLISIS:
"""
            for file_type, file_path in self.csv_files.items():
                if file_path.exists():
                    size_kb = file_path.stat().st_size / 1024
                    report += f"- {file_type}: {file_path.name} ({size_kb:.1f} KB)\n"
            
            report += f"""
================================================================
Sistema de logging completo activo
Registrando TODA la actividad del trading algorítmico
================================================================
"""
            
            # Guardar reporte
            report_file = self.base_dir / f"daily_report_{self.date_str}.txt"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            return report
            
        except Exception as e:
            self.log_error('DAILY_REPORT_ERROR', e)
            return f"Error generando reporte: {e}"
    
    def shutdown(self):
        """Cerrar sistema de logging"""
        try:
            self.log_system_event('SYSTEM_SHUTDOWN', 'Sistema de logging cerrando')
            self.save_daily_summary()
            
            # Crear reporte final
            report = self.create_daily_report()
            print(report)
            
        except Exception as e:
            self.logger.error(f"Error durante shutdown: {e}")

# Instancia global para uso fácil
comprehensive_logger = ComprehensiveLogger()