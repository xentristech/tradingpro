#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GENERADOR AVANZADO DE SEÑALES
============================
Sistema mejorado de análisis técnico con múltiples indicadores
- RSI, MACD, Bollinger Bands, SMA, EMA
- Análisis de tendencia
- Scoring avanzado
- Confluencias técnicas
"""

import requests
import time
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(message)s')
logger = logging.getLogger(__name__)

class AdvancedSignalGenerator:
    """Generador avanzado de señales con múltiples indicadores"""
    
    def __init__(self):
        self.api_key = '23d17ce5b7044ad5aef9766770a6252b'
        self.base_url = 'https://api.twelvedata.com'
        
        # Símbolos
        self.symbols = {
            'XAUUSDm': 'XAU/USD',
            'EURUSD': 'EUR/USD',
            'GBPUSD': 'GBP/USD',
            'BTCUSD': 'BTC/USD'
        }
        
        logger.info("Generador de señales avanzado inicializado")
    
    def get_multiple_indicators(self, symbol: str) -> Dict:
        """Obtiene múltiples indicadores técnicos"""
        try:
            mapped_symbol = self.symbols.get(symbol, symbol)
            indicators = {}
            
            # Lista de indicadores esenciales
            indicator_configs = [
                ('rsi', {'time_period': 14}),
                ('rsi', {'time_period': 21}, 'rsi_21'),
                ('macd', {'fast_period': 12, 'slow_period': 26, 'signal_period': 9}),
                ('bbands', {'time_period': 20, 'series_type': 'close'}),
                ('sma', {'time_period': 20}),
                ('sma', {'time_period': 50}, 'sma_50'),
                ('ema', {'time_period': 12}),
                ('ema', {'time_period': 26}, 'ema_26'),
                ('stoch', {'k_period': 14, 'd_period': 3}),
                ('williams', {'time_period': 14}),
                ('cci', {'time_period': 20}),
                ('atr', {'time_period': 14})
            ]
            
            for config in indicator_configs:
                if len(config) == 2:
                    indicator_name, params = config
                    key = indicator_name
                else:
                    indicator_name, params, key = config
                
                try:
                    url = f"{self.base_url}/{indicator_name}"
                    request_params = {
                        'symbol': mapped_symbol,
                        'interval': '30min',
                        'outputsize': 10,
                        'apikey': self.api_key,
                        **params
                    }
                    
                    response = requests.get(url, params=request_params, timeout=8)
                    
                    if response.status_code == 200:
                        data = response.json()
                        if 'values' in data and data['values']:
                            indicators[key] = data['values']
                    
                    time.sleep(0.2)  # Respetar rate limit
                    
                except Exception as e:
                    logger.warning(f"Error obteniendo {indicator_name}: {e}")
                    continue
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error obteniendo indicadores para {symbol}: {e}")
            return {}
    
    def get_price_data(self, symbol: str) -> Optional[List]:
        """Obtiene datos de precios recientes"""
        try:
            mapped_symbol = self.symbols.get(symbol, symbol)
            
            url = f"{self.base_url}/time_series"
            params = {
                'symbol': mapped_symbol,
                'interval': '30min',
                'outputsize': 20,
                'apikey': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'values' in data:
                    return data['values']
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo precios {symbol}: {e}")
            return None
    
    def analyze_rsi_signals(self, indicators: Dict) -> Tuple[float, List[str]]:
        """Analiza señales RSI"""
        score = 0
        reasons = []
        
        try:
            # RSI 14
            if 'rsi' in indicators and indicators['rsi']:
                rsi = float(indicators['rsi'][0]['rsi'])
                
                if rsi < 25:
                    score += 25
                    reasons.append(f"RSI(14) sobreventa extrema: {rsi:.1f}")
                elif rsi < 35:
                    score += 15
                    reasons.append(f"RSI(14) sobreventa: {rsi:.1f}")
                elif rsi > 75:
                    score -= 25
                    reasons.append(f"RSI(14) sobrecompra extrema: {rsi:.1f}")
                elif rsi > 65:
                    score -= 15
                    reasons.append(f"RSI(14) sobrecompra: {rsi:.1f}")
                elif 45 <= rsi <= 55:
                    score += 5
                    reasons.append("RSI(14) neutro")
            
            # RSI 21 para confirmación
            if 'rsi_21' in indicators and indicators['rsi_21']:
                rsi_21 = float(indicators['rsi_21'][0]['rsi'])
                
                if 'rsi' in indicators:
                    rsi_14 = float(indicators['rsi'][0]['rsi'])
                    
                    # Confluencia RSI
                    if rsi_14 < 35 and rsi_21 < 40:
                        score += 10
                        reasons.append("Confluencia RSI alcista")
                    elif rsi_14 > 65 and rsi_21 > 60:
                        score -= 10
                        reasons.append("Confluencia RSI bajista")
        
        except Exception as e:
            logger.warning(f"Error analizando RSI: {e}")
        
        return score, reasons
    
    def analyze_macd_signals(self, indicators: Dict) -> Tuple[float, List[str]]:
        """Analiza señales MACD"""
        score = 0
        reasons = []
        
        try:
            if 'macd' in indicators and len(indicators['macd']) >= 2:
                current = indicators['macd'][0]
                previous = indicators['macd'][1]
                
                macd_current = float(current['macd'])
                signal_current = float(current['macd_signal'])
                hist_current = float(current['macd_hist'])
                
                macd_prev = float(previous['macd'])
                signal_prev = float(previous['macd_signal'])
                hist_prev = float(previous['macd_hist'])
                
                # Cruce MACD
                if macd_prev <= signal_prev and macd_current > signal_current:
                    score += 20
                    reasons.append("MACD cruce alcista")
                elif macd_prev >= signal_prev and macd_current < signal_current:
                    score -= 20
                    reasons.append("MACD cruce bajista")
                
                # Histograma MACD
                if hist_prev < 0 and hist_current > 0:
                    score += 15
                    reasons.append("Histograma MACD positivo")
                elif hist_prev > 0 and hist_current < 0:
                    score -= 15
                    reasons.append("Histograma MACD negativo")
                
                # MACD por encima/debajo de cero
                if macd_current > 0 and macd_current > signal_current:
                    score += 10
                    reasons.append("MACD alcista fuerte")
                elif macd_current < 0 and macd_current < signal_current:
                    score -= 10
                    reasons.append("MACD bajista fuerte")
        
        except Exception as e:
            logger.warning(f"Error analizando MACD: {e}")
        
        return score, reasons
    
    def analyze_bollinger_bands(self, indicators: Dict, price_data: List) -> Tuple[float, List[str]]:
        """Analiza señales Bollinger Bands"""
        score = 0
        reasons = []
        
        try:
            if 'bbands' in indicators and indicators['bbands'] and price_data:
                bb = indicators['bbands'][0]
                current_price = float(price_data[0]['close'])
                
                upper = float(bb['upper_band'])
                middle = float(bb['middle_band'])
                lower = float(bb['lower_band'])
                
                # Posición respecto a las bandas
                if current_price <= lower:
                    score += 20
                    reasons.append("Precio en banda inferior BB")
                elif current_price <= lower * 1.005:
                    score += 15
                    reasons.append("Precio cerca banda inferior BB")
                elif current_price >= upper:
                    score -= 20
                    reasons.append("Precio en banda superior BB")
                elif current_price >= upper * 0.995:
                    score -= 15
                    reasons.append("Precio cerca banda superior BB")
                
                # Squeeze detection
                band_width = (upper - lower) / middle
                if band_width < 0.02:  # Ajustar según símbolo
                    score += 5
                    reasons.append("Bollinger Bands squeeze")
        
        except Exception as e:
            logger.warning(f"Error analizando BB: {e}")
        
        return score, reasons
    
    def analyze_moving_averages(self, indicators: Dict, price_data: List) -> Tuple[float, List[str]]:
        """Analiza señales de medias móviles"""
        score = 0
        reasons = []
        
        try:
            if price_data and len(price_data) >= 2:
                current_price = float(price_data[0]['close'])
                
                # SMA 20 vs precio
                if 'sma' in indicators and indicators['sma']:
                    sma_20 = float(indicators['sma'][0]['sma'])
                    
                    if current_price > sma_20:
                        score += 10
                        reasons.append("Precio sobre SMA(20)")
                    else:
                        score -= 10
                        reasons.append("Precio bajo SMA(20)")
                    
                    # Pendiente SMA
                    if len(indicators['sma']) >= 2:
                        sma_prev = float(indicators['sma'][1]['sma'])
                        if sma_20 > sma_prev:
                            score += 5
                            reasons.append("SMA(20) ascendente")
                        else:
                            score -= 5
                            reasons.append("SMA(20) descendente")
                
                # SMA 50 vs SMA 20
                if 'sma' in indicators and 'sma_50' in indicators:
                    if indicators['sma'] and indicators['sma_50']:
                        sma_20 = float(indicators['sma'][0]['sma'])
                        sma_50 = float(indicators['sma_50'][0]['sma'])
                        
                        if sma_20 > sma_50:
                            score += 8
                            reasons.append("SMA(20) > SMA(50)")
                        else:
                            score -= 8
                            reasons.append("SMA(20) < SMA(50)")
                
                # EMA crossover
                if 'ema' in indicators and 'ema_26' in indicators:
                    if indicators['ema'] and indicators['ema_26']:
                        ema_12 = float(indicators['ema'][0]['ema'])
                        ema_26 = float(indicators['ema_26'][0]['ema'])
                        
                        if ema_12 > ema_26:
                            score += 10
                            reasons.append("EMA(12) > EMA(26)")
                        else:
                            score -= 10
                            reasons.append("EMA(12) < EMA(26)")
        
        except Exception as e:
            logger.warning(f"Error analizando MAs: {e}")
        
        return score, reasons
    
    def analyze_momentum_oscillators(self, indicators: Dict) -> Tuple[float, List[str]]:
        """Analiza osciladores de momentum"""
        score = 0
        reasons = []
        
        try:
            # Stochastic
            if 'stoch' in indicators and indicators['stoch']:
                stoch_k = float(indicators['stoch'][0]['k_percent'])
                stoch_d = float(indicators['stoch'][0]['d_percent'])
                
                if stoch_k < 20 and stoch_d < 20:
                    score += 15
                    reasons.append(f"Stoch sobreventa: K={stoch_k:.1f}")
                elif stoch_k > 80 and stoch_d > 80:
                    score -= 15
                    reasons.append(f"Stoch sobrecompra: K={stoch_k:.1f}")
                
                # Cruce Stoch
                if len(indicators['stoch']) >= 2:
                    prev_k = float(indicators['stoch'][1]['k_percent'])
                    prev_d = float(indicators['stoch'][1]['d_percent'])
                    
                    if prev_k <= prev_d and stoch_k > stoch_d and stoch_k < 50:
                        score += 12
                        reasons.append("Stoch cruce alcista")
                    elif prev_k >= prev_d and stoch_k < stoch_d and stoch_k > 50:
                        score -= 12
                        reasons.append("Stoch cruce bajista")
            
            # Williams %R
            if 'williams' in indicators and indicators['williams']:
                williams = float(indicators['williams'][0]['williams_r'])
                
                if williams < -80:
                    score += 12
                    reasons.append(f"Williams %R sobreventa: {williams:.1f}")
                elif williams > -20:
                    score -= 12
                    reasons.append(f"Williams %R sobrecompra: {williams:.1f}")
            
            # CCI
            if 'cci' in indicators and indicators['cci']:
                cci = float(indicators['cci'][0]['cci'])
                
                if cci < -150:
                    score += 10
                    reasons.append(f"CCI sobreventa extrema: {cci:.1f}")
                elif cci < -100:
                    score += 8
                    reasons.append(f"CCI sobreventa: {cci:.1f}")
                elif cci > 150:
                    score -= 10
                    reasons.append(f"CCI sobrecompra extrema: {cci:.1f}")
                elif cci > 100:
                    score -= 8
                    reasons.append(f"CCI sobrecompra: {cci:.1f}")
        
        except Exception as e:
            logger.warning(f"Error analizando osciladores: {e}")
        
        return score, reasons
    
    def generate_advanced_signal(self, symbol: str) -> Tuple[str, float, List[str], Dict]:
        """Genera señal avanzada con análisis completo"""
        try:
            logger.info(f"\n[{symbol}] Generando señal avanzada...")
            
            # Obtener datos
            indicators = self.get_multiple_indicators(symbol)
            price_data = self.get_price_data(symbol)
            
            if not indicators or not price_data:
                return 'NEUTRAL', 0.0, ['Sin datos suficientes'], {}
            
            # Análisis por componentes
            total_score = 0
            all_reasons = []
            
            # 1. RSI Analysis
            rsi_score, rsi_reasons = self.analyze_rsi_signals(indicators)
            total_score += rsi_score
            all_reasons.extend(rsi_reasons)
            
            # 2. MACD Analysis  
            macd_score, macd_reasons = self.analyze_macd_signals(indicators)
            total_score += macd_score
            all_reasons.extend(macd_reasons)
            
            # 3. Bollinger Bands
            bb_score, bb_reasons = self.analyze_bollinger_bands(indicators, price_data)
            total_score += bb_score
            all_reasons.extend(bb_reasons)
            
            # 4. Moving Averages
            ma_score, ma_reasons = self.analyze_moving_averages(indicators, price_data)
            total_score += ma_score
            all_reasons.extend(ma_reasons)
            
            # 5. Momentum Oscillators
            momentum_score, momentum_reasons = self.analyze_momentum_oscillators(indicators)
            total_score += momentum_score
            all_reasons.extend(momentum_reasons)
            
            # Determinar dirección y confianza
            if total_score >= 30:
                direction = 'BUY'
                confidence = min(total_score * 1.5, 100)
            elif total_score <= -30:
                direction = 'SELL'  
                confidence = min(abs(total_score) * 1.5, 100)
            elif total_score >= 15:
                direction = 'BUY'
                confidence = min(total_score * 2, 85)
            elif total_score <= -15:
                direction = 'SELL'
                confidence = min(abs(total_score) * 2, 85)
            else:
                direction = 'NEUTRAL'
                confidence = 0
            
            # Metadata del análisis
            analysis_meta = {
                'total_score': total_score,
                'rsi_score': rsi_score,
                'macd_score': macd_score,
                'bb_score': bb_score,
                'ma_score': ma_score,
                'momentum_score': momentum_score,
                'indicators_count': len(indicators),
                'timestamp': datetime.now().strftime('%H:%M:%S')
            }
            
            logger.info(f"[{symbol}] SEÑAL: {direction} ({confidence:.1f}%) | Score: {total_score}")
            logger.info(f"[{symbol}] Componentes: RSI={rsi_score}, MACD={macd_score}, BB={bb_score}, MA={ma_score}, MOM={momentum_score}")
            
            return direction, confidence, all_reasons[:5], analysis_meta  # Top 5 reasons
            
        except Exception as e:
            logger.error(f"Error generando señal para {symbol}: {e}")
            return 'NEUTRAL', 0.0, [f'Error: {str(e)}'], {}

def test_signal_generator():
    """Prueba el generador de señales"""
    generator = AdvancedSignalGenerator()
    
    print("="*70)
    print("    PRUEBA GENERADOR AVANZADO DE SEÑALES")
    print("="*70)
    
    for symbol in generator.symbols.keys():
        direction, confidence, reasons, meta = generator.generate_advanced_signal(symbol)
        
        print(f"\n{symbol}:")
        print(f"  SEÑAL: {direction} ({confidence:.1f}%)")
        print(f"  Score total: {meta.get('total_score', 0)}")
        print(f"  Indicadores analizados: {meta.get('indicators_count', 0)}")
        print(f"  Principales razones:")
        for i, reason in enumerate(reasons[:3], 1):
            print(f"    {i}. {reason}")
        
        time.sleep(2)

if __name__ == "__main__":
    test_signal_generator()