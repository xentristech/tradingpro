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
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            encoding='utf-8'
        )
        self.logger = logging.getLogger(__name__)
        
        # Verificar API key
        self.verify_connection()
        
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
            url = f"{self.base_url}/price"
            params = {
                'symbol': symbol,
                'apikey': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return float(data.get('price', 0))
            else:
                self.logger.error(f"Error obteniendo precio de {symbol}: {response.status_code}")
                return None
        except Exception as e:
            self.logger.error(f"Error en get_realtime_price: {e}")
            return None
            
    def get_quote(self, symbol):
        """Obtiene cotización completa"""
        try:
            url = f"{self.base_url}/quote"
            params = {
                'symbol': symbol,
                'apikey': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Error obteniendo quote de {symbol}: {response.status_code}")
                return None
        except Exception as e:
            self.logger.error(f"Error en get_quote: {e}")
            return None
            
    def get_time_series(self, symbol, interval='5min', outputsize=100):
        """Obtiene series temporales de datos históricos"""
        try:
            url = f"{self.base_url}/time_series"
            params = {
                'symbol': symbol,
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
                    
                    self.logger.info(f"Obtenidos {len(df)} datos de {symbol}")
                    return df
                else:
                    self.logger.error(f"No hay datos para {symbol}: {data}")
                    return None
            else:
                self.logger.error(f"Error obteniendo series de {symbol}: {response.status_code}")
                return None
        except Exception as e:
            self.logger.error(f"Error en get_time_series: {e}")
            return None
            
    def get_technical_indicators(self, symbol, interval='5min'):
        """Obtiene indicadores técnicos"""
        indicators = {}
        
        try:
            # RSI
            url = f"{self.base_url}/rsi"
            params = {
                'symbol': symbol,
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
                'symbol': symbol,
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
                'symbol': symbol,
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
                'symbol': symbol,
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
                'symbol': symbol,
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
                'symbol': symbol,
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
                'symbol': symbol,
                'interval': interval,
                'apikey': self.api_key
            }
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'values' in data and len(data['values']) > 0:
                    indicators['stoch_k'] = float(data['values'][0].get('slow_k', 0))
                    indicators['stoch_d'] = float(data['values'][0].get('slow_d', 0))
                    
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
            
    def get_market_state(self, symbol):
        """Obtiene el estado del mercado"""
        try:
            url = f"{self.base_url}/market_state"
            params = {
                'symbol': symbol,
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
            
    def get_complete_analysis(self, symbol):
        """Obtiene análisis completo del símbolo"""
        analysis = {
            'symbol': symbol,
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
