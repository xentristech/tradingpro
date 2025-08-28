"""
Sistema de Logging Avanzado con Rotación
Incluye rotación por tamaño y tiempo, colores, y múltiples niveles
"""
import os
import sys
import logging
import logging.handlers
from pathlib import Path
from typing import Optional
from datetime import datetime
import json

# Colores ANSI para consola
class ColoredFormatter(logging.Formatter):
    """Formatter con colores para consola"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # Aplicar color según el nivel
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        
        # Colorear el mensaje si es error o crítico
        if record.levelno >= logging.ERROR:
            record.msg = f"{self.COLORS[levelname]}{record.msg}{self.RESET}"
        
        return super().format(record)

class JsonFormatter(logging.Formatter):
    """Formatter para logs en formato JSON"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Añadir información de excepción si existe
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Añadir campos extra si existen
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 
                          'funcName', 'levelname', 'levelno', 'lineno', 
                          'module', 'msecs', 'pathname', 'process', 'processName',
                          'relativeCreated', 'thread', 'threadName', 'exc_info',
                          'exc_text', 'stack_info']:
                log_data[key] = value
        
        return json.dumps(log_data)

def setup_rotating_logger(name: str,
                         log_file: str,
                         level: int = logging.INFO,
                         max_bytes: int = 10*1024*1024,  # 10MB
                         backup_count: int = 10,
                         console: bool = True,
                         json_format: bool = False) -> logging.Logger:
    """
    Configurar logger con rotación automática
    
    Args:
        name: Nombre del logger
        log_file: Archivo de log
        level: Nivel de logging
        max_bytes: Tamaño máximo del archivo antes de rotar
        backup_count: Número de backups a mantener
        console: Si mostrar logs en consola
        json_format: Si usar formato JSON
        
    Returns:
        Logger configurado
    """
    # Crear directorio de logs si no existe
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Crear logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Limpiar handlers existentes
    logger.handlers = []
    
    # Handler para archivo con rotación por tamaño
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    
    # Formatter para archivo
    if json_format:
        file_formatter = JsonFormatter()
    else:
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Handler para consola si está habilitado
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        
        # Usar formatter con colores para consola
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(name)-12s - %(levelname)-8s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    return logger

def setup_time_rotating_logger(name: str,
                              log_file: str,
                              when: str = 'midnight',
                              interval: int = 1,
                              backup_count: int = 30,
                              level: int = logging.INFO) -> logging.Logger:
    """
    Configurar logger con rotación por tiempo
    
    Args:
        name: Nombre del logger
        log_file: Archivo de log
        when: Cuándo rotar ('midnight', 'h', 'd', 'w0'-'w6')
        interval: Intervalo de rotación
        backup_count: Número de backups a mantener
        level: Nivel de logging
        
    Returns:
        Logger configurado
    """
    # Crear directorio de logs si no existe
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Crear logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Limpiar handlers existentes
    logger.handlers = []
    
    # Handler para archivo con rotación por tiempo
    time_handler = logging.handlers.TimedRotatingFileHandler(
        log_file,
        when=when,
        interval=interval,
        backupCount=backup_count,
        encoding='utf-8'
    )
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    time_handler.setFormatter(formatter)
    logger.addHandler(time_handler)
    
    return logger

class TradingLogger:
    """Logger especializado para trading con métricas"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Logger principal
        self.main_logger = setup_rotating_logger(
            'trading_main',
            self.log_dir / 'trading.log',
            level=logging.INFO
        )
        
        # Logger de trades (JSON para análisis)
        self.trade_logger = setup_rotating_logger(
            'trading_trades',
            self.log_dir / 'trades.json',
            level=logging.INFO,
            json_format=True,
            console=False
        )
        
        # Logger de errores
        self.error_logger = setup_rotating_logger(
            'trading_errors',
            self.log_dir / 'errors.log',
            level=logging.ERROR,
            max_bytes=50*1024*1024,  # 50MB para errores
            console=False
        )
        
        # Logger de rendimiento
        self.performance_logger = setup_time_rotating_logger(
            'trading_performance',
            self.log_dir / 'performance.log',
            when='midnight',
            backup_count=90  # Mantener 3 meses
        )
    
    def log_trade(self, trade_data: dict):
        """Registrar trade con datos estructurados"""
        self.trade_logger.info('Trade ejecutado', extra=trade_data)
        
        # También en el log principal
        self.main_logger.info(
            f"Trade: {trade_data.get('action')} {trade_data.get('symbol')} "
            f"@ {trade_data.get('price')} - PnL: {trade_data.get('pnl', 0)}"
        )
    
    def log_signal(self, signal_data: dict):
        """Registrar señal de trading"""
        self.main_logger.info(
            f"Señal: {signal_data.get('action')} {signal_data.get('symbol')} "
            f"- Confianza: {signal_data.get('confidence', 0):.2%}"
        )
    
    def log_error(self, error: str, exc_info: bool = True):
        """Registrar error con stack trace"""
        self.error_logger.error(error, exc_info=exc_info)
        self.main_logger.error(error)
    
    def log_performance(self, metrics: dict):
        """Registrar métricas de rendimiento"""
        self.performance_logger.info(
            f"Rendimiento - Balance: ${metrics.get('balance', 0):.2f}, "
            f"PnL Diario: ${metrics.get('daily_pnl', 0):.2f}, "
            f"Win Rate: {metrics.get('win_rate', 0):.2%}",
            extra=metrics
        )

# Logger global para el sistema
trading_logger = TradingLogger()

# Funciones de conveniencia
def log_trade(trade_data: dict):
    """Registrar un trade"""
    trading_logger.log_trade(trade_data)

def log_signal(signal_data: dict):
    """Registrar una señal"""
    trading_logger.log_signal(signal_data)

def log_error(error: str, exc_info: bool = True):
    """Registrar un error"""
    trading_logger.log_error(error, exc_info)

def log_performance(metrics: dict):
    """Registrar métricas de rendimiento"""
    trading_logger.log_performance(metrics)
