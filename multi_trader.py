#!/usr/bin/env python3
"""
MULTI-SYMBOL REAL TRADER
Sistema de trading en tiempo real para múltiples símbolos
BTCUSD, EURUSD, XAUUSD con análisis técnico completo
"""
import MetaTrader5 as mt5
import time
import logging
from datetime import datetime
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import os

# Cargar configuración
load_dotenv('.env')

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(message)s',
    handlers=[
        logging.FileHandler('logs/multi_trader.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class MultiSymbolTrader:
    def __init__(self):
        # Símbolos a operar (Exness disponibles)
        self.symbols = {
            'BTCUSDm': {'volume': 0.01, 'pip_value': 0.01, 'spread_limit': 50},
            'ETHUSDm': {'volume': 0.01, 'pip_value': 0.01, 'spread_limit': 50},
            'XAUUSDm': {'volume': 0.01, 'pip_value': 0.01, 'spread_limit': 30},  # Oro agregado
        }
        
        self.magic = 20250828
        self.cycle = 0
        self.api_key = os.getenv('TWELVEDATA_API_KEY', 'demo')
        
        # Verificar qué símbolos están disponibles
        self._verify_symbols()
        
    def _verify_symbols(self):
        """Verificar y ajustar símbolos disponibles"""
        if not mt5.initialize():
            logging.error("No se pudo conectar a MT5")
            return
            
        available_symbols = []
        
        # Verificar cada símbolo
        for symbol, config in self.symbols.items():
            tick = mt5.symbol_info_tick(symbol)
            if tick:
                available_symbols.append(symbol)
                logging.info(f"✓ {symbol} disponible - Precio: {tick.bid:.5f}")
            else:
                logging.warning(f"✗ {symbol} no disponible")
        
        # Los símbolos ya están configurados para Exness, no buscar alternativas
        pass
        
        # Mantener solo símbolos disponibles
        self.symbols = {k: v for k, v in self.symbols.items() if k in available_symbols}
        logging.info(f"Símbolos activos: {list(self.symbols.keys())}")
        
        mt5.shutdown()
    
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
    
    def get_twelvedata_price(self, symbol):
        """Obtener precio de TwelveData API"""
        try:
            from data.twelvedata import price as td_price
            # Normalizar símbolo para TwelveData
            if 'XAU' in symbol or 'GOLD' in symbol:
                td_symbol = 'XAU/USD'
            elif symbol == 'EURUSD':
                td_symbol = 'EUR/USD'
            elif 'BTC' in symbol:
                td_symbol = 'BTC/USD'
            elif 'ETH' in symbol:
                td_symbol = 'ETH/USD'
            else:
                td_symbol = symbol
            
            price = td_price(td_symbol)
            return price
        except Exception as e:
            logging.debug(f"TwelveData error para {symbol}: {e}")
            return None
    
    def get_twelvedata_indicators(self, symbol):
        """Obtener indicadores de TwelveData"""
        try:
            from data.twelvedata import indicator as td_indicator
            
            # Normalizar símbolo
            if 'XAU' in symbol or 'GOLD' in symbol:
                td_symbol = 'XAU/USD'
            elif symbol == 'EURUSD':
                td_symbol = 'EUR/USD'
            elif 'BTC' in symbol:
                td_symbol = 'BTC/USD'
            elif 'ETH' in symbol:
                td_symbol = 'ETH/USD'
            else:
                td_symbol = symbol
            
            # Obtener RSI
            rsi = td_indicator(td_symbol, 'RSI', '15min', time_period=14)
            # Obtener MACD
            macd = td_indicator(td_symbol, 'MACD', '15min')
            
            return {
                'rsi': rsi.get('rsi', 50),
                'macd': macd.get('macd', 0),
                'macd_signal': macd.get('macd_signal', 0)
            }
        except Exception as e:
            logging.debug(f"Error indicadores TwelveData {symbol}: {e}")
            return {'rsi': 50, 'macd': 0, 'macd_signal': 0}
    
    def _analyze_with_twelvedata(self, symbol):
        """Análisis avanzado usando TwelveData API"""
        try:
            from advanced_analysis import AdvancedAnalyzer
            analyzer = AdvancedAnalyzer()
            result = analyzer.analyze_symbol_advanced(symbol)
            
            if result and result['signal'] != 'HOLD':
                return {
                    'signal': result['signal'],
                    'strength': result['strength'],
                    'confidence': result['confidence'],
                    'price': result['current_price'],
                    'rsi': result['rsi'],
                    'reasons': result['signals']
                }
            return None
        except Exception as e:
            logging.error(f"Error TwelveData analysis {symbol}: {e}")
            return None
    
    def analyze_symbol(self, symbol):
        """Análisis completo de un símbolo"""
        try:
            # Usar análisis avanzado para símbolos soportados
            if symbol in ['XAUUSDm', 'BTCUSDm', 'ETHUSDm']:
                advanced_result = self._analyze_with_twelvedata(symbol)
                if advanced_result:
                    return advanced_result
                # Si falla TwelveData, continuar con análisis tradicional
            
            # Análisis tradicional MT5
            # 1. Datos MT5
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 20)
            if rates is None or len(rates) < 15:
                return None
            
            df = pd.DataFrame(rates)
            
            # 2. Análisis técnico local
            df['sma_5'] = df['close'].rolling(5).mean()
            df['sma_10'] = df['close'].rolling(10).mean()
            df['sma_20'] = df['close'].rolling(20).mean()
            
            # RSI local
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            current = df.iloc[-1]
            
            # 3. Datos TwelveData (más precisos)
            td_price = self.get_twelvedata_price(symbol)
            td_indicators = self.get_twelvedata_indicators(symbol)
            
            # 4. Combinar análisis
            price = td_price if td_price else current['close']
            rsi = td_indicators['rsi'] if td_indicators['rsi'] != 50 else current.get('rsi', 50)
            
            # 5. Lógica de señales mejorada
            signal_strength = 0
            reasons = []
            
            # Tendencia (SMA)
            if current['sma_5'] > current['sma_10'] > current['sma_20']:
                trend_score = 0.3
                reasons.append("Tendencia alcista (SMA 5>10>20)")
            elif current['sma_5'] < current['sma_10'] < current['sma_20']:
                trend_score = -0.3
                reasons.append("Tendencia bajista (SMA 5<10<20)")
            else:
                trend_score = 0
                reasons.append("Tendencia neutral")
            
            # RSI
            if 30 < rsi < 45:
                rsi_score = 0.2  # Posible recuperación
                reasons.append(f"RSI {rsi:.1f} - zona de compra")
            elif 55 < rsi < 70:
                rsi_score = -0.2  # Posible corrección
                reasons.append(f"RSI {rsi:.1f} - zona de venta")
            else:
                rsi_score = 0
                reasons.append(f"RSI {rsi:.1f} - neutral")
            
            # MACD
            macd_score = 0
            if td_indicators['macd'] > td_indicators['macd_signal']:
                macd_score = 0.15
                reasons.append("MACD positivo")
            elif td_indicators['macd'] < td_indicators['macd_signal']:
                macd_score = -0.15
                reasons.append("MACD negativo")
            
            # Precio vs TwelveData
            if td_price and abs(td_price - current['close']) / current['close'] < 0.001:
                data_confidence = 0.1
                reasons.append("Datos sincronizados")
            else:
                data_confidence = 0
            
            # Señal final
            signal_strength = trend_score + rsi_score + macd_score + data_confidence
            
            if signal_strength > 0.3:
                return {
                    'signal': 'BUY',
                    'strength': signal_strength,
                    'confidence': min(signal_strength * 1.5, 0.9),
                    'price': price,
                    'rsi': rsi,
                    'reasons': reasons[:3]  # Top 3 razones
                }
            elif signal_strength < -0.3:
                return {
                    'signal': 'SELL', 
                    'strength': abs(signal_strength),
                    'confidence': min(abs(signal_strength) * 1.5, 0.9),
                    'price': price,
                    'rsi': rsi,
                    'reasons': reasons[:3]
                }
            
            return None
            
        except Exception as e:
            logging.error(f"Error analizando {symbol}: {e}")
            return None
    
    def execute_order(self, symbol, signal, analysis):
        """Ejecutar orden para un símbolo específico"""
        try:
            config = self.symbols[symbol]
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                logging.error(f"No tick para {symbol}")
                return False
            
            # Verificar spread
            spread = tick.ask - tick.bid
            if spread > config['spread_limit'] * config['pip_value']:
                logging.warning(f"{symbol} spread muy alto: {spread}")
                return False
            
            # Configurar orden
            if signal == 'BUY':
                order_type = mt5.ORDER_TYPE_BUY
                price = tick.ask
                sl = price - (50 * config['pip_value'])
                tp = price + (100 * config['pip_value'])
            else:
                order_type = mt5.ORDER_TYPE_SELL
                price = tick.bid
                sl = price + (50 * config['pip_value'])
                tp = price - (100 * config['pip_value'])
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": config['volume'],
                "type": order_type,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": 20,
                "magic": self.magic,
                "comment": f"MultiTrader {signal}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_FOK,
            }
            
            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                logging.info(f"ORDEN {signal} EJECUTADA: {symbol} - Ticket: {result.order}")
                self.send_telegram(f"ORDEN EJECUTADA: {signal} {symbol} a {price:.5f} - Confianza: {analysis['confidence']:.1%}")
                return True
            else:
                error_msg = result.comment if result else "Sin respuesta"
                logging.error(f"ERROR {symbol}: {error_msg}")
                return False
            
        except Exception as e:
            logging.error(f"Error ejecutando {symbol}: {e}")
            return False
    
    def get_positions_count(self, symbol=None):
        """Obtener número de posiciones por símbolo"""
        try:
            if symbol:
                positions = mt5.positions_get(symbol=symbol)
            else:
                positions = mt5.positions_get()
            return len(positions) if positions else 0
        except:
            return 0
    
    def send_telegram(self, message):
        """Enviar notificación Telegram"""
        try:
            from notifiers.telegram_notifier import send_telegram_message
            send_telegram_message(f"MultiTrader: {message}")
        except Exception as e:
            logging.debug(f"Error Telegram: {e}")
    
    def run(self):
        """Ejecutar trading multi-símbolo"""
        logging.info("=" * 60)
        logging.info("MULTI-SYMBOL REAL TRADER INICIANDO")
        logging.info(f"Símbolos: {', '.join(self.symbols.keys())}")
        logging.info("ATENCION: Sistema ejecuta operaciones REALES")
        logging.info("=" * 60)
        
        if not self.connect_mt5():
            return
        
        if not self.symbols:
            logging.error("No hay símbolos disponibles")
            return
        
        self.send_telegram(f"Sistema Multi-Símbolo iniciado: {', '.join(self.symbols.keys())}")
        
        try:
            while True:
                self.cycle += 1
                timestamp = datetime.now().strftime('%H:%M:%S')
                
                logging.info(f"[{self.cycle:03d}] {timestamp} - Analizando {len(self.symbols)} símbolos...")
                
                total_positions = self.get_positions_count()
                
                # Analizar cada símbolo
                for symbol in self.symbols.keys():
                    try:
                        # Verificar posiciones del símbolo
                        symbol_positions = self.get_positions_count(symbol)
                        
                        # Obtener precio actual
                        tick = mt5.symbol_info_tick(symbol)
                        price = tick.bid if tick else 0
                        
                        logging.info(f"  {symbol}: ${price:.5f} | Posiciones: {symbol_positions}")
                        
                        # Solo analizar si no hay posiciones en este símbolo
                        if symbol_positions == 0 and total_positions < 2:  # Máximo 2 posiciones totales (ya hay 1 manual)
                            analysis = self.analyze_symbol(symbol)
                            
                            if analysis:
                                signal = analysis['signal']
                                confidence = analysis['confidence']
                                reasons = ', '.join(analysis['reasons'])
                                
                                logging.info(f"  🎯 SEÑAL {symbol}: {signal} - Confianza: {confidence:.1%}")
                                logging.info(f"     Razones: {reasons}")
                                
                                # Ejecutar si confianza > 50%
                                if confidence > 0.5:
                                    if self.execute_order(symbol, signal, analysis):
                                        # Actualizar contador de posiciones
                                        total_positions += 1
                    
                    except Exception as e:
                        logging.error(f"Error procesando {symbol}: {e}")
                        continue
                
                # Resumen del ciclo
                logging.info(f"[{self.cycle:03d}] Completado - Total posiciones: {self.get_positions_count()}")
                
                # Notificación cada 10 ciclos
                if self.cycle % 10 == 0:
                    positions = self.get_positions_count()
                    self.send_telegram(f"Ciclo {self.cycle} - {positions} posiciones activas")
                
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
            self.send_telegram("Sistema Multi-Símbolo detenido")

if __name__ == "__main__":
    trader = MultiSymbolTrader()
    trader.run()