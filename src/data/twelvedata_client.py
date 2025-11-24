#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CLIENTE TWELVEDATA API - ALGO TRADER V3
========================================
Obtiene datos reales del mercado desde TwelveData
"""

import os
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import json
import logging

class TwelveDataClient:
    def __init__(self):
        self.api_key = os.getenv('TWELVEDATA_API_KEY', '23d17ce5b7044ad5aef9766770a6252b')
        self.base_url = 'https://api.twelvedata.com'
        # Mapeo de símbolos MT5 a TwelveData
        self.symbol_map = {
            'XAUUSDm': 'XAU/USD',
            'XAUUSD': 'XAU/USD',
            'BTCXAUm': 'CALCULATED',  # Se calcula usando BTC/USD ÷ XAU/USD
            'BTCXAU': 'CALCULATED',   # Se calcula usando BTC/USD ÷ XAU/USD
            'BTCUSDm': 'BTC/USD',
            'BTCUSD': 'BTC/USD',
            'ETHUSDm': 'ETH/USD',
            'ETHUSD': 'ETH/USD',
            'EURUSDm': 'EUR/USD',
            'EURUSD': 'EUR/USD',
            'GBPUSDm': 'GBP/USD',
            'GBPUSD': 'GBP/USD',
            'USDJPY': 'USD/JPY',
            'AUDUSD': 'AUD/USD',
            'USDCHF': 'USD/CHF'
        }
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            encoding='utf-8'
        )
        self.logger = logging.getLogger(__name__)
        
        # Verificar API key
        self.verify_connection()
        
    def map_symbol(self, symbol):
        """Mapea símbolo MT5 a formato TwelveData"""
        mapped = self.symbol_map.get(symbol, symbol)
        if mapped != symbol:
            self.logger.info(f"Mapeando {symbol} -> {mapped}")
        return mapped
        
    def verify_connection(self):
        """Verifica la conexión con TwelveData"""
        try:
            url = f"{self.base_url}/api_usage"
            params = {'apikey': self.api_key}
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"TwelveData API conectada - Uso: {data.get('current_usage', 0)}/{data.get('plan_limit', 0)}")
                return True
            else:
                self.logger.error(f"Error conectando con TwelveData: {response.status_code}")
                return False
        except Exception as e:
            self.logger.error(f"Error verificando TwelveData: {e}")
            return False
            
    def get_realtime_price(self, symbol):
        """Obtiene precio en tiempo real"""
        try:
            # Mapear símbolo MT5 a TwelveData
            api_symbol = self.symbol_map.get(symbol, symbol)
            
            # Manejar símbolos calculados (BTCXAUm = BTC/USD ÷ XAU/USD)
            if api_symbol == 'CALCULATED':
                if symbol in ['BTCXAUm', 'BTCXAU']:
                    btc_price = self._get_single_price('BTC/USD')
                    xau_price = self._get_single_price('XAU/USD')
                    
                    if btc_price and xau_price:
                        calculated_price = btc_price / xau_price
                        self.logger.info(f"Precio calculado para {symbol}: {btc_price} / {xau_price} = {calculated_price:.6f}")
                        return calculated_price
                    else:
                        self.logger.error(f"Error obteniendo precios base para calcular {symbol}")
                        return None
                else:
                    self.logger.error(f"Símbolo calculado no soportado: {symbol}")
                    return None
            
            # Obtener precio directo para símbolos normales
            return self._get_single_price(api_symbol)
            
        except Exception as e:
            self.logger.error(f"Error en get_realtime_price: {e}")
            return None
    
    def _get_single_price(self, api_symbol):
        """Obtiene un precio individual de TwelveData"""
        try:
            url = f"{self.base_url}/price"
            params = {
                'symbol': api_symbol,
                'apikey': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return float(data.get('price', 0))
            else:
                self.logger.error(f"Error obteniendo precio de {api_symbol}: {response.status_code}")
                return None
        except Exception as e:
            self.logger.error(f"Error en _get_single_price para {api_symbol}: {e}")
            return None
            
    def get_quote(self, symbol):
        """Obtiene cotización completa"""
        try:
            # Mapear símbolo MT5 a TwelveData
            api_symbol = self.symbol_map.get(symbol, symbol)
            
            # Manejar símbolos calculados
            if api_symbol == 'CALCULATED':
                if symbol in ['BTCXAUm', 'BTCXAU']:
                    btc_quote = self._get_single_quote('BTC/USD')
                    xau_quote = self._get_single_quote('XAU/USD')
                    
                    if btc_quote and xau_quote:
                        btc_price = float(btc_quote.get('close', 0))
                        xau_price = float(xau_quote.get('close', 0))
                        calculated_price = btc_price / xau_price
                        
                        # Crear quote calculado
                        calculated_quote = {
                            'symbol': symbol,
                            'open': calculated_price,
                            'high': calculated_price,
                            'low': calculated_price,
                            'close': calculated_price,
                            'volume': 0,
                            'datetime': btc_quote.get('datetime', ''),
                            'timestamp': btc_quote.get('timestamp', 0)
                        }
                        
                        self.logger.info(f"Quote calculado para {symbol}: {calculated_price:.6f}")
                        return calculated_quote
                    else:
                        self.logger.error(f"Error obteniendo quotes base para calcular {symbol}")
                        return None
                else:
                    self.logger.error(f"Símbolo calculado no soportado: {symbol}")
                    return None
            
            # Obtener quote directo para símbolos normales
            return self._get_single_quote(api_symbol)
            
        except Exception as e:
            self.logger.error(f"Error en get_quote: {e}")
            return None
    
    def _get_single_quote(self, api_symbol):
        """Obtiene un quote individual de TwelveData"""
        try:
            url = f"{self.base_url}/quote"
            params = {
                'symbol': api_symbol,
                'apikey': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Error obteniendo quote de {api_symbol}: {response.status_code}")
                return None
        except Exception as e:
            self.logger.error(f"Error en _get_single_quote para {api_symbol}: {e}")
            return None
            
    def get_time_series(self, symbol, interval='5min', outputsize=100):
        """Obtiene series temporales de datos históricos"""
        try:
            # Mapear símbolo MT5 a TwelveData
            api_symbol = self.symbol_map.get(symbol, symbol)
            
            # Manejar símbolos calculados
            if api_symbol == 'CALCULATED':
                if symbol in ['BTCXAUm', 'BTCXAU']:
                    btc_df = self._get_single_time_series('BTC/USD', interval, outputsize)
                    xau_df = self._get_single_time_series('XAU/USD', interval, outputsize)
                    
                    if btc_df is not None and xau_df is not None and len(btc_df) > 0 and len(xau_df) > 0:
                        # Sincronizar timestamps (usar intersección de fechas)
                        common_times = pd.merge(btc_df[['time']], xau_df[['time']], on='time')['time']
                        
                        btc_filtered = btc_df[btc_df['time'].isin(common_times)].sort_values('time').reset_index(drop=True)
                        xau_filtered = xau_df[xau_df['time'].isin(common_times)].sort_values('time').reset_index(drop=True)
                        
                        if len(btc_filtered) > 0 and len(xau_filtered) > 0:
                            # Calcular precios dividiendo BTC/USD por XAU/USD
                            calculated_df = pd.DataFrame()
                            calculated_df['time'] = btc_filtered['time']
                            calculated_df['open'] = btc_filtered['open'] / xau_filtered['open']
                            calculated_df['high'] = btc_filtered['high'] / xau_filtered['low']  # BTC alto / XAU bajo = máximo ratio
                            calculated_df['low'] = btc_filtered['low'] / xau_filtered['high']   # BTC bajo / XAU alto = mínimo ratio
                            calculated_df['close'] = btc_filtered['close'] / xau_filtered['close']
                            calculated_df['volume'] = 1000000  # Volumen sintético
                            
                            self.logger.info(f"Serie temporal calculada para {symbol}: {len(calculated_df)} velas")
                            return calculated_df
                        else:
                            self.logger.error(f"No hay datos comunes entre BTC/USD y XAU/USD para calcular {symbol}")
                            return None
                    else:
                        self.logger.error(f"Error obteniendo series base para calcular {symbol}")
                        return None
                else:
                    self.logger.error(f"Símbolo calculado no soportado: {symbol}")
                    return None
            
            # Obtener serie temporal directa para símbolos normales
            return self._get_single_time_series(api_symbol, interval, outputsize)
            
        except Exception as e:
            self.logger.error(f"Error en get_time_series: {e}")
            return None
    
    def _get_single_time_series(self, api_symbol, interval='5min', outputsize=100):
        """Obtiene una serie temporal individual de TwelveData"""
        try:
            url = f"{self.base_url}/time_series"
            params = {
                'symbol': api_symbol,
                'interval': interval,
                'outputsize': outputsize,
                'apikey': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                
                if 'values' in data:
                    df = pd.DataFrame(data['values'])
                    df['datetime'] = pd.to_datetime(df['datetime'])
                    df['open'] = df['open'].astype(float)
                    df['high'] = df['high'].astype(float)
                    df['low'] = df['low'].astype(float)
                    df['close'] = df['close'].astype(float)
                    # Manejar volumen si existe
                    if 'volume' in df.columns:
                        df['volume'] = df['volume'].astype(float)
                    else:
                        # Usar volumen sintético basado en volatilidad para crypto
                        df['volume'] = 1000000  # Volumen base para crypto
                    
                    # Renombrar columnas para compatibilidad
                    df.rename(columns={'datetime': 'time'}, inplace=True)
                    
                    # Ordenar por fecha ascendente
                    df = df.sort_values('time').reset_index(drop=True)
                    
                    self.logger.info(f"Obtenidos {len(df)} datos de {api_symbol}")
                    return df
                else:
                    self.logger.error(f"No hay datos para {api_symbol}: {data}")
                    return None
            else:
                self.logger.error(f"Error obteniendo series de {api_symbol}: {response.status_code}")
                return None
        except Exception as e:
            self.logger.error(f"Error en _get_single_time_series para {api_symbol}: {e}")
            return None
            
    def get_technical_indicators(self, symbol, interval='5min'):
        """Obtiene indicadores técnicos"""
        indicators = {}
        
        try:
            # RSI
            url = f"{self.base_url}/rsi"
            params = {
                'symbol': self.map_symbol(symbol),
                'interval': interval,
                'time_period': 14,
                'series_type': 'close',
                'apikey': self.api_key
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'values' in data and len(data['values']) > 0:
                    indicators['rsi'] = float(data['values'][0]['rsi'])
                    
            # MACD
            url = f"{self.base_url}/macd"
            params = {
                'symbol': self.map_symbol(symbol),
                'interval': interval,
                'series_type': 'close',
                'apikey': self.api_key
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'values' in data and len(data['values']) > 0:
                    indicators['macd'] = float(data['values'][0].get('macd', 0))
                    indicators['macd_signal'] = float(data['values'][0].get('macd_signal', 0))
                    indicators['macd_histogram'] = float(data['values'][0].get('macd_hist', 0))
                    
            # Bollinger Bands
            url = f"{self.base_url}/bbands"
            params = {
                'symbol': self.map_symbol(symbol),
                'interval': interval,
                'time_period': 20,
                'series_type': 'close',
                'sd': 2,
                'apikey': self.api_key
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'values' in data and len(data['values']) > 0:
                    indicators['bb_upper'] = float(data['values'][0].get('upper_band', 0))
                    indicators['bb_middle'] = float(data['values'][0].get('middle_band', 0))
                    indicators['bb_lower'] = float(data['values'][0].get('lower_band', 0))
                    
            # SMA
            url = f"{self.base_url}/sma"
            params = {
                'symbol': self.map_symbol(symbol),
                'interval': interval,
                'time_period': 20,
                'series_type': 'close',
                'apikey': self.api_key
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'values' in data and len(data['values']) > 0:
                    indicators['sma_20'] = float(data['values'][0]['sma'])
                    
            # EMA
            url = f"{self.base_url}/ema"
            params = {
                'symbol': self.map_symbol(symbol),
                'interval': interval,
                'time_period': 12,
                'series_type': 'close',
                'apikey': self.api_key
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'values' in data and len(data['values']) > 0:
                    indicators['ema_12'] = float(data['values'][0]['ema'])
                    
            # ATR
            url = f"{self.base_url}/atr"
            params = {
                'symbol': self.map_symbol(symbol),
                'interval': interval,
                'time_period': 14,
                'apikey': self.api_key
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'values' in data and len(data['values']) > 0:
                    indicators['atr'] = float(data['values'][0]['atr'])
                    
            # Stochastic
            url = f"{self.base_url}/stoch"
            params = {
                'symbol': self.map_symbol(symbol),
                'interval': interval,
                'apikey': self.api_key
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'values' in data and len(data['values']) > 0:
                    indicators['stoch_k'] = float(data['values'][0].get('slow_k', 0))
                    indicators['stoch_d'] = float(data['values'][0].get('slow_d', 0))
                    
            # VWAP
            url = f"{self.base_url}/vwap"
            params = {
                'symbol': self.map_symbol(symbol),
                'interval': interval,
                'apikey': self.api_key
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'values' in data and len(data['values']) > 0:
                    indicators['vwap'] = float(data['values'][0].get('vwap', 0))
                    
            # ADX
            url = f"{self.base_url}/adx"
            params = {
                'symbol': self.map_symbol(symbol),
                'interval': interval,
                'time_period': 14,
                'apikey': self.api_key
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'values' in data and len(data['values']) > 0:
                    indicators['adx'] = float(data['values'][0].get('adx', 0))
                    
            # OBV
            url = f"{self.base_url}/obv"
            params = {
                'symbol': self.map_symbol(symbol),
                'interval': interval,
                'apikey': self.api_key
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'values' in data and len(data['values']) > 0:
                    indicators['obv'] = float(data['values'][0].get('obv', 0))
                    
            # CCI
            url = f"{self.base_url}/cci"
            params = {
                'symbol': self.map_symbol(symbol),
                'interval': interval,
                'time_period': 14,
                'apikey': self.api_key
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'values' in data and len(data['values']) > 0:
                    indicators['cci'] = float(data['values'][0].get('cci', 0))
                    
            # BOP (Balance of Power)
            url = f"{self.base_url}/bop"
            params = {
                'symbol': self.map_symbol(symbol),
                'interval': interval,
                'apikey': self.api_key
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'values' in data and len(data['values']) > 0:
                    indicators['bop'] = float(data['values'][0].get('bop', 0))
                    
        except Exception as e:
            self.logger.error(f"Error obteniendo indicadores: {e}")
            
        return indicators
        
    def get_forex_data(self, symbol, interval='5min'):
        """Obtiene datos específicos de Forex"""
        try:
            # Para forex, el símbolo debe estar en formato EUR/USD
            if 'USD' in symbol and '/' not in symbol:
                if symbol == 'EURUSD':
                    symbol = 'EUR/USD'
                elif symbol == 'GBPUSD':
                    symbol = 'GBP/USD'
                elif symbol == 'XAUUSD':
                    symbol = 'XAU/USD'
                    
            return self.get_time_series(symbol, interval)
        except Exception as e:
            self.logger.error(f"Error en get_forex_data: {e}")
            return None
            
    def get_crypto_data(self, symbol, interval='5min'):
        """Obtiene datos de criptomonedas"""
        try:
            # Para crypto, el símbolo debe estar en formato BTC/USD
            if symbol == 'BTCUSD':
                symbol = 'BTC/USD'
                
            return self.get_time_series(symbol, interval)
        except Exception as e:
            self.logger.error(f"Error en get_crypto_data: {e}")
            return None
    
    def _make_request(self, url: str, params: dict) -> dict:
        """Método auxiliar para hacer requests a TwelveData"""
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Error en request: {response.status_code}")
                return {}
        except Exception as e:
            self.logger.error(f"Error en request: {e}")
            return {}
            
    def batch_request(self, requests):
        """
        Realiza múltiples requests en batch para optimizar uso de API
        
        Args:
            requests (dict): Diccionario con requests {"req_1": {"url": "/time_series?..."}}
        
        Returns:
            dict: Respuesta del batch con todas las consultas
        """
        try:
            import requests as req
            url = f"{self.base_url}/batch"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'apikey {self.api_key}'
            }
            
            response = req.post(url, json=requests, headers=headers, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                self.logger.info(f"Batch request exitoso: {len(requests)} consultas")
                return data.get('data', {})
            else:
                self.logger.error(f"Error en batch request: {response.status_code}")
                return {}
                
        except Exception as e:
            self.logger.error(f"Error en batch_request: {e}")
            return {}
    
    def get_symbol_batch_data(self, symbols, intervals=['5min', '15min', '1h']):
        """
        Obtiene todos los datos necesarios para múltiples símbolos en batch
        
        Args:
            symbols (list): Lista de símbolos
            intervals (list): Lista de intervalos
        
        Returns:
            dict: Datos organizados por símbolo e indicador
        """
        try:
            batch_requests = {}
            
            for symbol in symbols:
                mapped_symbol = self.map_symbol(symbol)
                
                # Time series para cada intervalo
                for interval in intervals:
                    batch_requests[f"ts_{symbol}_{interval}"] = {
                        "url": f"/time_series?symbol={mapped_symbol}&interval={interval}&outputsize=30&apikey={self.api_key}"
                    }
                
                # Indicadores técnicos para 5min (intervalo principal)
                indicators = ['rsi', 'macd', 'ema', 'sma', 'bbands']
                for indicator in indicators:
                    batch_requests[f"{indicator}_{symbol}"] = {
                        "url": f"/{indicator}?symbol={mapped_symbol}&interval=5min&apikey={self.api_key}"
                    }
                
                # Quote actual
                batch_requests[f"quote_{symbol}"] = {
                    "url": f"/quote?symbol={mapped_symbol}&apikey={self.api_key}"
                }
            
            # Ejecutar batch
            batch_response = self.batch_request(batch_requests)
            
            # Organizar respuesta
            organized_data = {}
            for symbol in symbols:
                organized_data[symbol] = {
                    'time_series': {},
                    'indicators': {},
                    'quote': None
                }
                
                # Extraer time series
                for interval in intervals:
                    key = f"ts_{symbol}_{interval}"
                    if key in batch_response and batch_response[key].get('status') == 'success':
                        organized_data[symbol]['time_series'][interval] = batch_response[key]['response']
                
                # Extraer indicadores
                for indicator in ['rsi', 'macd', 'ema', 'sma', 'bbands']:
                    key = f"{indicator}_{symbol}"
                    if key in batch_response and batch_response[key].get('status') == 'success':
                        organized_data[symbol]['indicators'][indicator] = batch_response[key]['response']
                
                # Extraer quote
                quote_key = f"quote_{symbol}"
                if quote_key in batch_response and batch_response[quote_key].get('status') == 'success':
                    organized_data[symbol]['quote'] = batch_response[quote_key]['response']
            
            self.logger.info(f"Datos batch obtenidos para {len(symbols)} símbolos")
            return organized_data
            
        except Exception as e:
            self.logger.error(f"Error en get_symbol_batch_data: {e}")
            return {}
            
    def get_market_state(self, symbol):
        """Obtiene el estado del mercado"""
        try:
            url = f"{self.base_url}/market_state"
            params = {
                'symbol': self.map_symbol(symbol),
                'apikey': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return {'is_market_open': True}  # Asumir abierto por defecto
        except Exception as e:
            self.logger.error(f"Error en get_market_state: {e}")
            return {'is_market_open': True}
            
    def analyze_market_sentiment(self, symbol):
        """Analiza el sentimiento del mercado basado en datos"""
        try:
            # Obtener datos recientes
            df = self.get_time_series(symbol, '5min', 20)
            if df is None or len(df) < 10:
                return 'neutral'
                
            # Calcular cambio porcentual
            current_price = df['close'].iloc[-1]
            prev_price = df['close'].iloc[0]
            change_pct = ((current_price - prev_price) / prev_price) * 100
            
            # Calcular volumen promedio
            avg_volume = df['volume'].mean()
            current_volume = df['volume'].iloc[-1]
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
            
            # Determinar sentimiento
            if change_pct > 0.5 and volume_ratio > 1.2:
                return 'bullish'
            elif change_pct < -0.5 and volume_ratio > 1.2:
                return 'bearish'
            else:
                return 'neutral'
                
        except Exception as e:
            self.logger.error(f"Error analizando sentimiento: {e}")
            return 'neutral'
            
    def get_historical_data(self, symbol, interval='1min', outputsize=100):
        """
        Método de compatibilidad para get_historical_data 
        (alias para get_time_series)
        """
        return self.get_time_series(symbol, interval, outputsize)
    
    def get_complete_analysis(self, symbol):
        """Obtiene análisis completo del símbolo"""
        analysis = {
            'symbol': self.map_symbol(symbol),
            'timestamp': datetime.now(),
            'price': None,
            'quote': None,
            'indicators': {},
            'sentiment': 'neutral',
            'data': None
        }
        
        try:
            # Precio actual
            analysis['price'] = self.get_realtime_price(symbol)
            
            # Quote completo
            analysis['quote'] = self.get_quote(symbol)
            
            # Indicadores técnicos
            analysis['indicators'] = self.get_technical_indicators(symbol)
            
            # Sentimiento del mercado
            analysis['sentiment'] = self.analyze_market_sentiment(symbol)
            
            # Datos históricos
            if 'USD' in symbol:
                if symbol in ['EURUSD', 'GBPUSD', 'XAUUSD']:
                    analysis['data'] = self.get_forex_data(symbol)
                elif symbol == 'BTCUSD':
                    analysis['data'] = self.get_crypto_data(symbol)
            else:
                analysis['data'] = self.get_time_series(symbol)
                
            self.logger.info(f"Análisis completo de {symbol} obtenido")
            
        except Exception as e:
            self.logger.error(f"Error en análisis completo: {e}")
            
        return analysis

def main():
    print("""
╔════════════════════════════════════════════════════════════╗
║           CLIENTE TWELVEDATA - ALGO TRADER V3             ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    # Crear cliente
    client = TwelveDataClient()
    
    # Probar con diferentes símbolos
    symbols = ['EUR/USD', 'GBP/USD', 'XAU/USD', 'BTC/USD']
    
    for symbol in symbols:
        print(f"\n📊 Analizando {symbol}...")
        
        # Obtener precio actual
        price = client.get_realtime_price(symbol)
        if price:
            print(f"  💰 Precio actual: {price}")
            
        # Obtener indicadores
        indicators = client.get_technical_indicators(symbol)
        if indicators:
            print(f"  📈 RSI: {indicators.get('rsi', 'N/A'):.2f}")
            print(f"  📊 MACD: {indicators.get('macd', 'N/A'):.4f}")
            
        # Obtener sentimiento
        sentiment = client.analyze_market_sentiment(symbol)
        print(f"  🎯 Sentimiento: {sentiment}")
        
    print("\n✅ Prueba completada")

if __name__ == "__main__":
    main()
