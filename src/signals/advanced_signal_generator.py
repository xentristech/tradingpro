#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GENERADOR DE SEÑALES CON IA - ALGO TRADER V3 (FIXED)
====================================================
Sistema avanzado de generación de señales con múltiples estrategias
"""

import os
import sys
import time
import json
import threading
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import logging
import random

# Configurar encoding UTF-8
if sys.platform == 'win32':
    import locale
    locale.setlocale(locale.LC_ALL, '')

# Añadir path del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Importar notificador de Telegram y historial
try:
    from src.notifiers.telegram_notifier import TelegramNotifier
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("Advertencia: Telegram no disponible")

# Importar gestor de historial
try:
    from src.utils.signal_history import signal_history
    HISTORY_AVAILABLE = True
except ImportError:
    HISTORY_AVAILABLE = False
    signal_history = None
    print("Advertencia: Historial CSV no disponible")

# Importar MT5 y conexión
try:
    import MetaTrader5 as mt5
    from src.broker.mt5_connection import MT5Connection
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False
    print("Advertencia: MetaTrader5 no disponible")

class SignalGenerator:
    def __init__(self, symbols=None, auto_execute=False, require_real_data=True):
        """
        Inicializa el generador de señales
        Args:
            symbols: Lista de símbolos a analizar
            auto_execute: Si True, ejecuta trades automáticamente en MT5
            require_real_data: Si True, solo usa datos reales (NO simulados)
        """
        self.symbols = symbols or ['XAUUSD', 'EURUSD', 'GBPUSD', 'BTCUSD']
        self.auto_execute = auto_execute
        self.require_real_data = require_real_data
        self.timeframes = {
            'M1': 1,
            'M5': 5,
            'M15': 15,
            'M30': 30,
            'H1': 60,
            'H4': 240,
            'D1': 1440
        }
        
        self.is_running = False
        self.signals_generated = 0
        self.trades_executed = 0
        self.positions_corrected = 0
        self.last_signals = {}
        self.signal_history = []
        
        # Umbral de confianza para ejecutar trades (15% - Más agresivo para detectar oportunidades)
        self.confidence_threshold = 0.15
        
        # Configurar logging con encoding UTF-8
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ],
            encoding='utf-8'
        )
        self.logger = logging.getLogger(__name__)
        
        # Inicializar Telegram
        self.telegram = None
        if TELEGRAM_AVAILABLE:
            try:
                self.telegram = TelegramNotifier()
                self.logger.info("Telegram notifier inicializado")
            except Exception as e:
                self.logger.error(f"Error inicializando Telegram: {e}")
                self.telegram = None
            
        # Inicializar MT5 y conexión
        self.mt5_connected = False
        self.mt5_connection = None
        if MT5_AVAILABLE:
            self.initialize_mt5()
            if self.auto_execute:
                try:
                    self.mt5_connection = MT5Connection()
                    if self.mt5_connection.connect():
                        self.logger.info("MT5 Connection establecida para auto-ejecución")
                    else:
                        self.logger.warning("No se pudo conectar MT5 para auto-ejecución")
                        self.auto_execute = False
                except Exception as e:
                    self.logger.error(f"Error iniciando MT5Connection: {e}")
                    self.auto_execute = False
            
        # Inicializar cliente TwelveData para obtener datos reales
        self.twelvedata_client = None
        try:
            from src.data.twelvedata_client import TwelveDataClient
            self.twelvedata_client = TwelveDataClient()
            self.logger.info("[OK] TwelveData client inicializado para datos reales")
        except Exception as e:
            self.logger.warning(f"[WARNING] TwelveData client no disponible: {e}")
            
        # Intentar cargar estrategia híbrida IA
        self.ai_hybrid_available = False
        try:
            from src.signals.ai_hybrid_strategy import ai_hybrid_strategy_function
            self.ai_hybrid_strategy = ai_hybrid_strategy_function
            self.ai_hybrid_available = True
            self.logger.info("[OK] Estrategia AI Hybrid cargada (Ollama + TwelveData)")
        except ImportError as e:
            self.logger.warning(f"[WARNING] AI Hybrid Strategy no disponible: {e}")
            self.ai_hybrid_strategy = None
        
        # Cargar nueva estrategia Multi-Timeframe
        self.multi_tf_available = False
        try:
            from src.signals.multi_timeframe_strategy import multi_timeframe_strategy_function
            self.multi_tf_strategy = multi_timeframe_strategy_function
            self.multi_tf_available = True
            self.logger.info("[OK] Estrategia Multi-Timeframe cargada (TwelveData + IA)")
        except ImportError as e:
            self.logger.warning(f"[WARNING] Multi-Timeframe Strategy no disponible: {e}")
            self.multi_tf_strategy = None

        # Cargar detector anticipatorio institucional (MT5)
        self.anticipatory_detector = None
        try:
            sys.path.append(str(Path(__file__).parent.parent.parent))
            from DETECTOR_ANTICIPATORIO_INSTITUCIONAL import DetectorAnticipatorioInstitucional
            self.anticipatory_detector = DetectorAnticipatorioInstitucional()
            self.logger.info("[OK] Detector Anticipatorio Institucional cargado (MT5)")
        except ImportError as e:
            self.logger.warning(f"[WARNING] Detector Anticipatorio no disponible: {e}")
            self.anticipatory_detector = None
        
        # SOLO DATOS REALES - Estrategias tradicionales DESACTIVADAS temporalmente
        strategies_dict = {
            # TODAS DESACTIVADAS - SOLO AI HYBRID CON DATOS REALES
            # 'test_strategy': self.test_strategy,
            # 'momentum': self.momentum_strategy,
            # 'mean_reversion': self.mean_reversion_strategy,
            # 'breakout': self.breakout_strategy,
            # 'ai_pattern': self.ai_pattern_strategy,
            # 'volume_analysis': self.volume_analysis_strategy,
            # 'multi_timeframe': self.multi_timeframe_strategy
        }
        
        # Agregar estrategia IA si está disponible
        if self.ai_hybrid_available:
            strategies_dict['ai_hybrid_ollama'] = self.ai_hybrid_strategy
        
        # Agregar estrategia Multi-Timeframe si está disponible
        if self.multi_tf_available:
            strategies_dict['multi_timeframe_ai'] = self.multi_tf_strategy
        
        self.strategies = strategies_dict
        
        self.logger.info("Generador de señales inicializado")
    
    def is_forex_market_open(self):
        """Verifica si el mercado Forex está abierto"""
        from datetime import datetime, timezone
        
        utc_now = datetime.now(timezone.utc)
        weekday = utc_now.weekday()  # 0=Monday, 6=Sunday
        hour = utc_now.hour
        
        # Forex cierra viernes 22:00 UTC y abre domingo 22:00 UTC
        if weekday == 5:  # Saturday
            return False
        elif weekday == 6:  # Sunday
            return hour >= 22  # Abre domingo 22:00 UTC
        elif weekday == 4:  # Friday
            return hour < 22   # Cierra viernes 22:00 UTC
        else:  # Monday-Thursday
            return True
    
    def get_active_symbols(self):
        """Retorna símbolos activos según horarios de mercado"""
        active_symbols = []
        
        # BTC siempre activo (crypto 24/7) - soporte para ambos formatos
        if 'BTCUSD' in self.symbols:
            active_symbols.append('BTCUSD')
        if 'BTCUSDm' in self.symbols:
            active_symbols.append('BTCUSDm')
        
        # XAUUSDm (Oro) - activo casi 24h excepto sábados
        from datetime import datetime
        current_hour = datetime.utcnow().weekday()
        if current_hour != 5:  # Sábado es día 5
            if 'XAUUSDm' in self.symbols:
                active_symbols.append('XAUUSDm')
            elif 'XAUUSD' in self.symbols:  # Soporte legacy
                active_symbols.append('XAUUSD')
        
        # Otros Forex symbols solo cuando mercado esté abierto
        if self.is_forex_market_open():
            forex_symbols = ['EURUSD', 'GBPUSD']
            for symbol in forex_symbols:
                if symbol in self.symbols:
                    active_symbols.append(symbol)
        
        return active_symbols
    
    def enable_auto_trading(self):
        """Habilita trading automático e inicializa MT5Connection si es necesario"""
        self.auto_execute = True
        
        if MT5_AVAILABLE and not self.mt5_connection:
            try:
                from src.broker.mt5_connection import MT5Connection
                self.mt5_connection = MT5Connection()
                if self.mt5_connection.connect():
                    self.logger.info("MT5 Connection inicializada para auto-trading")
                    return True
                else:
                    self.logger.warning("No se pudo conectar MT5 para auto-trading")
                    self.auto_execute = False
                    return False
            except Exception as e:
                self.logger.error(f"Error iniciando MT5Connection: {e}")
                self.auto_execute = False
                return False
        return True
    
    def check_and_reconnect_mt5(self):
        """Verifica el estado de MT5 y reconecta si es necesario"""
        if not self.mt5_connection:
            return False
        
        try:
            # Verificar conexión
            was_connected = self.mt5_connection.connected
            is_connected = self.mt5_connection.ensure_connected()
            
            if not was_connected and is_connected:
                self.logger.info("[OK] MT5 reconectado exitosamente")
                
                # Notificar reconexión por Telegram si está disponible
                if self.telegram and self.telegram.is_active:
                    try:
                        reconnect_msg = (
                            "**MT5 RECONECTADO**\n\n"
                            f"Estado: Conectado\n"
                            f"Cuenta: {self.mt5_connection.login}\n"
                            f"Servidor: {self.mt5_connection.server}\n"
                            f"Hora: {datetime.now().strftime('%H:%M:%S')}\n\n"
                            "Sistema de trading reactivado"
                        )
                        self.telegram.send_message(reconnect_msg)
                    except:
                        pass
            
            elif was_connected and not is_connected:
                self.logger.error("[ERROR] MT5 desconectado - No se pudo reconectar")
                
                # Notificar desconexión
                if self.telegram and self.telegram.is_active:
                    try:
                        disconnect_msg = (
                            "**MT5 DESCONECTADO**\n\n"
                            "Estado: Sin conexión\n"
                            f"Hora: {datetime.now().strftime('%H:%M:%S')}\n\n"
                            "Trading automático suspendido"
                        )
                        self.telegram.send_message(disconnect_msg)
                    except:
                        pass
            
            return is_connected
            
        except Exception as e:
            self.logger.error(f"Error verificando conexión MT5: {e}")
            return False
    
    def monitor_and_correct_positions(self):
        """Monitorea y corrige posiciones abiertas sin SL/TP"""
        if not self.mt5_connection:
            self.logger.debug("[MONITOR] No hay conexión MT5 disponible")
            return 0
            
        # Verificar y reconectar MT5 si es necesario
        if not self.mt5_connection.ensure_connected():
            self.logger.warning("[MONITOR] No se pudo reconectar MT5 para monitoreo de posiciones")
            return 0
        
        self.logger.info("[MONITOR] MT5 conectado - Revisando posiciones abiertas...")
        
        corrected_count = 0
        
        try:
            # Obtener todas las posiciones abiertas
            all_positions = self.mt5_connection.get_positions()
            
            if not all_positions:
                self.logger.info("[MONITOR] No hay posiciones abiertas en MT5")
                return 0
            
            self.logger.info(f"[MONITOR] Encontradas {len(all_positions)} posiciones abiertas")
            
            for position in all_positions:
                symbol = position.symbol
                ticket = position.ticket
                
                # Verificar si necesita corrección
                needs_correction = False
                
                if position.sl == 0.0:  # Sin Stop Loss
                    needs_correction = True
                if position.tp == 0.0:  # Sin Take Profit  
                    needs_correction = True
                
                if needs_correction:
                    # Notificar detección de trade sin SL/TP
                    sl_status = "Sin SL" if position.sl == 0.0 else f"SL: {position.sl:.5f}"
                    tp_status = "Sin TP" if position.tp == 0.0 else f"TP: {position.tp:.5f}"
                    
                    self.logger.warning(f"[DETECTED] Trade sin protección: {symbol} #{ticket} - {sl_status}, {tp_status}")
                    
                    # Notificar detección por Telegram
                    if self.telegram and self.telegram.is_active:
                        detection_msg = (
                            f"[ALERT] **TRADE SIN PROTECCION DETECTADO** [ALERT]\n\n"
                            f"Simbolo: {symbol}\n"
                            f"Ticket: #{ticket}\n"
                            f"Tipo: {'BUY' if position.type == 0 else 'SELL'}\n"
                            f"Volumen: {position.volume} lotes\n"
                            f"Precio Entrada: {position.price_open:.5f}\n"
                            f"Estado: {sl_status}, {tp_status}\n"
                            f"P&L Actual: {position.profit:.2f} USD\n\n"
                            f"[WARNING] Corrigiendo automáticamente..."
                        )
                        
                        try:
                            self.telegram.send_message(detection_msg)
                        except Exception as e:
                            self.logger.error(f"Error enviando notificación: {e}")
                    
                    # Calcular SL y TP apropiados
                    entry_price = position.price_open
                    position_type = 'BUY' if position.type == 0 else 'SELL'
                    
                    # Obtener ATR para cálculo dinámico
                    try:
                        df = self.get_market_data(symbol, '5min', 50)
                        if df is not None and len(df) > 14:
                            df = self.calculate_indicators(df)
                            atr = df['atr'].iloc[-1]
                        else:
                            atr = entry_price * 0.01  # 1% fallback
                    except:
                        atr = entry_price * 0.01
                    
                    # Calcular SL y TP con ATR
                    if position_type == 'BUY':
                        new_sl = entry_price - (atr * 2) if position.sl == 0.0 else position.sl
                        new_tp = entry_price + (atr * 3) if position.tp == 0.0 else position.tp
                    else:  # SELL
                        new_sl = entry_price + (atr * 2) if position.sl == 0.0 else position.sl
                        new_tp = entry_price - (atr * 3) if position.tp == 0.0 else position.tp
                    
                    # Modificar posición
                    result = self.mt5_connection.modify_position(ticket, new_sl, new_tp)
                    
                    if result:
                        corrected_count += 1
                        self.positions_corrected += 1
                        
                        self.logger.info(f"[CORRECTED] Posición corregida: {symbol} #{ticket}")
                        self.logger.info(f"   SL: {position.sl:.5f} -> {new_sl:.5f}")
                        self.logger.info(f"   TP: {position.tp:.5f} -> {new_tp:.5f}")
                        
                        # Notificar corrección
                        if self.telegram and self.telegram.is_active:
                            correction_msg = (
                                f"[OK] **POSICION CORREGIDA EXITOSAMENTE** [OK]\n\n"
                                f"[INFO] **Detalles:**\n"
                                f"Simbolo: {symbol}\n"
                                f"Tipo: {position_type}\n"
                                f"Ticket: #{ticket}\n"
                                f"Volumen: {position.volume} lotes\n"
                                f"Precio Entrada: {entry_price:.5f}\n\n"
                                f"[PROTECTION] **Protección Agregada:**\n"
                                f"Stop Loss: {new_sl:.5f} {'(NUEVO)' if position.sl == 0.0 else '(CORREGIDO)'}\n"
                                f"Take Profit: {new_tp:.5f} {'(NUEVO)' if position.tp == 0.0 else '(CORREGIDO)'}\n"
                                f"ATR usado: {atr:.5f}\n"
                                f"Riesgo: 2x ATR | Beneficio: 3x ATR\n\n"
                                f"[STATS] **Estadísticas:**\n"
                                f"Total Correcciones Hoy: {self.positions_corrected}"
                            )
                            
                            try:
                                self.telegram.send_message(correction_msg)
                            except:
                                pass
                    else:
                        self.logger.error(f"[ERROR] Error corrigiendo posición {symbol} #{ticket}")
                        
        except Exception as e:
            self.logger.error(f"Error monitoreando posiciones: {e}")
            
        return corrected_count
        
    def initialize_mt5(self):
        """Inicializa conexión con MT5"""
        try:
            if mt5.initialize():
                self.mt5_connected = True
                self.logger.info("MT5 conectado")
                return True
        except Exception as e:
            self.logger.error(f"Error conectando MT5: {e}")
            self.mt5_connected = False
        return False
        
    def get_market_data(self, symbol, timeframe='M5', bars=100):
        """Obtiene datos del mercado"""
        if self.mt5_connected and MT5_AVAILABLE:
            try:
                tf_map = {
                    'M1': mt5.TIMEFRAME_M1,
                    'M5': mt5.TIMEFRAME_M5,
                    'M15': mt5.TIMEFRAME_M15,
                    'M30': mt5.TIMEFRAME_M30,
                    'H1': mt5.TIMEFRAME_H1,
                    'H4': mt5.TIMEFRAME_H4,
                    'D1': mt5.TIMEFRAME_D1
                }
                tf = tf_map.get(timeframe, mt5.TIMEFRAME_M5)
                rates = mt5.copy_rates_from_pos(symbol, tf, 0, bars)
                
                if rates is not None and len(rates) > 0:
                    df = pd.DataFrame(rates)
                    df['time'] = pd.to_datetime(df['time'], unit='s')
                    return df
            except Exception as e:
                self.logger.error(f"Error obteniendo datos de {symbol}: {e}")
                
        # Intentar usar TwelveData API para datos reales
        if self.twelvedata_client:
            try:
                # Usar el método apropiado según el tipo de símbolo
                if symbol == 'BTCUSD':
                    df = self.twelvedata_client.get_crypto_data(symbol, interval=timeframe)
                elif symbol in ['EURUSD', 'GBPUSD', 'XAUUSD']:
                    df = self.twelvedata_client.get_forex_data(symbol, interval=timeframe)
                else:
                    df = self.twelvedata_client.get_time_series(symbol, interval=timeframe, outputsize=bars)
                
                if df is not None and len(df) > 0:
                    # Renombrar columnas para compatibilidad
                    if 'time' not in df.columns and 'datetime' in df.columns:
                        df = df.rename(columns={'datetime': 'time'})
                    
                    # Añadir tick_volume si no existe
                    if 'tick_volume' not in df.columns:
                        df['tick_volume'] = df['volume']
                    
                    # Añadir spread simulado
                    if 'spread' not in df.columns:
                        df['spread'] = 2
                    
                    # Añadir real_volume si no existe
                    if 'real_volume' not in df.columns:
                        df['real_volume'] = df['volume']
                    
                    self.logger.info(f"[OK] Datos reales obtenidos para {symbol}: {len(df)} barras")
                    return df
                else:
                    self.logger.warning(f"[WARNING] No se obtuvieron datos TwelveData para {symbol}")
            except Exception as e:
                self.logger.error(f"[ERROR] Error TwelveData para {symbol}: {e}")
        
        # Si no hay datos reales, retornar None (NO usar simulados)
        self.logger.error(f"NO HAY DATOS REALES para {symbol}. No se generarán señales.")
        return None
        
        
    def calculate_indicators(self, df):
        """Calcula indicadores técnicos"""
        try:
            # SMA
            df['sma_20'] = df['close'].rolling(window=20, min_periods=1).mean()
            df['sma_50'] = df['close'].rolling(window=50, min_periods=1).mean()
            
            # EMA
            df['ema_12'] = df['close'].ewm(span=12, adjust=False, min_periods=1).mean()
            df['ema_26'] = df['close'].ewm(span=26, adjust=False, min_periods=1).mean()
            
            # MACD
            df['macd'] = df['ema_12'] - df['ema_26']
            df['signal'] = df['macd'].ewm(span=9, adjust=False, min_periods=1).mean()
            df['histogram'] = df['macd'] - df['signal']
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14, min_periods=1).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14, min_periods=1).mean()
            rs = gain / (loss + 0.0001)  # Evitar división por cero
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # Bollinger Bands
            df['bb_middle'] = df['close'].rolling(window=20, min_periods=1).mean()
            bb_std = df['close'].rolling(window=20, min_periods=1).std()
            df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
            df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
            
            # ATR (Average True Range)
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            ranges = pd.concat([high_low, high_close, low_close], axis=1)
            true_range = np.max(ranges, axis=1)
            df['atr'] = true_range.rolling(14, min_periods=1).mean()
            
            # Volume indicators
            df['volume_sma'] = df['tick_volume'].rolling(window=20, min_periods=1).mean()
            df['volume_ratio'] = df['tick_volume'] / (df['volume_sma'] + 1)  # Evitar división por cero
            
            # Rellenar NaN con valores por defecto
            df = df.ffill()
            df = df.fillna(0)
            
        except Exception as e:
            self.logger.error(f"Error calculando indicadores: {e}")
            
        return df

    def test_strategy(self, df, symbol):
        """Estrategia de prueba que genera señales ocasionalmente"""
        signals = []
        
        try:
            if len(df) < 1:
                return signals
                
            # Generar una señal cada 5 ciclos aproximadamente (20% probabilidad)
            if np.random.random() < 0.2:
                signal_type = np.random.choice(['BUY', 'SELL'])
                last_row = df.iloc[-1]
                
                signal = {
                    'symbol': symbol,
                    'type': signal_type,
                    'price': last_row['close'],
                    'strength': np.random.uniform(0.7, 0.9),  # Alta confianza
                    'strategy': 'Test Strategy',
                    'reason': f'Señal de prueba {signal_type} generada aleatoriamente'
                }
                signals.append(signal)
                
        except Exception as e:
            self.logger.error(f"Error en test_strategy: {e}")
            
        return signals
        
    def momentum_strategy(self, df, symbol):
        """Estrategia de momentum"""
        signals = []
        
        try:
            # Calcular momentum
            df['momentum'] = df['close'] - df['close'].shift(10)
            
            if len(df) < 2:
                return signals
                
            last_row = df.iloc[-1]
            prev_row = df.iloc[-2]
            
            # Señal de compra (condiciones más flexibles)
            if (last_row['momentum'] > 0 and 
                prev_row['momentum'] <= 0 and 
                last_row['rsi'] < 75 and
                last_row['volume_ratio'] > 1.1):
                
                signal = {
                    'symbol': symbol,
                    'type': 'BUY',
                    'price': last_row['close'],
                    'strength': min(0.85, last_row['volume_ratio'] / 2),
                    'strategy': 'Momentum',
                    'reason': 'Cruce de momentum positivo con volumen alto'
                }
                signals.append(signal)
                
            # Señal de venta
            elif (last_row['momentum'] < 0 and 
                  prev_row['momentum'] >= 0 and 
                  last_row['rsi'] > 25 and
                  last_row['volume_ratio'] > 1.1):
                
                signal = {
                    'symbol': symbol,
                    'type': 'SELL',
                    'price': last_row['close'],
                    'strength': min(0.85, last_row['volume_ratio'] / 2),
                    'strategy': 'Momentum',
                    'reason': 'Cruce de momentum negativo con volumen alto'
                }
                signals.append(signal)
                
        except Exception as e:
            self.logger.error(f"Error en momentum_strategy: {e}")
            
        return signals
        
    def mean_reversion_strategy(self, df, symbol):
        """Estrategia de reversión a la media"""
        signals = []
        
        try:
            if len(df) < 1:
                return signals
                
            last_row = df.iloc[-1]
            
            # Distancia a Bollinger Bands
            bb_range = last_row['bb_upper'] - last_row['bb_lower']
            if bb_range > 0:
                bb_position = (last_row['close'] - last_row['bb_lower']) / bb_range
            else:
                bb_position = 0.5
            
            # Señal de compra (sobreventa) - más sensible
            if bb_position < 0.25 and last_row['rsi'] < 45:
                signal = {
                    'symbol': symbol,
                    'type': 'BUY',
                    'price': last_row['close'],
                    'strength': 0.75,
                    'strategy': 'Mean Reversion',
                    'reason': 'Precio en banda inferior con RSI sobreventa'
                }
                signals.append(signal)
                
            # Señal de venta (sobrecompra) - más sensible
            elif bb_position > 0.75 and last_row['rsi'] > 55:
                signal = {
                    'symbol': symbol,
                    'type': 'SELL',
                    'price': last_row['close'],
                    'strength': 0.75,
                    'strategy': 'Mean Reversion',
                    'reason': 'Precio en banda superior con RSI sobrecompra'
                }
                signals.append(signal)
                
        except Exception as e:
            self.logger.error(f"Error en mean_reversion_strategy: {e}")
            
        return signals
        
    def breakout_strategy(self, df, symbol):
        """Estrategia de ruptura"""
        signals = []
        
        try:
            if len(df) < 20:
                return signals
                
            # Calcular niveles de soporte y resistencia
            recent_high = df['high'].rolling(window=20, min_periods=1).max()
            recent_low = df['low'].rolling(window=20, min_periods=1).min()
            
            last_row = df.iloc[-1]
            prev_high = recent_high.iloc[-2] if len(recent_high) > 1 else last_row['high']
            prev_low = recent_low.iloc[-2] if len(recent_low) > 1 else last_row['low']
            
            # Ruptura alcista
            if last_row['close'] > prev_high and last_row['volume_ratio'] > 1.5:
                signal = {
                    'symbol': symbol,
                    'type': 'BUY',
                    'price': last_row['close'],
                    'strength': 0.80,
                    'strategy': 'Breakout',
                    'reason': f'Ruptura de resistencia en {prev_high:.5f}'
                }
                signals.append(signal)
                
            # Ruptura bajista
            elif last_row['close'] < prev_low and last_row['volume_ratio'] > 1.5:
                signal = {
                    'symbol': symbol,
                    'type': 'SELL',
                    'price': last_row['close'],
                    'strength': 0.80,
                    'strategy': 'Breakout',
                    'reason': f'Ruptura de soporte en {prev_low:.5f}'
                }
                signals.append(signal)
                
        except Exception as e:
            self.logger.error(f"Error en breakout_strategy: {e}")
            
        return signals
        
    def ai_pattern_strategy(self, df, symbol):
        """Estrategia basada en patrones con IA"""
        signals = []
        
        try:
            if len(df) < 3:
                return signals
                
            # Detectar patrones de velas
            last_rows = df.tail(3)
            
            # Patrón Bullish Engulfing
            if len(last_rows) >= 2:
                prev = last_rows.iloc[-2]
                curr = last_rows.iloc[-1]
                
                if (prev['close'] < prev['open'] and  # Vela bajista previa
                    curr['close'] > curr['open'] and  # Vela alcista actual
                    curr['open'] < prev['close'] and  # Apertura menor que cierre previo
                    curr['close'] > prev['open']):    # Cierre mayor que apertura previa
                    
                    signal = {
                        'symbol': symbol,
                        'type': 'BUY',
                        'price': curr['close'],
                        'strength': 0.70,
                        'strategy': 'AI Pattern',
                        'reason': 'Patrón Bullish Engulfing detectado'
                    }
                    signals.append(signal)
                    
            # Patrón Bearish Engulfing
            if len(last_rows) >= 2:
                prev = last_rows.iloc[-2]
                curr = last_rows.iloc[-1]
                
                if (prev['close'] > prev['open'] and  # Vela alcista previa
                    curr['close'] < curr['open'] and  # Vela bajista actual
                    curr['open'] > prev['close'] and  # Apertura mayor que cierre previo
                    curr['close'] < prev['open']):    # Cierre menor que apertura previa
                    
                    signal = {
                        'symbol': symbol,
                        'type': 'SELL',
                        'price': curr['close'],
                        'strength': 0.70,
                        'strategy': 'AI Pattern',
                        'reason': 'Patrón Bearish Engulfing detectado'
                    }
                    signals.append(signal)
                    
        except Exception as e:
            self.logger.error(f"Error en ai_pattern_strategy: {e}")
            
        return signals
        
    def volume_analysis_strategy(self, df, symbol):
        """Estrategia basada en análisis de volumen"""
        signals = []
        
        try:
            if len(df) < 1:
                return signals
                
            last_row = df.iloc[-1]
            
            # Detectar picos de volumen
            if last_row['volume_ratio'] > 2.0:
                # Determinar dirección basada en precio
                if last_row['close'] > last_row['open']:
                    signal = {
                        'symbol': symbol,
                        'type': 'BUY',
                        'price': last_row['close'],
                        'strength': min(0.90, last_row['volume_ratio'] / 3),
                        'strategy': 'Volume Analysis',
                        'reason': f'Pico de volumen alcista ({last_row["volume_ratio"]:.1f}x)'
                    }
                    signals.append(signal)
                else:
                    signal = {
                        'symbol': symbol,
                        'type': 'SELL',
                        'price': last_row['close'],
                        'strength': min(0.90, last_row['volume_ratio'] / 3),
                        'strategy': 'Volume Analysis',
                        'reason': f'Pico de volumen bajista ({last_row["volume_ratio"]:.1f}x)'
                    }
                    signals.append(signal)
                    
        except Exception as e:
            self.logger.error(f"Error en volume_analysis_strategy: {e}")
            
        return signals
        
    def multi_timeframe_strategy(self, df, symbol):
        """Estrategia multi-timeframe"""
        signals = []
        
        try:
            if len(df) < 1:
                return signals
                
            last_row = df.iloc[-1]
            
            # Confluencia de indicadores
            bullish_score = 0
            bearish_score = 0
            
            # RSI
            if last_row['rsi'] < 40:
                bullish_score += 1
            elif last_row['rsi'] > 60:
                bearish_score += 1
                
            # MACD
            if last_row['macd'] > last_row['signal']:
                bullish_score += 1
            else:
                bearish_score += 1
                
            # Moving Averages
            if last_row['close'] > last_row['sma_20']:
                bullish_score += 1
            else:
                bearish_score += 1
                
            # Bollinger Bands
            bb_range = last_row['bb_upper'] - last_row['bb_lower']
            if bb_range > 0:
                bb_position = (last_row['close'] - last_row['bb_lower']) / bb_range
                if bb_position < 0.3:
                    bullish_score += 1
                elif bb_position > 0.7:
                    bearish_score += 1
                    
            # Generar señal basada en puntuación
            if bullish_score >= 3:
                signal = {
                    'symbol': symbol,
                    'type': 'BUY',
                    'price': last_row['close'],
                    'strength': bullish_score / 4.0,
                    'strategy': 'Multi-Timeframe',
                    'reason': f'Confluencia alcista ({bullish_score}/4 indicadores)'
                }
                signals.append(signal)
                
            elif bearish_score >= 3:
                signal = {
                    'symbol': symbol,
                    'type': 'SELL',
                    'price': last_row['close'],
                    'strength': bearish_score / 4.0,
                    'strategy': 'Multi-Timeframe',
                    'reason': f'Confluencia bajista ({bearish_score}/4 indicadores)'
                }
                signals.append(signal)
                
        except Exception as e:
            self.logger.error(f"Error en multi_timeframe_strategy: {e}")
            
        return signals
        
    def calculate_tp_sl(self, signal, df):
        """Calcula Take Profit y Stop Loss dinámicos"""
        try:
            atr = df['atr'].iloc[-1]
            
            # Si ATR es 0 o muy pequeño, usar un valor por defecto
            if atr < 0.0001:
                atr = signal['price'] * 0.002  # 0.2% del precio
            
            if signal['type'] == 'BUY':
                signal['tp'] = signal['price'] + (atr * 2.0)  # 2x ATR para TP
                signal['sl'] = signal['price'] - (atr * 1.0)  # 1x ATR para SL
            else:
                signal['tp'] = signal['price'] - (atr * 2.0)
                signal['sl'] = signal['price'] + (atr * 1.0)
                
            # Ajustar según la fuerza de la señal
            if signal['strength'] > 0.8:
                # Señal fuerte, TP más ambicioso
                multiplier = 1.5
            else:
                multiplier = 1.0
                
            if signal['type'] == 'BUY':
                signal['tp'] = signal['price'] + ((signal['tp'] - signal['price']) * multiplier)
            else:
                signal['tp'] = signal['price'] - ((signal['price'] - signal['tp']) * multiplier)
                
        except Exception as e:
            self.logger.error(f"Error calculando TP/SL: {e}")
            # Valores por defecto si hay error
            if signal['type'] == 'BUY':
                signal['tp'] = signal['price'] * 1.002
                signal['sl'] = signal['price'] * 0.998
            else:
                signal['tp'] = signal['price'] * 0.998
                signal['sl'] = signal['price'] * 1.002
                
        return signal
        
    def analyze_symbol(self, symbol):
        """Analiza un símbolo con todas las estrategias"""
        all_signals = []
        
        try:
            # Obtener datos
            df = self.get_market_data(symbol, '5min', 100)
            
            if df is None:
                self.logger.warning(f"No hay datos reales para {symbol}. Saltando análisis.")
                return all_signals
            
            if len(df) < 50:
                self.logger.warning(f"Datos insuficientes para {symbol}: {len(df)} barras")
                return all_signals
                
            # Calcular indicadores
            df = self.calculate_indicators(df)

            # DETECTOR ANTICIPATORIO INSTITUCIONAL - PRIORIDAD MÁXIMA
            if self.anticipatory_detector:
                try:
                    anticipatory_signal = self.anticipatory_detector.analizar_momentum_actual(symbol)
                    if anticipatory_signal and anticipatory_signal.get('tipo'):
                        # Crear señal basada en detección anticipatoria
                        signal = {
                            'symbol': symbol,
                            'type': anticipatory_signal['tipo'],
                            'price': anticipatory_signal['precio_actual'],
                            'confidence': anticipatory_signal['confianza'],  # Usar confianza del detector
                            'strength': 0.95,  # Alta fuerza para señales anticipatorias
                            'strategy': 'ANTICIPATORY_INSTITUTIONAL',
                            'reason': f"Detección anticipatoria: {anticipatory_signal['razon']}",
                            'ratio_tamaño': anticipatory_signal['ratio_tamaño'],
                            'tiempo_restante': anticipatory_signal['tiempo_restante_vela']
                        }
                        signal = self.calculate_tp_sl(signal, df)
                        signal['timeframe'] = 'M1'
                        signal['timestamp'] = datetime.now()
                        all_signals.append(signal)
                        self.logger.info(f"SEÑAL ANTICIPATORIA DETECTADA: {symbol} {signal['type']} - Confianza: {signal['confidence']:.1%}")
                        self.logger.info(f"   Tiempo restante: {anticipatory_signal['tiempo_restante_vela']:.0f}s")
                except Exception as e:
                    self.logger.error(f"Error en detector anticipatorio: {e}")

            # Aplicar todas las estrategias
            for strategy_name, strategy_func in self.strategies.items():
                try:
                    signals = strategy_func(df, symbol)
                    for signal in signals:
                        # Añadir TP/SL
                        signal = self.calculate_tp_sl(signal, df)
                        signal['timeframe'] = 'M5'
                        signal['timestamp'] = datetime.now()
                        all_signals.append(signal)
                except Exception as e:
                    self.logger.error(f"Error en {strategy_name}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error analizando {symbol}: {e}")
            
        return all_signals
        
    def filter_signals(self, signals):
        """Filtra y prioriza señales por confianza y fuerza"""
        # Eliminar duplicados del mismo símbolo
        filtered = {}
        confidence_filtered = []
        
        # Primero filtrar por umbral de confianza
        for signal in signals:
            confidence = signal.get('confidence', 0.0)
            if confidence >= self.confidence_threshold:
                confidence_filtered.append(signal)
        
        # Luego eliminar duplicados por símbolo
        for signal in confidence_filtered:
            key = signal['symbol']
            
            # Si no existe o la nueva señal es más fuerte
            if key not in filtered or signal['strength'] > filtered[key]['strength']:
                filtered[key] = signal
                
        return list(filtered.values())
        
    def calculate_position_size(self, symbol, signal):
        """Calcula el tamaño de posición basado en riesgo"""
        try:
            if not self.mt5_connection:
                return 0.01  # Tamaño mínimo por defecto
            
            # Obtener información de la cuenta
            account_info = self.mt5_connection.get_account_info()
            if not account_info:
                return 0.01
            
            # Riesgo del 2% del balance
            risk_percent = 0.02
            risk_amount = account_info.balance * risk_percent
            
            # Calcular pips de SL
            entry_price = signal['price']
            sl_price = signal.get('sl', entry_price * 0.995 if signal['type'] == 'BUY' else entry_price * 1.005)
            sl_pips = abs(entry_price - sl_price) / (0.0001 if 'JPY' not in symbol else 0.01)
            
            # Calcular tamaño usando MT5Connection
            position_size = self.mt5_connection.calculate_position_size(symbol, risk_amount, sl_pips)
            
            # Aplicar límites de seguridad
            return max(0.01, min(position_size, 1.0))  # Entre 0.01 y 1.0 lotes
            
        except Exception as e:
            self.logger.error(f"Error calculando tamaño de posición: {e}")
            return 0.01

    def execute_trade(self, signal):
        """Ejecuta un trade en MT5 basado en la señal"""
        try:
            if not self.auto_execute or not self.mt5_connection:
                return False
            
            # Verificar y reconectar MT5 si es necesario
            if not self.mt5_connection.ensure_connected():
                self.logger.error("No se pudo conectar/reconectar MT5 para ejecutar trade")
                return False
            
            symbol = signal['symbol']
            
            # Verificar si ya hay posición en este símbolo
            positions = self.mt5_connection.get_positions(symbol)
            if positions:
                # Permitir múltiples posiciones si la señal es muy fuerte (>75%)
                signal_strength = signal.get('strength', 0)
                if signal_strength > 0.75:  # 75% o más
                    self.logger.info(f"Señal FUERTE ({signal_strength:.1%}) - Permitiendo posición adicional en {symbol}")
                else:
                    self.logger.info(f"Ya hay posición abierta en {symbol}, saltando...")
                    return False
            
            # Calcular tamaño de posición
            volume = self.calculate_position_size(symbol, signal)
            
            # Obtener precios actualizados
            tick = self.mt5_connection.get_tick(symbol)
            if not tick:
                self.logger.error(f"No se pudo obtener tick para {symbol}")
                return False
            
            # Usar precio actual del mercado
            current_price = tick.ask if signal['type'] == 'BUY' else tick.bid
            
            # Calcular SL y TP actualizados
            sl = signal.get('sl')
            tp = signal.get('tp')
            
            # Ejecutar orden
            order_type = 'buy' if signal['type'] == 'BUY' else 'sell'
            result = self.mt5_connection.place_order(
                symbol=symbol,
                order_type=order_type,
                volume=volume,
                price=current_price,
                sl=sl,
                tp=tp,
                comment=f"Signal_{signal.get('strategy', 'AI')[:8]}"
            )
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                self.trades_executed += 1
                
                self.logger.info(f"[OK] TRADE EJECUTADO: {symbol} {signal['type']} {volume} lotes")
                
                # Notificar ejecución exitosa
                if self.telegram and self.telegram.is_active:
                    trade_message = (
                        f"[OK] **TRADE EJECUTADO** [OK]\n\n"
                        f"[INFO] **Símbolo:** {symbol}\n"
                        f"[STATS] **Tipo:** {signal['type']}\n"
                        f"💰 **Volumen:** {volume} lotes\n"
                        f"💵 **Precio:** {current_price:.5f}\n"
                        f"[PROTECTION] **Stop Loss:** {sl:.5f}\n"
                        f"🎯 **Take Profit:** {tp:.5f}\n"
                        f"💪 **Fuerza:** {signal.get('strength', 0)*100:.0f}%\n"
                        f"🤖 **Estrategia:** {signal.get('strategy', 'AI')}\n"
                        f"🎫 **Ticket:** #{result.order}\n\n"
                        f"[STATS] **Total Trades:** {self.trades_executed}"
                    )
                    
                    try:
                        self.telegram.send_message(trade_message)
                    except:
                        pass
                
                return True
            else:
                error_msg = result.comment if result else "Error desconocido"
                self.logger.error(f"[ERROR] Trade rechazado: {error_msg}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error ejecutando trade: {e}")
            return False

    def send_signal_notifications(self, signals):
        """Envía señales por Telegram y ejecuta trades si está habilitado"""
        for signal in signals:
            try:
                # Guardar señal en historial CSV
                if HISTORY_AVAILABLE and signal_history:
                    try:
                        # Crear respuesta simulada para guardado
                        ia_response = f"""
📊 **INDICADORES CLAVE**
RSI: {signal.get('rsi', 'N/A')}, MACD: {signal.get('macd', 'N/A')}, ATR: {signal.get('atr', 'N/A')}

✅ **SEÑAL FINAL: {signal['type'].upper()}**

🧠 **RAZONAMIENTO**
{signal.get('reasoning', 'Análisis técnico automático')}

📈 **SETUP OPERATIVO**
- Entrada: {signal.get('price', 0)}
- SL: {signal.get('sl', 0)}
- TP: {signal.get('tp', 0)}
- Ratio: {signal.get('ratio', 0)}
- Confianza: {signal.get('strength', 70)}%
"""
                        signal_history.save_signal(
                            ia_response=ia_response,
                            symbol=signal['symbol'],
                            strategy=signal.get('strategy', 'AI_Hybrid'),
                            timeframes="5min,15min,1h"
                        )
                    except Exception as e:
                        self.logger.error(f"Error guardando historial: {e}")
                
                # Enviar notificación de señal
                if self.telegram and self.telegram.is_active:
                    self.telegram.send_signal(signal)
                    self.logger.info(f"Señal enviada: {signal['symbol']} {signal['type']}")
                
                # Ejecutar trade si está habilitado
                if self.auto_execute:
                    success = self.execute_trade(signal)
                    if success:
                        self.logger.info(f"Trade ejecutado para señal: {signal['symbol']} {signal['type']}")
                    else:
                        self.logger.warning(f"No se pudo ejecutar trade para: {signal['symbol']} {signal['type']}")
                else:
                    self.logger.info(f"Auto-ejecución deshabilitada. Solo notificación enviada.")
                    
            except Exception as e:
                self.logger.error(f"Error procesando señal: {e}")

    def calculate_dynamic_sl_tp(self, symbol, position_type, entry_price):
        """Calcula SL/TP dinámicos basados en ATR y análisis técnico"""
        try:
            # Obtener datos recientes para calcular ATR
            df = self.get_market_data(symbol, 'M5', 50)
            if df is None or len(df) < 20:
                # Valores por defecto si no hay datos
                if position_type == 0:  # BUY
                    sl = entry_price * 0.995  # -0.5%
                    tp = entry_price * 1.015  # +1.5%
                else:  # SELL
                    sl = entry_price * 1.005  # +0.5%
                    tp = entry_price * 0.985  # -1.5%
                return sl, tp
            
            df = self.calculate_indicators(df)
            atr = df['atr'].iloc[-1]
            
            # Si ATR es muy pequeño, usar valor por defecto
            if atr < entry_price * 0.001:
                atr = entry_price * 0.002
            
            if position_type == 0:  # BUY
                sl = entry_price - (atr * 1.5)  # 1.5x ATR para SL
                tp = entry_price + (atr * 2.5)  # 2.5x ATR para TP
            else:  # SELL
                sl = entry_price + (atr * 1.5)
                tp = entry_price - (atr * 2.5)
            
            return sl, tp
            
        except Exception as e:
            self.logger.error(f"Error calculando SL/TP dinámicos: {e}")
            # Valores de seguridad
            if position_type == 0:  # BUY
                return entry_price * 0.995, entry_price * 1.015
            else:  # SELL
                return entry_price * 1.005, entry_price * 0.985

    def monitor_and_fix_positions(self):
        """Monitorea y corrige posiciones sin SL/TP"""
        if not self.mt5_connection or not self.mt5_connection.connected:
            return
        
        try:
            # Obtener todas las posiciones abiertas
            positions = self.mt5_connection.get_positions()
            
            if not positions:
                return
            
            positions_fixed = 0
            
            for position in positions:
                needs_fix = False
                
                # Verificar si falta SL o TP
                if position.sl == 0.0 or position.tp == 0.0:
                    needs_fix = True
                    
                    self.logger.warning(f"🔧 Posición sin SL/TP detectada: {position.symbol} #{position.ticket}")
                    
                    # Calcular SL/TP dinámicos
                    sl, tp = self.calculate_dynamic_sl_tp(
                        position.symbol, 
                        position.type, 
                        position.price_open
                    )
                    
                    # Solo modificar los valores que faltan
                    new_sl = sl if position.sl == 0.0 else position.sl
                    new_tp = tp if position.tp == 0.0 else position.tp
                    
                    # Modificar la posición
                    success = self.mt5_connection.modify_position(
                        position.ticket, 
                        sl=new_sl, 
                        tp=new_tp
                    )
                    
                    if success:
                        self.positions_corrected += 1
                        positions_fixed += 1
                        
                        position_type = "BUY" if position.type == 0 else "SELL"
                        
                        self.logger.info(f"[OK] Posición corregida: {position.symbol} #{position.ticket}")
                        self.logger.info(f"   Tipo: {position_type} | Volumen: {position.volume}")
                        self.logger.info(f"   SL: {new_sl:.5f} | TP: {new_tp:.5f}")
                        
                        # Notificar por Telegram
                        if self.telegram and self.telegram.is_active:
                            try:
                                fix_message = (
                                    f"🔧 **POSICIÓN CORREGIDA** 🔧\n\n"
                                    f"[INFO] **Símbolo:** {position.symbol}\n"
                                    f"🎫 **Ticket:** #{position.ticket}\n"
                                    f"[STATS] **Tipo:** {position_type}\n"
                                    f"💰 **Volumen:** {position.volume} lotes\n"
                                    f"💵 **Precio Entrada:** {position.price_open:.5f}\n"
                                    f"[PROTECTION] **Stop Loss:** {new_sl:.5f}\n"
                                    f"🎯 **Take Profit:** {new_tp:.5f}\n\n"
                                    f"⚡ **Razón:** Faltaba SL/TP automático\n"
                                    f"[STATS] **Total Corregidas:** {self.positions_corrected}"
                                )
                                self.telegram.send_message(fix_message)
                            except Exception as e:
                                self.logger.error(f"Error enviando notificación de corrección: {e}")
                    else:
                        self.logger.error(f"[ERROR] No se pudo corregir posición: {position.symbol} #{position.ticket}")
            
            if positions_fixed > 0:
                self.logger.info(f"[OK] {positions_fixed} posiciones corregidas en este ciclo")
            
        except Exception as e:
            self.logger.error(f"Error monitoreando posiciones: {e}")

    def get_positions_summary(self):
        """Obtiene resumen de posiciones abiertas"""
        if not self.mt5_connection:
            return "MT5 no inicializado"
            
        # Verificar y reconectar MT5 si es necesario
        if not self.mt5_connection.ensure_connected():
            return "MT5 no conectado - Error de reconexión"
        
        try:
            positions = self.mt5_connection.get_positions()
            
            if not positions:
                return "No hay posiciones abiertas"
            
            summary = []
            total_profit = 0
            
            for position in positions:
                position_type = "BUY" if position.type == 0 else "SELL"
                sl_status = "[OK]" if position.sl != 0.0 else "[ERROR]"
                tp_status = "[OK]" if position.tp != 0.0 else "[ERROR]"
                
                summary.append(
                    f"• {position.symbol} #{position.ticket}: {position_type} {position.volume} "
                    f"(SL:{sl_status} TP:{tp_status}) P&L: {position.profit:.2f}"
                )
                total_profit += position.profit
            
            return f"\n".join(summary) + f"\n\n💰 P&L Total: ${total_profit:.2f}"
            
        except Exception as e:
            return f"Error obteniendo posiciones: {e}"
                    
    def run_analysis_cycle(self):
        """Ejecuta un ciclo de análisis usando símbolos activos según horarios de mercado"""
        # Obtener símbolos activos según horarios
        active_symbols = self.get_active_symbols()
        
        forex_status = "ABIERTO" if self.is_forex_market_open() else "CERRADO"
        self.logger.info(f"Mercado Forex: {forex_status} - Analizando {len(active_symbols)} símbolos activos...")
        
        if not active_symbols:
            self.logger.info("No hay símbolos activos en este momento (Forex cerrado, solo crypto disponible)")
            return []
        
        all_signals = []
        
        for symbol in active_symbols:
            signals = self.analyze_symbol(symbol)
            all_signals.extend(signals)
            
        # Filtrar señales
        filtered_signals = self.filter_signals(all_signals)
        
        # Enviar notificaciones
        if filtered_signals:
            self.logger.info(f"{len(filtered_signals)} señales generadas")
            self.send_signal_notifications(filtered_signals)
            
            # Guardar en historial
            for signal in filtered_signals:
                self.signal_history.append(signal)
                self.last_signals[signal['symbol']] = signal
                self.signals_generated += 1
        else:
            self.logger.info("No hay señales en este ciclo")
            
        # Monitorear y corregir posiciones abiertas (si está conectado a MT5)
        if self.auto_execute and self.mt5_connection:
            self.monitor_and_fix_positions()
            
        return filtered_signals
        
    def start(self):
        """Inicia el generador de señales"""
        self.is_running = True
        self.logger.info("Generador de señales iniciado")
        
        # Enviar notificación de inicio
        if self.telegram and self.telegram.is_active:
            self.telegram.send_alert(
                'info',
                f'Generador de señales iniciado\nSímbolos: {", ".join(self.symbols)}\nEstrategias: 6 activas'
            )
        
        cycle_count = 0
        while self.is_running:
            try:
                cycle_count += 1
                self.logger.info(f"Ciclo #{cycle_count}")
                
                # Verificar y reconectar MT5 si es necesario (cada 5 ciclos)
                if cycle_count % 5 == 0:
                    self.check_and_reconnect_mt5()
                
                # Ejecutar análisis
                self.run_analysis_cycle()
                
                # Enviar reporte cada 10 ciclos
                if cycle_count % 10 == 0 and self.telegram and self.telegram.is_active:
                    # Obtener estadísticas reales de MT5 si está conectado
                    account_info = None
                    if self.mt5_connection:
                        account_info = self.mt5_connection.get_account_info()
                    
                    # Obtener resumen de posiciones
                    positions_summary = self.get_positions_summary()
                    
                    report = {
                        'signals_generated': self.signals_generated,
                        'total_trades': self.trades_executed,
                        'positions_corrected': self.positions_corrected,
                        'winning_trades': 0,
                        'losing_trades': 0,
                        'win_rate': 0,
                        'total_profit': 0,
                        'best_trade': 0,
                        'worst_trade': 0,
                        'avg_profit': 0,
                        'balance': account_info.balance if account_info else 10000,
                        'equity': account_info.equity if account_info else 10000,
                        'margin': account_info.margin if account_info else 0,
                        'drawdown': 0,
                        'signals_executed': self.trades_executed,
                        'signal_accuracy': (self.trades_executed / max(1, self.signals_generated)) * 100,
                        'positions_summary': positions_summary
                    }
                    self.telegram.send_daily_report(report)
                
                # Esperar antes del próximo ciclo
                self.logger.info(f"Esperando 60 segundos hasta el próximo análisis...")
                time.sleep(60)
                
            except KeyboardInterrupt:
                self.logger.info("Deteniendo generador...")
                break
            except Exception as e:
                self.logger.error(f"Error en ciclo: {e}")
                time.sleep(5)
                
    def stop(self):
        """Detiene el generador de señales"""
        self.is_running = False
        self.logger.info("Generador de señales detenido")
        
        # Enviar resumen final
        if self.telegram and self.telegram.is_active:
            self.telegram.send_alert(
                'info',
                f'Generador detenido\nSeñales generadas: {self.signals_generated}\nTrades ejecutados: {self.trades_executed}\nPosiciones corregidas: {self.positions_corrected}'
            )
        
        # Desconectar MT5 si estaba conectado
        if self.mt5_connection:
            self.mt5_connection.disconnect()
            
    def get_status(self):
        """Obtiene el estado actual"""
        return {
            'running': self.is_running,
            'auto_execute': self.auto_execute,
            'signals_generated': self.signals_generated,
            'trades_executed': self.trades_executed,
            'positions_corrected': self.positions_corrected,
            'last_signals': self.last_signals,
            'symbols': self.symbols,
            'mt5_connected': self.mt5_connected,
            'mt5_connection_active': self.mt5_connection is not None and self.mt5_connection.connected,
            'telegram_active': self.telegram.is_active if self.telegram else False,
            'positions_summary': self.get_positions_summary() if self.mt5_connection else "MT5 no conectado",
            'ai_hybrid_available': self.ai_hybrid_available,
            'total_strategies': len(self.strategies),
            'strategies_list': list(self.strategies.keys())
        }

def main():
    import argparse
    
    print("""
============================================================
       GENERADOR DE SENALES CON IA - ALGO TRADER V3        
============================================================
    """)
    
    # Configurar argumentos
    parser = argparse.ArgumentParser(description='Generador de Señales con IA')
    parser.add_argument('--auto-execute', action='store_true', 
                       help='Activar ejecución automática de trades en MT5')
    parser.add_argument('--symbols', nargs='+', 
                       default=['XAUUSD', 'EURUSD', 'GBPUSD', 'BTCUSD'],
                       help='Símbolos a analizar')
    
    args = parser.parse_args()
    
    # Mostrar configuración
    print(f"\n[INFO] CONFIGURACIÓN:")
    print(f"  • Auto-ejecución: {'[OK] ACTIVADA' if args.auto_execute else '[ERROR] DESACTIVADA'}")
    print(f"  • Símbolos: {', '.join(args.symbols)}")
    
    if args.auto_execute:
        print(f"\n[WARNING]  MODO AUTO-EJECUCIÓN ACTIVADO")
        print(f"     Las señales se ejecutarán automáticamente en MT5")
        response = input(f"\n¿Continuar? (yes/no): ")
        if response.lower() != 'yes':
            print("Operación cancelada")
            return
    
    # Crear generador
    generator = SignalGenerator(symbols=args.symbols, auto_execute=args.auto_execute)
    
    # Mostrar estado
    status = generator.get_status()
    print(f"\n🔧 ESTADO DEL SISTEMA:")
    print(f"  • MT5 Datos: {'[OK] Conectado' if status['mt5_connected'] else '[WARNING]  Modo simulación'}")
    print(f"  • MT5 Trading: {'[OK] Conectado' if status['mt5_connection_active'] else '[ERROR] Desconectado'}")
    print(f"  • Telegram: {'[OK] Activo' if status['telegram_active'] else '[ERROR] Inactivo'}")
    print(f"  • Símbolos: {', '.join(status['symbols'])}")
    total_strategies = len(generator.strategies)
    ai_status = "CON IA (Ollama+TwelveData)" if generator.ai_hybrid_available else "SIN IA"
    print(f"  • Estrategias: {total_strategies} activas {ai_status}")
    print(f"  • Auto-ejecución: {'[OK] ACTIVADA' if status['auto_execute'] else '[ERROR] DESACTIVADA'}")
    print(f"  • Monitor SL/TP: {'[OK] ACTIVADO' if status['auto_execute'] and status['mt5_connection_active'] else '[ERROR] DESACTIVADO'}")
    
    # Mostrar posiciones si están conectadas
    if status['mt5_connection_active'] and status['positions_summary'] != "MT5 no conectado":
        print(f"\n[INFO] POSICIONES ACTUALES:")
        print(f"  {status['positions_summary']}")
    
    print(f"\n🚀 Iniciando análisis continuo...")
    print(f"   Presiona Ctrl+C para detener\n")
    
    try:
        generator.start()
    except KeyboardInterrupt:
        generator.stop()
        print("\nGenerador detenido correctamente")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
