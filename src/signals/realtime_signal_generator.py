#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GENERADOR DE SEÑALES CON IA Y DATOS REALES - ALGO TRADER V3
============================================================
Sistema avanzado con datos reales de TwelveData API
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

# Configurar encoding UTF-8
if sys.platform == 'win32':
    import locale
    locale.setlocale(locale.LC_ALL, '')

# Añadir path del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Importar clientes
try:
    from src.notifiers.telegram_notifier import TelegramNotifier
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    print("Advertencia: Telegram no disponible")

try:
    from src.data.twelvedata_client import TwelveDataClient
    TWELVEDATA_AVAILABLE = True
except ImportError:
    TWELVEDATA_AVAILABLE = False
    print("Advertencia: TwelveData client no disponible")

try:
    import MetaTrader5 as mt5
    MT5_AVAILABLE = True
except ImportError:
    MT5_AVAILABLE = False

class RealTimeSignalGenerator:
    def __init__(self, symbols=None):
        """
        Inicializa el generador de señales con datos reales
        """
        # Símbolos con formato correcto para TwelveData
        self.symbols = symbols or ['EUR/USD', 'GBP/USD', 'XAU/USD', 'BTC/USD']
        self.symbol_map = {
            'EUR/USD': 'EURUSD',
            'GBP/USD': 'GBPUSD', 
            'XAU/USD': 'XAUUSD',
            'BTC/USD': 'BTCUSD'
        }
        
        self.is_running = False
        self.signals_generated = 0
        self.last_signals = {}
        self.signal_history = []
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ],
            encoding='utf-8'
        )
        self.logger = logging.getLogger(__name__)
        
        # Inicializar TwelveData
        self.twelvedata = None
        if TWELVEDATA_AVAILABLE:
            try:
                self.twelvedata = TwelveDataClient()
                self.logger.info("✅ TwelveData API conectada")
            except Exception as e:
                self.logger.error(f"Error inicializando TwelveData: {e}")
                
        # Inicializar Telegram
        self.telegram = None
        if TELEGRAM_AVAILABLE:
            try:
                self.telegram = TelegramNotifier()
                self.logger.info("✅ Telegram notifier inicializado")
            except Exception as e:
                self.logger.error(f"Error inicializando Telegram: {e}")
                
        # Estrategias disponibles
        self.strategies = {
            'ai_analysis': self.ai_analysis_strategy,
            'momentum': self.momentum_strategy,
            'mean_reversion': self.mean_reversion_strategy,
            'breakout': self.breakout_strategy,
            'volume_spike': self.volume_spike_strategy,
            'multi_indicator': self.multi_indicator_strategy
        }
        
        self.logger.info("🚀 Generador de señales con datos reales inicializado")
        
    def get_real_market_data(self, symbol):
        """Obtiene datos reales del mercado desde TwelveData"""
        if not self.twelvedata:
            self.logger.error("TwelveData no disponible")
            return None
            
        try:
            # Obtener análisis completo
            analysis = self.twelvedata.get_complete_analysis(symbol)
            
            if analysis and analysis['data'] is not None:
                df = analysis['data']
                
                # Añadir indicadores del análisis
                if analysis['indicators']:
                    last_idx = len(df) - 1
                    for key, value in analysis['indicators'].items():
                        if value is not None:
                            df.loc[last_idx, key] = value
                            
                # Añadir precio actual si está disponible
                if analysis['price']:
                    df.loc[last_idx, 'current_price'] = analysis['price']
                    
                # Añadir sentimiento
                df['sentiment'] = analysis['sentiment']
                
                self.logger.info(f"📊 Datos reales obtenidos para {symbol}: {len(df)} barras")
                return df
            else:
                self.logger.warning(f"No se pudieron obtener datos para {symbol}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error obteniendo datos reales de {symbol}: {e}")
            return None
            
    def ai_analysis_strategy(self, df, symbol, indicators):
        """Estrategia basada en IA con análisis profundo"""
        signals = []
        
        try:
            if df is None or len(df) < 10:
                return signals
                
            # Obtener último precio y datos
            last_row = df.iloc[-1]
            current_price = last_row['close']
            
            # Análisis de tendencia con IA
            trend_score = 0
            
            # 1. Análisis de precio
            price_change = (df['close'].iloc[-1] - df['close'].iloc[-5]) / df['close'].iloc[-5] * 100
            if price_change > 0.2:
                trend_score += 2
            elif price_change < -0.2:
                trend_score -= 2
                
            # 2. Análisis de volumen
            if 'volume' in df.columns:
                vol_avg = df['volume'].mean()
                vol_current = df['volume'].iloc[-1]
                if vol_current > vol_avg * 1.5:
                    trend_score += 1 if price_change > 0 else -1
                    
            # 3. Análisis de indicadores
            if indicators:
                # RSI
                rsi = indicators.get('rsi', 50)
                if rsi < 30:
                    trend_score += 2  # Sobreventa
                elif rsi > 70:
                    trend_score -= 2  # Sobrecompra
                    
                # MACD
                macd = indicators.get('macd', 0)
                macd_signal = indicators.get('macd_signal', 0)
                if macd > macd_signal:
                    trend_score += 1
                else:
                    trend_score -= 1
                    
                # Bollinger Bands
                bb_upper = indicators.get('bb_upper', current_price)
                bb_lower = indicators.get('bb_lower', current_price)
                bb_position = (current_price - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else 0.5
                
                if bb_position < 0.2:
                    trend_score += 1
                elif bb_position > 0.8:
                    trend_score -= 1
                    
            # 4. Análisis de sentimiento
            sentiment = df['sentiment'].iloc[-1] if 'sentiment' in df.columns else 'neutral'
            if sentiment == 'bullish':
                trend_score += 1
            elif sentiment == 'bearish':
                trend_score -= 1
                
            # Generar señal basada en puntuación
            if trend_score >= 4:
                signal = {
                    'symbol': self.symbol_map.get(symbol, symbol),
                    'type': 'BUY',
                    'price': current_price,
                    'strength': min(0.95, 0.60 + (trend_score * 0.05)),
                    'strategy': 'AI Analysis',
                    'reason': f'Análisis IA: Puntuación alcista {trend_score}/10',
                    'rsi': indicators.get('rsi', 'N/A'),
                    'macd': indicators.get('macd', 'N/A')
                }
                signals.append(signal)
                
            elif trend_score <= -4:
                signal = {
                    'symbol': self.symbol_map.get(symbol, symbol),
                    'type': 'SELL',
                    'price': current_price,
                    'strength': min(0.95, 0.60 + (abs(trend_score) * 0.05)),
                    'strategy': 'AI Analysis',
                    'reason': f'Análisis IA: Puntuación bajista {trend_score}/10',
                    'rsi': indicators.get('rsi', 'N/A'),
                    'macd': indicators.get('macd', 'N/A')
                }
                signals.append(signal)
                
        except Exception as e:
            self.logger.error(f"Error en ai_analysis_strategy: {e}")
            
        return signals
        
    def momentum_strategy(self, df, symbol, indicators):
        """Estrategia de momentum con datos reales"""
        signals = []
        
        try:
            if df is None or len(df) < 20:
                return signals
                
            # Calcular momentum
            momentum = df['close'].pct_change(10).iloc[-1] * 100
            
            # RSI desde indicadores
            rsi = indicators.get('rsi', 50)
            
            # Volumen
            volume_ratio = 1.0
            if 'volume' in df.columns:
                vol_avg = df['volume'].rolling(20).mean().iloc[-1]
                vol_current = df['volume'].iloc[-1]
                volume_ratio = vol_current / vol_avg if vol_avg > 0 else 1.0
                
            current_price = df['close'].iloc[-1]
            
            # Señal de compra
            if momentum > 0.5 and rsi < 65 and volume_ratio > 1.2:
                signal = {
                    'symbol': self.symbol_map.get(symbol, symbol),
                    'type': 'BUY',
                    'price': current_price,
                    'strength': min(0.85, 0.60 + (momentum * 0.05)),
                    'strategy': 'Momentum',
                    'reason': f'Momentum alcista: {momentum:.2f}% con volumen {volume_ratio:.1f}x'
                }
                signals.append(signal)
                
            # Señal de venta
            elif momentum < -0.5 and rsi > 35 and volume_ratio > 1.2:
                signal = {
                    'symbol': self.symbol_map.get(symbol, symbol),
                    'type': 'SELL',
                    'price': current_price,
                    'strength': min(0.85, 0.60 + (abs(momentum) * 0.05)),
                    'strategy': 'Momentum',
                    'reason': f'Momentum bajista: {momentum:.2f}% con volumen {volume_ratio:.1f}x'
                }
                signals.append(signal)
                
        except Exception as e:
            self.logger.error(f"Error en momentum_strategy: {e}")
            
        return signals
        
    def mean_reversion_strategy(self, df, symbol, indicators):
        """Estrategia de reversión a la media con datos reales"""
        signals = []
        
        try:
            if df is None or len(df) < 5:
                return signals
                
            current_price = df['close'].iloc[-1]
            rsi = indicators.get('rsi', 50)
            
            # Bollinger Bands
            bb_upper = indicators.get('bb_upper', current_price)
            bb_lower = indicators.get('bb_lower', current_price)
            bb_middle = indicators.get('bb_middle', current_price)
            
            # Posición en Bollinger Bands
            bb_range = bb_upper - bb_lower
            if bb_range > 0:
                bb_position = (current_price - bb_lower) / bb_range
            else:
                bb_position = 0.5
                
            # Señal de compra (sobreventa)
            if bb_position < 0.1 and rsi < 30:
                signal = {
                    'symbol': self.symbol_map.get(symbol, symbol),
                    'type': 'BUY',
                    'price': current_price,
                    'strength': 0.80,
                    'strategy': 'Mean Reversion',
                    'reason': f'Sobreventa: RSI {rsi:.1f}, cerca de banda inferior'
                }
                signals.append(signal)
                
            # Señal de venta (sobrecompra)
            elif bb_position > 0.9 and rsi > 70:
                signal = {
                    'symbol': self.symbol_map.get(symbol, symbol),
                    'type': 'SELL',
                    'price': current_price,
                    'strength': 0.80,
                    'strategy': 'Mean Reversion',
                    'reason': f'Sobrecompra: RSI {rsi:.1f}, cerca de banda superior'
                }
                signals.append(signal)
                
        except Exception as e:
            self.logger.error(f"Error en mean_reversion_strategy: {e}")
            
        return signals
        
    def breakout_strategy(self, df, symbol, indicators):
        """Estrategia de ruptura con datos reales"""
        signals = []
        
        try:
            if df is None or len(df) < 20:
                return signals
                
            # Calcular niveles de soporte y resistencia
            recent_high = df['high'].rolling(window=20).max().iloc[-1]
            recent_low = df['low'].rolling(window=20).min().iloc[-1]
            prev_high = df['high'].rolling(window=20).max().iloc[-2]
            prev_low = df['low'].rolling(window=20).min().iloc[-2]
            
            current_price = df['close'].iloc[-1]
            
            # Volumen
            volume_spike = 1.0
            if 'volume' in df.columns:
                vol_avg = df['volume'].rolling(20).mean().iloc[-1]
                vol_current = df['volume'].iloc[-1]
                volume_spike = vol_current / vol_avg if vol_avg > 0 else 1.0
                
            # Ruptura alcista
            if current_price > prev_high and volume_spike > 1.5:
                signal = {
                    'symbol': self.symbol_map.get(symbol, symbol),
                    'type': 'BUY',
                    'price': current_price,
                    'strength': min(0.90, 0.70 + (volume_spike * 0.1)),
                    'strategy': 'Breakout',
                    'reason': f'Ruptura alcista de {prev_high:.5f} con volumen {volume_spike:.1f}x'
                }
                signals.append(signal)
                
            # Ruptura bajista
            elif current_price < prev_low and volume_spike > 1.5:
                signal = {
                    'symbol': self.symbol_map.get(symbol, symbol),
                    'type': 'SELL',
                    'price': current_price,
                    'strength': min(0.90, 0.70 + (volume_spike * 0.1)),
                    'strategy': 'Breakout',
                    'reason': f'Ruptura bajista de {prev_low:.5f} con volumen {volume_spike:.1f}x'
                }
                signals.append(signal)
                
        except Exception as e:
            self.logger.error(f"Error en breakout_strategy: {e}")
            
        return signals
        
    def volume_spike_strategy(self, df, symbol, indicators):
        """Estrategia basada en picos de volumen"""
        signals = []
        
        try:
            if df is None or len(df) < 20 or 'volume' not in df.columns:
                return signals
                
            # Análisis de volumen
            vol_avg = df['volume'].rolling(20).mean().iloc[-1]
            vol_current = df['volume'].iloc[-1]
            volume_ratio = vol_current / vol_avg if vol_avg > 0 else 1.0
            
            current_price = df['close'].iloc[-1]
            price_change = (df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2] * 100
            
            # Pico de volumen significativo
            if volume_ratio > 2.5:
                if price_change > 0.1:
                    signal = {
                        'symbol': self.symbol_map.get(symbol, symbol),
                        'type': 'BUY',
                        'price': current_price,
                        'strength': min(0.90, 0.60 + (volume_ratio * 0.1)),
                        'strategy': 'Volume Spike',
                        'reason': f'Pico de volumen {volume_ratio:.1f}x con precio alcista'
                    }
                    signals.append(signal)
                    
                elif price_change < -0.1:
                    signal = {
                        'symbol': self.symbol_map.get(symbol, symbol),
                        'type': 'SELL',
                        'price': current_price,
                        'strength': min(0.90, 0.60 + (volume_ratio * 0.1)),
                        'strategy': 'Volume Spike',
                        'reason': f'Pico de volumen {volume_ratio:.1f}x con precio bajista'
                    }
                    signals.append(signal)
                    
        except Exception as e:
            self.logger.error(f"Error en volume_spike_strategy: {e}")
            
        return signals
        
    def multi_indicator_strategy(self, df, symbol, indicators):
        """Estrategia con múltiples indicadores"""
        signals = []
        
        try:
            if df is None or len(df) < 5 or not indicators:
                return signals
                
            current_price = df['close'].iloc[-1]
            
            # Puntuación de indicadores
            bull_score = 0
            bear_score = 0
            
            # RSI
            rsi = indicators.get('rsi', 50)
            if rsi < 40:
                bull_score += 1
            elif rsi > 60:
                bear_score += 1
                
            # MACD
            macd = indicators.get('macd', 0)
            macd_signal = indicators.get('macd_signal', 0)
            if macd > macd_signal:
                bull_score += 1
            else:
                bear_score += 1
                
            # Stochastic
            stoch_k = indicators.get('stoch_k', 50)
            stoch_d = indicators.get('stoch_d', 50)
            if stoch_k < 20 and stoch_k > stoch_d:
                bull_score += 1
            elif stoch_k > 80 and stoch_k < stoch_d:
                bear_score += 1
                
            # Moving Averages
            sma_20 = indicators.get('sma_20', current_price)
            ema_12 = indicators.get('ema_12', current_price)
            if current_price > sma_20 and current_price > ema_12:
                bull_score += 1
            elif current_price < sma_20 and current_price < ema_12:
                bear_score += 1
                
            # Generar señal si hay consenso
            if bull_score >= 3:
                signal = {
                    'symbol': self.symbol_map.get(symbol, symbol),
                    'type': 'BUY',
                    'price': current_price,
                    'strength': min(0.90, 0.60 + (bull_score * 0.08)),
                    'strategy': 'Multi-Indicator',
                    'reason': f'Confluencia alcista: {bull_score}/4 indicadores positivos'
                }
                signals.append(signal)
                
            elif bear_score >= 3:
                signal = {
                    'symbol': self.symbol_map.get(symbol, symbol),
                    'type': 'SELL',
                    'price': current_price,
                    'strength': min(0.90, 0.60 + (bear_score * 0.08)),
                    'strategy': 'Multi-Indicator',
                    'reason': f'Confluencia bajista: {bear_score}/4 indicadores negativos'
                }
                signals.append(signal)
                
        except Exception as e:
            self.logger.error(f"Error en multi_indicator_strategy: {e}")
            
        return signals
        
    def calculate_dynamic_tp_sl(self, signal, indicators):
        """Calcula TP/SL dinámicos basados en ATR y volatilidad"""
        try:
            atr = indicators.get('atr', signal['price'] * 0.002)
            
            # Ajustar multiplicadores según la fuerza de la señal
            tp_multiplier = 2.5 if signal['strength'] > 0.8 else 2.0
            sl_multiplier = 1.0
            
            if signal['type'] == 'BUY':
                signal['tp'] = signal['price'] + (atr * tp_multiplier)
                signal['sl'] = signal['price'] - (atr * sl_multiplier)
            else:
                signal['tp'] = signal['price'] - (atr * tp_multiplier)
                signal['sl'] = signal['price'] + (atr * sl_multiplier)
                
            # Añadir ratio Risk/Reward
            risk = abs(signal['price'] - signal['sl'])
            reward = abs(signal['tp'] - signal['price'])
            signal['rr_ratio'] = reward / risk if risk > 0 else 2.0
            
        except Exception as e:
            self.logger.error(f"Error calculando TP/SL: {e}")
            # Valores por defecto
            if signal['type'] == 'BUY':
                signal['tp'] = signal['price'] * 1.003
                signal['sl'] = signal['price'] * 0.998
            else:
                signal['tp'] = signal['price'] * 0.997
                signal['sl'] = signal['price'] * 1.002
            signal['rr_ratio'] = 2.0
            
        return signal
        
    def analyze_symbol_realtime(self, symbol):
        """Analiza un símbolo con datos en tiempo real"""
        all_signals = []
        
        try:
            self.logger.info(f"📊 Analizando {symbol} con datos reales...")
            
            # Obtener datos reales
            df = self.get_real_market_data(symbol)
            
            if df is None or len(df) < 10:
                self.logger.warning(f"Datos insuficientes para {symbol}")
                return all_signals
                
            # Obtener indicadores técnicos
            indicators = {}
            if self.twelvedata:
                indicators = self.twelvedata.get_technical_indicators(symbol)
                
            # Aplicar todas las estrategias
            for strategy_name, strategy_func in self.strategies.items():
                try:
                    signals = strategy_func(df, symbol, indicators)
                    for signal in signals:
                        # Añadir TP/SL dinámicos
                        signal = self.calculate_dynamic_tp_sl(signal, indicators)
                        signal['timeframe'] = '5min'
                        signal['timestamp'] = datetime.now()
                        signal['data_source'] = 'TwelveData API'
                        all_signals.append(signal)
                        
                except Exception as e:
                    self.logger.error(f"Error en {strategy_name}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error analizando {symbol}: {e}")
            
        return all_signals
        
    def filter_best_signals(self, signals):
        """Filtra y selecciona las mejores señales"""
        if not signals:
            return []
            
        # Agrupar por símbolo
        symbol_signals = {}
        for signal in signals:
            symbol = signal['symbol']
            if symbol not in symbol_signals:
                symbol_signals[symbol] = []
            symbol_signals[symbol].append(signal)
            
        # Seleccionar mejor señal por símbolo
        best_signals = []
        for symbol, symbol_list in symbol_signals.items():
            # Ordenar por fuerza y RR ratio
            sorted_signals = sorted(
                symbol_list, 
                key=lambda x: (x['strength'], x.get('rr_ratio', 2.0)), 
                reverse=True
            )
            
            # Tomar la mejor señal si supera el umbral
            if sorted_signals[0]['strength'] >= 0.70:
                best_signals.append(sorted_signals[0])
                
        return best_signals
        
    def send_signal_notifications(self, signals):
        """Envía señales por Telegram"""
        if self.telegram and self.telegram.is_active:
            for signal in signals:
                try:
                    # Enriquecer señal con información adicional
                    enriched_signal = signal.copy()
                    enriched_signal['data_source'] = 'TwelveData API (Datos Reales)'
                    
                    self.telegram.send_signal(enriched_signal)
                    self.logger.info(f"📤 Señal enviada: {signal['symbol']} {signal['type']} @ {signal['price']:.5f}")
                    
                except Exception as e:
                    self.logger.error(f"Error enviando señal: {e}")
                    
    def run_analysis_cycle(self):
        """Ejecuta un ciclo de análisis con datos reales"""
        self.logger.info(f"🔄 Iniciando análisis con datos reales de {len(self.symbols)} símbolos...")
        
        all_signals = []
        
        for symbol in self.symbols:
            try:
                # Pequeña pausa para no sobrecargar la API
                time.sleep(1)
                
                # Analizar símbolo
                signals = self.analyze_symbol_realtime(symbol)
                all_signals.extend(signals)
                
            except Exception as e:
                self.logger.error(f"Error analizando {symbol}: {e}")
                
        # Filtrar mejores señales
        best_signals = self.filter_best_signals(all_signals)
        
        if best_signals:
            self.logger.info(f"✅ {len(best_signals)} señales de alta calidad generadas")
            
            # Enviar notificaciones
            self.send_signal_notifications(best_signals)
            
            # Guardar en historial
            for signal in best_signals:
                self.signal_history.append(signal)
                self.last_signals[signal['symbol']] = signal
                self.signals_generated += 1
        else:
            self.logger.info("📊 No hay señales de alta confianza en este ciclo")
            
        return best_signals
        
    def start(self):
        """Inicia el generador de señales con datos reales"""
        self.is_running = True
        self.logger.info("🚀 Generador de señales con DATOS REALES iniciado")
        
        # Enviar notificación de inicio
        if self.telegram and self.telegram.is_active:
            self.telegram.send_alert(
                'success',
                f'🎯 Sistema iniciado con DATOS REALES\n\n'
                f'📊 Símbolos: {", ".join(self.symbols)}\n'
                f'🤖 Estrategias: 6 activas\n'
                f'📡 Fuente: TwelveData API\n'
                f'⏰ Análisis cada 2 minutos',
                critical=True
            )
            
        cycle_count = 0
        while self.is_running:
            try:
                cycle_count += 1
                self.logger.info(f"\n{'='*60}")
                self.logger.info(f"📈 CICLO #{cycle_count} - ANÁLISIS CON DATOS REALES")
                self.logger.info(f"{'='*60}")
                
                # Ejecutar análisis
                signals = self.run_analysis_cycle()
                
                # Enviar resumen cada 5 ciclos
                if cycle_count % 5 == 0 and self.telegram and self.telegram.is_active:
                    summary = f"""
📊 <b>RESUMEN DE ACTIVIDAD</b>

🔄 Ciclos completados: {cycle_count}
📈 Señales generadas: {self.signals_generated}
📡 Fuente de datos: TwelveData API
✅ Sistema funcionando correctamente

<i>Análisis con datos reales del mercado</i>
"""
                    self.telegram.send_message(summary, parse_mode='HTML')
                    
                # Esperar 2 minutos antes del próximo ciclo
                self.logger.info(f"⏳ Esperando 2 minutos hasta el próximo análisis...")
                time.sleep(120)  # 2 minutos entre análisis
                
            except KeyboardInterrupt:
                self.logger.info("Deteniendo generador...")
                break
            except Exception as e:
                self.logger.error(f"Error en ciclo: {e}")
                time.sleep(30)
                
    def stop(self):
        """Detiene el generador de señales"""
        self.is_running = False
        self.logger.info("Generador de señales detenido")
        
        if self.telegram and self.telegram.is_active:
            self.telegram.send_alert(
                'warning',
                f'Sistema detenido\nSeñales generadas: {self.signals_generated}'
            )

def main():
    print("""
╔════════════════════════════════════════════════════════════╗
║    GENERADOR DE SEÑALES CON DATOS REALES - ALGO TRADER V3║
║                   Powered by TwelveData API               ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    # Crear generador
    generator = RealTimeSignalGenerator()
    
    print("\n📊 Sistema configurado:")
    print(f"  • Fuente de datos: TwelveData API (REAL)")
    print(f"  • Símbolos: {', '.join(generator.symbols)}")
    print(f"  • Estrategias: 6 con IA")
    print(f"  • Telegram: {'✅ Activo' if generator.telegram else '❌ Inactivo'}")
    print(f"  • Análisis cada: 2 minutos")
    
    print("\n🚀 Iniciando análisis con datos reales...")
    print("Presiona Ctrl+C para detener\n")
    
    try:
        generator.start()
    except KeyboardInterrupt:
        generator.stop()
        print("\n✅ Generador detenido correctamente")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
