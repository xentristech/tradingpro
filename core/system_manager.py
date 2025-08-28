"""
System Manager - Coordinador Principal
Gestiona todos los componentes del sistema de trading
"""
import os
import sys
import time
import threading
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path
import logging

# Añadir path del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent))

# Importaciones del sistema
from dotenv import load_dotenv
from core.state_manager import state_manager
from core.mt5_connection import mt5_connection
from core.rate_limiter import acquire_limit, get_rate_limit_stats
from core.circuit_breaker import circuit_manager
from core.health_check import health_monitor
from utils.logger import trading_logger, log_performance

# Importaciones de módulos de trading
from orchestrator.run import load_settings
from signals.llm_validator import validate_signal
from notifiers.telegram import send_message

logger = logging.getLogger(__name__)

class SystemManager:
    """Gestor principal del sistema de trading"""
    
    def __init__(self):
        # Cargar configuración
        load_dotenv('configs/.env')
        self.settings = load_settings()
        
        # Estado del sistema
        self.running = False
        self.mode = 'demo'
        self.debug = False
        
        # Threads
        self.trading_thread = None
        self.monitoring_thread = None
        
        # Event para detener threads
        self.stop_event = threading.Event()
        
        # Inicializar componentes
        self._initialize_components()
    
    def _initialize_components(self):
        """Inicializar todos los componentes del sistema"""
        logger.info("Inicializando componentes del sistema...")
        
        # Configurar callbacks de conexión MT5
        mt5_connection.on_connect = self._on_mt5_connect
        mt5_connection.on_disconnect = self._on_mt5_disconnect
        mt5_connection.on_reconnect = self._on_mt5_reconnect
        
        # Registrar observador de estado
        state_manager.register_observer(self._on_state_change)
        
        logger.info("✅ Componentes inicializados")
    
    def start(self, mode: str = 'demo', debug: bool = False):
        """
        Iniciar el sistema de trading
        
        Args:
            mode: 'demo' o 'live'
            debug: Si activar modo debug
        """
        if self.running:
            logger.warning("El sistema ya está en ejecución")
            return
        
        try:
            self.mode = mode
            self.debug = debug
            
            logger.info("="*70)
            logger.info(f"🚀 Iniciando sistema en modo {mode.upper()}")
            logger.info("="*70)
            
            # Actualizar estado
            state_manager.update(
                is_running=True,
                mode=mode,
                start_time=datetime.now()
            )
            
            # Conectar MT5
            if not mt5_connection.connect():
                raise Exception("No se pudo conectar a MT5")
            
            # Iniciar health monitoring
            health_monitor.start_monitoring(interval=60)
            
            # Iniciar threads
            self.stop_event.clear()
            self.running = True
            
            # Thread de trading
            self.trading_thread = threading.Thread(
                target=self._trading_loop,
                name="TradingThread",
                daemon=True
            )
            self.trading_thread.start()
            
            # Thread de monitoreo
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                name="MonitoringThread",
                daemon=True
            )
            self.monitoring_thread.start()
            
            # Notificar inicio
            self._notify_start()
            
            logger.info("✅ Sistema iniciado correctamente")
            
            # Mantener el sistema en ejecución
            self._main_loop()
            
        except KeyboardInterrupt:
            logger.info("Interrupción por teclado detectada")
            self.stop()
        except Exception as e:
            logger.exception(f"Error iniciando sistema: {e}")
            self.stop()
    
    def stop(self):
        """Detener el sistema de trading"""
        if not self.running:
            return
        
        logger.info("🛑 Deteniendo sistema...")
        
        # Señalar a los threads que se detengan
        self.stop_event.set()
        self.running = False
        
        # Esperar a que los threads terminen
        if self.trading_thread:
            self.trading_thread.join(timeout=10)
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=10)
        
        # Detener monitoreo de salud
        health_monitor.stop_monitoring()
        
        # Desconectar MT5
        mt5_connection.disconnect()
        
        # Actualizar estado
        state_manager.update(
            is_running=False,
            start_time=None
        )
        
        # Notificar detención
        self._notify_stop()
        
        logger.info("✅ Sistema detenido")
    
    def _main_loop(self):
        """Loop principal del sistema"""
        while self.running:
            try:
                # El loop principal solo espera
                time.sleep(1)
                
                # Verificar si los threads siguen vivos
                if not self.trading_thread.is_alive():
                    logger.error("Thread de trading murió, reiniciando...")
                    self._restart_trading_thread()
                
                if not self.monitoring_thread.is_alive():
                    logger.error("Thread de monitoreo murió, reiniciando...")
                    self._restart_monitoring_thread()
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error en loop principal: {e}")
                time.sleep(5)
    
    def _trading_loop(self):
        """Loop principal de trading"""
        logger.info("Thread de trading iniciado")
        
        while not self.stop_event.is_set():
            try:
                # Verificar si debemos operar
                if not self._should_trade():
                    time.sleep(30)
                    continue
                
                # Obtener datos de mercado con rate limiting
                if acquire_limit('twelvedata'):
                    market_data = self._get_market_data()
                    
                    if market_data:
                        # Analizar señales
                        signal = self._analyze_signals(market_data)
                        
                        if signal and signal.get('action') != 'HOLD':
                            # Ejecutar trade si es necesario
                            self._execute_trade(signal)
                
                # Gestionar posiciones abiertas
                self._manage_positions()
                
                # Esperar antes del siguiente ciclo
                poll_seconds = self.settings.get('POLL_SECONDS', 20)
                time.sleep(poll_seconds)
                
            except Exception as e:
                logger.error(f"Error en loop de trading: {e}")
                state_manager.update(
                    last_error=str(e),
                    error_count=state_manager.get('error_count') + 1
                )
                time.sleep(60)
        
        logger.info("Thread de trading detenido")
    
    def _monitoring_loop(self):
        """Loop de monitoreo y reportes"""
        logger.info("Thread de monitoreo iniciado")
        
        last_report = datetime.now()
        report_interval = 3600  # 1 hora
        
        while not self.stop_event.is_set():
            try:
                now = datetime.now()
                
                # Actualizar métricas
                self._update_metrics()
                
                # Generar reporte periódico
                if (now - last_report).seconds >= report_interval:
                    self._generate_report()
                    last_report = now
                
                # Verificar alertas
                self._check_alerts()
                
                # Esperar
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"Error en loop de monitoreo: {e}")
                time.sleep(60)
        
        logger.info("Thread de monitoreo detenido")
    
    def _should_trade(self) -> bool:
        """Verificar si debemos operar"""
        # Verificar modo
        if self.mode == 'live' and os.getenv('LIVE_TRADING', 'false').lower() != 'true':
            logger.warning("Modo LIVE pero LIVE_TRADING no está habilitado")
            return False
        
        # Verificar salud del sistema
        health = health_monitor.check_all()
        if not health['healthy']:
            logger.warning("Sistema no saludable, saltando trading")
            return False
        
        # Verificar límites diarios
        daily_loss = state_manager.get('daily_pnl')
        max_daily_loss = float(os.getenv('MAX_DAILY_LOSS', '200'))
        
        if daily_loss and daily_loss < -max_daily_loss:
            logger.warning(f"Límite de pérdida diaria alcanzado: ${daily_loss:.2f}")
            return False
        
        return True
    
    def _get_market_data(self) -> Optional[Dict]:
        """Obtener datos de mercado"""
        try:
            # Aquí iría la lógica para obtener datos
            # Por ahora retornamos None
            return None
        except Exception as e:
            logger.error(f"Error obteniendo datos de mercado: {e}")
            return None
    
    def _analyze_signals(self, market_data: Dict) -> Optional[Dict]:
        """Analizar señales de trading"""
        try:
            # Usar circuit breaker para proteger la llamada
            result = circuit_manager.call_with_breaker(
                'ollama',
                validate_signal,
                market_data
            )
            
            if result:
                state_manager.add_signal(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error analizando señales: {e}")
            return None
    
    def _execute_trade(self, signal: Dict):
        """Ejecutar trade basado en señal"""
        try:
            logger.info(f"Ejecutando trade: {signal}")
            # Aquí iría la lógica de ejecución
            
        except Exception as e:
            logger.error(f"Error ejecutando trade: {e}")
    
    def _manage_positions(self):
        """Gestionar posiciones abiertas"""
        try:
            positions = state_manager.get('open_positions')
            
            for position in positions:
                # Aquí iría la lógica de gestión
                pass
                
        except Exception as e:
            logger.error(f"Error gestionando posiciones: {e}")
    
    def _update_metrics(self):
        """Actualizar métricas del sistema"""
        try:
            # Obtener info de cuenta MT5
            if mt5_connection.is_connected():
                account_info = mt5_connection.execute_with_reconnect(
                    lambda: __import__('MetaTrader5').account_info()
                )
                
                if account_info:
                    state_manager.update(
                        balance=account_info.balance,
                        equity=account_info.equity,
                        margin=account_info.margin,
                        free_margin=account_info.margin_free
                    )
                    
                    # Log de rendimiento
                    log_performance({
                        'balance': account_info.balance,
                        'equity': account_info.equity,
                        'daily_pnl': state_manager.get('daily_pnl'),
                        'win_rate': state_manager.get_win_rate()
                    })
            
        except Exception as e:
            logger.error(f"Error actualizando métricas: {e}")
    
    def _generate_report(self):
        """Generar reporte periódico"""
        try:
            state = state_manager.get_dict()
            
            report = f"""
📊 **REPORTE DE TRADING**
========================
⏰ Tiempo: {state_manager.get_uptime()}
💰 Balance: ${state.get('balance', 0):.2f}
📈 P&L Diario: ${state.get('daily_pnl', 0):.2f}
🎯 Win Rate: {state_manager.get_win_rate():.1f}%
📍 Posiciones: {len(state.get('open_positions', []))}
⚠️ Errores: {state.get('error_count', 0)}
"""
            
            # Enviar por Telegram si está configurado
            if os.getenv('TELEGRAM_TOKEN'):
                send_message(report)
            
            logger.info(report)
            
        except Exception as e:
            logger.error(f"Error generando reporte: {e}")
    
    def _check_alerts(self):
        """Verificar condiciones de alerta"""
        try:
            state = state_manager.get_dict()
            
            # Alerta de pérdida
            if state.get('daily_pnl', 0) < -100:
                self._send_alert("⚠️ Pérdida diaria supera $100")
            
            # Alerta de errores
            if state.get('error_count', 0) > 10:
                self._send_alert("⚠️ Muchos errores detectados")
            
        except Exception as e:
            logger.error(f"Error verificando alertas: {e}")
    
    def _send_alert(self, message: str):
        """Enviar alerta"""
        logger.warning(f"ALERTA: {message}")
        
        if os.getenv('TELEGRAM_TOKEN'):
            try:
                send_message(f"🚨 ALERTA\n{message}")
            except Exception as e:
                logger.error(f"Error enviando alerta: {e}")
    
    def _restart_trading_thread(self):
        """Reiniciar thread de trading"""
        if not self.running:
            return
        
        self.trading_thread = threading.Thread(
            target=self._trading_loop,
            name="TradingThread",
            daemon=True
        )
        self.trading_thread.start()
    
    def _restart_monitoring_thread(self):
        """Reiniciar thread de monitoreo"""
        if not self.running:
            return
        
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            name="MonitoringThread",
            daemon=True
        )
        self.monitoring_thread.start()
    
    # Callbacks
    def _on_mt5_connect(self):
        """Callback cuando MT5 se conecta"""
        logger.info("✅ MT5 conectado")
        state_manager.update(mt5_connected=True)
    
    def _on_mt5_disconnect(self):
        """Callback cuando MT5 se desconecta"""
        logger.warning("⚠️ MT5 desconectado")
        state_manager.update(mt5_connected=False)
    
    def _on_mt5_reconnect(self):
        """Callback cuando MT5 se reconecta"""
        logger.info("✅ MT5 reconectado")
        state_manager.update(mt5_connected=True)
        self._send_alert("MT5 reconectado exitosamente")
    
    def _on_state_change(self, new_state: Dict):
        """Callback cuando el estado cambia"""
        # Aquí se pueden añadir acciones basadas en cambios de estado
        pass
    
    def _notify_start(self):
        """Notificar inicio del sistema"""
        message = f"""
🚀 **SISTEMA INICIADO**
Modo: {self.mode.upper()}
Servidor: {os.getenv('MT5_SERVER')}
Símbolo: {os.getenv('SYMBOL')}
"""
        
        if os.getenv('TELEGRAM_TOKEN'):
            try:
                send_message(message)
            except Exception as e:
                logger.error(f"Error notificando inicio: {e}")
    
    def _notify_stop(self):
        """Notificar detención del sistema"""
        message = f"""
🛑 **SISTEMA DETENIDO**
Uptime: {state_manager.get_uptime()}
Trades: {state_manager.get('total_trades')}
P&L: ${state_manager.get('daily_pnl', 0):.2f}
"""
        
        if os.getenv('TELEGRAM_TOKEN'):
            try:
                send_message(message)
            except Exception as e:
                logger.error(f"Error notificando detención: {e}")
    
    def get_status(self) -> Dict:
        """Obtener estado del sistema"""
        state = state_manager.get_dict()
        
        return {
            'bot_status': 'Running' if self.running else 'Stopped',
            'mode': self.mode,
            'uptime': state_manager.get_uptime(),
            'balance': state.get('balance', 0),
            'equity': state.get('equity', 0),
            'daily_pnl': state.get('daily_pnl', 0),
            'open_positions': len(state.get('open_positions', [])),
            'total_trades': state.get('total_trades', 0),
            'win_rate': state_manager.get_win_rate(),
            'last_signals': state.get('last_signals', [])[-5:],
            'health': health_monitor.check_all(),
            'rate_limits': get_rate_limit_stats(),
            'circuit_breakers': circuit_manager.get_all_status()
        }
