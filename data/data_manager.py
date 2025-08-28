"""
Data Manager - Gestor de Datos de Mercado
Integra múltiples fuentes de datos y gestiona cache
Version: 3.0.0
"""
import os
import json
import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd
import numpy as np
from pathlib import Path

logger = logging.getLogger(__name__)

class DataManager:
    """
    Gestor centralizado de datos de mercado
    Soporta TwelveData, MT5, y cache local
    """
    
    def __init__(self, config: Dict):
        """
        Inicializa el data manager
        Args:
            config: Configuración del sistema
        """
        self.config = config
        self.api_key = os.getenv('TWELVEDATA_API_KEY')
        self.cache_dir = Path('data/cache')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache en memoria
        self.memory_cache = {}
        self.cache_ttl = 300  # 5 minutos
        
        logger.info("DataManager inicializado")
    
    async def get_data(self, 
                      symbol: str, 
                      interval: str = '1h',
                      outputsize: int = 100,
                      use_cache: bool = True) -> Optional[pd.DataFrame]:
        """
        Obtiene datos de mercado
        Args:
            symbol: Símbolo (ej: BTC/USD)
            interval: Intervalo temporal
            outputsize: Número de barras
            use_cache: Usar cache si está disponible
        Returns:
            DataFrame con datos OHLCV o None
        """
        # Verificar cache
        if use_cache:
            cached_data = self._get_from_cache(symbol, interval)
            if cached_data is not None:
                logger.debug(f"Datos obtenidos de cache para {symbol} {interval}")
                return cached_data
        
        # Obtener de API
        try:
            data = await self._fetch_from_twelvedata(symbol, interval, outputsize)
            
            if data is not None:
                # Guardar en cache
                self._save_to_cache(symbol, interval, data)
                
                # Procesar indicadores técnicos básicos
                data = self._add_basic_indicators(data)
                
                return data
                
        except Exception as e:
            logger.error(f"Error obteniendo datos para {symbol}: {e}")
        
        return None
    
    async def _fetch_from_twelvedata(self, 
                                    symbol: str, 
                                    interval: str,
                                    outputsize: int) -> Optional[pd.DataFrame]:
        """
        Obtiene datos de TwelveData API
        """
        if not self.api_key:
            logger.error("No se configuró API key de TwelveData")
            return None
        
        base_url = "https://api.twelvedata.com/time_series"
        params = {
            'symbol': symbol,
            'interval': interval,
            'outputsize': outputsize,
            'apikey': self.api_key,
            'format': 'JSON'
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if 'values' in data:
                            # Convertir a DataFrame
                            df = pd.DataFrame(data['values'])
                            df['datetime'] = pd.to_datetime(df['datetime'])
                            df.set_index('datetime', inplace=True)
                            
                            # Convertir a numérico
                            for col in ['open', 'high', 'low', 'close', 'volume']:
                                df[col] = pd.to_numeric(df[col])
                            
                            # Ordenar por fecha
                            df.sort_index(inplace=True)
                            
                            logger.info(f"✅ Datos obtenidos: {symbol} {interval} - {len(df)} barras")
                            return df
                        else:
                            logger.error(f"Respuesta sin datos: {data}")
                    else:
                        logger.error(f"Error API: Status {response.status}")
                        
            except Exception as e:
                logger.error(f"Error en request: {e}")
        
        return None
    
    def _add_basic_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Agrega indicadores técnicos básicos
        Args:
            df: DataFrame con datos OHLCV
        Returns:
            DataFrame con indicadores agregados
        """
        try:
            # Moving Averages
            df['sma_20'] = df['close'].rolling(window=20).mean()
            df['sma_50'] = df['close'].rolling(window=50).mean()
            df['ema_12'] = df['close'].ewm(span=12, adjust=False).mean()
            df['ema_26'] = df['close'].ewm(span=26, adjust=False).mean()
            
            # MACD
            df['macd'] = df['ema_12'] - df['ema_26']
            df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
            df['macd_histogram'] = df['macd'] - df['macd_signal']
            
            # RSI
            df['rsi'] = self._calculate_rsi(df['close'])
            
            # Bollinger Bands
            df['bb_middle'] = df['close'].rolling(window=20).mean()
            bb_std = df['close'].rolling(window=20).std()
            df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
            df['bb_lower'] = df['bb_middle'] - (bb_std * 2)
            
            # ATR
            df['atr'] = self._calculate_atr(df)
            
            # Volume indicators
            df['volume_sma'] = df['volume'].rolling(window=20).mean()
            df['volume_ratio'] = df['volume'] / df['volume_sma']
            
            # Price action
            df['body'] = abs(df['close'] - df['open'])
            df['upper_wick'] = df['high'] - df[['open', 'close']].max(axis=1)
            df['lower_wick'] = df[['open', 'close']].min(axis=1) - df['low']
            
        except Exception as e:
            logger.warning(f"Error calculando indicadores: {e}")
        
        return df
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Calcula RSI
        Args:
            prices: Serie de precios
            period: Período para RSI
        Returns:
            Serie con valores RSI
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        Calcula Average True Range
        Args:
            df: DataFrame con OHLC
            period: Período para ATR
        Returns:
            Serie con valores ATR
        """
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = np.max(ranges, axis=1)
        
        atr = true_range.rolling(period).mean()
        
        return atr
    
    def _get_from_cache(self, symbol: str, interval: str) -> Optional[pd.DataFrame]:
        """
        Obtiene datos del cache
        Args:
            symbol: Símbolo
            interval: Intervalo
        Returns:
            DataFrame si existe en cache y es válido, None si no
        """
        cache_key = f"{symbol}_{interval}"
        
        # Verificar cache en memoria
        if cache_key in self.memory_cache:
            cached_time, cached_data = self.memory_cache[cache_key]
            if (datetime.now() - cached_time).seconds < self.cache_ttl:
                return cached_data.copy()
        
        # Verificar cache en disco
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        if cache_file.exists():
            try:
                # Verificar antigüedad
                file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
                if (datetime.now() - file_time).seconds < self.cache_ttl * 2:
                    df = pd.read_pickle(cache_file)
                    # Actualizar cache en memoria
                    self.memory_cache[cache_key] = (datetime.now(), df)
                    return df.copy()
            except Exception as e:
                logger.warning(f"Error leyendo cache: {e}")
        
        return None
    
    def _save_to_cache(self, symbol: str, interval: str, data: pd.DataFrame):
        """
        Guarda datos en cache
        Args:
            symbol: Símbolo
            interval: Intervalo
            data: DataFrame a guardar
        """
        cache_key = f"{symbol}_{interval}"
        
        # Guardar en memoria
        self.memory_cache[cache_key] = (datetime.now(), data.copy())
        
        # Guardar en disco
        try:
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            data.to_pickle(cache_file)
        except Exception as e:
            logger.warning(f"Error guardando cache: {e}")
    
    async def get_multi_timeframe_data(self, 
                                      symbol: str,
                                      timeframes: List[str] = None) -> Dict[str, pd.DataFrame]:
        """
        Obtiene datos de múltiples timeframes
        Args:
            symbol: Símbolo
            timeframes: Lista de timeframes
        Returns:
            Dict con DataFrames por timeframe
        """
        if timeframes is None:
            timeframes = ['5min', '15min', '1h', '4h', '1day']
        
        data = {}
        tasks = []
        
        # Crear tareas asíncronas
        for tf in timeframes:
            task = self.get_data(symbol, tf)
            tasks.append(task)
        
        # Ejecutar en paralelo
        results = await asyncio.gather(*tasks)
        
        # Organizar resultados
        for tf, result in zip(timeframes, results):
            if result is not None:
                data[tf] = result
        
        logger.info(f"Datos multi-timeframe obtenidos: {list(data.keys())}")
        
        return data
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """
        Obtiene el precio más reciente
        Args:
            symbol: Símbolo
        Returns:
            Precio actual o None
        """
        # Intentar obtener de cache primero
        for interval in ['1min', '5min', '15min']:
            data = self._get_from_cache(symbol, interval)
            if data is not None and not data.empty:
                return data['close'].iloc[-1]
        
        # Si no hay cache, obtener nuevo
        asyncio.run(self.get_data(symbol, '1min', 1))
        
        return None
    
    def clear_cache(self):
        """Limpia todo el cache"""
        self.memory_cache.clear()
        
        # Limpiar archivos de cache
        for cache_file in self.cache_dir.glob("*.pkl"):
            try:
                cache_file.unlink()
            except Exception as e:
                logger.warning(f"Error borrando cache file {cache_file}: {e}")
        
        logger.info("Cache limpiado")

# Clase auxiliar para datos en tiempo real
class RealTimeDataStream:
    """
    Stream de datos en tiempo real usando WebSocket
    """
    
    def __init__(self, symbol: str, callback):
        """
        Inicializa stream de datos
        Args:
            symbol: Símbolo a monitorear
            callback: Función a llamar con cada tick
        """
        self.symbol = symbol
        self.callback = callback
        self.running = False
        self.ws = None
        
    async def start(self):
        """Inicia el stream de datos"""
        self.running = True
        # Implementar conexión WebSocket
        pass
    
    async def stop(self):
        """Detiene el stream de datos"""
        self.running = False
        if self.ws:
            await self.ws.close()

# Testing
if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    # Cargar configuración
    load_dotenv('configs/.env')
    
    # Crear data manager
    config = {
        'symbol': 'BTCUSDm',
        'twelvedata_symbol': 'BTC/USD'
    }
    
    dm = DataManager(config)
    
    # Test obtener datos
    async def test():
        data = await dm.get_data('BTC/USD', '1h', 100)
        if data is not None:
            print(f"\n✅ Datos obtenidos: {len(data)} barras")
            print(f"Columnas: {data.columns.tolist()}")
            print(f"\nÚltimas 5 barras:")
            print(data.tail())
            print(f"\nÚltimo precio: ${data['close'].iloc[-1]:.2f}")
            print(f"RSI: {data['rsi'].iloc[-1]:.2f}")
        else:
            print("❌ No se pudieron obtener datos")
    
    asyncio.run(test())
