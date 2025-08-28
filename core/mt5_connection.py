"""
Sistema de Reconexión Automática para MetaTrader 5
Maneja desconexiones y reconecta automáticamente
"""
import os
import time
import threading
from typing import Optional, Callable, Any
from datetime import datetime, timedelta
import MetaTrader5 as mt5
import logging

logger = logging.getLogger(__name__)

class MT5ConnectionManager:
    """Gestor de conexión con reconexión automática para MT5"""
    
    def __init__(self, 
                 max_retries: int = 5,
                 retry_delay: int = 30,
                 heartbeat_interval: int = 60):
        """
        Args:
            max_retries: Número máximo de intentos de reconexión
            retry_delay: Segundos entre intentos de reconexión
            heartbeat_interval: Segundos entre verificaciones de conexión
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.heartbeat_interval = heartbeat_interval
        
        # Estado de conexión
        self.connected = False
        self.connecting = False
        self.last_connection = None
        self.connection_failures = 0
        
        # Configuración MT5
        self.mt5_config = {
            'path': os.getenv('MT5_PATH'),
            'login': int(os.getenv('MT5_LOGIN', '0')),
            'password': os.getenv('MT5_PASSWORD'),
            'server': os.getenv('MT5_SERVER'),
            'timeout': int(os.getenv('MT5_TIMEOUT', '60000'))
        }
        
        # Thread de heartbeat
        self.heartbeat_thread = None
        self.stop_heartbeat = threading.Event()
        
        # Callbacks
        self.on_connect = None
        self.on_disconnect = None
        self.on_reconnect = None
        
        # Lock para operaciones thread-safe
        self.lock = threading.RLock()
    
    def connect(self) -> bool:
        """Conectar a MT5"""
        with self.lock:
            if self.connected:
                return True
            
            if self.connecting:
                logger.warning("Ya hay un intento de conexión en progreso")
                return False
            
            self.connecting = True
            
        try:
            logger.info("Intentando conectar a MT5...")
            
            # Verificar configuración
            if not self._validate_config():
                logger.error("Configuración MT5 inválida")
                return False
            
            # Intentar inicializar MT5
            success = mt5.initialize(
                path=self.mt5_config['path'],
                login=self.mt5_config['login'],
                password=self.mt5_config['password'],
                server=self.mt5_config['server'],
                timeout=self.mt5_config['timeout']
            )
            
            if success:
                # Verificar que realmente estamos conectados
                account_info = mt5.account_info()
                if account_info:
                    with self.lock:
                        self.connected = True
                        self.last_connection = datetime.now()
                        self.connection_failures = 0
                    
                    logger.info(f"✅ Conectado a MT5 - Cuenta: {account_info.login}")
                    logger.info(f"   Balance: ${account_info.balance:.2f}")
                    logger.info(f"   Servidor: {account_info.server}")
                    
                    # Ejecutar callback
                    if self.on_connect:
                        self._safe_callback(self.on_connect)
                    
                    # Iniciar heartbeat
                    self._start_heartbeat()
                    
                    return True
                else:
                    logger.error("MT5 inicializado pero no se pudo obtener info de cuenta")
                    mt5.shutdown()
            else:
                error = mt5.last_error()
                logger.error(f"Fallo al inicializar MT5: {error}")
            
            with self.lock:
                self.connection_failures += 1
                
            return False
            
        except Exception as e:
            logger.exception(f"Error conectando a MT5: {e}")
            with self.lock:
                self.connection_failures += 1
            return False
            
        finally:
            with self.lock:
                self.connecting = False
    
    def disconnect(self):
        """Desconectar de MT5"""
        with self.lock:
            if not self.connected:
                return
            
            logger.info("Desconectando de MT5...")
            
            # Detener heartbeat
            self._stop_heartbeat()
            
            # Cerrar MT5
            try:
                mt5.shutdown()
            except Exception as e:
                logger.error(f"Error al cerrar MT5: {e}")
            
            self.connected = False
            
            # Ejecutar callback
            if self.on_disconnect:
                self._safe_callback(self.on_disconnect)
            
            logger.info("✅ Desconectado de MT5")
    
    def reconnect(self) -> bool:
        """Intentar reconectar a MT5"""
        logger.info("Iniciando proceso de reconexión...")
        
        # Desconectar primero si estamos conectados
        if self.connected:
            self.disconnect()
        
        # Intentar reconectar con reintentos
        for attempt in range(1, self.max_retries + 1):
            logger.info(f"Intento de reconexión {attempt}/{self.max_retries}")
            
            if self.connect():
                logger.info("✅ Reconexión exitosa")
                
                # Ejecutar callback
                if self.on_reconnect:
                    self._safe_callback(self.on_reconnect)
                
                return True
            
            if attempt < self.max_retries:
                wait_time = self.retry_delay * attempt  # Backoff exponencial
                logger.info(f"Esperando {wait_time}s antes del siguiente intento...")
                time.sleep(wait_time)
        
        logger.error(f"❌ Fallo al reconectar después de {self.max_retries} intentos")
        return False
    
    def ensure_connected(self) -> bool:
        """Asegurar que estamos conectados, reconectar si es necesario"""
        if self.is_connected():
            return True
        
        logger.warning("No hay conexión con MT5, intentando reconectar...")
        return self.reconnect()
    
    def is_connected(self) -> bool:
        """Verificar si estamos conectados"""
        with self.lock:
            if not self.connected:
                return False
            
            # Verificar que MT5 responde
            try:
                terminal_info = mt5.terminal_info()
                return terminal_info is not None
            except Exception:
                self.connected = False
                return False
    
    def execute_with_reconnect(self, func: Callable, *args, **kwargs) -> Any:
        """
        Ejecutar una función con reconexión automática si falla
        
        Args:
            func: Función a ejecutar
            *args, **kwargs: Argumentos para la función
            
        Returns:
            Resultado de la función o None si falla
        """
        # Primer intento
        if self.ensure_connected():
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error ejecutando {func.__name__}: {e}")
                
                # Verificar si es un error de conexión
                if "IPC" in str(e) or "connection" in str(e).lower():
                    logger.info("Detectado error de conexión, intentando reconectar...")
                    if self.reconnect():
                        # Segundo intento después de reconectar
                        try:
                            return func(*args, **kwargs)
                        except Exception as e2:
                            logger.error(f"Fallo después de reconexión: {e2}")
        
        return None
    
    def _validate_config(self) -> bool:
        """Validar configuración MT5"""
        required = ['login', 'password', 'server']
        
        for field in required:
            if not self.mt5_config.get(field):
                logger.error(f"Falta configuración MT5: {field}")
                return False
        
        return True
    
    def _start_heartbeat(self):
        """Iniciar thread de heartbeat"""
        if self.heartbeat_thread and self.heartbeat_thread.is_alive():
            return
        
        self.stop_heartbeat.clear()
        self.heartbeat_thread = threading.Thread(
            target=self._heartbeat_loop,
            daemon=True
        )
        self.heartbeat_thread.start()
        logger.debug("Heartbeat iniciado")
    
    def _stop_heartbeat(self):
        """Detener thread de heartbeat"""
        if self.heartbeat_thread:
            self.stop_heartbeat.set()
            self.heartbeat_thread.join(timeout=5)
            logger.debug("Heartbeat detenido")
    
    def _heartbeat_loop(self):
        """Loop de heartbeat para verificar conexión"""
        while not self.stop_heartbeat.is_set():
            try:
                if not self.is_connected():
                    logger.warning("Heartbeat detectó desconexión")
                    
                    # Intentar reconectar
                    self.reconnect()
                
            except Exception as e:
                logger.error(f"Error en heartbeat: {e}")
            
            # Esperar hasta el siguiente heartbeat
            self.stop_heartbeat.wait(self.heartbeat_interval)
    
    def _safe_callback(self, callback: Callable):
        """Ejecutar callback de forma segura"""
        try:
            callback()
        except Exception as e:
            logger.error(f"Error en callback: {e}")
    
    def get_status(self) -> dict:
        """Obtener estado de la conexión"""
        with self.lock:
            return {
                'connected': self.connected,
                'connecting': self.connecting,
                'last_connection': self.last_connection,
                'connection_failures': self.connection_failures,
                'server': self.mt5_config['server'],
                'login': self.mt5_config['login']
            }

# Instancia global
mt5_connection = MT5ConnectionManager()

# Funciones de conveniencia
def ensure_mt5_connected() -> bool:
    """Asegurar conexión con MT5"""
    return mt5_connection.ensure_connected()

def mt5_execute(func: Callable, *args, **kwargs) -> Any:
    """Ejecutar función con reconexión automática"""
    return mt5_connection.execute_with_reconnect(func, *args, **kwargs)
