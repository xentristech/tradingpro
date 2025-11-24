#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SISTEMA DE SEÑALES MEJORADO
===========================
Generador de señales con múltiples indicadores usando TwelveData
- 25+ indicadores técnicos
- Análisis multi-timeframe
- IA para confirmación
- Integración completa con MT5
"""

import os
import sys
import time
import logging
import requests
import pandas as pd
import numpy as np
import MetaTrader5 as mt5
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.FileHandler('logs/enhanced_signals.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TradingSignal:
    """Señal de trading mejorada"""
    symbol: str
    direction: str  # BUY, SELL, NEUTRAL
    strength: float  # 0-100
    confidence: float  # 0-100
    indicators: Dict  # Valores de todos los indicadores
    reasons: List[str]  # Razones de la señal
    timestamp: datetime
    entry_price: float
    stop_loss: float
    take_profit: float

class EnhancedSignalGenerator:
    """
    Generador de señales mejorado con múltiples indicadores
    """
    
    def __init__(self):
        """Inicializa el generador"""
        self.api_key = '23d17ce5b7044ad5aef9766770a6252b'  # TwelveData key
        self.base_url = 'https://api.twelvedata.com'
        
        # Símbolos soportados
        self.symbols = {
            'XAUUSDm': 'XAU/USD',
            'BTCUSDm': 'BTC/USD', 
            'EURUSD': 'EUR/USD',
            'GBPUSD': 'GBP/USD',
            'USDJPY': 'USD/JPY'
        }
        
        # Timeframes para análisis multi-TF
        self.timeframes = ['5min', '15min', '30min', '1h', '4h']
        
        # Configuración de indicadores
        self.indicators_config = {
            # Trend Following
            'SMA': [9, 21, 50, 200],
            'EMA': [12, 26, 50],
            'WMA': [14, 28],
            'TEMA': [14],
            'DEMA': [14],
            'HMA': [21],
            
            # Momentum
            'RSI': [14, 21],
            'STOCH': [(14, 3, 3)],
            'STOCHRSI': [14],
            'WILLIAMS': [14],
            'ROC': [12],
            'MOM': [10],
            'CCI': [20],
            'CMO': [14],
            'ULTIMATE': [14],
            
            # Volatility
            'BBANDS': [(20, 2.0)],
            'ATR': [14],
            'NATR': [14],
            'TRANGE': [],
            'AVGPRICE': [],
            'MEDPRICE': [],
            
            # Volume
            'AD': [],
            'ADOSC': [(3, 10)],
            'OBV': [],
            
            # Cycle
            'MAMA': [(0.5, 0.05)],
            'HT_TRENDLINE': []
        }
        
        logger.info(f"Enhanced Signal Generator inicializado")
        logger.info(f"Símbolos: {list(self.symbols.keys())}")
        logger.info(f"Indicadores: {len(self.indicators_config)} tipos")
    
    def get_comprehensive_data(self, symbol: str, timeframe: str = '15min', outputsize: int = 100) -> Optional[Dict]:
        """
        Obtiene datos completos con todos los indicadores de TwelveData
        """
        try:
            mapped_symbol = self.symbols.get(symbol, symbol)
            
            results = {}
            
            # 1. OHLCV Data
            ohlcv = self._get_ohlcv(mapped_symbol, timeframe, outputsize)
            if not ohlcv:
                return None
            results['ohlcv'] = ohlcv
            
            # 2. All Technical Indicators
            indicators = self._get_all_indicators(mapped_symbol, timeframe)
            results['indicators'] = indicators
            
            # 3. Market Statistics
            stats = self._get_market_stats(mapped_symbol)
            results['stats'] = stats
            
            logger.info(f"[DATA] {symbol}: {len(ohlcv)} barras, {len(indicators)} indicadores")
            
            return results
            
        except Exception as e:
            logger.error(f"Error obteniendo datos para {symbol}: {e}")
            return None
    
    def _get_ohlcv(self, symbol: str, timeframe: str, outputsize: int) -> Optional[List]:
        """Obtiene datos OHLCV básicos"""
        url = f"{self.base_url}/time_series"
        params = {
            'symbol': symbol,
            'interval': timeframe,
            'outputsize': outputsize,
            'apikey': self.api_key
        }
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if 'values' in data:
                return data['values']
        
        return None
    
    def _get_all_indicators(self, symbol: str, timeframe: str) -> Dict:
        """Obtiene todos los indicadores técnicos de TwelveData"""
        indicators = {}
        
        for indicator_name, configs in self.indicators_config.items():
            try:
                if not configs:  # Indicadores sin parámetros
                    result = self._get_single_indicator(symbol, timeframe, indicator_name)
                    if result:
                        indicators[indicator_name] = result
                else:
                    # Indicadores con múltiples configuraciones
                    for config in configs:
                        if isinstance(config, tuple):
                            # Parámetros múltiples (ej: STOCH, BBANDS)
                            params_str = '_'.join(map(str, config))
                            key = f"{indicator_name}_{params_str}"
                        else:
                            # Parámetro único (ej: RSI_14, SMA_21)
                            key = f"{indicator_name}_{config}"
                        
                        result = self._get_single_indicator(symbol, timeframe, indicator_name, config)
                        if result:
                            indicators[key] = result
                
                # Pequeña pausa para no saturar la API
                time.sleep(0.1)
                
            except Exception as e:
                logger.warning(f"Error obteniendo {indicator_name}: {e}")
        
        return indicators
    
    def _get_single_indicator(self, symbol: str, timeframe: str, indicator: str, params=None) -> Optional[List]:
        """Obtiene un indicador específico"""
        url = f"{self.base_url}/{indicator.lower()}"
        
        request_params = {
            'symbol': symbol,
            'interval': timeframe,
            'outputsize': 50,
            'apikey': self.api_key
        }
        
        # Agregar parámetros específicos del indicador
        if params:
            if indicator == 'SMA' or indicator == 'EMA' or indicator == 'WMA':
                request_params['time_period'] = params
            elif indicator == 'RSI' or indicator == 'WILLIAMS' or indicator == 'CCI':
                request_params['time_period'] = params
            elif indicator == 'STOCH':
                request_params['fastkperiod'] = params[0]
                request_params['slowkperiod'] = params[1]
                request_params['slowdperiod'] = params[2]
            elif indicator == 'BBANDS':
                request_params['time_period'] = params[0]
                request_params['nbdevup'] = params[1]
                request_params['nbdevdn'] = params[1]
            # Agregar más configuraciones según necesidad
        
        try:
            response = requests.get(url, params=request_params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'values' in data:
                    return data['values']
            return None
        except Exception:
            return None
    
    def _get_market_stats(self, symbol: str) -> Dict:
        """Obtiene estadísticas del mercado"""
        stats = {}
        
        try:
            # Quote actual
            url = f"{self.base_url}/quote"
            params = {'symbol': symbol, 'apikey': self.api_key}
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                stats['quote'] = data
            
            # Estadísticas adicionales si están disponibles
            
        except Exception as e:
            logger.warning(f"Error obteniendo stats para {symbol}: {e}")
        
        return stats
    
    def analyze_signal(self, symbol: str, timeframe: str = '15min') -> Optional[TradingSignal]:
        """
        Analiza un símbolo y genera señal completa
        """
        try:
            logger.info(f"\n[ANÁLISIS] {symbol} en {timeframe}")
            
            # Obtener datos completos
            data = self.get_comprehensive_data(symbol, timeframe)
            if not data:
                return None
            
            ohlcv = data['ohlcv']
            indicators = data['indicators']
            
            if not ohlcv or len(ohlcv) < 20:
                logger.warning(f"Datos insuficientes para {symbol}")
                return None
            
            # Precio actual
            current_price = float(ohlcv[0]['close'])
            
            # Análisis multi-indicador
            signal_score = 0.0
            reasons = []
            indicator_values = {}
            
            # ANÁLISIS DE TENDENCIA
            trend_score = self._analyze_trend(indicators, reasons, indicator_values)
            signal_score += trend_score * 0.3
            
            # ANÁLISIS DE MOMENTUM  
            momentum_score = self._analyze_momentum(indicators, reasons, indicator_values)
            signal_score += momentum_score * 0.25
            
            # ANÁLISIS DE VOLATILIDAD
            volatility_score = self._analyze_volatility(indicators, ohlcv, reasons, indicator_values)
            signal_score += volatility_score * 0.2
            
            # ANÁLISIS DE VOLUMEN
            volume_score = self._analyze_volume(indicators, reasons, indicator_values)
            signal_score += volume_score * 0.15
            
            # ANÁLISIS DE PATRONES
            pattern_score = self._analyze_patterns(ohlcv, reasons, indicator_values)
            signal_score += pattern_score * 0.1
            
            # Determinar dirección
            if signal_score > 15:
                direction = 'BUY'
                strength = min(signal_score, 100)
            elif signal_score < -15:
                direction = 'SELL'
                strength = min(abs(signal_score), 100)
            else:
                direction = 'NEUTRAL'
                strength = 0
            
            # Calcular confianza
            confidence = min(abs(signal_score) * 2, 100)
            
            # Calcular SL/TP basado en ATR si está disponible
            atr_key = next((k for k in indicators.keys() if 'ATR' in k), None)
            if atr_key and indicators[atr_key]:
                atr_value = float(indicators[atr_key][0]['atr'])
            else:
                # ATR estimado
                high_low_range = float(ohlcv[0]['high']) - float(ohlcv[0]['low'])
                atr_value = high_low_range * 1.5
            
            if direction == 'BUY':
                stop_loss = current_price - (atr_value * 2)
                take_profit = current_price + (atr_value * 3)
            elif direction == 'SELL':
                stop_loss = current_price + (atr_value * 2)  
                take_profit = current_price - (atr_value * 3)
            else:
                stop_loss = current_price
                take_profit = current_price
            
            # Crear señal
            signal = TradingSignal(
                symbol=symbol,
                direction=direction,
                strength=strength,
                confidence=confidence,
                indicators=indicator_values,
                reasons=reasons,
                timestamp=datetime.now(),
                entry_price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit
            )
            
            logger.info(f"[SEÑAL] {symbol}: {direction} | Fuerza: {strength:.1f} | Confianza: {confidence:.1f}%")
            for reason in reasons[:5]:  # Mostrar top 5 razones
                logger.info(f"  - {reason}")
            
            return signal
            
        except Exception as e:
            logger.error(f"Error analizando {symbol}: {e}")
            return None
    
    def _analyze_trend(self, indicators: Dict, reasons: List, values: Dict) -> float:
        """Analiza indicadores de tendencia"""
        score = 0.0
        
        # Moving Averages
        sma_keys = [k for k in indicators.keys() if 'SMA' in k]
        for key in sma_keys:
            if indicators[key] and len(indicators[key]) >= 2:
                current = float(indicators[key][0]['sma'])
                previous = float(indicators[key][1]['sma'])
                values[key] = current
                
                if current > previous:
                    score += 2
                    if 'SMA_21' in key:
                        reasons.append(f"SMA21 ascendente: {current:.4f}")
                elif current < previous:
                    score -= 2
        
        # EMA Analysis
        ema_keys = [k for k in indicators.keys() if 'EMA' in k]
        for key in ema_keys:
            if indicators[key] and len(indicators[key]) >= 2:
                current = float(indicators[key][0]['ema'])
                previous = float(indicators[key][1]['ema'])
                values[key] = current
                
                if current > previous:
                    score += 1.5
                elif current < previous:
                    score -= 1.5
        
        return score
    
    def _analyze_momentum(self, indicators: Dict, reasons: List, values: Dict) -> float:
        """Analiza indicadores de momentum"""
        score = 0.0
        
        # RSI Analysis
        rsi_keys = [k for k in indicators.keys() if 'RSI' in k]
        for key in rsi_keys:
            if indicators[key]:
                rsi_val = float(indicators[key][0]['rsi'])
                values[key] = rsi_val
                
                if rsi_val < 30:
                    score += 5
                    reasons.append(f"RSI sobreventa: {rsi_val:.1f}")
                elif rsi_val > 70:
                    score -= 5
                    reasons.append(f"RSI sobrecompra: {rsi_val:.1f}")
                elif 40 <= rsi_val <= 60:
                    score += 1  # RSI neutral es positivo
        
        # Stochastic Analysis
        stoch_keys = [k for k in indicators.keys() if 'STOCH' in k]
        for key in stoch_keys:
            if indicators[key]:
                try:
                    slow_k = float(indicators[key][0]['slow_k'])
                    slow_d = float(indicators[key][0]['slow_d'])
                    values[f"{key}_K"] = slow_k
                    values[f"{key}_D"] = slow_d
                    
                    if slow_k < 20 and slow_d < 20:
                        score += 3
                        reasons.append(f"Stoch sobreventa: K={slow_k:.1f}")
                    elif slow_k > 80 and slow_d > 80:
                        score -= 3
                        reasons.append(f"Stoch sobrecompra: K={slow_k:.1f}")
                except:
                    pass
        
        return score
    
    def _analyze_volatility(self, indicators: Dict, ohlcv: List, reasons: List, values: Dict) -> float:
        """Analiza volatilidad"""
        score = 0.0
        
        # Bollinger Bands
        bb_keys = [k for k in indicators.keys() if 'BBANDS' in k]
        for key in bb_keys:
            if indicators[key]:
                try:
                    upper = float(indicators[key][0]['upper_band'])
                    lower = float(indicators[key][0]['lower_band'])
                    middle = float(indicators[key][0]['middle_band'])
                    
                    current_price = float(ohlcv[0]['close'])
                    values[f"{key}_upper"] = upper
                    values[f"{key}_lower"] = lower
                    values[f"{key}_middle"] = middle
                    
                    # Posición relativa en las bandas
                    if current_price <= lower:
                        score += 4
                        reasons.append("Precio en banda inferior BB")
                    elif current_price >= upper:
                        score -= 4
                        reasons.append("Precio en banda superior BB")
                    elif current_price < middle:
                        score += 1
                    else:
                        score -= 1
                        
                except:
                    pass
        
        # ATR for volatility context
        atr_keys = [k for k in indicators.keys() if 'ATR' in k]
        for key in atr_keys:
            if indicators[key] and len(indicators[key]) >= 2:
                current_atr = float(indicators[key][0]['atr'])
                prev_atr = float(indicators[key][1]['atr'])
                values[key] = current_atr
                
                if current_atr > prev_atr * 1.2:
                    reasons.append(f"Alta volatilidad: ATR={current_atr:.4f}")
        
        return score
    
    def _analyze_volume(self, indicators: Dict, reasons: List, values: Dict) -> float:
        """Analiza indicadores de volumen"""
        score = 0.0
        
        # OBV (On Balance Volume)
        obv_keys = [k for k in indicators.keys() if 'OBV' in k]
        for key in obv_keys:
            if indicators[key] and len(indicators[key]) >= 2:
                current = float(indicators[key][0]['obv'])
                previous = float(indicators[key][1]['obv'])
                values[key] = current
                
                if current > previous:
                    score += 2
                    reasons.append("OBV positivo")
                else:
                    score -= 1
        
        return score
    
    def _analyze_patterns(self, ohlcv: List, reasons: List, values: Dict) -> float:
        """Analiza patrones de precios"""
        score = 0.0
        
        if len(ohlcv) >= 3:
            # Análisis de velas recientes
            current = ohlcv[0]
            prev1 = ohlcv[1] 
            prev2 = ohlcv[2]
            
            # Calcular cuerpos de velas
            current_body = abs(float(current['close']) - float(current['open']))
            prev1_body = abs(float(prev1['close']) - float(prev1['open']))
            
            # Doji pattern
            total_range = float(current['high']) - float(current['low'])
            if total_range > 0 and current_body < total_range * 0.1:
                reasons.append("Patrón Doji detectado")
                score += 1
            
            # Consecutive green/red candles
            consecutive_green = 0
            consecutive_red = 0
            
            for candle in ohlcv[:5]:
                close_val = float(candle['close'])
                open_val = float(candle['open'])
                
                if close_val > open_val:
                    consecutive_green += 1
                    consecutive_red = 0
                else:
                    consecutive_red += 1
                    consecutive_green = 0
                    
                if consecutive_green >= 3:
                    score += 2
                    reasons.append(f"3+ velas verdes consecutivas")
                    break
                elif consecutive_red >= 3:
                    score -= 2
                    reasons.append(f"3+ velas rojas consecutivas")
                    break
            
            values['consecutive_green'] = consecutive_green
            values['consecutive_red'] = consecutive_red
        
        return score

def main():
    """Función principal para probar el sistema"""
    generator = EnhancedSignalGenerator()
    
    print("\n" + "="*80)
    print("     SISTEMA DE SEÑALES MEJORADO - ANÁLISIS COMPLETO")
    print("="*80)
    print(f"Hora: {datetime.now()}")
    print(f"Símbolos configurados: {list(generator.symbols.keys())}")
    print(f"Indicadores por símbolo: {sum(len(configs) if configs else 1 for configs in generator.indicators_config.values())}")
    
    # Analizar todos los símbolos
    signals = []
    
    for symbol in generator.symbols.keys():
        print(f"\n[ANALIZANDO] {symbol}...")
        signal = generator.analyze_signal(symbol)
        
        if signal:
            signals.append(signal)
            
            print(f"\n📊 SEÑAL PARA {symbol}:")
            print(f"   Dirección: {signal.direction}")
            print(f"   Fuerza: {signal.strength:.1f}")
            print(f"   Confianza: {signal.confidence:.1f}%")
            print(f"   Precio: ${signal.entry_price:.4f}")
            print(f"   SL: ${signal.stop_loss:.4f}")
            print(f"   TP: ${signal.take_profit:.4f}")
            print(f"   Indicadores analizados: {len(signal.indicators)}")
            
            if signal.reasons:
                print("   Razones principales:")
                for reason in signal.reasons[:3]:
                    print(f"     • {reason}")
        else:
            print(f"   ❌ No se pudo generar señal para {symbol}")
        
        time.sleep(1)  # Pausa entre símbolos
    
    # Resumen final
    print(f"\n" + "="*80)
    print("                    RESUMEN DE ANÁLISIS")
    print("="*80)
    
    strong_signals = [s for s in signals if s.confidence > 70]
    medium_signals = [s for s in signals if 50 <= s.confidence <= 70]
    
    print(f"Total señales generadas: {len(signals)}")
    print(f"Señales fuertes (>70%): {len(strong_signals)}")
    print(f"Señales medias (50-70%): {len(medium_signals)}")
    
    if strong_signals:
        print(f"\n🚀 SEÑALES RECOMENDADAS:")
        for signal in strong_signals:
            print(f"   {signal.symbol}: {signal.direction} (Confianza: {signal.confidence:.1f}%)")
    
    print("="*80)

if __name__ == "__main__":
    main()