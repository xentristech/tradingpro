"""
Logger Configuration - Configuración del Sistema de Logging
Maneja todos los logs del sistema de trading
Version: 3.0.0
"""
import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path
import colorlog
import json

def setup_logging(level=logging.INFO, log_dir='logs', console=True, file=True):
    """
    Configura el sistema de logging
    Args:
        level: Nivel de logging
        log_dir: Directorio para logs
        console: Habilitar logs en consola
        file: Habilitar logs en archivo
    Returns:
        Logger configurado
    """
    # Crear directorio de logs
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Nombre del archivo de log con timestamp
    log_file = log_path / f"algo_trader_{datetime.now().strftime('%Y%m%d')}.log"
    
    # Formato para archivo
    file_formatter = logging.Formatter(
        '%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Formato para consola con colores
    console_formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s',
        datefmt='%H:%M:%S',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        }
    )
    
    # Obtener root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Limpiar handlers existentes
    root_logger.handlers.clear()
    
    # Handler para archivo
    if file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Handler para consola
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    # Handler especial para errores críticos
    error_file = log_path / f"errors_{datetime.now().strftime('%Y%m%d')}.log"
    error_handler = logging.FileHandler(error_file, encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(file_formatter)
    root_logger.addHandler(error_handler)
    
    # Configurar loggers específicos
    configure_module_loggers()
    
    # Log inicial
    root_logger.info("="*60)
    root_logger.info("ALGO TRADER v3.0 - Sistema de Trading Algorítmico")
    root_logger.info(f"Logging inicializado - Nivel: {logging.getLevelName(level)}")
    root_logger.info("="*60)
    
    return root_logger

def configure_module_loggers():
    """Configura niveles específicos para módulos"""
    # Silenciar logs muy verbosos
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    
    # Configurar niveles específicos
    logging.getLogger('broker.mt5_connection').setLevel(logging.INFO)
    logging.getLogger('data.data_manager').setLevel(logging.INFO)
    logging.getLogger('signals.signal_generator').setLevel(logging.INFO)
    logging.getLogger('risk.risk_manager').setLevel(logging.INFO)
    logging.getLogger('ml.ml_predictor').setLevel(logging.INFO)

class TradingLogger:
    """Logger especializado para operaciones de trading"""
    
    def __init__(self, name='TradingLogger', trade_log_dir='logs/trades'):
        """
        Inicializa el trading logger
        Args:
            name: Nombre del logger
            trade_log_dir: Directorio para logs de trades
        """
        self.logger = logging.getLogger(name)
        self.trade_log_dir = Path(trade_log_dir)
        self.trade_log_dir.mkdir(parents=True, exist_ok=True)
        
        # Archivo de log de trades
        self.trade_log_file = self.trade_log_dir / f"trades_{datetime.now().strftime('%Y%m')}.json"
        
    def log_trade(self, trade_data):
        """
        Registra una operación
        Args:
            trade_data: Datos de la operación
        """
        try:
            # Agregar timestamp
            trade_data['timestamp'] = datetime.now().isoformat()
            
            # Leer trades existentes
            trades = []
            if self.trade_log_file.exists():
                with open(self.trade_log_file, 'r') as f:
                    content = f.read()
                    if content:
                        trades = json.loads(content)
            
            # Agregar nuevo trade
            trades.append(trade_data)
            
            # Guardar
            with open(self.trade_log_file, 'w') as f:
                json.dump(trades, f, indent=2)
            
            # Log normal
            self.logger.info(f"Trade registrado: {trade_data.get('symbol')} - {trade_data.get('type')}")
            
        except Exception as e:
            self.logger.error(f"Error registrando trade: {e}")
    
    def log_position_update(self, position_data):
        """
        Registra actualización de posición
        Args:
            position_data: Datos de la posición
        """
        self.logger.info(
            f"Position Update - {position_data.get('symbol')}: "
            f"PnL: ${position_data.get('pnl', 0):.2f}"
        )
    
    def log_signal(self, signal_data):
        """
        Registra una señal generada
        Args:
            signal_data: Datos de la señal
        """
        self.logger.info(
            f"Signal Generated - Direction: {signal_data.get('direction')}, "
            f"Strength: {signal_data.get('strength', 0):.2f}"
        )
    
    def log_error(self, error, context=None):
        """
        Registra un error con contexto
        Args:
            error: Exception o mensaje de error
            context: Contexto adicional
        """
        error_data = {
            'timestamp': datetime.now().isoformat(),
            'error': str(error),
            'context': context
        }
        
        # Guardar en archivo de errores
        error_file = self.trade_log_dir / f"errors_{datetime.now().strftime('%Y%m%d')}.json"
        
        try:
            errors = []
            if error_file.exists():
                with open(error_file, 'r') as f:
                    content = f.read()
                    if content:
                        errors = json.loads(content)
            
            errors.append(error_data)
            
            with open(error_file, 'w') as f:
                json.dump(errors, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error guardando log de error: {e}")
        
        # Log normal
        self.logger.error(f"Error: {error} | Context: {context}")
    
    def get_trade_history(self, limit=None):
        """
        Obtiene historial de trades
        Args:
            limit: Límite de trades a retornar
        Returns:
            Lista de trades
        """
        if not self.trade_log_file.exists():
            return []
        
        try:
            with open(self.trade_log_file, 'r') as f:
                trades = json.load(f)
                
            if limit:
                return trades[-limit:]
            return trades
            
        except Exception as e:
            self.logger.error(f"Error leyendo historial: {e}")
            return []

class PerformanceLogger:
    """Logger para métricas de performance"""
    
    def __init__(self, metrics_file='logs/performance_metrics.json'):
        """
        Inicializa el performance logger
        Args:
            metrics_file: Archivo para guardar métricas
        """
        self.logger = logging.getLogger('PerformanceLogger')
        self.metrics_file = Path(metrics_file)
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Cargar métricas existentes
        self.metrics = self._load_metrics()
    
    def _load_metrics(self):
        """Carga métricas desde archivo"""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'total_pnl': 0.0,
            'best_trade': 0.0,
            'worst_trade': 0.0,
            'daily_metrics': {}
        }
    
    def log_trade_result(self, pnl, symbol=None):
        """
        Registra resultado de trade
        Args:
            pnl: Ganancia/pérdida
            symbol: Símbolo operado
        """
        self.metrics['total_trades'] += 1
        
        if pnl > 0:
            self.metrics['winning_trades'] += 1
        else:
            self.metrics['losing_trades'] += 1
        
        self.metrics['total_pnl'] += pnl
        self.metrics['best_trade'] = max(self.metrics['best_trade'], pnl)
        self.metrics['worst_trade'] = min(self.metrics['worst_trade'], pnl)
        
        # Métricas diarias
        today = datetime.now().strftime('%Y-%m-%d')
        if today not in self.metrics['daily_metrics']:
            self.metrics['daily_metrics'][today] = {
                'trades': 0,
                'pnl': 0.0,
                'wins': 0,
                'losses': 0
            }
        
        daily = self.metrics['daily_metrics'][today]
        daily['trades'] += 1
        daily['pnl'] += pnl
        if pnl > 0:
            daily['wins'] += 1
        else:
            daily['losses'] += 1
        
        # Guardar
        self._save_metrics()
        
        # Log
        self.logger.info(f"Trade Result - Symbol: {symbol}, PnL: ${pnl:.2f}")
    
    def _save_metrics(self):
        """Guarda métricas en archivo"""
        try:
            with open(self.metrics_file, 'w') as f:
                json.dump(self.metrics, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error guardando métricas: {e}")
    
    def get_summary(self):
        """
        Obtiene resumen de performance
        Returns:
            Dict con resumen
        """
        total = self.metrics['total_trades']
        if total == 0:
            return {'message': 'No hay trades registrados'}
        
        return {
            'total_trades': total,
            'win_rate': (self.metrics['winning_trades'] / total * 100),
            'total_pnl': self.metrics['total_pnl'],
            'avg_trade': self.metrics['total_pnl'] / total,
            'best_trade': self.metrics['best_trade'],
            'worst_trade': self.metrics['worst_trade']
        }

# Testing
if __name__ == "__main__":
    # Test setup logging
    logger = setup_logging(level=logging.DEBUG)
    
    logger.debug("Mensaje de debug")
    logger.info("Mensaje informativo")
    logger.warning("Mensaje de advertencia")
    logger.error("Mensaje de error")
    logger.critical("Mensaje crítico")
    
    # Test trading logger
    trade_logger = TradingLogger()
    
    # Registrar un trade
    trade_data = {
        'symbol': 'BTCUSD',
        'type': 'buy',
        'price': 43000,
        'volume': 0.1,
        'sl': 42500,
        'tp': 44000
    }
    trade_logger.log_trade(trade_data)
    
    # Test performance logger
    perf_logger = PerformanceLogger()
    
    # Registrar resultados
    perf_logger.log_trade_result(150.50, 'BTCUSD')
    perf_logger.log_trade_result(-75.25, 'ETHUSD')
    perf_logger.log_trade_result(225.00, 'SOLUSD')
    
    # Obtener resumen
    summary = perf_logger.get_summary()
    print("\n📊 Performance Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")
