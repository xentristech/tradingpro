#!/usr/bin/env python
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
