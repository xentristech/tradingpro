"""
Signal Executor - Ejecutor de Señales en MetaTrader 5
Genera señales de trading y las ejecuta automáticamente en MT5
"""
import os
import sys
import time
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from dotenv import load_dotenv

# Configurar path
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from signals.signal_generator import SignalGenerator
from risk.risk_manager import RiskManager
from notifiers.telegram_notifier import TelegramNotifier

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.FileHandler('logs/signal_executor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SignalExecutor:
    """Ejecutor de señales de trading en MT5"""
    
    def __init__(self):
        """Inicializa el ejecutor de señales"""
        logger.info("="*60)
        logger.info(" SIGNAL EXECUTOR - GENERADOR Y EJECUTOR DE SEÑALES")
        logger.info("="*60)
        
        # Cargar configuración
        load_dotenv('configs/.env')
        
        # Símbolos Forex principales
        self.symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCHF']
        self.timeframe = mt5.TIMEFRAME_M15  # 15 minutos
        self.lookback_periods = 100  # Periodos históricos para análisis
        
        # Componentes
        self.signal_generator = SignalGenerator()
        self.risk_manager = RiskManager()
        self.telegram = None
        
        # Estado
        self.running = False
        self.signals_generated = 0
        self.trades_executed = 0
        
    def initialize(self):
        """Inicializa conexión MT5 y componentes"""
        try:
            # Conectar MT5
            if not mt5.initialize():
                logger.error("Error inicializando MT5")
                return False
            
            account = mt5.account_info()
            if not account:
                logger.error("No se pudo obtener información de cuenta")
                return False
            
            logger.info(f"Conectado a MT5 - Cuenta: {account.login}")
            logger.info(f"Balance: ${account.balance:.2f}")
            logger.info(f"Broker: {account.company}")
            
            # Inicializar Telegram si está configurado
            if os.getenv('TELEGRAM_TOKEN') and os.getenv('TELEGRAM_CHAT_ID'):
                self.telegram = TelegramNotifier()
                logger.info("Telegram notifier activado")
            
            # Verificar símbolos disponibles
            available_symbols = []
            for symbol in self.symbols:
                info = mt5.symbol_info(symbol)
                if info and info.visible:
                    available_symbols.append(symbol)
                    logger.info(f"[OK] {symbol} disponible")
                else:
                    logger.warning(f"[X] {symbol} no disponible")
            
            self.symbols = available_symbols
            
            if not self.symbols:
                logger.error("No hay símbolos disponibles")
                return False
            
            logger.info(f"Símbolos activos: {', '.join(self.symbols)}")
            return True
            
        except Exception as e:
            logger.error(f"Error en inicialización: {e}")
            return False
    
    def get_market_data(self, symbol: str) -> Optional[pd.DataFrame]:
        """Obtiene datos históricos del mercado"""
        try:
            # Obtener datos históricos
            rates = mt5.copy_rates_from_pos(symbol, self.timeframe, 0, self.lookback_periods)
            
            if rates is None or len(rates) == 0:
                logger.warning(f"No se pudieron obtener datos para {symbol}")
                return None
            
            # Convertir a DataFrame
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            # Calcular indicadores técnicos
            df = self.calculate_indicators(df)
            
            return df
            
        except Exception as e:
            logger.error(f"Error obteniendo datos de {symbol}: {e}")
            return None
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calcula indicadores técnicos"""
        try:
            # Moving Averages
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['sma_50'] = df['close'].rolling(window=50).mean()
            df['ema_12'] = df['close'].ewm(span=12).mean()
            df['ema_26'] = df['close'].ewm(span=26).mean()
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # Bollinger Bands
            df['bb_middle'] = df['close'].rolling(window=20).mean()
            bb_std = df['close'].rolling(window=20).std()
            df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
            df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
            
            # MACD
            df['macd'] = df['ema_12'] - df['ema_26']
            df['macd_signal'] = df['macd'].ewm(span=9).mean()
            df['macd_histogram'] = df['macd'] - df['macd_signal']
            
            # ATR
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = np.max(ranges, axis=1)
            df['atr'] = true_range.rolling(14).mean()
            
            # Stochastic
            low_14 = df['low'].rolling(window=14).min()
            high_14 = df['high'].rolling(window=14).max()
            df['stoch_k'] = 100 * ((df['close'] - low_14) / (high_14 - low_14))
            df['stoch_d'] = df['stoch_k'].rolling(window=3).mean()
            
            return df
            
        except Exception as e:
            logger.error(f"Error calculando indicadores: {e}")
            return df
    
    async def analyze_and_execute(self):
        """Analiza mercados y ejecuta señales"""
        self.running = True
        iteration = 0
        
        while self.running:
            iteration += 1
            current_time = datetime.now()
            
            logger.info(f"\n[{iteration:04d}] Análisis - {current_time.strftime('%H:%M:%S')}")
            logger.info("-" * 40)
            
            signals_found = []
            
            # Analizar cada símbolo
            for symbol in self.symbols:
                # Obtener datos de mercado
                df = self.get_market_data(symbol)
                if df is None:
                    continue
                
                # Generar señales
                signal_result = self.signal_generator.generate(df)
                
                if signal_result and signal_result.get('action') in ['BUY', 'SELL']:
                    self.signals_generated += 1
                    
                    current_price = df['close'].iloc[-1]
                    confidence = signal_result.get('confidence', 0)
                    
                    logger.info(f"\n[SEÑAL DETECTADA] {symbol}")
                    logger.info(f"  Precio: {current_price:.5f}")
                    logger.info(f"  Acción: {signal_result['action']}")
                    logger.info(f"  Confianza: {confidence:.1%}")
                    logger.info(f"  Estrategias: {', '.join(signal_result.get('strategies', []))}")
                    
                    if confidence > 0.7:  # Solo ejecutar con alta confianza
                        signals_found.append({
                            'symbol': symbol,
                            'signal': signal_result,
                            'price': current_price
                        })
                        
                        # Notificar señal fuerte
                        if self.telegram:
                            await self.telegram.send_message(
                                f"[SEÑAL FUERTE DETECTADA]\\n\\n"
                                f"Símbolo: {symbol}\\n"
                                f"Acción: {signal_result['action']}\\n"
                                f"Precio: {current_price:.5f}\\n"
                                f"Confianza: {confidence:.1%}\\n"
                                f"Estrategias: {', '.join(signal_result.get('strategies', []))}\\n\\n"
                                f"Sistema listo para ejecutar"
                            )
            
            # Ejecutar las mejores señales
            if signals_found:
                logger.info(f"\n{len(signals_found)} señales fuertes detectadas")
                
                # Seleccionar la mejor señal
                best_signal = max(signals_found, key=lambda x: x['signal'].get('confidence', 0))
                
                # Verificar si ya tenemos posición en ese símbolo
                positions = mt5.positions_get(symbol=best_signal['symbol'])
                
                if not positions or len(positions) == 0:
                    # Ejecutar trade
                    success = await self.execute_trade(
                        symbol=best_signal['symbol'],
                        signal=best_signal['signal'],
                        price=best_signal['price']
                    )
                    
                    if success:
                        self.trades_executed += 1
                        logger.info(f"Trade ejecutado exitosamente - Total: {self.trades_executed}")
                else:
                    logger.info(f"Ya hay posición abierta en {best_signal['symbol']}")
            else:
                logger.info("No hay señales fuertes en este momento")
            
            # Mostrar estadísticas
            if iteration % 10 == 0:
                logger.info(f"\n[ESTADÍSTICAS]")
                logger.info(f"  Señales generadas: {self.signals_generated}")
                logger.info(f"  Trades ejecutados: {self.trades_executed}")
                logger.info(f"  Ratio ejecución: {self.trades_executed/max(1, self.signals_generated):.1%}")
            
            # Esperar antes del próximo análisis
            await asyncio.sleep(60)  # Analizar cada minuto
    
    async def execute_trade(self, symbol: str, signal: Dict, price: float) -> bool:
        """Ejecuta una operación en MT5"""
        try:
            # Obtener información del símbolo
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                logger.error(f"No se pudo obtener info de {symbol}")
                return False
            
            # Calcular tamaño de posición
            account_info = mt5.account_info()
            position_size = self.risk_manager.calculate_position_size(
                account_balance=account_info.balance,
                stop_loss_pips=30
            )
            
            # Ajustar volumen
            volume = max(symbol_info.volume_min, min(position_size, symbol_info.volume_max))
            
            # Configurar orden
            if signal['action'] == 'BUY':
                order_type = mt5.ORDER_TYPE_BUY
                sl = price - (30 * symbol_info.point)
                tp = price + (60 * symbol_info.point)
            else:
                order_type = mt5.ORDER_TYPE_SELL
                sl = price + (30 * symbol_info.point)
                tp = price - (60 * symbol_info.point)
            
            # Preparar request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": order_type,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": 20,
                "magic": 123456,
                "comment": f"Signal_{signal.get('strategies', ['NA'])[0][:10]}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Enviar orden
            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(f"[TRADE EJECUTADO]")
                logger.info(f"  Ticket: {result.order}")
                logger.info(f"  Símbolo: {symbol}")
                logger.info(f"  Tipo: {signal['action']}")
                logger.info(f"  Volumen: {volume}")
                logger.info(f"  Precio: {price:.5f}")
                logger.info(f"  SL: {sl:.5f} | TP: {tp:.5f}")
                
                if self.telegram:
                    await self.telegram.send_message(
                        f"[TRADE EJECUTADO]\\n\\n"
                        f"Ticket: #{result.order}\\n"
                        f"Símbolo: {symbol}\\n"
                        f"Tipo: {signal['action']}\\n"
                        f"Volumen: {volume}\\n"
                        f"Precio: {price:.5f}\\n"
                        f"SL: {sl:.5f}\\n"
                        f"TP: {tp:.5f}\\n\\n"
                        f"Confianza: {signal.get('confidence', 0):.1%}"
                    )
                
                return True
            else:
                logger.warning(f"Trade rechazado: {result.comment if result else 'Error desconocido'}")
                return False
                
        except Exception as e:
            logger.error(f"Error ejecutando trade: {e}")
            return False
    
    def run(self):
        """Ejecuta el sistema"""
        if not self.initialize():
            logger.error("No se pudo inicializar el sistema")
            return
        
        logger.info("\n" + "="*60)
        logger.info(" SISTEMA DE SEÑALES ACTIVO")
        logger.info(" Analizando mercados y ejecutando señales...")
        logger.info("="*60)
        
        # Notificar inicio
        if self.telegram:
            asyncio.run(self.telegram.send_message(
                "[SIGNAL EXECUTOR INICIADO]\\n\\n"
                f"Símbolos: {', '.join(self.symbols)}\\n"
                "Timeframe: M15\\n"
                "Confianza mínima: 70%\\n\\n"
                "Sistema analizando mercados..."
            ))
        
        try:
            # Ejecutar loop principal
            asyncio.run(self.analyze_and_execute())
            
        except KeyboardInterrupt:
            logger.info("\nDeteniendo sistema por usuario...")
        except Exception as e:
            logger.error(f"Error en sistema: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Limpia recursos"""
        self.running = False
        
        logger.info("\n" + "="*60)
        logger.info(" RESUMEN DE SESIÓN")
        logger.info(f" Señales generadas: {self.signals_generated}")
        logger.info(f" Trades ejecutados: {self.trades_executed}")
        logger.info("="*60)
        
        mt5.shutdown()
        logger.info("Sistema detenido")

def main():
    """Función principal"""
    executor = SignalExecutor()
    executor.run()

if __name__ == "__main__":
    main()