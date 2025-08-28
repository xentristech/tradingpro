#!/usr/bin/env python3
"""
ALGOTRADER REAL - Sistema de Trading Real Simplificado
Ejecuta operaciones reales basadas en señales técnicas
"""
import MetaTrader5 as mt5
import time
import logging
from datetime import datetime
import pandas as pd
import numpy as np

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(message)s',
    handlers=[
        logging.FileHandler('logs/real_trader.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class RealTrader:
    def __init__(self):
        self.symbol = "EURUSD"
        self.volume = 0.01  # Volumen mínimo
        self.magic = 20250828
        self.cycle = 0
        
    def connect_mt5(self):
        """Conectar MT5"""
        if not mt5.initialize():
            logging.error("No se pudo conectar a MT5")
            return False
        
        account = mt5.account_info()
        if not account:
            logging.error("No se pudo obtener cuenta")
            return False
        
        logging.info(f"Conectado - Cuenta: {account.login} | Balance: ${account.balance:.2f}")
        return True
    
    def get_price(self):
        """Obtener precio actual"""
        tick = mt5.symbol_info_tick(self.symbol)
        return tick.bid if tick else None
    
    def check_positions(self):
        """Verificar posiciones abiertas"""
        positions = mt5.positions_get(symbol=self.symbol)
        return len(positions) if positions else 0
    
    def analyze_market(self):
        """Análisis técnico simple"""
        try:
            # Obtener velas de 15 minutos
            rates = mt5.copy_rates_from_pos(self.symbol, mt5.TIMEFRAME_M15, 0, 15)
            if rates is None or len(rates) < 10:
                return None
            
            df = pd.DataFrame(rates)
            
            # Medias móviles
            df['sma_5'] = df['close'].rolling(5).mean()
            df['sma_10'] = df['close'].rolling(10).mean()
            
            # RSI básico
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(5).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(5).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            current = df.iloc[-1]
            current_rsi = rsi.iloc[-1]
            
            # Lógica de señal
            if (current['close'] > current['sma_5'] > current['sma_10'] and 
                30 < current_rsi < 70):
                return {'signal': 'BUY', 'rsi': current_rsi, 'price': current['close']}
            elif (current['close'] < current['sma_5'] < current['sma_10'] and 
                  30 < current_rsi < 70):
                return {'signal': 'SELL', 'rsi': current_rsi, 'price': current['close']}
            
            return None
        except Exception as e:
            logging.error(f"Error en análisis: {e}")
            return None
    
    def execute_buy(self, price):
        """Ejecutar orden de compra"""
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": self.volume,
            "type": mt5.ORDER_TYPE_BUY,
            "price": price,
            "sl": price - (50 * mt5.symbol_info(self.symbol).point),
            "tp": price + (100 * mt5.symbol_info(self.symbol).point),
            "deviation": 20,
            "magic": self.magic,
            "comment": "AlgoTrader BUY",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }
        
        result = mt5.order_send(request)
        return result
    
    def execute_sell(self, price):
        """Ejecutar orden de venta"""
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.symbol,
            "volume": self.volume,
            "type": mt5.ORDER_TYPE_SELL,
            "price": price,
            "sl": price + (50 * mt5.symbol_info(self.symbol).point),
            "tp": price - (100 * mt5.symbol_info(self.symbol).point),
            "deviation": 20,
            "magic": self.magic,
            "comment": "AlgoTrader SELL",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_FOK,
        }
        
        result = mt5.order_send(request)
        return result
    
    def send_telegram(self, message):
        """Enviar notificación Telegram"""
        try:
            from notifiers.telegram_notifier import send_telegram_message
            send_telegram_message(f"RealTrader: {message}")
        except:
            pass
    
    def run(self):
        """Ejecutar trading en vivo"""
        logging.info("=" * 50)
        logging.info("ALGOTRADER REAL - INICIANDO")
        logging.info("ATENCION: Este sistema ejecuta operaciones REALES")
        logging.info("=" * 50)
        
        if not self.connect_mt5():
            return
        
        self.send_telegram("Sistema de trading REAL iniciado - EURUSD")
        
        try:
            while True:
                self.cycle += 1
                timestamp = datetime.now().strftime('%H:%M:%S')
                
                # Precio actual
                price = self.get_price()
                if not price:
                    logging.warning("No se pudo obtener precio")
                    continue
                
                # Verificar posiciones
                positions = self.check_positions()
                
                logging.info(f"[{self.cycle:03d}] {timestamp} | ${price:,.2f} | Posiciones: {positions}")
                
                # Solo analizar si no hay posiciones
                if positions == 0:
                    analysis = self.analyze_market()
                    
                    if analysis:
                        signal = analysis['signal']
                        rsi = analysis['rsi']
                        
                        logging.info(f"SEÑAL DETECTADA: {signal} | RSI: {rsi:.1f}")
                        self.send_telegram(f"SEÑAL {signal} detectada - RSI: {rsi:.1f} - Ejecutando...")
                        
                        # Obtener precio actual para la orden
                        tick = mt5.symbol_info_tick(self.symbol)
                        if not tick:
                            logging.error("No se pudo obtener tick")
                            continue
                        
                        # Ejecutar orden
                        if signal == 'BUY':
                            result = self.execute_buy(tick.ask)
                        else:
                            result = self.execute_sell(tick.bid)
                        
                        # Verificar resultado
                        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                            logging.info(f"ORDEN EJECUTADA: {signal} | Ticket: {result.order}")
                            self.send_telegram(f"ORDEN EJECUTADA: {signal} {self.volume} {self.symbol} - Ticket: {result.order}")
                        else:
                            error_msg = result.comment if result else "Sin respuesta"
                            logging.error(f"ERROR EN ORDEN: {error_msg}")
                            self.send_telegram(f"ERROR: No se pudo ejecutar {signal} - {error_msg}")
                
                # Esperar 30 segundos
                time.sleep(30)
                
        except KeyboardInterrupt:
            logging.info("Sistema detenido por usuario")
        except Exception as e:
            logging.error(f"Error crítico: {e}")
            self.send_telegram(f"ERROR CRITICO: {e}")
        finally:
            mt5.shutdown()
            logging.info("MT5 desconectado")
            self.send_telegram("Sistema de trading REAL detenido")

if __name__ == "__main__":
    trader = RealTrader()
    trader.run()