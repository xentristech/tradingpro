"""
MT5 Connection Manager - Sistema Profesional de Trading
Version: 3.0.0
"""
import os
import time
import logging
import subprocess
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class MT5Connection:
    """
    Gestor profesional de conexión con MetaTrader 5
    Incluye reconexión automática, gestión de errores y logging
    """
    
    def __init__(self):
        """Inicializa el gestor de conexión MT5"""
        # Cargar configuración
        load_dotenv('configs/.env')
        
        self.login = int(os.getenv('MT5_LOGIN', '0'))
        self.password = os.getenv('MT5_PASSWORD', '')
        self.server = os.getenv('MT5_SERVER', '')
        self.timeout = int(os.getenv('MT5_TIMEOUT', '60000'))
        self.magic = int(os.getenv('MT5_MAGIC', '20250817'))
        self.deviation = int(os.getenv('MT5_DEVIATION', '20'))
        
        self.connected = False
        self.account_info = None
        self.retry_count = 0
        self.max_retries = 3
        
        logger.info(f"MT5Connection inicializado para cuenta {self.login}")
        
    def connect(self) -> bool:
        """
        Establece conexión con MT5
        Returns: True si conecta exitosamente
        """
        try:
            # Intentar inicializar MT5
            if not mt5.initialize():
                logger.error(f"MT5 initialize failed: {mt5.last_error()}")
                return False
            
            # Login a la cuenta
            authorized = mt5.login(
                login=self.login,
                password=self.password,
                server=self.server,
                timeout=self.timeout
            )
            
            if not authorized:
                logger.error(f"Login failed for account {self.login}: {mt5.last_error()}")
                mt5.shutdown()
                return False
            
            # Obtener información de cuenta
            self.account_info = mt5.account_info()
            if self.account_info is None:
                logger.error("Failed to get account info")
                mt5.shutdown()
                return False
            
            self.connected = True
            logger.info(f"[OK] Connected to MT5 - Account: {self.login}")
            logger.info(f"   Balance: ${self.account_info.balance:.2f}")
            logger.info(f"   Leverage: 1:{self.account_info.leverage}")
            logger.info(f"   Server: {self.server}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to MT5: {e}")
            return False
    
    def start_mt5_terminal(self):
        """Intenta abrir el terminal MT5 automáticamente"""
        try:
            mt5_path = os.getenv("MT5_PATH", r"C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe")
            if os.path.exists(mt5_path):
                logger.info(f"Abriendo MT5 terminal: {mt5_path}")
                subprocess.Popen([mt5_path], shell=True)
                time.sleep(5)  # Esperar que MT5 se abra
                return True
            else:
                logger.error(f"MT5 terminal no encontrado en: {mt5_path}")
                return False
        except Exception as e:
            logger.error(f"Error abriendo MT5 terminal: {e}")
            return False
    
    def disconnect(self):
        """Desconecta de MT5"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            logger.info("Disconnected from MT5")
    
    def ensure_connected(self) -> bool:
        """Asegura que hay conexión activa"""
        if not self.connected:
            return self.connect()
        
        # Verificar si la conexión sigue activa con múltiples checks
        try:
            # Check 1: Verificar si MT5 está inicializado
            if not mt5.terminal_info():
                logger.warning("MT5 terminal not running, starting and reconnecting...")
                self.connected = False
                
                # Intentar abrir MT5 automáticamente
                self.start_mt5_terminal()
                
                return self.connect()
            
            # Check 2: Verificar información de cuenta
            if mt5.account_info() is None:
                logger.warning("Account info not available, reconnecting...")
                self.connected = False
                return self.connect()
            
            # Check 3: Verificar si hay errores reales (códigos > 1)
            error_code = mt5.last_error()[0]
            if error_code > 1:  # Error codes 0=success, 1=success con data, >1=real errors
                logger.warning(f"MT5 real error detected: {mt5.last_error()}, reconnecting...")
                self.connected = False
                return self.connect()
                
        except Exception as e:
            logger.warning(f"Connection check failed: {e}, reconnecting...")
            self.connected = False
            return self.connect()
        
        return True
    
    def map_symbol_to_mt5(self, symbol: str) -> str:
        """
        Mapea símbolo de análisis al símbolo real de MT5
        Args:
            symbol: Símbolo para análisis (ej: BTCUSD)
        Returns: Símbolo para MT5 (ej: BTCUSDm)
        """
        symbol_mapping = {
            'BTCUSD': 'BTCUSDm',
            'ETHUSD': 'ETHUSDm', 
            'LTCUSD': 'LTCUSDm',
            # Agregar más mapeos según sea necesario
        }
        return symbol_mapping.get(symbol, symbol)  # Devuelve el original si no está mapeado
    
    def get_symbol_info(self, symbol: str) -> Optional[mt5.SymbolInfo]:
        """
        Obtiene información del símbolo
        Args:
            symbol: Símbolo a consultar
        Returns: SymbolInfo o None
        """
        if not self.ensure_connected():
            return None
        
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            logger.error(f"Symbol {symbol} not found")
            return None
        
        if not symbol_info.visible:
            if not mt5.symbol_select(symbol, True):
                logger.error(f"Failed to select symbol {symbol}")
                return None
        
        return symbol_info
    
    def get_tick(self, symbol: str) -> Optional[mt5.Tick]:
        """
        Obtiene el último tick del símbolo
        Args:
            symbol: Símbolo a consultar
        Returns: Tick o None
        """
        if not self.ensure_connected():
            return None
        
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            logger.error(f"Failed to get tick for {symbol}")
            return None
        
        return tick
    
    def get_rates(self, symbol: str, timeframe: int, count: int) -> Optional[pd.DataFrame]:
        """
        Obtiene datos históricos
        Args:
            symbol: Símbolo
            timeframe: Timeframe (mt5.TIMEFRAME_*)
            count: Número de barras
        Returns: DataFrame con datos OHLCV
        """
        if not self.ensure_connected():
            return None
        
        rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
        if rates is None:
            logger.error(f"Failed to get rates for {symbol}")
            return None
        
        # Convertir a DataFrame
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)
        
        return df
    
    def place_order(self, 
                   symbol: str,
                   order_type: str,
                   volume: float,
                   price: Optional[float] = None,
                   sl: Optional[float] = None,
                   tp: Optional[float] = None,
                   comment: str = "") -> Optional[mt5.OrderSendResult]:
        """
        Coloca una orden en el mercado
        Args:
            symbol: Símbolo a operar
            order_type: 'buy' o 'sell'
            volume: Volumen (lotes)
            price: Precio (None para mercado)
            sl: Stop Loss
            tp: Take Profit
            comment: Comentario
        Returns: OrderSendResult o None
        """
        if not self.ensure_connected():
            return None
        
        # Mapear símbolo al formato MT5
        mt5_symbol = self.map_symbol_to_mt5(symbol)
        
        # Obtener información del símbolo
        symbol_info = self.get_symbol_info(mt5_symbol)
        if symbol_info is None:
            return None
        
        # Obtener precio actual si no se especifica
        if price is None:
            tick = self.get_tick(mt5_symbol)
            if tick is None:
                return None
            price = tick.ask if order_type == 'buy' else tick.bid
        
        # Preparar request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": mt5_symbol,
            "volume": volume,
            "type": mt5.ORDER_TYPE_BUY if order_type == 'buy' else mt5.ORDER_TYPE_SELL,
            "price": price,
            "deviation": self.deviation,
            "magic": self.magic,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Agregar SL/TP si se especifican
        if sl is not None:
            request["sl"] = sl
        if tp is not None:
            request["tp"] = tp
        
        # Enviar orden
        result = mt5.order_send(request)
        
        if result is None:
            logger.error("Order send failed: No result")
            return None
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Order failed: {result.comment}")
            return None
        
        logger.info(f"[OK] Order placed: {order_type.upper()} {volume} {symbol} @ {price}")
        logger.info(f"   Order: {result.order} | Deal: {result.deal}")
        
        return result
    
    def close_position(self, position_id: int) -> bool:
        """
        Cierra una posición específica
        Args:
            position_id: ID de la posición
        Returns: True si cierra exitosamente
        """
        if not self.ensure_connected():
            return False
        
        position = mt5.positions_get(ticket=position_id)
        if not position:
            logger.error(f"Position {position_id} not found")
            return False
        
        position = position[0]
        
        # Preparar request de cierre
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": position_id,
            "symbol": position.symbol,
            "volume": position.volume,
            "type": mt5.ORDER_TYPE_SELL if position.type == 0 else mt5.ORDER_TYPE_BUY,
            "price": mt5.symbol_info_tick(position.symbol).bid if position.type == 0 else mt5.symbol_info_tick(position.symbol).ask,
            "deviation": self.deviation,
            "magic": self.magic,
            "comment": f"Close #{position_id}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Failed to close position: {result.comment}")
            return False
        
        logger.info(f"[OK] Position {position_id} closed")
        return True
    
    def get_positions(self, symbol: Optional[str] = None) -> List[mt5.TradePosition]:
        """
        Obtiene posiciones abiertas
        Args:
            symbol: Filtrar por símbolo (None = todas)
        Returns: Lista de posiciones
        """
        if not self.ensure_connected():
            return []
        
        if symbol:
            positions = mt5.positions_get(symbol=symbol)
        else:
            positions = mt5.positions_get()
        
        return list(positions) if positions else []
    
    def get_history(self, days: int = 7) -> pd.DataFrame:
        """
        Obtiene historial de operaciones
        Args:
            days: Días de historia
        Returns: DataFrame con historial
        """
        if not self.ensure_connected():
            return pd.DataFrame()
        
        # Calcular rango de fechas
        from_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        from_date = from_date.timestamp() - (days * 86400)
        to_date = datetime.now().timestamp()
        
        # Obtener deals
        deals = mt5.history_deals_get(from_date, to_date)
        
        if not deals:
            return pd.DataFrame()
        
        # Convertir a DataFrame
        df = pd.DataFrame(list(deals), columns=deals[0]._asdict().keys())
        df['time'] = pd.to_datetime(df['time'], unit='s')
        
        return df
    
    def modify_position(self, position_id: int, sl: Optional[float] = None, tp: Optional[float] = None) -> bool:
        """
        Modifica SL/TP de una posición
        Args:
            position_id: ID de la posición
            sl: Nuevo Stop Loss
            tp: Nuevo Take Profit
        Returns: True si modifica exitosamente
        """
        if not self.ensure_connected():
            return False
        
        position = mt5.positions_get(ticket=position_id)
        if not position:
            logger.error(f"Position {position_id} not found")
            return False
        
        position = position[0]
        
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": position_id,
            "symbol": position.symbol,
            "sl": sl if sl is not None else position.sl,
            "tp": tp if tp is not None else position.tp,
            "magic": self.magic,
            "comment": f"Modify #{position_id}"
        }
        
        result = mt5.order_send(request)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            logger.error(f"Failed to modify position: {result.comment}")
            return False
        
        logger.info(f"[OK] Position {position_id} modified - SL: {sl}, TP: {tp}")
        return True
    
    def get_account_info(self) -> Optional[mt5.AccountInfo]:
        """
        Obtiene información de la cuenta
        Returns: AccountInfo o None
        """
        if not self.ensure_connected():
            return None
        
        self.account_info = mt5.account_info()
        return self.account_info
    
    def calculate_position_size(self, symbol: str, risk_amount: float, sl_pips: float) -> float:
        """
        Calcula el tamaño de posición basado en riesgo
        Args:
            symbol: Símbolo
            risk_amount: Cantidad a arriesgar ($)
            sl_pips: Stop Loss en pips
        Returns: Tamaño de posición en lotes
        """
        if not self.ensure_connected():
            return 0.0
        
        symbol_info = self.get_symbol_info(symbol)
        if symbol_info is None:
            return 0.0
        
        # Calcular valor del pip
        pip_value = symbol_info.trade_contract_size * symbol_info.point
        if 'JPY' in symbol:
            pip_value *= 100
        else:
            pip_value *= 10
        
        # Calcular lotes
        lots = risk_amount / (sl_pips * pip_value)
        
        # Ajustar al step mínimo
        lot_step = symbol_info.volume_step
        lots = round(lots / lot_step) * lot_step
        
        # Aplicar límites
        lots = max(symbol_info.volume_min, min(lots, symbol_info.volume_max))
        
        return lots

# Ejemplo de uso
if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Crear conexión
    mt5_conn = MT5Connection()
    
    # Conectar
    if mt5_conn.connect():
        print("\n[OK] Conexión exitosa!")
        
        # Obtener info de cuenta
        account = mt5_conn.get_account_info()
        if account:
            print(f"Balance: ${account.balance:.2f}")
            print(f"Equity: ${account.equity:.2f}")
            print(f"Free Margin: ${account.margin_free:.2f}")
        
        # Obtener símbolo
        symbol = "BTCUSDm"
        symbol_info = mt5_conn.get_symbol_info(symbol)
        if symbol_info:
            print(f"\nSímbolo {symbol}:")
            print(f"  Spread: {symbol_info.spread}")
            print(f"  Digits: {symbol_info.digits}")
        
        # Desconectar
        mt5_conn.disconnect()
    else:
        print("[ERROR] Error al conectar")
