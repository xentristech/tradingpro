#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TWELVEDATA API CLIENT OPTIMIZADO - ELITE TRADER V4
==================================================
Sistema profesional con websockets, cache inteligente y análisis avanzado
"""

import os
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from functools import lru_cache
import asyncio
import aiohttp
from collections import deque
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import websocket
import talib

class TwelveDataOptimized:
    """Cliente optimizado de TwelveData con WebSockets y análisis avanzado"""
    
    def __init__(self):
        self.api_key = os.getenv('TWELVEDATA_API_KEY', '23d17ce5b7044ad5aef9766770a6252b')
        self.base_url = 'https://api.twelvedata.com'
        self.ws_url = 'wss://ws.twelvedata.com/v1/quotes/price'
        
        # Cache multinivel con TTL
        self.cache = {
            'realtime': {},  # Cache de 5 segundos
            'minute': {},    # Cache de 1 minuto
            'indicators': {},  # Cache de 5 minutos
            'historical': {}  # Cache de 30 minutos
        }
        self.cache_ttl = {
            'realtime': 5,
            'minute': 60,
            'indicators': 300,
            'historical': 1800
        }
        
        # WebSocket para datos en tiempo real
        self.ws = None
        self.ws_thread = None
        self.realtime_data = {}
        
        # Pool de threads para llamadas paralelas
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Mapeo optimizado de símbolos
        self.symbol_map = {
            'XAUUSDm': 'XAU/USD', 'XAUUSD': 'XAU/USD',
            'BTCUSDm': 'BTC/USD', 'BTCUSD': 'BTC/USD',
            'ETHUSDm': 'ETH/USD', 'ETHUSD': 'ETH/USD',
            'EURUSDm': 'EUR/USD', 'EURUSD': 'EUR/USD',
            'GBPUSDm': 'GBP/USD', 'GBPUSD': 'GBP/USD',
            'USDJPYm': 'USD/JPY', 'USDJPY': 'USD/JPY',
            'AUDUSDm': 'AUD/USD', 'AUDUSD': 'AUD/USD',
            'USDCHFm': 'USD/CHF', 'USDCHF': 'USD/CHF',
            'NZDUSDm': 'NZD/USD', 'NZDUSD': 'NZD/USD',
            'USDCADm': 'USD/CAD', 'USDCAD': 'USD/CAD'
        }
        
        # Métricas de rendimiento
        self.api_calls = 0
        self.cache_hits = 0
        self.ws_messages = 0
        
        self.logger = logging.getLogger(__name__)
        
        # Inicializar WebSocket
        self.start_websocket()
        
    def start_websocket(self):
        """Inicializa conexión WebSocket para datos en tiempo real"""
        def on_message(ws, message):
            try:
                data = json.loads(message)
                if data.get('event') == 'price':
                    symbol = data.get('symbol')
                    price = float(data.get('price', 0))
                    self.realtime_data[symbol] = {
                        'price': price,
                        'timestamp': datetime.now(),
                        'volume': data.get('volume'),
                        'bid': data.get('bid'),
                        'ask': data.get('ask')
                    }
                    self.ws_messages += 1
            except Exception as e:
                self.logger.error(f"WebSocket message error: {e}")
        
        def on_error(ws, error):
            self.logger.error(f"WebSocket error: {error}")
        
        def on_close(ws):
            self.logger.info("WebSocket closed")
            # Reconectar automáticamente
            time.sleep(5)
            self.start_websocket()
        
        def on_open(ws):
            # Suscribirse a símbolos principales
            symbols = ['XAU/USD', 'BTC/USD', 'EUR/USD', 'GBP/USD']
            for symbol in symbols:
                ws.send(json.dumps({
                    "action": "subscribe",
                    "params": {
                        "symbols": symbol
                    }
                }))
            self.logger.info(f"WebSocket connected - Subscribed to {len(symbols)} symbols")
        
        def run_ws():
            self.ws = websocket.WebSocketApp(
                f"{self.ws_url}?apikey={self.api_key}",
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                on_open=on_open
            )
            self.ws.run_forever()
        
        self.ws_thread = threading.Thread(target=run_ws, daemon=True)
        self.ws_thread.start()
        
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
        """Obtiene precio en tiempo real del WebSocket"""
        api_symbol = self.symbol_map.get(symbol, symbol)
        if api_symbol in self.realtime_data:
            data = self.realtime_data[api_symbol]
            if (datetime.now() - data['timestamp']).seconds < 5:
                return data['price']
        return None
        
    def get_multiple_prices(self, symbols: List[str]) -> Dict[str, float]:
        """Obtiene precios de múltiples símbolos en paralelo"""
        prices = {}
        
        # Primero intentar WebSocket
        for symbol in symbols:
            ws_price = self.get_realtime_price_ws(symbol)
            if ws_price:
                prices[symbol] = ws_price
        
        # Para los que no están en WebSocket, usar API en paralelo
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
        
    def get_realtime_price_api(self, symbol: str) -> Optional[float]:
        """Obtiene precio desde API con cache"""
        # Verificar cache primero
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
        
    def get_advanced_indicators(self, symbol: str, interval: str = '1h', 
                              outputsize: int = 100) -> Dict[str, Any]:
        """Calcula indicadores técnicos avanzados"""
        cache_key = f"{symbol}_{interval}_{outputsize}"
        cached = self.get_from_cache('indicators', cache_key)
        if cached:
            return cached
        
        try:
            # Obtener datos históricos
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
                
                # Convertir a DataFrame
                df = pd.DataFrame(values)
                df['close'] = pd.to_numeric(df['close'])
                df['high'] = pd.to_numeric(df['high'])
                df['low'] = pd.to_numeric(df['low'])
                df['open'] = pd.to_numeric(df['open'])
                df['volume'] = pd.to_numeric(df['volume'])
                
                # Calcular indicadores con TA-Lib
                indicators = {}
                
                # Tendencia
                indicators['sma_20'] = talib.SMA(df['close'], timeperiod=20).iloc[-1]
                indicators['sma_50'] = talib.SMA(df['close'], timeperiod=50).iloc[-1]
                indicators['ema_12'] = talib.EMA(df['close'], timeperiod=12).iloc[-1]
                indicators['ema_26'] = talib.EMA(df['close'], timeperiod=26).iloc[-1]
                
                # MACD
                macd, signal, hist = talib.MACD(df['close'])
                indicators['macd'] = macd.iloc[-1]
                indicators['macd_signal'] = signal.iloc[-1]
                indicators['macd_histogram'] = hist.iloc[-1]
                
                # RSI
                indicators['rsi'] = talib.RSI(df['close'], timeperiod=14).iloc[-1]
                indicators['rsi_oversold'] = indicators['rsi'] < 30
                indicators['rsi_overbought'] = indicators['rsi'] > 70
                
                # Bollinger Bands
                upper, middle, lower = talib.BBANDS(df['close'], timeperiod=20)
                indicators['bb_upper'] = upper.iloc[-1]
                indicators['bb_middle'] = middle.iloc[-1]
                indicators['bb_lower'] = lower.iloc[-1]
                indicators['bb_width'] = upper.iloc[-1] - lower.iloc[-1]
                indicators['bb_position'] = (df['close'].iloc[-1] - lower.iloc[-1]) / indicators['bb_width']
                
                # ATR para volatilidad
                indicators['atr'] = talib.ATR(df['high'], df['low'], df['close'], timeperiod=14).iloc[-1]
                indicators['atr_percent'] = (indicators['atr'] / df['close'].iloc[-1]) * 100
                
                # Stochastic
                slowk, slowd = talib.STOCH(df['high'], df['low'], df['close'])
                indicators['stoch_k'] = slowk.iloc[-1]
                indicators['stoch_d'] = slowd.iloc[-1]
                
                # ADX para fuerza de tendencia
                indicators['adx'] = talib.ADX(df['high'], df['low'], df['close'], timeperiod=14).iloc[-1]
                
                # Williams %R
                indicators['williams_r'] = talib.WILLR(df['high'], df['low'], df['close'], timeperiod=14).iloc[-1]
                
                # CCI
                indicators['cci'] = talib.CCI(df['high'], df['low'], df['close'], timeperiod=20).iloc[-1]
                
                # Volume indicators
                indicators['obv'] = talib.OBV(df['close'], df['volume']).iloc[-1]
                indicators['volume_sma'] = talib.SMA(df['volume'], timeperiod=20).iloc[-1]
                indicators['volume_ratio'] = df['volume'].iloc[-1] / indicators['volume_sma']
                
                # Patrones de velas (Candlestick patterns)
                indicators['hammer'] = talib.CDLHAMMER(df['open'], df['high'], df['low'], df['close']).iloc[-1]
                indicators['doji'] = talib.CDLDOJI(df['open'], df['high'], df['low'], df['close']).iloc[-1]
                indicators['engulfing'] = talib.CDLENGULFING(df['open'], df['high'], df['low'], df['close']).iloc[-1]
                
                # Pivote points
                indicators['pivot'] = (df['high'].iloc[-1] + df['low'].iloc[-1] + df['close'].iloc[-1]) / 3
                indicators['r1'] = 2 * indicators['pivot'] - df['low'].iloc[-1]
                indicators['s1'] = 2 * indicators['pivot'] - df['high'].iloc[-1]
                
                # Market Profile
                indicators['vwap'] = (df['close'] * df['volume']).sum() / df['volume'].sum()
                
                # Guardar en cache
                self.set_cache('indicators', cache_key, indicators)
                return indicators
                
        except Exception as e:
            self.logger.error(f"Error calculating indicators for {symbol}: {e}")
            return {}
    
    def get_market_sentiment(self, symbols: List[str]) -> Dict[str, str]:
        """Analiza sentimiento del mercado para múltiples símbolos"""
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
                bearish_signals += 1  # Overbought
            elif indicators.get('bb_position', 0.5) < 0.2:
                bullish_signals += 1  # Oversold
            
            # ADX - Fuerza de tendencia
            if indicators.get('adx', 0) > 25:
                if indicators.get('macd', 0) > 0:
                    bullish_signals += 2
                else:
                    bearish_signals += 2
            
            # Volumen
            if indicators.get('volume_ratio', 1) > 1.5:
                if indicators.get('close', 0) > indicators.get('sma_20', 0):
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
    
    def get_correlation_matrix(self, symbols: List[str], interval: str = '1h', 
                              periods: int = 100) -> pd.DataFrame:
        """Calcula matriz de correlación entre símbolos"""
        prices = {}
        
        for symbol in symbols:
            try:
                api_symbol = self.symbol_map.get(symbol, symbol)
                url = f"{self.base_url}/time_series"
                params = {
                    'symbol': api_symbol,
                    'interval': interval,
                    'outputsize': periods,
                    'apikey': self.api_key
                }
                
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    values = data.get('values', [])
                    if values:
                        closes = [float(v['close']) for v in values]
                        prices[symbol] = closes
            except Exception as e:
                self.logger.error(f"Error getting correlation data for {symbol}: {e}")
        
        if prices:
            df = pd.DataFrame(prices)
            return df.corr()
        return pd.DataFrame()
    
    def get_volatility_analysis(self, symbol: str, periods: List[int] = [14, 30, 60]) -> Dict[str, float]:
        """Analiza volatilidad en múltiples períodos"""
        volatility = {}
        
        try:
            api_symbol = self.symbol_map.get(symbol, symbol)
            url = f"{self.base_url}/time_series"
            params = {
                'symbol': api_symbol,
                'interval': '1day',
                'outputsize': max(periods) + 1,
                'apikey': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                values = data.get('values', [])
                
                if values:
                    closes = np.array([float(v['close']) for v in values])
                    returns = np.diff(np.log(closes))
                    
                    for period in periods:
                        if len(returns) >= period:
                            period_returns = returns[-period:]
                            volatility[f'volatility_{period}d'] = np.std(period_returns) * np.sqrt(252) * 100
                            volatility[f'sharpe_{period}d'] = np.mean(period_returns) / np.std(period_returns) if np.std(period_returns) > 0 else 0
        
        except Exception as e:
            self.logger.error(f"Error calculating volatility for {symbol}: {e}")
        
        return volatility
    
    def get_market_profile(self, symbol: str, interval: str = '5min', periods: int = 288) -> Dict[str, Any]:
        """Genera perfil de mercado con zonas de alto volumen"""
        try:
            api_symbol = self.symbol_map.get(symbol, symbol)
            url = f"{self.base_url}/time_series"
            params = {
                'symbol': api_symbol,
                'interval': interval,
                'outputsize': periods,
                'apikey': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                values = data.get('values', [])
                
                if values:
                    df = pd.DataFrame(values)
                    df['close'] = pd.to_numeric(df['close'])
                    df['volume'] = pd.to_numeric(df['volume'])
                    df['high'] = pd.to_numeric(df['high'])
                    df['low'] = pd.to_numeric(df['low'])
                    
                    # Calcular VWAP
                    df['vwap'] = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()
                    
                    # Identificar niveles de alto volumen (POC - Point of Control)
                    price_levels = np.linspace(df['low'].min(), df['high'].max(), 50)
                    volume_profile = []
                    
                    for price in price_levels:
                        volume_at_price = df[
                            (df['low'] <= price) & (df['high'] >= price)
                        ]['volume'].sum()
                        volume_profile.append(volume_at_price)
                    
                    poc_index = np.argmax(volume_profile)
                    poc_price = price_levels[poc_index]
                    
                    # Value Area (70% del volumen)
                    total_volume = sum(volume_profile)
                    target_volume = total_volume * 0.7
                    accumulated = 0
                    va_high = poc_price
                    va_low = poc_price
                    
                    for i in range(len(volume_profile)):
                        if accumulated < target_volume:
                            if i < poc_index:
                                va_low = price_levels[i]
                            elif i > poc_index:
                                va_high = price_levels[i]
                            accumulated += volume_profile[i]
                    
                    return {
                        'vwap': df['vwap'].iloc[-1],
                        'poc': poc_price,
                        'value_area_high': va_high,
                        'value_area_low': va_low,
                        'current_price': df['close'].iloc[-1],
                        'volume_trend': 'increasing' if df['volume'].iloc[-6:].mean() > df['volume'].iloc[-12:-6].mean() else 'decreasing'
                    }
        
        except Exception as e:
            self.logger.error(f"Error generating market profile for {symbol}: {e}")
        
        return {}
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estadísticas de rendimiento del cliente"""
        return {
            'api_calls': self.api_calls,
            'cache_hits': self.cache_hits,
            'cache_hit_rate': (self.cache_hits / (self.api_calls + self.cache_hits)) * 100 if (self.api_calls + self.cache_hits) > 0 else 0,
            'ws_messages': self.ws_messages,
            'realtime_symbols': len(self.realtime_data),
            'cache_sizes': {k: len(v) for k, v in self.cache.items()}
        }
    
    def close(self):
        """Cierra conexiones y limpia recursos"""
        if self.ws:
            self.ws.close()
        self.executor.shutdown(wait=True)
        self.logger.info("TwelveData client closed")