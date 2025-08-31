#!/usr/bin/env python3
"""
ALGOTRADER LIVE - Sistema de Trading en Vivo
Versión simplificada y estable para trading real
"""
import os
import sys
import time
import logging
from datetime import datetime
from dotenv import load_dotenv
import MetaTrader5 as mt5

# Cargar configuración
load_dotenv('.env')

# Configurar logging básico
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('logs/live_trader.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class LiveTrader:
    def __init__(self):
        self.symbol = os.getenv('TRADING_SYMBOL', 'BTCUSD')
        self.mode = os.getenv('TRADING_MODE', 'DEMO')
        self.cycle = 0
        
    def connect_mt5(self):
        """Conectar a MT5 de manera simple"""
        try:
            if not mt5.initialize():
                logger.error("No se pudo inicializar MT5")
                return False
            
            account = mt5.account_info()
            if not account:
                logger.error("No se pudo obtener info de cuenta")
                return False
            
            logger.info(f"MT5 Conectado - Cuenta: {account.login} | Balance: ${account.balance:.2f}")
            return True
            
        except Exception as e:
            logger.error(f"Error conectando MT5: {e}")
            return False
    
    def get_price(self):
        """Obtener precio actual"""
        try:
            tick = mt5.symbol_info_tick(self.symbol)
            if tick:
                return {
                    'bid': tick.bid,
                    'ask': tick.ask,
                    'time': datetime.fromtimestamp(tick.time)
                }
        except Exception as e:
            logger.error(f"Error obteniendo precio: {e}")
        return None
    
    def check_positions(self):
        """Verificar posiciones abiertas"""
        try:
            positions = mt5.positions_get(symbol=self.symbol)
            return len(positions) if positions else 0
        except:
            return 0
    
    def get_signal(self):
        """Obtener señal de trading usando análisis técnico básico con MT5"""
        try:
            # Obtener datos históricos de MT5
            rates = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_M15, 0, 20)
            if rates is None or len(rates) < 10:
                return None
            
            import pandas as pd
            import numpy as np
            
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            # Análisis técnico básico
            # 1. Media móvil simple
            df['sma_5'] = df['close'].rolling(window=5).mean()
            df['sma_10'] = df['close'].rolling(window=10).mean()
            
            # 2. RSI simplificado
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=5).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=5).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            # 3. Precio actual vs medias
            current_price = df['close'].iloc[-1]
            sma5 = df['sma_5'].iloc[-1]
            sma10 = df['sma_10'].iloc[-1]
            current_rsi = rsi.iloc[-1]
            
            # Lógica de señales
            signal = None
            strength = 0
            reasons = []
            
            # Señal de COMPRA
            if (current_price > sma5 > sma10 and  # Tendencia alcista
                current_rsi < 70 and              # No sobrecomprado
                current_rsi > 30):                # Momento positivo
                signal = 'buy'
                strength = min((current_price - sma10) / sma10 * 100, 0.8)
                reasons = [f"Precio ${current_price:.2f} > SMA5 ${sma5:.2f} > SMA10 ${sma10:.2f}",
                          f"RSI {current_rsi:.1f} en zona favorable"]
            
            # Señal de VENTA
            elif (current_price < sma5 < sma10 and  # Tendencia bajista
                  current_rsi > 30 and              # No sobrevendido
                  current_rsi < 70):                # Momento negativo
                signal = 'sell'
                strength = min((sma10 - current_price) / sma10 * 100, 0.8)
                reasons = [f"Precio ${current_price:.2f} < SMA5 ${sma5:.2f} < SMA10 ${sma10:.2f}",
                          f"RSI {current_rsi:.1f} en zona favorable"]
            
            if signal and strength > 0.1:  # Fuerza mínima requerida
                return {
                    'direction': signal,
                    'strength': strength,
                    'confidence': min(strength * 2, 0.9),  # Confianza basada en fuerza
                    'reasons': reasons,
                    'price': current_price,
                    'rsi': current_rsi
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error generando señal: {e}")
            return None
    
    def execute_order(self, signal):
        """Ejecutar orden de trading real"""
        try:
            # Parámetros de trading
            volume = 0.01  # Tamaño mínimo para BTCUSD
            deviation = 20
            magic = 20250828
            
            # Obtener precio actual
            tick = mt5.symbol_info_tick(self.symbol)
            if not tick:
                logger.error("No se pudo obtener precio actual")
                return False
            
            # Determinar tipo de orden
            if signal['direction'] == 'buy':
                order_type = mt5.ORDER_TYPE_BUY
                price = tick.ask
                sl = price - (50 * mt5.symbol_info(self.symbol).point)  # SL 50 puntos
                tp = price + (100 * mt5.symbol_info(self.symbol).point)  # TP 100 puntos
            else:
                order_type = mt5.ORDER_TYPE_SELL
                price = tick.bid
                sl = price + (50 * mt5.symbol_info(self.symbol).point)  # SL 50 puntos
                tp = price - (100 * mt5.symbol_info(self.symbol).point)  # TP 100 puntos
            
            # Preparar orden
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": self.symbol,
                "volume": volume,
                "type": order_type,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": deviation,
                "magic": magic,
                "comment": f"AlgoTrader {signal['direction'].upper()}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_FOK,
            }
            
            # Enviar orden
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Error ejecutando orden: {result.retcode} - {result.comment}")
                self.send_notification(f"ERROR: No se pudo ejecutar orden {signal['direction'].upper()} - {result.comment}")
                return False
            
            # Orden exitosa
            logger.info(f"ORDEN EJECUTADA: {signal['direction'].upper()} {volume} {self.symbol} a ${price:.2f}")
            self.send_notification(f"ORDEN EJECUTADA: {signal['direction'].upper()} {volume} {self.symbol} a ${price:.2f} - Ticket: {result.order}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error ejecutando orden: {e}")
            self.send_notification(f"ERROR ejecutando orden: {e}")
            return False
    
    def send_notification(self, message):
        """Enviar notificación Telegram"""
        try:
            from notifiers.telegram_notifier import send_telegram_message
            send_telegram_message(f"AlgoTrader LIVE: {message}")
        except Exception as e:
            logger.warning(f"Error enviando notificación: {e}")
    
    def run(self):
        """Ejecutar el trading en vivo"""
        logger.info("=" * 60)
        logger.info("ALGOTRADER LIVE v3.0 - INICIANDO")
        logger.info(f"Modo: {self.mode} | Símbolo: {self.symbol}")
        logger.info("=" * 60)
        
        # Conectar MT5
        if not self.connect_mt5():
            logger.error("No se pudo conectar a MT5. Sistema detenido.")
            return
        
        # Notificación inicial
        self.send_notification(f"Sistema iniciado en modo {self.mode} - {self.symbol}")
        
        try:
            while True:
                self.cycle += 1
                timestamp = datetime.now().strftime('%H:%M:%S')
                
                # Obtener precio
                price_data = self.get_price()
                if price_data:
                    price = price_data['bid']
                    
                    # Verificar posiciones
                    positions = self.check_positions()
                    
                    # Log del estado
                    logger.info(f"[{self.cycle:04d}] {timestamp} | {self.symbol}: ${price:,.2f} | Posiciones: {positions}")
                    
                    # LÓGICA DE TRADING REAL
                    if positions == 0:  # Solo si no hay posiciones abiertas
                        # Obtener señal
                        signal = self.get_signal()
                        if signal:
                            logger.info(f"SEÑAL DETECTADA: {signal['direction'].upper()} - Fuerza: {signal.get('strength', 0):.2f}")
                            self.send_notification(f"SEÑAL: {signal['direction'].upper()} - Fuerza: {signal.get('strength', 0):.2f} - Ejecutando orden...")
                            
                            # Ejecutar orden
                            if self.execute_order(signal):
                                logger.info("Orden ejecutada exitosamente")
                            else:
                                logger.error("Error ejecutando orden")
                    else:
                        logger.info(f"Posiciones abiertas: {positions} - No se ejecutan nuevas órdenes")
                    
                    # Cada 10 ciclos, enviar actualización
                    if self.cycle % 10 == 0:
                        self.send_notification(f"Ciclo {self.cycle} - Precio {self.symbol}: ${price:,.2f}")
                
                else:
                    logger.warning(f"[{self.cycle:04d}] {timestamp} | No se pudo obtener precio")
                
                # Esperar 30 segundos para el próximo ciclo
                time.sleep(30)
                
        except KeyboardInterrupt:
            logger.info("Sistema detenido por el usuario")
        except Exception as e:
            logger.error(f"Error en el sistema: {e}")
            self.send_notification(f"ERROR: {e}")
        finally:
            mt5.shutdown()
            logger.info("MT5 desconectado")
            self.send_notification("Sistema AlgoTrader detenido")

if __name__ == "__main__":
    trader = LiveTrader()
    trader.run()