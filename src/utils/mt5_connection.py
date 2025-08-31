"""
MT5 Connection Manager - Gestión robusta de conexión con MetaTrader 5
Incluye reconexión automática, reintentos y health checks
"""
import os
import time
import threading
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import logging
import MetaTrader5 as mt5

logger = logging.getLogger(__name__)

class MT5ConnectionManager:
    """
    Gestor de conexión con MetaTrader 5
    Maneja reconexión automática, reintentos y monitoreo de salud
    """
    
    def __init__(self, 
                 max_retries: int = 5,
                 retry_delay: float = 5.0,
                 health_check_interval: int = 30):
        """
        Inicializa el gestor de conexión MT5
        
        Args:
            max_retries: Número máximo de reintentos de conexión
            retry_delay: Segundos entre reintentos
            health_check_interval: Segundos entre health checks
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.health_check_interval = health_check_interval
        
        # Configuración desde .env
        self.config = {
            'path': os.getenv('MT5_PATH'),
            'login': int(os.getenv('MT5_LOGIN', 0)),
            'password': os.getenv('MT5_PASSWORD'),
            'server': os.getenv('MT5_SERVER'),
            'timeout': int(os.getenv('MT5_TIMEOUT', 60000))
        }
        
        # Estado de conexión
        self._connected = False
        self._connection_lock = threading.RLock()
        self._last_error = None
        self._reconnect_attempts = 0
        self._last_health_check = time.time()
        
        # Thread de monitoreo
        self._monitor_thread = None
        self._stop_monitor = threading.Event()
        
        # Estadísticas
        self.stats = {
            'connections': 0,
            'disconnections': 0,
            'failed_attempts': 0,
            'successful_trades': 0,
            'failed_trades': 0
        }
        
        logger.info("MT5ConnectionManager inicializado")
    
    def connect(self) -> bool:
        """
        Establece conexión con MT5
        
        Returns:
            bool: True si la conexión fue exitosa
        """
        with self._connection_lock:
            if self._connected:
                logger.debug("Ya conectado a MT5")
                return True
            
            logger.info("Iniciando conexión con MT5...")
            
            for attempt in range(self.max_retries):
                try:
                    # Intentar inicializar MT5
                    kwargs = {}
                    if self.config['path']:
                        kwargs['path'] = self.config['path']
                    if self.config['login']:
                        kwargs['login'] = self.config['login']
                    if self.config['password']:
                        kwargs['password'] = self.config['password']
                    if self.config['server']:
                        kwargs['server'] = self.config['server']
                    if self.config['timeout']:
                        kwargs['timeout'] = self.config['timeout']
                    
                    if not kwargs:
                        # Intento básico sin parámetros
                        success = mt5.initialize()
                    else:
                        success = mt5.initialize(**kwargs)
                    
                    if success:
                        # Verificar conexión
                        account_info = mt5.account_info()
                        if account_info is not None:
                            self._connected = True
                            self._reconnect_attempts = 0
                            self.stats['connections'] += 1
                            
                            logger.info(f"✅ Conectado a MT5 - Cuenta: {account_info.login}")
                            logger.info(f"   Balance: ${account_info.balance:.2f}")
                            logger.info(f"   Servidor: {account_info.server}")
                            
                            # Iniciar monitoreo
                            self._start_monitor()
                            
                            return True
                        else:
                            logger.warning("MT5 inicializado pero no se pudo obtener info de cuenta")
                    
                    # Obtener error
                    error = mt5.last_error()
                    self._last_error = error
                    logger.warning(f"Intento {attempt + 1}/{self.max_retries} falló: {error}")
                    
                except Exception as e:
                    logger.error(f"Excepción durante conexión: {e}")
                    self._last_error = str(e)
                
                # Esperar antes de reintentar
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    
            # Todos los intentos fallaron
            self.stats['failed_attempts'] += 1
            logger.error(f"❌ No se pudo conectar a MT5 después de {self.max_retries} intentos")
            return False
    
    def disconnect(self):
        """Desconecta de MT5"""
        with self._connection_lock:
            if self._connected:
                try:
                    # Detener monitoreo
                    self._stop_monitor.set()
                    if self._monitor_thread and self._monitor_thread.is_alive():
                        self._monitor_thread.join(timeout=2)
                    
                    # Cerrar MT5
                    mt5.shutdown()
                    self._connected = False
                    self.stats['disconnections'] += 1
                    
                    logger.info("Desconectado de MT5")
                except Exception as e:
                    logger.error(f"Error durante desconexión: {e}")
    
    def is_connected(self) -> bool:
        """
        Verifica si está conectado a MT5
        
        Returns:
            bool: True si está conectado y funcionando
        """
        with self._connection_lock:
            if not self._connected:
                return False
            
            # Verificar que MT5 responde
            try:
                terminal_info = mt5.terminal_info()
                return terminal_info is not None and terminal_info.connected
            except:
                self._connected = False
                return False
    
    def reconnect(self) -> bool:
        """
        Intenta reconectar a MT5
        
        Returns:
            bool: True si la reconexión fue exitosa
        """
        logger.info("Intentando reconectar a MT5...")
        
        with self._connection_lock:
            self._reconnect_attempts += 1
            
            # Desconectar primero si es necesario
            if self._connected:
                self.disconnect()
            
            # Espera progresiva entre reconexiones
            wait_time = min(self.retry_delay * self._reconnect_attempts, 60)
            logger.info(f"Esperando {wait_time}s antes de reconectar...")
            time.sleep(wait_time)
            
            # Intentar reconectar
            return self.connect()
    
    def _start_monitor(self):
        """Inicia el thread de monitoreo de conexión"""
        if self._monitor_thread and self._monitor_thread.is_alive():
            return
        
        self._stop_monitor.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_connection)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
        logger.debug("Monitor de conexión iniciado")
    
    def _monitor_connection(self):
        """Thread que monitorea la salud de la conexión"""
        logger.debug("Monitor de conexión MT5 activo")
        
        while not self._stop_monitor.is_set():
            try:
                # Health check periódico
                if time.time() - self._last_health_check > self.health_check_interval:
                    self._last_health_check = time.time()
                    
                    if not self.is_connected():
                        logger.warning("⚠️ Conexión MT5 perdida, intentando reconectar...")
                        
                        # Intentar reconexión automática
                        if self.reconnect():
                            logger.info("✅ Reconexión exitosa")
                        else:
                            logger.error("❌ Reconexión fallida")
                
                # Esperar antes del próximo check
                self._stop_monitor.wait(timeout=5)
                
            except Exception as e:
                logger.error(f"Error en monitor de conexión: {e}")
                time.sleep(10)
        
        logger.debug("Monitor de conexión detenido")
    
    def ensure_connected(self) -> bool:
        """
        Asegura que hay conexión activa, reconectando si es necesario
        
        Returns:
            bool: True si hay conexión activa
        """
        if self.is_connected():
            return True
        
        logger.warning("No hay conexión activa, intentando establecer...")
        return self.reconnect()
    
    def execute_with_retry(self, func, *args, max_retries: int = 3, **kwargs):
        """
        Ejecuta una función MT5 con reintentos automáticos
        
        Args:
            func: Función a ejecutar
            max_retries: Número máximo de reintentos
            *args, **kwargs: Argumentos para la función
            
        Returns:
            Resultado de la función o None si falla
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Asegurar conexión
                if not self.ensure_connected():
                    raise ConnectionError("No se pudo establecer conexión con MT5")
                
                # Ejecutar función
                result = func(*args, **kwargs)
                
                # Verificar si fue exitoso
                if result is not None:
                    return result
                
                # Obtener último error
                last_error = mt5.last_error()
                logger.warning(f"Intento {attempt + 1} falló: {last_error}")
                
            except Exception as e:
                last_error = str(e)
                logger.error(f"Excepción en intento {attempt + 1}: {e}")
            
            # Esperar antes de reintentar
            if attempt < max_retries - 1:
                time.sleep(2)
        
        logger.error(f"Operación falló después de {max_retries} intentos. Último error: {last_error}")
        return None
    
    def get_account_info(self) -> Optional[Any]:
        """
        Obtiene información de la cuenta
        
        Returns:
            AccountInfo o None si falla
        """
        def _get_info():
            return mt5.account_info()
        
        return self.execute_with_retry(_get_info)
    
    def get_symbol_info(self, symbol: str) -> Optional[Any]:
        """
        Obtiene información de un símbolo
        
        Args:
            symbol: Símbolo a consultar
            
        Returns:
            SymbolInfo o None si falla
        """
        def _get_symbol():
            mt5.symbol_select(symbol, True)
            return mt5.symbol_info(symbol)
        
        return self.execute_with_retry(_get_symbol)
    
    def get_symbol_tick(self, symbol: str) -> Optional[Any]:
        """
        Obtiene el tick actual de un símbolo
        
        Args:
            symbol: Símbolo a consultar
            
        Returns:
            Tick o None si falla
        """
        def _get_tick():
            return mt5.symbol_info_tick(symbol)
        
        return self.execute_with_retry(_get_tick)
    
    def get_open_positions(self, symbol: Optional[str] = None) -> List[Any]:
        """
        Obtiene posiciones abiertas
        
        Args:
            symbol: Filtrar por símbolo (None para todas)
            
        Returns:
            Lista de posiciones
        """
        def _get_positions():
            if symbol:
                positions = mt5.positions_get(symbol=symbol)
            else:
                positions = mt5.positions_get()
            return list(positions) if positions else []
        
        result = self.execute_with_retry(_get_positions)
        return result if result is not None else []
    
    def place_order(self, request: Dict[str, Any]) -> Optional[Any]:
        """
        Coloca una orden
        
        Args:
            request: Diccionario con parámetros de la orden
            
        Returns:
            OrderSendResult o None si falla
        """
        def _send_order():
            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                self.stats['successful_trades'] += 1
                logger.info(f"✅ Orden ejecutada: {result.order}")
                return result
            else:
                self.stats['failed_trades'] += 1
                logger.warning(f"Orden rechazada: {result.retcode if result else 'None'}")
                return None
        
        return self.execute_with_retry(_send_order)
    
    def close_position(self, ticket: int, volume: Optional[float] = None) -> bool:
        """
        Cierra una posición
        
        Args:
            ticket: Ticket de la posición
            volume: Volumen a cerrar (None para todo)
            
        Returns:
            bool: True si se cerró exitosamente
        """
        try:
            # Obtener información de la posición
            positions = self.get_open_positions()
            position = next((p for p in positions if p.ticket == ticket), None)
            
            if not position:
                logger.warning(f"Posición {ticket} no encontrada")
                return False
            
            # Preparar orden de cierre
            symbol = position.symbol
            symbol_info = self.get_symbol_info(symbol)
            
            if not symbol_info:
                logger.error(f"No se pudo obtener info del símbolo {symbol}")
                return False
            
            # Determinar tipo de orden y precio
            if position.type == mt5.ORDER_TYPE_BUY:
                order_type = mt5.ORDER_TYPE_SELL
                price = self.get_symbol_tick(symbol).bid
            else:
                order_type = mt5.ORDER_TYPE_BUY
                price = self.get_symbol_tick(symbol).ask
            
            # Volumen a cerrar
            close_volume = volume if volume else position.volume
            
            # Preparar request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "position": ticket,
                "type": order_type,
                "volume": close_volume,
                "price": price,
                "deviation": int(os.getenv('MT5_DEVIATION', 20)),
                "magic": int(os.getenv('MT5_MAGIC', 20250817)),
                "comment": "Close by bot",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC
            }
            
            # Ejecutar cierre
            result = self.place_order(request)
            return result is not None
            
        except Exception as e:
            logger.error(f"Error cerrando posición {ticket}: {e}")
            return False
    
    def modify_position(self, ticket: int, sl: Optional[float] = None, tp: Optional[float] = None) -> bool:
        """
        Modifica SL/TP de una posición
        
        Args:
            ticket: Ticket de la posición
            sl: Nuevo stop loss (None para no cambiar)
            tp: Nuevo take profit (None para no cambiar)
            
        Returns:
            bool: True si se modificó exitosamente
        """
        try:
            # Obtener posición actual
            positions = self.get_open_positions()
            position = next((p for p in positions if p.ticket == ticket), None)
            
            if not position:
                logger.warning(f"Posición {ticket} no encontrada")
                return False
            
            # Preparar request
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": ticket,
                "sl": sl if sl is not None else position.sl,
                "tp": tp if tp is not None else position.tp
            }
            
            # Ejecutar modificación
            result = self.place_order(request)
            
            if result:
                logger.info(f"✅ Posición {ticket} modificada: SL={sl}, TP={tp}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error modificando posición {ticket}: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de conexión
        
        Returns:
            Dict con estadísticas
        """
        return {
            **self.stats,
            'connected': self._connected,
            'reconnect_attempts': self._reconnect_attempts,
            'last_error': self._last_error
        }
