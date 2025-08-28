"""
📊 DETECTOR AVANZADO DE PATRONES CHARTISTAS
Detecta Head & Shoulders, Triángulos, Banderas, Doble Techo/Piso, etc.
"""
import numpy as np
import pandas as pd
from scipy.signal import find_peaks
from scipy import stats
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class AdvancedPatternDetector:
    """
    Detecta patrones técnicos complejos usando algoritmos matemáticos
    """
    
    def __init__(self, sensitivity: float = 0.7):
        """
        Args:
            sensitivity: 0-1, mayor = más sensible pero más falsas señales
        """
        self.sensitivity = sensitivity
        self.detected_patterns = []
        
    def detect_all_patterns(self, df: pd.DataFrame) -> List[Dict]:
        """
        Detecta todos los patrones posibles en los datos
        
        Returns:
            Lista de patrones detectados con su información
        """
        patterns = []
        
        # Ejecutar todos los detectores
        detectors = [
            self.detect_head_and_shoulders,
            self.detect_double_top_bottom,
            self.detect_triangle_patterns,
            self.detect_flag_pennant,
            self.detect_wedge_pattern,
            self.detect_channel_pattern,
            self.detect_gap_patterns
        ]
        
        for detector in detectors:
            try:
                pattern = detector(df)
                if pattern:
                    patterns.append(pattern)
            except Exception as e:
                logger.error(f"Error en detector {detector.__name__}: {e}")
        
        return patterns
    
    def detect_head_and_shoulders(self, df: pd.DataFrame, window: int = 50) -> Optional[Dict]:
        """
        Detecta patrón Head & Shoulders (normal o invertido)
        
        Estructura:
             Cabeza
               /\
              /  \
        Hombro    Hombro
          /\        /\
         /  \      /  \
        ----------------  ← Línea de cuello
        """
        
        if len(df) < window:
            return None
        
        try:
            prices = df['close'].values[-window:]
            highs = df['high'].values[-window:]
            lows = df['low'].values[-window:]
            
            # Encontrar picos y valles
            peaks, peak_props = find_peaks(highs, distance=5, prominence=prices.mean()*0.001)
            valleys, valley_props = find_peaks(-lows, distance=5, prominence=prices.mean()*0.001)
            
            # Necesitamos al menos 3 picos y 2 valles
            if len(peaks) >= 3 and len(valleys) >= 2:
                
                # Tomar los últimos 3 picos
                last_peaks = peaks[-3:]
                peak_prices = highs[last_peaks]
                
                # Verificar estructura H&S
                left_shoulder = peak_prices[0]
                head = peak_prices[1]
                right_shoulder = peak_prices[2]
                
                # La cabeza debe ser el pico más alto
                if head > left_shoulder and head > right_shoulder:
                    
                    # Los hombros deben ser similares (tolerancia según sensibilidad)
                    shoulder_diff = abs(left_shoulder - right_shoulder)
                    avg_shoulder = (left_shoulder + right_shoulder) / 2
                    tolerance = 0.02 * (2 - self.sensitivity)  # 1-3% tolerancia
                    
                    if shoulder_diff / avg_shoulder < tolerance:
                        
                        # Calcular línea de cuello (neckline)
                        last_valleys = valleys[-2:]
                        neckline_points = lows[last_valleys]
                        neckline = np.mean(neckline_points)
                        
                        # Verificar si el precio rompió la línea de cuello
                        current_price = df['close'].iloc[-1]
                        pattern_height = head - neckline
                        
                        if current_price < neckline:
                            # Patrón confirmado con ruptura
                            target = neckline - pattern_height  # Proyección
                            
                            return {
                                'pattern': 'HEAD_AND_SHOULDERS',
                                'type': 'BEARISH',
                                'confidence': 0.85,
                                'neckline': neckline,
                                'target': target,
                                'stop_loss': head,
                                'current_price': current_price,
                                'message': f"H&S confirmado - Objetivo: {target:.2f}",
                                'data': {
                                    'left_shoulder': left_shoulder,
                                    'head': head,
                                    'right_shoulder': right_shoulder,
                                    'pattern_height': pattern_height
                                }
                            }
                
                # Verificar H&S invertido
                elif head < left_shoulder and head < right_shoulder:
                    
                    shoulder_diff = abs(left_shoulder - right_shoulder)
                    avg_shoulder = (left_shoulder + right_shoulder) / 2
                    tolerance = 0.02 * (2 - self.sensitivity)
                    
                    if shoulder_diff / avg_shoulder < tolerance:
                        
                        last_valleys = peaks[-2:]  # Usar picos como "valles" invertidos
                        neckline_points = highs[last_valleys]
                        neckline = np.mean(neckline_points)
                        
                        current_price = df['close'].iloc[-1]
                        pattern_height = neckline - head
                        
                        if current_price > neckline:
                            target = neckline + pattern_height
                            
                            return {
                                'pattern': 'INVERSE_HEAD_AND_SHOULDERS',
                                'type': 'BULLISH',
                                'confidence': 0.85,
                                'neckline': neckline,
                                'target': target,
                                'stop_loss': head,
                                'current_price': current_price,
                                'message': f"H&S invertido - Objetivo: {target:.2f}"
                            }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detectando H&S: {e}")
            return None
    
    def detect_double_top_bottom(self, df: pd.DataFrame, window: int = 30) -> Optional[Dict]:
        """
        Detecta doble techo o doble piso
        """
        
        if len(df) < window:
            return None
        
        try:
            highs = df['high'].values[-window:]
            lows = df['low'].values[-window:]
            closes = df['close'].values[-window:]
            
            # Buscar picos para doble techo
            peaks, _ = find_peaks(highs, distance=5)
            
            if len(peaks) >= 2:
                last_two_peaks = peaks[-2:]
                peak1_price = highs[last_two_peaks[0]]
                peak2_price = highs[last_two_peaks[1]]
                
                # Verificar si los picos son similares
                peak_diff = abs(peak1_price - peak2_price)
                avg_peak = (peak1_price + peak2_price) / 2
                
                if peak_diff / avg_peak < 0.01 * (2 - self.sensitivity):  # <1% diferencia
                    
                    # Encontrar el valle entre los picos
                    valley_region = lows[last_two_peaks[0]:last_two_peaks[1]]
                    if len(valley_region) > 0:
                        support = np.min(valley_region)
                        current_price = closes[-1]
                        
                        # Verificar ruptura
                        if current_price < support:
                            pattern_height = avg_peak - support
                            target = support - pattern_height
                            
                            return {
                                'pattern': 'DOUBLE_TOP',
                                'type': 'BEARISH',
                                'confidence': 0.80,
                                'resistance': avg_peak,
                                'support': support,
                                'target': target,
                                'current_price': current_price,
                                'message': f"Doble techo confirmado en {avg_peak:.2f}"
                            }
            
            # Buscar valles para doble piso
            valleys, _ = find_peaks(-lows, distance=5)
            
            if len(valleys) >= 2:
                last_two_valleys = valleys[-2:]
                valley1_price = lows[last_two_valleys[0]]
                valley2_price = lows[last_two_valleys[1]]
                
                valley_diff = abs(valley1_price - valley2_price)
                avg_valley = (valley1_price + valley2_price) / 2
                
                if valley_diff / avg_valley < 0.01 * (2 - self.sensitivity):
                    
                    # Encontrar el pico entre los valles
                    peak_region = highs[last_two_valleys[0]:last_two_valleys[1]]
                    if len(peak_region) > 0:
                        resistance = np.max(peak_region)
                        current_price = closes[-1]
                        
                        if current_price > resistance:
                            pattern_height = resistance - avg_valley
                            target = resistance + pattern_height
                            
                            return {
                                'pattern': 'DOUBLE_BOTTOM',
                                'type': 'BULLISH',
                                'confidence': 0.80,
                                'support': avg_valley,
                                'resistance': resistance,
                                'target': target,
                                'current_price': current_price,
                                'message': f"Doble piso confirmado en {avg_valley:.2f}"
                            }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detectando doble techo/piso: {e}")
            return None
    
    def detect_triangle_patterns(self, df: pd.DataFrame, window: int = 30) -> Optional[Dict]:
        """
        Detecta triángulos: ascendente, descendente, simétrico
        """
        
        if len(df) < window:
            return None
        
        try:
            highs = df['high'].values[-window:]
            lows = df['low'].values[-window:]
            closes = df['close'].values[-window:]
            
            # Crear índices para regresión
            x = np.arange(len(highs))
            
            # Calcular líneas de tendencia
            high_slope, high_intercept, _, _, _ = stats.linregress(x, highs)
            low_slope, low_intercept, _, _, _ = stats.linregress(x, lows)
            
            # Calcular líneas proyectadas
            high_line = high_slope * x + high_intercept
            low_line = low_slope * x + low_intercept
            
            # Tolerancia para considerar una línea horizontal
            horizontal_threshold = 0.00001
            
            current_price = closes[-1]
            
            # Triángulo Ascendente: resistencia plana, soporte ascendente
            if abs(high_slope) < horizontal_threshold and low_slope > horizontal_threshold:
                resistance = np.mean(highs[-5:])
                
                # Verificar si el precio está cerca del vértice
                if (high_line[-1] - low_line[-1]) < (high_line[0] - low_line[0]) * 0.3:
                    
                    pattern_height = resistance - lows[0]
                    target = resistance + pattern_height
                    
                    return {
                        'pattern': 'ASCENDING_TRIANGLE',
                        'type': 'BULLISH',
                        'confidence': 0.75,
                        'resistance': resistance,
                        'breakout_target': target,
                        'current_price': current_price,
                        'message': "Triángulo ascendente - Ruptura esperada al alza"
                    }
            
            # Triángulo Descendente: soporte plano, resistencia descendente
            elif abs(low_slope) < horizontal_threshold and high_slope < -horizontal_threshold:
                support = np.mean(lows[-5:])
                
                if (high_line[-1] - low_line[-1]) < (high_line[0] - low_line[0]) * 0.3:
                    
                    pattern_height = highs[0] - support
                    target = support - pattern_height
                    
                    return {
                        'pattern': 'DESCENDING_TRIANGLE',
                        'type': 'BEARISH',
                        'confidence': 0.75,
                        'support': support,
                        'breakdown_target': target,
                        'current_price': current_price,
                        'message': "Triángulo descendente - Ruptura esperada a la baja"
                    }
            
            # Triángulo Simétrico: ambas líneas convergen
            elif high_slope < -horizontal_threshold and low_slope > horizontal_threshold:
                
                # Calcular punto de convergencia (apex)
                apex_x = (low_intercept - high_intercept) / (high_slope - low_slope)
                
                if 0 < apex_x < len(highs) * 1.5:  # Apex razonable
                    
                    pattern_height = highs[0] - lows[0]
                    
                    # Determinar dirección probable basada en tendencia previa
                    prev_trend = closes[-1] - closes[0]
                    
                    if prev_trend > 0:
                        target = current_price + pattern_height
                        direction = 'NEUTRAL_BULLISH'
                    else:
                        target = current_price - pattern_height
                        direction = 'NEUTRAL_BEARISH'
                    
                    return {
                        'pattern': 'SYMMETRIC_TRIANGLE',
                        'type': direction,
                        'confidence': 0.65,
                        'apex': apex_x,
                        'target': target,
                        'current_price': current_price,
                        'message': f"Triángulo simétrico - Ruptura inminente"
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detectando triángulos: {e}")
            return None
    
    def detect_flag_pennant(self, df: pd.DataFrame, window: int = 20) -> Optional[Dict]:
        """
        Detecta banderas y banderines (patrones de continuación)
        """
        
        if len(df) < window * 2:
            return None
        
        try:
            # Necesitamos el movimiento previo (mástil) y la consolidación (bandera)
            prices = df['close'].values[-(window*2):]
            volumes = df['volume'].values[-(window*2):]
            
            # Dividir en mástil y bandera
            pole_prices = prices[:window]
            flag_prices = prices[window:]
            
            # Calcular el movimiento del mástil
            pole_change = pole_prices[-1] - pole_prices[0]
            pole_change_pct = pole_change / pole_prices[0]
            
            # El mástil debe ser significativo (>2%)
            if abs(pole_change_pct) > 0.02:
                
                # Analizar la consolidación (bandera)
                flag_high = np.max(flag_prices)
                flag_low = np.min(flag_prices)
                flag_range = flag_high - flag_low
                
                # La bandera debe ser estrecha comparada con el mástil
                if flag_range < abs(pole_change) * 0.4:
                    
                    # Calcular pendiente de la bandera
                    x = np.arange(len(flag_prices))
                    flag_slope, _, _, _, _ = stats.linregress(x, flag_prices)
                    
                    # Bandera alcista: mástil alcista, consolidación con ligera pendiente bajista
                    if pole_change > 0 and flag_slope <= 0:
                        
                        target = flag_prices[-1] + abs(pole_change)
                        
                        return {
                            'pattern': 'BULL_FLAG',
                            'type': 'BULLISH',
                            'confidence': 0.70,
                            'pole_height': pole_change,
                            'target': target,
                            'current_price': prices[-1],
                            'message': f"Bandera alcista - Objetivo: {target:.2f}"
                        }
                    
                    # Bandera bajista: mástil bajista, consolidación con ligera pendiente alcista
                    elif pole_change < 0 and flag_slope >= 0:
                        
                        target = flag_prices[-1] - abs(pole_change)
                        
                        return {
                            'pattern': 'BEAR_FLAG',
                            'type': 'BEARISH',
                            'confidence': 0.70,
                            'pole_height': pole_change,
                            'target': target,
                            'current_price': prices[-1],
                            'message': f"Bandera bajista - Objetivo: {target:.2f}"
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detectando bandera/banderín: {e}")
            return None
    
    def detect_wedge_pattern(self, df: pd.DataFrame, window: int = 30) -> Optional[Dict]:
        """
        Detecta cuñas ascendentes y descendentes
        """
        
        if len(df) < window:
            return None
        
        try:
            highs = df['high'].values[-window:]
            lows = df['low'].values[-window:]
            closes = df['close'].values[-window:]
            
            # Calcular líneas de tendencia
            x = np.arange(len(highs))
            high_slope, high_intercept, _, _, _ = stats.linregress(x, highs)
            low_slope, low_intercept, _, _, _ = stats.linregress(x, lows)
            
            # Ambas líneas deben tener pendiente del mismo signo
            if high_slope > 0 and low_slope > 0:
                # Cuña ascendente (bearish)
                if high_slope < low_slope:  # Líneas convergen
                    
                    current_price = closes[-1]
                    support = low_slope * len(lows) + low_intercept
                    target = current_price - (highs[0] - lows[0])
                    
                    return {
                        'pattern': 'RISING_WEDGE',
                        'type': 'BEARISH',
                        'confidence': 0.70,
                        'support': support,
                        'target': target,
                        'current_price': current_price,
                        'message': "Cuña ascendente - Patrón de reversión bajista"
                    }
            
            elif high_slope < 0 and low_slope < 0:
                # Cuña descendente (bullish)
                if abs(high_slope) < abs(low_slope):  # Líneas convergen
                    
                    current_price = closes[-1]
                    resistance = high_slope * len(highs) + high_intercept
                    target = current_price + (highs[0] - lows[0])
                    
                    return {
                        'pattern': 'FALLING_WEDGE',
                        'type': 'BULLISH',
                        'confidence': 0.70,
                        'resistance': resistance,
                        'target': target,
                        'current_price': current_price,
                        'message': "Cuña descendente - Patrón de reversión alcista"
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detectando cuñas: {e}")
            return None
    
    def detect_channel_pattern(self, df: pd.DataFrame, window: int = 40) -> Optional[Dict]:
        """
        Detecta canales de precio (paralelos)
        """
        
        if len(df) < window:
            return None
        
        try:
            highs = df['high'].values[-window:]
            lows = df['low'].values[-window:]
            closes = df['close'].values[-window:]
            
            # Encontrar picos y valles
            peaks, _ = find_peaks(highs, distance=5)
            valleys, _ = find_peaks(-lows, distance=5)
            
            if len(peaks) >= 2 and len(valleys) >= 2:
                # Calcular líneas de tendencia para picos y valles
                peak_x = peaks
                peak_y = highs[peaks]
                valley_x = valleys
                valley_y = lows[valleys]
                
                # Regresión para línea de resistencia (picos)
                res_slope, res_intercept, res_r, _, _ = stats.linregress(peak_x, peak_y)
                
                # Regresión para línea de soporte (valles)
                sup_slope, sup_intercept, sup_r, _, _ = stats.linregress(valley_x, valley_y)
                
                # Verificar si las líneas son paralelas (pendientes similares)
                slope_diff = abs(res_slope - sup_slope)
                avg_slope = (abs(res_slope) + abs(sup_slope)) / 2
                
                if avg_slope > 0:
                    parallelism = slope_diff / avg_slope
                else:
                    parallelism = 0
                
                # Si son suficientemente paralelas y hay buen ajuste
                if parallelism < 0.2 and abs(res_r) > 0.8 and abs(sup_r) > 0.8:
                    
                    current_price = closes[-1]
                    current_x = len(closes) - 1
                    
                    # Proyectar líneas al punto actual
                    resistance = res_slope * current_x + res_intercept
                    support = sup_slope * current_x + sup_intercept
                    channel_width = resistance - support
                    
                    # Determinar posición en el canal
                    position_in_channel = (current_price - support) / channel_width
                    
                    # Determinar tipo de canal
                    if res_slope > 0.00001:
                        channel_type = 'ASCENDING_CHANNEL'
                    elif res_slope < -0.00001:
                        channel_type = 'DESCENDING_CHANNEL'
                    else:
                        channel_type = 'HORIZONTAL_CHANNEL'
                    
                    return {
                        'pattern': channel_type,
                        'type': 'NEUTRAL',
                        'confidence': 0.75,
                        'resistance': resistance,
                        'support': support,
                        'channel_width': channel_width,
                        'position': position_in_channel,
                        'current_price': current_price,
                        'message': f"Canal detectado - Posición: {position_in_channel:.1%}"
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detectando canal: {e}")
            return None
    
    def detect_gap_patterns(self, df: pd.DataFrame) -> Optional[Dict]:
        """
        Detecta gaps (huecos de precio)
        """
        
        if len(df) < 2:
            return None
        
        try:
            # Gap entre el cierre anterior y la apertura actual
            gap = df['open'].iloc[-1] - df['close'].iloc[-2]
            gap_pct = gap / df['close'].iloc[-2]
            
            # Considerar gap significativo si es > 0.5%
            if abs(gap_pct) > 0.005:
                
                current_price = df['close'].iloc[-1]
                gap_filled = False
                
                # Verificar si el gap se ha llenado
                if gap > 0:  # Gap alcista
                    gap_filled = current_price <= df['close'].iloc[-2]
                    gap_type = 'BULLISH_GAP'
                else:  # Gap bajista
                    gap_filled = current_price >= df['close'].iloc[-2]
                    gap_type = 'BEARISH_GAP'
                
                return {
                    'pattern': gap_type,
                    'type': 'BULLISH' if gap > 0 else 'BEARISH',
                    'confidence': 0.60,
                    'gap_size': gap,
                    'gap_percentage': gap_pct,
                    'gap_filled': gap_filled,
                    'current_price': current_price,
                    'message': f"Gap {gap_pct:.1%} {'llenado' if gap_filled else 'sin llenar'}"
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detectando gaps: {e}")
            return None
    
    def calculate_pattern_strength(self, pattern: Dict) -> float:
        """
        Calcula la fuerza de un patrón basándose en varios factores
        """
        
        strength = pattern.get('confidence', 0.5)
        
        # Ajustar por tipo de patrón
        strong_patterns = ['HEAD_AND_SHOULDERS', 'DOUBLE_TOP', 'DOUBLE_BOTTOM']
        medium_patterns = ['TRIANGLE', 'FLAG', 'WEDGE']
        
        if any(p in pattern.get('pattern', '') for p in strong_patterns):
            strength *= 1.2
        elif any(p in pattern.get('pattern', '') for p in medium_patterns):
            strength *= 1.0
        else:
            strength *= 0.8
        
        return min(1.0, strength)