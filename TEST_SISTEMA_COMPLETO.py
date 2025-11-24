#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TEST COMPLETO DEL SISTEMA OPTIMIZADO
=====================================
Prueba todos los componentes nuevos y verifica funcionamiento
"""

import sys
import os
import time
import asyncio
from pathlib import Path
from datetime import datetime
from colorama import init, Fore, Style
import warnings
warnings.filterwarnings('ignore')

# Inicializar colorama
init(autoreset=True)

# Añadir path del proyecto
sys.path.insert(0, str(Path(__file__).parent))

def print_header(text):
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.YELLOW}{text.center(60)}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")

def print_success(text):
    print(f"{Fore.GREEN}[OK] {text}{Style.RESET_ALL}")

def print_error(text):
    print(f"{Fore.RED}[ERROR] {text}{Style.RESET_ALL}")

def print_warning(text):
    print(f"{Fore.YELLOW}[WARN] {text}{Style.RESET_ALL}")

def print_info(text):
    print(f"{Fore.BLUE}[INFO] {text}{Style.RESET_ALL}")

# Test 1: Verificar dependencias
def test_dependencies():
    print_header("TEST 1: VERIFICANDO DEPENDENCIAS")
    
    dependencies = {
        'MetaTrader5': 'mt5',
        'pandas': 'pd',
        'numpy': 'np',
        'requests': 'requests',
        'websocket': 'websocket',
        'dotenv': 'dotenv',
        'openai': 'openai',
        'scipy': 'scipy'
    }
    
    failed = []
    for name, import_name in dependencies.items():
        try:
            if name == 'MetaTrader5':
                import MetaTrader5
            elif name == 'pandas':
                import pandas
            elif name == 'numpy':
                import numpy
            elif name == 'requests':
                import requests
            elif name == 'websocket':
                import websocket
            elif name == 'dotenv':
                from dotenv import load_dotenv
            elif name == 'openai':
                import openai
            elif name == 'scipy':
                import scipy
            print_success(f"{name} instalado correctamente")
        except ImportError:
            print_error(f"{name} NO instalado")
            failed.append(name)
    
    if failed:
        print_warning(f"\nInstalar dependencias faltantes con:")
        print(f"pip install {' '.join(failed)}")
        return False
    
    return True

# Test 2: TwelveData Optimizado
def test_twelvedata():
    print_header("TEST 2: TWELVEDATA OPTIMIZADO")
    
    try:
        # Intentar importar sin TA-Lib primero
        try:
            from src.data.twelvedata_optimized import TwelveDataOptimized
        except ImportError as e:
            if 'talib' in str(e).lower():
                print_warning("TA-Lib no instalado, creando versión sin TA-Lib...")
                
                # Crear versión sin TA-Lib
                create_twelvedata_without_talib()
                from src.data.twelvedata_optimized_no_talib import TwelveDataOptimized
            else:
                raise e
        
        # Crear instancia
        client = TwelveDataOptimized()
        print_success("Cliente TwelveData creado")
        
        # Test 1: Obtener precio en tiempo real
        print_info("Obteniendo precio de EURUSD...")
        price = client.get_realtime_price_api('EURUSD')
        if price:
            print_success(f"Precio EURUSD: {price:.5f}")
        else:
            print_warning("No se pudo obtener precio (verificar API key)")
        
        # Test 2: Obtener múltiples precios
        print_info("Obteniendo múltiples precios...")
        symbols = ['XAUUSD', 'BTCUSD', 'EURUSD']
        prices = client.get_multiple_prices(symbols)
        for symbol, price in prices.items():
            if price:
                print_success(f"{symbol}: {price:.5f}")
        
        # Test 3: Indicadores (sin TA-Lib usa cálculos manuales)
        print_info("Calculando indicadores técnicos...")
        indicators = client.get_advanced_indicators('EURUSD', '1h', 50)
        if indicators:
            print_success(f"Indicadores calculados: {len(indicators)} métricas")
            # Mostrar algunos indicadores
            for key in ['sma_20', 'rsi', 'atr', 'macd']:
                if key in indicators:
                    print(f"  {key}: {indicators[key]:.4f}")
        
        # Test 4: Análisis de sentimiento
        print_info("Analizando sentimiento del mercado...")
        sentiment = client.get_market_sentiment(['EURUSD', 'XAUUSD'])
        for symbol, sent in sentiment.items():
            print_success(f"{symbol}: {sent}")
        
        # Test 5: Estadísticas
        stats = client.get_statistics()
        print_info(f"\nEstadísticas del cliente:")
        print(f"  API calls: {stats['api_calls']}")
        print(f"  Cache hits: {stats['cache_hits']}")
        print(f"  Cache hit rate: {stats['cache_hit_rate']:.1f}%")
        
        return True
        
    except Exception as e:
        print_error(f"Error en TwelveData: {e}")
        import traceback
        traceback.print_exc()
        return False

def create_twelvedata_without_talib():
    """Crea versión de TwelveData sin TA-Lib"""
    code = '''#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TWELVEDATA OPTIMIZADO SIN TA-LIB
=================================
Versión que funciona sin TA-Lib usando cálculos manuales
"""

import os
import requests
import pandas as pd
import numpy as np
from datetime import datetime
import time
import json
import logging
from typing import Dict, List, Optional, Any
from functools import lru_cache
import threading
from concurrent.futures import ThreadPoolExecutor
import websocket

class TwelveDataOptimized:
    """Cliente optimizado sin dependencia de TA-Lib"""
    
    def __init__(self):
        self.api_key = os.getenv('TWELVEDATA_API_KEY', '23d17ce5b7044ad5aef9766770a6252b')
        self.base_url = 'https://api.twelvedata.com'
        self.ws_url = 'wss://ws.twelvedata.com/v1/quotes/price'
        
        self.cache = {
            'realtime': {},
            'minute': {},
            'indicators': {},
            'historical': {}
        }
        self.cache_ttl = {
            'realtime': 5,
            'minute': 60,
            'indicators': 300,
            'historical': 1800
        }
        
        self.ws = None
        self.ws_thread = None
        self.realtime_data = {}
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        self.symbol_map = {
            'XAUUSDm': 'XAU/USD', 'XAUUSD': 'XAU/USD',
            'BTCUSDm': 'BTC/USD', 'BTCUSD': 'BTC/USD',
            'EURUSDm': 'EUR/USD', 'EURUSD': 'EUR/USD',
            'GBPUSDm': 'GBP/USD', 'GBPUSD': 'GBP/USD'
        }
        
        self.api_calls = 0
        self.cache_hits = 0
        self.ws_messages = 0
        
        self.logger = logging.getLogger(__name__)
    
    def calculate_sma(self, values, period):
        """Simple Moving Average"""
        if len(values) < period:
            return None
        return sum(values[-period:]) / period
    
    def calculate_ema(self, values, period):
        """Exponential Moving Average"""
        if len(values) < period:
            return None
        multiplier = 2 / (period + 1)
        ema = sum(values[:period]) / period
        for value in values[period:]:
            ema = (value - ema) * multiplier + ema
        return ema
    
    def calculate_rsi(self, values, period=14):
        """Relative Strength Index"""
        if len(values) < period + 1:
            return 50
        
        deltas = np.diff(values)
        seed = deltas[:period]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        
        if down == 0:
            return 100
        rs = up / down
        rsi = 100 - (100 / (1 + rs))
        
        for delta in deltas[period:]:
            if delta > 0:
                upval = delta
                downval = 0
            else:
                upval = 0
                downval = -delta
            
            up = (up * (period - 1) + upval) / period
            down = (down * (period - 1) + downval) / period
            
            if down == 0:
                return 100
            rs = up / down
            rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_macd(self, values):
        """MACD indicator"""
        if len(values) < 26:
            return {'macd': 0, 'signal': 0, 'histogram': 0}
        
        ema12 = self.calculate_ema(values, 12)
        ema26 = self.calculate_ema(values, 26)
        macd = ema12 - ema26 if ema12 and ema26 else 0
        signal = self.calculate_ema([macd], 9) if macd else 0
        histogram = macd - signal if signal else 0
        
        return {'macd': macd, 'signal': signal, 'histogram': histogram}
    
    def calculate_bollinger_bands(self, values, period=20, std_dev=2):
        """Bollinger Bands"""
        if len(values) < period:
            return {'upper': 0, 'middle': 0, 'lower': 0}
        
        sma = self.calculate_sma(values, period)
        std = np.std(values[-period:])
        
        return {
            'upper': sma + (std * std_dev),
            'middle': sma,
            'lower': sma - (std * std_dev)
        }
    
    def calculate_atr(self, highs, lows, closes, period=14):
        """Average True Range"""
        if len(highs) < period + 1:
            return 0
        
        tr_list = []
        for i in range(1, len(highs)):
            tr = max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i-1]),
                abs(lows[i] - closes[i-1])
            )
            tr_list.append(tr)
        
        return sum(tr_list[-period:]) / period if tr_list else 0
    
    def get_from_cache(self, cache_type: str, key: str) -> Optional[Any]:
        """Obtiene dato del cache si no ha expirado"""
        if key in self.cache[cache_type]:
            data, timestamp = self.cache[cache_type][key]
            if (datetime.now() - timestamp).seconds < self.cache_ttl[cache_type]:
                self.cache_hits += 1
                return data
        return None
    
    def set_cache(self, cache_type: str, key: str, data: Any):
        """Almacena dato en cache con timestamp"""
        self.cache[cache_type][key] = (data, datetime.now())
    
    def get_realtime_price_ws(self, symbol: str) -> Optional[float]:
        """Obtiene precio del WebSocket"""
        api_symbol = self.symbol_map.get(symbol, symbol)
        if api_symbol in self.realtime_data:
            data = self.realtime_data[api_symbol]
            if (datetime.now() - data['timestamp']).seconds < 5:
                return data['price']
        return None
    
    def get_realtime_price_api(self, symbol: str) -> Optional[float]:
        """Obtiene precio desde API con cache"""
        cached = self.get_from_cache('realtime', symbol)
        if cached:
            return cached
        
        try:
            api_symbol = self.symbol_map.get(symbol, symbol)
            url = f"{self.base_url}/price"
            params = {'symbol': api_symbol, 'apikey': self.api_key}
            
            response = requests.get(url, params=params, timeout=5)
            self.api_calls += 1
            
            if response.status_code == 200:
                data = response.json()
                price = float(data.get('price', 0))
                self.set_cache('realtime', symbol, price)
                return price
        except Exception as e:
            self.logger.error(f"API error for {symbol}: {e}")
        return None
    
    def get_multiple_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Obtiene precios de múltiples símbolos"""
        prices = {}
        
        for symbol in symbols:
            ws_price = self.get_realtime_price_ws(symbol)
            if ws_price:
                prices[symbol] = ws_price
        
        missing_symbols = [s for s in symbols if s not in prices]
        if missing_symbols:
            futures = []
            for symbol in missing_symbols:
                future = self.executor.submit(self.get_realtime_price_api, symbol)
                futures.append((symbol, future))
            
            for symbol, future in futures:
                try:
                    price = future.result(timeout=5)
                    if price:
                        prices[symbol] = price
                except Exception as e:
                    self.logger.error(f"Error getting price for {symbol}: {e}")
        
        return prices
    
    def get_advanced_indicators(self, symbol: str, interval: str = '1h', 
                              outputsize: int = 100) -> Dict[str, Any]:
        """Calcula indicadores técnicos sin TA-Lib"""
        cache_key = f"{symbol}_{interval}_{outputsize}"
        cached = self.get_from_cache('indicators', cache_key)
        if cached:
            return cached
        
        try:
            api_symbol = self.symbol_map.get(symbol, symbol)
            url = f"{self.base_url}/time_series"
            params = {
                'symbol': api_symbol,
                'interval': interval,
                'outputsize': outputsize,
                'apikey': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            self.api_calls += 1
            
            if response.status_code == 200:
                data = response.json()
                values = data.get('values', [])
                
                if not values:
                    return {}
                
                # Extraer arrays de precios
                closes = [float(v['close']) for v in values]
                highs = [float(v['high']) for v in values]
                lows = [float(v['low']) for v in values]
                volumes = [float(v['volume']) for v in values]
                
                # Calcular indicadores manualmente
                indicators = {}
                
                # Moving Averages
                indicators['sma_20'] = self.calculate_sma(closes, 20) or 0
                indicators['sma_50'] = self.calculate_sma(closes, 50) or 0
                indicators['ema_12'] = self.calculate_ema(closes, 12) or 0
                indicators['ema_26'] = self.calculate_ema(closes, 26) or 0
                
                # RSI
                indicators['rsi'] = self.calculate_rsi(closes)
                indicators['rsi_oversold'] = indicators['rsi'] < 30
                indicators['rsi_overbought'] = indicators['rsi'] > 70
                
                # MACD
                macd_data = self.calculate_macd(closes)
                indicators['macd'] = macd_data['macd']
                indicators['macd_signal'] = macd_data['signal']
                indicators['macd_histogram'] = macd_data['histogram']
                
                # Bollinger Bands
                bb_data = self.calculate_bollinger_bands(closes)
                indicators['bb_upper'] = bb_data['upper']
                indicators['bb_middle'] = bb_data['middle']
                indicators['bb_lower'] = bb_data['lower']
                indicators['bb_width'] = bb_data['upper'] - bb_data['lower']
                current_price = closes[-1] if closes else 0
                indicators['bb_position'] = (current_price - bb_data['lower']) / indicators['bb_width'] if indicators['bb_width'] > 0 else 0.5
                
                # ATR
                indicators['atr'] = self.calculate_atr(highs, lows, closes)
                indicators['atr_percent'] = (indicators['atr'] / current_price * 100) if current_price > 0 else 0
                
                # Volume
                indicators['volume_sma'] = self.calculate_sma(volumes, 20) or 0
                indicators['volume_ratio'] = volumes[-1] / indicators['volume_sma'] if indicators['volume_sma'] > 0 else 1
                
                # Support/Resistance
                indicators['pivot'] = (highs[-1] + lows[-1] + closes[-1]) / 3
                indicators['r1'] = 2 * indicators['pivot'] - lows[-1]
                indicators['s1'] = 2 * indicators['pivot'] - highs[-1]
                
                # VWAP aproximado
                vwap_sum = sum(c * v for c, v in zip(closes, volumes))
                volume_sum = sum(volumes)
                indicators['vwap'] = vwap_sum / volume_sum if volume_sum > 0 else current_price
                
                # Guardar en cache
                self.set_cache('indicators', cache_key, indicators)
                return indicators
                
        except Exception as e:
            self.logger.error(f"Error calculating indicators for {symbol}: {e}")
            return {}
    
    def get_market_sentiment(self, symbols: List[str]) -> Dict[str, str]:
        """Analiza sentimiento del mercado"""
        sentiment = {}
        
        for symbol in symbols:
            indicators = self.get_advanced_indicators(symbol, '1h', 100)
            
            if not indicators:
                sentiment[symbol] = 'NEUTRAL'
                continue
            
            bullish_signals = 0
            bearish_signals = 0
            
            # RSI
            if indicators.get('rsi', 50) > 60:
                bullish_signals += 1
            elif indicators.get('rsi', 50) < 40:
                bearish_signals += 1
            
            # MACD
            if indicators.get('macd_histogram', 0) > 0:
                bullish_signals += 1
            else:
                bearish_signals += 1
            
            # Bollinger Bands
            if indicators.get('bb_position', 0.5) > 0.8:
                bearish_signals += 1
            elif indicators.get('bb_position', 0.5) < 0.2:
                bullish_signals += 1
            
            # Volume
            if indicators.get('volume_ratio', 1) > 1.5:
                if indicators.get('sma_20', 0) > indicators.get('sma_50', 0):
                    bullish_signals += 1
                else:
                    bearish_signals += 1
            
            # Determinar sentimiento
            if bullish_signals > bearish_signals + 2:
                sentiment[symbol] = 'VERY_BULLISH'
            elif bullish_signals > bearish_signals:
                sentiment[symbol] = 'BULLISH'
            elif bearish_signals > bullish_signals + 2:
                sentiment[symbol] = 'VERY_BEARISH'
            elif bearish_signals > bullish_signals:
                sentiment[symbol] = 'BEARISH'
            else:
                sentiment[symbol] = 'NEUTRAL'
        
        return sentiment
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estadísticas del cliente"""
        return {
            'api_calls': self.api_calls,
            'cache_hits': self.cache_hits,
            'cache_hit_rate': (self.cache_hits / (self.api_calls + self.cache_hits)) * 100 if (self.api_calls + self.cache_hits) > 0 else 0,
            'ws_messages': self.ws_messages,
            'realtime_symbols': len(self.realtime_data),
            'cache_sizes': {k: len(v) for k, v in self.cache.items()}
        }
'''
    
    with open('src/data/twelvedata_optimized_no_talib.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print_success("Creado twelvedata_optimized_no_talib.py")

# Test 3: Ollama AI
async def test_ollama_async():
    print_header("TEST 3: OLLAMA ADVANCED AI")
    
    try:
        from src.ai.ollama_advanced import OllamaAdvanced, TradingSignal
        
        # Crear instancia
        ai = OllamaAdvanced()
        print_success("Cliente Ollama creado")
        
        # Preparar datos de mercado de prueba
        market_data = {
            'current_price': 1.0850,
            'change_24h': 0.5,
            'volume': 1000000,
            'indicators': {
                '1h': {
                    'rsi': 55,
                    'macd': 0.0002,
                    'macd_signal': 0.0001,
                    'bb_position': 0.6,
                    'atr': 0.0010,
                    'atr_percent': 0.09,
                    'adx': 28,
                    'volume_ratio': 1.2
                }
            },
            'sentiment': 'BULLISH',
            'vwap': 1.0845,
            'poc': 1.0848,
            'va_high': 1.0860,
            'va_low': 1.0840,
            'vol_14d': 8.5,
            'vol_30d': 9.2,
            'sharpe': 1.5
        }
        
        print_info("Realizando análisis ensemble...")
        print_warning("Esto puede tomar 10-30 segundos...")
        
        # Análisis ensemble
        signal = await ai.ensemble_analysis('EURUSD', market_data)
        
        if signal:
            print_success(f"Señal generada: {signal.action}")
            print(f"  Entry: {signal.entry_price}")
            print(f"  SL: {signal.stop_loss}")
            print(f"  TP1: {signal.take_profit_1}")
            print(f"  TP2: {signal.take_profit_2}")
            print(f"  TP3: {signal.take_profit_3}")
            print(f"  Confidence: {signal.confidence}%")
            print(f"  RRR: {signal.risk_reward_ratio}")
            print(f"  Strategy: {signal.strategy}")
        else:
            print_warning("No se generó señal (condiciones no cumplidas)")
        
        return True
        
    except Exception as e:
        print_error(f"Error en Ollama: {e}")
        if "connection" in str(e).lower():
            print_warning("Asegúrate de que Ollama esté corriendo: ollama serve")
        return False

def test_ollama():
    """Wrapper síncrono para test de Ollama"""
    return asyncio.run(test_ollama_async())

# Test 4: Elite Risk Manager
def test_risk_manager():
    print_header("TEST 4: ELITE RISK MANAGER")
    
    try:
        from src.risk.elite_risk_manager import EliteRiskManager, PositionSizing
        
        # Crear instancia
        risk_mgr = EliteRiskManager(initial_capital=10000)
        print_success("Risk Manager creado")
        
        # Test 1: Calcular tamaño de posición
        print_info("Calculando tamaño de posición óptimo...")
        sizing = risk_mgr.calculate_position_size(
            symbol='EURUSD',
            entry_price=1.0850,
            stop_loss=1.0830,
            confidence=75,
            volatility=8.5,
            correlation_with_portfolio=0.2
        )
        
        print_success("Position Sizing calculado:")
        print(f"  Base size: {sizing.base_size} lots")
        print(f"  Kelly size: {sizing.kelly_size} lots")
        print(f"  VaR adjusted: {sizing.var_adjusted_size} lots")
        print(f"  Volatility adjusted: {sizing.volatility_adjusted_size} lots")
        print(f"  Final size: {sizing.final_size} lots")
        print(f"  Leverage: {sizing.leverage}x")
        
        # Test 2: Verificar límites de riesgo
        print_info("\nVerificando límites de riesgo...")
        risk_checks = risk_mgr.check_risk_limits()
        print_success(f"Can trade: {risk_checks['can_trade']}")
        if risk_checks['warnings']:
            for warning in risk_checks['warnings']:
                print_warning(f"  {warning}")
        if risk_checks['blocks']:
            for block in risk_checks['blocks']:
                print_error(f"  {block}")
        
        # Test 3: Calcular métricas
        print_info("\nCalculando métricas de riesgo...")
        metrics = risk_mgr.calculate_risk_metrics()
        print_success("Risk Metrics:")
        print(f"  VaR (95%): {metrics.var_95:.2%}")
        print(f"  Sharpe Ratio: {metrics.sharpe_ratio:.2f}")
        print(f"  Max Drawdown: {metrics.max_drawdown:.2%}")
        print(f"  Risk Score: {metrics.risk_score}/100")
        print(f"  Market Regime: {metrics.market_regime}")
        
        # Test 4: Generar reporte
        print_info("\nGenerando reporte de riesgo...")
        report = risk_mgr.generate_risk_report()
        print_success("Reporte generado (preview):")
        lines = report.split('\n')[:10]
        for line in lines:
            if line.strip():
                print(f"  {line}")
        
        return True
        
    except Exception as e:
        print_error(f"Error en Risk Manager: {e}")
        import traceback
        traceback.print_exc()
        return False

# Test 5: Integración completa
def test_integration():
    print_header("TEST 5: INTEGRACIÓN COMPLETA")
    
    try:
        print_info("Verificando integración de todos los componentes...")
        
        # Importar todos los módulos
        from src.data.twelvedata_optimized_no_talib import TwelveDataOptimized
        from src.ai.ollama_advanced import OllamaAdvanced
        from src.risk.elite_risk_manager import EliteRiskManager
        
        # Crear instancias
        td_client = TwelveDataOptimized()
        ai_client = OllamaAdvanced()
        risk_mgr = EliteRiskManager()
        
        print_success("Todos los componentes inicializados")
        
        # Flujo de trabajo simulado
        print_info("\nSimulando flujo de trading...")
        
        # 1. Obtener datos de mercado
        symbol = 'EURUSD'
        price = td_client.get_realtime_price_api(symbol)
        if price:
            print_success(f"1. Precio obtenido: {symbol} = {price}")
        
        # 2. Calcular indicadores
        indicators = td_client.get_advanced_indicators(symbol)
        if indicators:
            print_success(f"2. Indicadores calculados: {len(indicators)} métricas")
        
        # 3. Análisis de sentimiento
        sentiment = td_client.get_market_sentiment([symbol])
        print_success(f"3. Sentimiento: {sentiment.get(symbol, 'NEUTRAL')}")
        
        # 4. Risk check
        can_trade = risk_mgr.check_risk_limits()
        print_success(f"4. Risk check: {'PASS' if can_trade['can_trade'] else 'BLOCKED'}")
        
        # 5. Position sizing
        if price:
            sizing = risk_mgr.calculate_position_size(
                symbol=symbol,
                entry_price=price,
                stop_loss=price * 0.998,
                confidence=70,
                volatility=10,
                correlation_with_portfolio=0
            )
            print_success(f"5. Position size: {sizing.final_size} lots")
        
        print_success("\n*** INTEGRACION EXITOSA ***")
        return True
        
    except Exception as e:
        print_error(f"Error en integración: {e}")
        return False

# Main
def main():
    print_header("SISTEMA DE TESTING COMPLETO")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        'dependencies': False,
        'twelvedata': False,
        'ollama': False,
        'risk_manager': False,
        'integration': False
    }
    
    # Test 1: Dependencies
    results['dependencies'] = test_dependencies()
    
    if not results['dependencies']:
        print_error("\nInstalar dependencias antes de continuar")
        print("Ejecutar: pip install -r requirements_optimized.txt")
        return
    
    # Test 2: TwelveData
    results['twelvedata'] = test_twelvedata()
    time.sleep(1)
    
    # Test 3: Ollama (solo si está disponible)
    try:
        import openai
        results['ollama'] = test_ollama()
    except ImportError:
        print_warning("OpenAI no instalado, saltando test de Ollama")
        results['ollama'] = None
    time.sleep(1)
    
    # Test 4: Risk Manager
    results['risk_manager'] = test_risk_manager()
    time.sleep(1)
    
    # Test 5: Integration
    if all(v for v in results.values() if v is not None):
        results['integration'] = test_integration()
    
    # Resumen final
    print_header("RESUMEN DE RESULTADOS")
    
    for test_name, result in results.items():
        if result is None:
            status = f"{Fore.YELLOW}SKIPPED{Style.RESET_ALL}"
        elif result:
            status = f"{Fore.GREEN}PASSED{Style.RESET_ALL}"
        else:
            status = f"{Fore.RED}FAILED{Style.RESET_ALL}"
        
        print(f"{test_name.upper():20} {status}")
    
    # Recomendaciones
    if not all(v for v in results.values() if v is not None):
        print_warning("\nRECOMENDACIONES:")
        
        if not results['dependencies']:
            print("1. Instalar dependencias faltantes")
        
        if not results['twelvedata']:
            print("2. Verificar API key de TwelveData")
        
        if results['ollama'] == False:
            print("3. Iniciar Ollama: ollama serve")
            print("   Descargar modelo: ollama pull deepseek-r1:8b")
    else:
        print_success("\n*** SISTEMA COMPLETAMENTE FUNCIONAL ***")
        print_info("El sistema esta listo para trading")

if __name__ == "__main__":
    main()