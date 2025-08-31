#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CLIENTE TWELVEDATA MEJORADO - ALGO TRADER V3
============================================
Versión optimizada con caché, rate limiting y manejo de errores
"""

import os
import sys
import time
import json
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import logging
from typing import Dict, Optional, List, Any
import hashlib
import pickle
from functools import lru_cache
from threading import Lock
import redis

class TwelveDataClientOptimized:
    def __init__(self, use_cache=True, use_redis=False):
        """
        Cliente optimizado con caché y rate limiting
        """
        # API Configuration - NUNCA hardcodear
        self.api_key = os.getenv('TWELVEDATA_API_KEY')
        if not self.api_key:
            raise ValueError("TWELVEDATA_API_KEY no configurada en .env")
            
        self.base_url = 'https://api.twelvedata.com'
        
        # Rate limiting
        self.calls_per_minute = 8  # Límite del plan gratuito
        self.calls_per_day = 800
        self.last_call_time = 0
        self.daily_calls = 0
        self.call_lock = Lock()
        
        # Cache configuration
        self.use_cache = use_cache
        self.cache_dir = Path(__file__).parent / 'cache'
        self.cache_dir.mkdir(exist_ok=True)
        self.memory_cache = {}
        self.cache_ttl = {
            'price': 60,  # 1 minuto
            'quote': 60,
            'time_series': 300,  # 5 minutos
            'indicators': 120,  # 2 minutos
        }
        
        # Redis cache (opcional)
        self.redis_client = None
        if use_redis:
            try:
                self.redis_client = redis.Redis(
                    host='localhost',
                    port=6379,
                    decode_responses=True
                )
                self.redis_client.ping()
                logging.info("Redis cache conectado")
            except:
                self.redis_client = None
                logging.warning("Redis no disponible, usando cache local")
                
        # Logging
        self.setup_logging()
        
        # Verificar conexión
        self.verify_connection()
        
    def setup_logging(self):
        """Configura logging mejorado"""
        log_dir = Path(__file__).parent.parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)
        
        # File handler con rotación
        from logging.handlers import RotatingFileHandler
        fh = RotatingFileHandler(
            log_dir / 'twelvedata.log',
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        fh.setLevel(logging.INFO)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
        
    def _rate_limit(self):
        """Implementa rate limiting para no exceder límites de la API"""
        with self.call_lock:
            # Verificar límite diario
            if self.daily_calls >= self.calls_per_day:
                raise Exception("Límite diario de API alcanzado (800 llamadas)")
                
            # Verificar límite por minuto
            current_time = time.time()
            time_since_last_call = current_time - self.last_call_time
            
            if time_since_last_call < 60 / self.calls_per_minute:
                sleep_time = (60 / self.calls_per_minute) - time_since_last_call
                self.logger.debug(f"Rate limiting: esperando {sleep_time:.2f}s")
                time.sleep(sleep_time)
                
            self.last_call_time = time.time()
            self.daily_calls += 1
            
    def _get_cache_key(self, endpoint: str, params: Dict) -> str:
        """Genera una clave única para el caché"""
        params_str = json.dumps(params, sort_keys=True)
        key = f"{endpoint}:{params_str}"
        return hashlib.md5(key.encode()).hexdigest()
        
    def _get_from_cache(self, cache_key: str, ttl: int) -> Optional[Any]:
        """Obtiene datos del caché si están frescos"""
        if not self.use_cache:
            return None
            
        # Intentar Redis primero
        if self.redis_client:
            try:
                data = self.redis_client.get(cache_key)
                if data:
                    return json.loads(data)
            except:
                pass
                
        # Cache en memoria
        if cache_key in self.memory_cache:
            cached_data, timestamp = self.memory_cache[cache_key]
            if time.time() - timestamp < ttl:
                self.logger.debug(f"Cache hit: {cache_key}")
                return cached_data
                
        # Cache en disco
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    cached_data, timestamp = pickle.load(f)
                    if time.time() - timestamp < ttl:
                        self.logger.debug(f"Disk cache hit: {cache_key}")
                        return cached_data
            except:
                pass
                
        return None
        
    def _save_to_cache(self, cache_key: str, data: Any):
        """Guarda datos en caché"""
        if not self.use_cache:
            return
            
        timestamp = time.time()
        
        # Guardar en Redis
        if self.redis_client:
            try:
                self.redis_client.setex(
                    cache_key,
                    300,  # 5 minutos TTL
                    json.dumps(data)
                )
            except:
                pass
                
        # Guardar en memoria
        self.memory_cache[cache_key] = (data, timestamp)
        
        # Guardar en disco
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump((data, timestamp), f)
        except:
            pass
            
    def _make_request(self, endpoint: str, params: Dict, cache_ttl: int = 60) -> Optional[Dict]:
        """
        Hace una petición a la API con caché y reintentos
        """
        # Verificar caché
        cache_key = self._get_cache_key(endpoint, params)
        cached_data = self._get_from_cache(cache_key, cache_ttl)
        if cached_data is not None:
            return cached_data
            
        # Rate limiting
        self._rate_limit()
        
        # Hacer petición con reintentos
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                url = f"{self.base_url}/{endpoint}"
                params['apikey'] = self.api_key
                
                response = requests.get(url, params=params, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Verificar si hay error en la respuesta
                    if 'status' in data and data['status'] == 'error':
                        self.logger.error(f"API error: {data.get('message', 'Unknown error')}")
                        return None
                        
                    # Guardar en caché
                    self._save_to_cache(cache_key, data)
                    
                    return data
                    
                elif response.status_code == 429:
                    # Rate limit exceeded
                    self.logger.warning("Rate limit excedido, esperando...")
                    time.sleep(60)
                    
                else:
                    self.logger.error(f"Error {response.status_code}: {response.text}")
                    
            except requests.exceptions.Timeout:
                self.logger.warning(f"Timeout en intento {attempt + 1}")
                
            except Exception as e:
                self.logger.error(f"Error en petición: {e}")
                
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
                
        return None
        
    def verify_connection(self):
        """Verifica la conexión y obtiene información de uso"""
        try:
            data = self._make_request('api_usage', {}, cache_ttl=300)
            
            if data:
                used = data.get('current_usage', 0)
                limit = data.get('plan_limit', 800)
                remaining = limit - used
                
                self.logger.info(f"TwelveData API conectada")
                self.logger.info(f"Uso: {used}/{limit} ({remaining} restantes)")
                
                # Ajustar daily_calls al uso actual
                self.daily_calls = used
                
                # Advertencia si queda poco
                if remaining < 100:
                    self.logger.warning(f"⚠️ Solo quedan {remaining} llamadas!")
                    
                return True
            else:
                self.logger.error("No se pudo verificar la conexión")
                return False
                
        except Exception as e:
            self.logger.error(f"Error verificando conexión: {e}")
            return False
            
    def get_realtime_price(self, symbol: str) -> Optional[float]:
        """Obtiene precio con caché"""
        data = self._make_request('price', {'symbol': symbol}, cache_ttl=60)
        
        if data and 'price' in data:
            return float(data['price'])
        return None
        
    def get_time_series(self, symbol: str, interval: str = '5min', outputsize: int = 100) -> Optional[pd.DataFrame]:
        """Obtiene series temporales con caché extendido"""
        params = {
            'symbol': symbol,
            'interval': interval,
            'outputsize': outputsize
        }
        
        # Cache más largo para datos históricos
        cache_ttl = 300 if interval in ['1min', '5min'] else 600
        
        data = self._make_request('time_series', params, cache_ttl=cache_ttl)
        
        if data and 'values' in data:
            df = pd.DataFrame(data['values'])
            
            # Convertir tipos de datos
            df['datetime'] = pd.to_datetime(df['datetime'])
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    
            # Renombrar y ordenar
            df.rename(columns={'datetime': 'time'}, inplace=True)
            df = df.sort_values('time').reset_index(drop=True)
            
            return df
            
        return None
        
    def get_batch_indicators(self, symbol: str, interval: str = '5min') -> Dict:
        """
        Obtiene múltiples indicadores en menos llamadas
        """
        indicators = {}
        
        # Obtener datos históricos una sola vez
        df = self.get_time_series(symbol, interval, 100)
        
        if df is not None and len(df) >= 20:
            # Calcular indicadores localmente para ahorrar llamadas API
            
            # RSI
            close_prices = df['close'].values
            deltas = np.diff(close_prices)
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            avg_gain = np.mean(gains[-14:]) if len(gains) >= 14 else 0
            avg_loss = np.mean(losses[-14:]) if len(losses) >= 14 else 0
            
            if avg_loss != 0:
                rs = avg_gain / avg_loss
                indicators['rsi'] = 100 - (100 / (1 + rs))
            else:
                indicators['rsi'] = 50
                
            # Moving Averages
            indicators['sma_20'] = df['close'].rolling(20).mean().iloc[-1]
            indicators['ema_12'] = df['close'].ewm(span=12).mean().iloc[-1]
            
            # Bollinger Bands
            sma = df['close'].rolling(20).mean()
            std = df['close'].rolling(20).std()
            indicators['bb_upper'] = (sma + (std * 2)).iloc[-1]
            indicators['bb_middle'] = sma.iloc[-1]
            indicators['bb_lower'] = (sma - (std * 2)).iloc[-1]
            
            # ATR (Average True Range)
            high = df['high'].values
            low = df['low'].values
            close = df['close'].values
            
            tr_list = []
            for i in range(1, len(df)):
                tr = max(
                    high[i] - low[i],
                    abs(high[i] - close[i-1]),
                    abs(low[i] - close[i-1])
                )
                tr_list.append(tr)
                
            if tr_list:
                indicators['atr'] = np.mean(tr_list[-14:])
            else:
                indicators['atr'] = 0
                
            # MACD (simplificado)
            ema_12 = df['close'].ewm(span=12).mean()
            ema_26 = df['close'].ewm(span=26).mean()
            macd_line = ema_12 - ema_26
            signal_line = macd_line.ewm(span=9).mean()
            
            indicators['macd'] = macd_line.iloc[-1]
            indicators['macd_signal'] = signal_line.iloc[-1]
            indicators['macd_histogram'] = macd_line.iloc[-1] - signal_line.iloc[-1]
            
            self.logger.info(f"Indicadores calculados localmente para {symbol}")
            
        else:
            # Si no hay suficientes datos, obtener de la API (última opción)
            self.logger.warning(f"Datos insuficientes para cálculo local, usando API")
            
            # Solo obtener RSI y MACD de la API (2 llamadas en vez de 7)
            rsi_data = self._make_request('rsi', {
                'symbol': symbol,
                'interval': interval,
                'time_period': 14,
                'series_type': 'close'
            })
            
            if rsi_data and 'values' in rsi_data and len(rsi_data['values']) > 0:
                indicators['rsi'] = float(rsi_data['values'][0]['rsi'])
                
        return indicators
        
    def get_complete_analysis_optimized(self, symbol: str) -> Dict:
        """
        Análisis completo optimizado con mínimas llamadas API
        """
        analysis = {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'price': None,
            'indicators': {},
            'sentiment': 'neutral',
            'data': None,
            'api_calls_used': self.daily_calls
        }
        
        try:
            # Una sola llamada para datos históricos
            df = self.get_time_series(symbol, '5min', 100)
            
            if df is not None and len(df) > 0:
                analysis['data'] = df
                analysis['price'] = df['close'].iloc[-1]
                
                # Calcular todos los indicadores localmente
                analysis['indicators'] = self.get_batch_indicators(symbol)
                
                # Calcular sentimiento basado en precio
                if len(df) >= 10:
                    price_change = (df['close'].iloc[-1] - df['close'].iloc[-10]) / df['close'].iloc[-10]
                    
                    if price_change > 0.002:
                        analysis['sentiment'] = 'bullish'
                    elif price_change < -0.002:
                        analysis['sentiment'] = 'bearish'
                    else:
                        analysis['sentiment'] = 'neutral'
                        
            self.logger.info(f"Análisis completo de {symbol} con {self.daily_calls} llamadas API usadas hoy")
            
        except Exception as e:
            self.logger.error(f"Error en análisis optimizado: {e}")
            
        return analysis
        
    def get_remaining_calls(self) -> int:
        """Retorna el número de llamadas API restantes"""
        return max(0, self.calls_per_day - self.daily_calls)
        
    def clear_cache(self):
        """Limpia todo el caché"""
        self.memory_cache.clear()
        
        # Limpiar caché de disco
        for cache_file in self.cache_dir.glob('*.pkl'):
            try:
                cache_file.unlink()
            except:
                pass
                
        # Limpiar Redis
        if self.redis_client:
            try:
                self.redis_client.flushdb()
            except:
                pass
                
        self.logger.info("Caché limpiado")
        
    def get_status(self) -> Dict:
        """Retorna el estado del cliente"""
        return {
            'api_calls_used': self.daily_calls,
            'api_calls_remaining': self.get_remaining_calls(),
            'cache_enabled': self.use_cache,
            'redis_connected': self.redis_client is not None,
            'memory_cache_size': len(self.memory_cache),
            'last_call_time': datetime.fromtimestamp(self.last_call_time).isoformat() if self.last_call_time > 0 else None
        }

def main():
    """Prueba del cliente optimizado"""
    print("""
╔════════════════════════════════════════════════════════════╗
║     CLIENTE TWELVEDATA OPTIMIZADO - ALGO TRADER V3        ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    # Verificar configuración
    if not os.getenv('TWELVEDATA_API_KEY'):
        print("\n❌ ERROR: Configura TWELVEDATA_API_KEY en tu archivo .env")
        print("   No uses la API key hardcodeada!")
        return
        
    # Crear cliente optimizado
    client = TwelveDataClientOptimized(use_cache=True)
    
    print(f"\n📊 Estado del cliente:")
    status = client.get_status()
    for key, value in status.items():
        print(f"  • {key}: {value}")
        
    # Probar con un símbolo
    symbol = 'EUR/USD'
    print(f"\n🔍 Analizando {symbol}...")
    
    analysis = client.get_complete_analysis_optimized(symbol)
    
    if analysis['price']:
        print(f"  💰 Precio: {analysis['price']:.5f}")
        print(f"  📈 RSI: {analysis['indicators'].get('rsi', 'N/A'):.2f}")
        print(f"  🎯 Sentimiento: {analysis['sentiment']}")
        print(f"  📞 Llamadas API usadas: {analysis['api_calls_used']}")
        print(f"  ⚡ Llamadas restantes: {client.get_remaining_calls()}")
    else:
        print("  ❌ No se pudieron obtener datos")
        
    print("\n✅ Prueba completada")

if __name__ == "__main__":
    main()
