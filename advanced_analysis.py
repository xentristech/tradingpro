#!/usr/bin/env python3
"""
ADVANCED ANALYSIS - Sistema híbrido de análisis técnico
MT5 + TwelveData API + Time Series + IA Simplificada
"""
import MetaTrader5 as mt5
import requests
import json
import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
import logging

load_dotenv('.env')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedAnalyzer:
    def __init__(self):
        self.api_key = os.getenv('TWELVEDATA_API_KEY', '23d17ce5b7044ad5aef9766770a6252b')
        self.base_url = 'https://api.twelvedata.com'
        
    def get_time_series(self, symbol, interval='15min', size=50):
        """Obtener time series de TwelveData"""
        try:
            url = f"{self.base_url}/time_series"
            params = {
                'symbol': symbol,
                'interval': interval,
                'outputsize': size,
                'apikey': self.api_key,
                'format': 'json'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'values' in data and data['values']:
                    # Convertir a DataFrame
                    df = pd.DataFrame(data['values'])
                    df['datetime'] = pd.to_datetime(df['datetime'])
                    df = df.sort_values('datetime')
                    
                    # Convertir precios a float
                    for col in ['open', 'high', 'low', 'close', 'volume']:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                    return df
                else:
                    logger.error(f"Sin datos time series para {symbol}")
                    return None
            else:
                logger.error(f"Error TwelveData time_series: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error obteniendo time series {symbol}: {e}")
            return None
    
    def get_technical_indicators(self, symbol, interval='15min'):
        """Obtener múltiples indicadores técnicos"""
        try:
            indicators = {}
            
            # RSI
            url = f"{self.base_url}/rsi"
            params = {
                'symbol': symbol,
                'interval': interval,
                'time_period': 14,
                'apikey': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'values' in data and data['values']:
                    indicators['rsi'] = float(data['values'][0]['rsi'])
            
            # MACD
            url = f"{self.base_url}/macd"
            params = {
                'symbol': symbol,
                'interval': interval,
                'fast_period': 12,
                'slow_period': 26,
                'signal_period': 9,
                'apikey': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'values' in data and data['values']:
                    indicators['macd'] = float(data['values'][0]['macd'])
                    indicators['macd_signal'] = float(data['values'][0]['macd_signal'])
                    indicators['macd_histogram'] = float(data['values'][0]['macd_histogram'])
            
            # SMA
            for period in [5, 10, 20, 50]:
                url = f"{self.base_url}/sma"
                params = {
                    'symbol': symbol,
                    'interval': interval,
                    'time_period': period,
                    'apikey': self.api_key
                }
                
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'values' in data and data['values']:
                        indicators[f'sma_{period}'] = float(data['values'][0]['sma'])
            
            # EMA
            for period in [12, 26]:
                url = f"{self.base_url}/ema"
                params = {
                    'symbol': symbol,
                    'interval': interval,
                    'time_period': period,
                    'apikey': self.api_key
                }
                
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'values' in data and data['values']:
                        indicators[f'ema_{period}'] = float(data['values'][0]['ema'])
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error obteniendo indicadores {symbol}: {e}")
            return {}
    
    def analyze_symbol_advanced(self, mt5_symbol):
        """Análisis avanzado combinando MT5 + TwelveData"""
        try:
            # 1. Datos MT5 básicos
            tick = mt5.symbol_info_tick(mt5_symbol)
            if not tick:
                return None
            
            current_price = tick.bid
            
            # 2. Normalizar símbolo para TwelveData
            if 'XAU' in mt5_symbol or 'GOLD' in mt5_symbol:
                td_symbol = 'XAU/USD'
            elif 'BTC' in mt5_symbol:
                td_symbol = 'BTC/USD'
            elif 'ETH' in mt5_symbol:
                td_symbol = 'ETH/USD'
            elif mt5_symbol == 'EURUSD':
                td_symbol = 'EUR/USD'
            else:
                td_symbol = mt5_symbol
            
            # 3. Obtener time series
            df = self.get_time_series(td_symbol)
            if df is None or df.empty:
                logger.warning(f"Sin time series para {td_symbol}")
                return None
            
            # 4. Obtener indicadores técnicos
            indicators = self.get_technical_indicators(td_symbol)
            
            # 5. Precio de TwelveData vs MT5
            td_price = df['close'].iloc[-1] if not df.empty else current_price
            price_diff = abs(td_price - current_price) / current_price
            
            # 6. Análisis de tendencia con time series
            if len(df) >= 20:
                df['sma_5'] = df['close'].rolling(5).mean()
                df['sma_10'] = df['close'].rolling(10).mean()
                df['sma_20'] = df['close'].rolling(20).mean()
                
                current_close = df['close'].iloc[-1]
                sma_5 = df['sma_5'].iloc[-1]
                sma_10 = df['sma_10'].iloc[-1]
                sma_20 = df['sma_20'].iloc[-1]
                
                # Determinar tendencia
                if sma_5 > sma_10 > sma_20:
                    trend = "alcista_fuerte"
                elif sma_5 > sma_10:
                    trend = "alcista"
                elif sma_5 < sma_10 < sma_20:
                    trend = "bajista_fuerte"
                elif sma_5 < sma_10:
                    trend = "bajista"
                else:
                    trend = "lateral"
            else:
                trend = "insuficientes_datos"
            
            # 7. Análisis de volatilidad
            if len(df) >= 14:
                df['returns'] = df['close'].pct_change()
                volatility = df['returns'].rolling(14).std().iloc[-1] * 100
            else:
                volatility = 0
            
            # 8. Señales de trading
            signals = []
            signal_strength = 0
            
            # RSI
            rsi = indicators.get('rsi', 50)
            if 20 < rsi < 35:
                signals.append("RSI oversold recovering")
                signal_strength += 0.3
            elif 65 < rsi < 80:
                signals.append("RSI overbought correction")
                signal_strength -= 0.3
            
            # MACD
            macd = indicators.get('macd', 0)
            macd_signal = indicators.get('macd_signal', 0)
            if macd > macd_signal and macd > 0:
                signals.append("MACD bullish crossover")
                signal_strength += 0.25
            elif macd < macd_signal and macd < 0:
                signals.append("MACD bearish crossover")
                signal_strength -= 0.25
            
            # Tendencia
            if trend in ["alcista", "alcista_fuerte"]:
                signals.append(f"Trend {trend}")
                signal_strength += 0.2 if trend == "alcista" else 0.35
            elif trend in ["bajista", "bajista_fuerte"]:
                signals.append(f"Trend {trend}")
                signal_strength -= 0.2 if trend == "bajista" else 0.35
            
            # Sincronización de precios
            if price_diff < 0.001:  # Precios sincronizados
                signals.append("Price sync confirmed")
                signal_strength += 0.1
            
            # 9. Decisión final
            if signal_strength > 0.4:
                signal = "BUY"
                confidence = min(signal_strength * 1.5, 0.95)
            elif signal_strength < -0.4:
                signal = "SELL"
                confidence = min(abs(signal_strength) * 1.5, 0.95)
            else:
                signal = "HOLD"
                confidence = 0.3
            
            return {
                'symbol': mt5_symbol,
                'signal': signal,
                'confidence': confidence,
                'strength': signal_strength,
                'current_price': current_price,
                'td_price': td_price,
                'rsi': rsi,
                'macd': macd,
                'trend': trend,
                'volatility': volatility,
                'signals': signals[:3],  # Top 3 señales
                'indicators': indicators,
                'time_series_points': len(df) if df is not None else 0
            }
            
        except Exception as e:
            logger.error(f"Error análisis avanzado {mt5_symbol}: {e}")
            return None

def test_advanced_analysis():
    """Probar análisis avanzado"""
    if not mt5.initialize():
        print("ERROR: No se pudo conectar a MT5")
        return
    
    analyzer = AdvancedAnalyzer()
    
    # Probar con XAUUSDm (oro)
    print("=== ANÁLISIS AVANZADO XAUUSD ===")
    
    result = analyzer.analyze_symbol_advanced('XAUUSDm')
    
    if result:
        print(f"Símbolo: {result['symbol']}")
        print(f"Señal: {result['signal']} (confianza: {result['confidence']:.1%})")
        print(f"Precio MT5: ${result['current_price']:.2f}")
        print(f"Precio TwelveData: ${result['td_price']:.2f}")
        print(f"RSI: {result['rsi']:.1f}")
        print(f"MACD: {result['macd']:.4f}")
        print(f"Tendencia: {result['trend']}")
        print(f"Volatilidad: {result['volatility']:.2f}%")
        print(f"Time series: {result['time_series_points']} puntos")
        print(f"Señales detectadas:")
        for signal in result['signals']:
            print(f"  - {signal}")
    else:
        print("No se pudo obtener análisis")
    
    mt5.shutdown()

if __name__ == "__main__":
    test_advanced_analysis()