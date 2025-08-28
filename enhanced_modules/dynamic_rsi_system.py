"""
🔄 SISTEMA RSI DINÁMICO AUTO-AJUSTABLE
Se adapta automáticamente a cada símbolo y condiciones del mercado
"""
import numpy as np
import pandas as pd
from collections import deque
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class DynamicRSISystem:
    """
    Sistema RSI que se auto-ajusta según el símbolo y las condiciones del mercado
    """
    
    def __init__(self, symbol: str):
        """
        Args:
            symbol: Símbolo a analizar (XAU, BTC, etc.)
        """
        self.symbol = symbol
        self.rsi_history = {
            '1min': deque(maxlen=1000),
            '5min': deque(maxlen=500),
            '15min': deque(maxlen=500),
            '1h': deque(maxlen=500),
            '4h': deque(maxlen=200),
            '1d': deque(maxlen=100)
        }
        
        # Umbrales dinámicos por temporalidad
        self.dynamic_thresholds = {}
        self.last_threshold_update = None
        
        # Configuración específica por símbolo
        self.symbol_configs = self._get_symbol_config()
        
        # Estadísticas de performance
        self.divergence_history = deque(maxlen=100)
        self.signal_accuracy = {'correct': 0, 'incorrect': 0}
        
        logger.info(f"RSI Dinámico inicializado para {symbol}")
    
    def _get_symbol_config(self) -> Dict:
        """
        Obtiene configuración específica según el símbolo
        """
        
        # Configuraciones predefinidas por tipo de activo
        if 'XAU' in self.symbol or 'GOLD' in self.symbol:
            return {
                'base_oversold': 30,
                'base_overbought': 70,
                'volatility_adjustment': 1.2,
                'trend_following': True,
                'divergence_weight': 0.8,
                'momentum_periods': 14,
                'description': 'Oro - Mayor peso a divergencias'
            }
        
        elif 'BTC' in self.symbol or 'ETH' in self.symbol:
            return {
                'base_oversold': 25,
                'base_overbought': 75,
                'volatility_adjustment': 1.5,
                'trend_following': False,
                'divergence_weight': 0.6,
                'momentum_periods': 12,
                'description': 'Crypto - Umbrales más extremos'
            }
        
        elif 'EUR' in self.symbol or 'GBP' in self.symbol or 'JPY' in self.symbol:
            return {
                'base_oversold': 35,
                'base_overbought': 65,
                'volatility_adjustment': 0.8,
                'trend_following': True,
                'divergence_weight': 0.7,
                'momentum_periods': 14,
                'description': 'Forex - Umbrales conservadores'
            }
        
        elif 'SPX' in self.symbol or 'NDX' in self.symbol:
            return {
                'base_oversold': 30,
                'base_overbought': 70,
                'volatility_adjustment': 1.0,
                'trend_following': True,
                'divergence_weight': 0.75,
                'momentum_periods': 14,
                'description': 'Índices - Configuración estándar'
            }
        
        else:
            # Configuración por defecto
            return {
                'base_oversold': 30,
                'base_overbought': 70,
                'volatility_adjustment': 1.0,
                'trend_following': True,
                'divergence_weight': 0.7,
                'momentum_periods': 14,
                'description': 'Activo genérico'
            }
    
    def calculate_rsi(self, prices: np.ndarray, period: int = None) -> float:
        """
        Calcula RSI con período dinámico
        """
        
        if period is None:
            period = self.symbol_configs['momentum_periods']
        
        if len(prices) < period + 1:
            return 50.0  # Valor neutral si no hay suficientes datos
        
        # Calcular cambios de precio
        deltas = np.diff(prices)
        
        # Separar ganancias y pérdidas
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        # Calcular medias móviles exponenciales
        alpha = 1.0 / period
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        
        for i in range(period, len(gains)):
            avg_gain = avg_gain * (1 - alpha) + gains[i] * alpha
            avg_loss = avg_loss * (1 - alpha) + losses[i] * alpha
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def calculate_adaptive_thresholds(self, timeframe: str = '1h') -> Dict[str, float]:
        """
        Calcula umbrales adaptativos basados en el histórico y condiciones actuales
        """
        
        if timeframe not in self.rsi_history:
            # Usar valores base si no hay histórico
            return {
                'oversold': self.symbol_configs['base_oversold'],
                'overbought': self.symbol_configs['base_overbought'],
                'extreme_oversold': self.symbol_configs['base_oversold'] - 10,
                'extreme_overbought': self.symbol_configs['base_overbought'] + 10
            }
        
        history = list(self.rsi_history[timeframe])
        
        if len(history) < 50:
            # No hay suficiente historia, usar valores base ajustados
            return {
                'oversold': self.symbol_configs['base_oversold'],
                'overbought': self.symbol_configs['base_overbought'],
                'extreme_oversold': self.symbol_configs['base_oversold'] - 10,
                'extreme_overbought': self.symbol_configs['base_overbought'] + 10
            }
        
        # Calcular estadísticas del histórico
        rsi_array = np.array(history)
        
        # Percentiles dinámicos
        p20 = np.percentile(rsi_array, 20)
        p80 = np.percentile(rsi_array, 80)
        p5 = np.percentile(rsi_array, 5)
        p95 = np.percentile(rsi_array, 95)
        
        # Media y desviación estándar
        mean_rsi = np.mean(rsi_array)
        std_rsi = np.std(rsi_array)
        
        # Calcular volatilidad del RSI
        rsi_volatility = std_rsi / mean_rsi if mean_rsi > 0 else 0.2
        
        # Ajustar umbrales basándose en volatilidad
        volatility_adjustment = self.symbol_configs['volatility_adjustment']
        
        if rsi_volatility > 0.25:  # Alta volatilidad
            # Ampliar umbrales
            oversold = max(20, p20 - 5 * volatility_adjustment)
            overbought = min(80, p80 + 5 * volatility_adjustment)
        elif rsi_volatility < 0.15:  # Baja volatilidad
            # Estrechar umbrales
            oversold = min(35, p20 + 3 * volatility_adjustment)
            overbought = max(65, p80 - 3 * volatility_adjustment)
        else:  # Volatilidad normal
            oversold = p20
            overbought = p80
        
        # Verificar sesgo del mercado (tendencia)
        recent_mean = np.mean(rsi_array[-20:])
        
        if recent_mean > 60:  # Sesgo alcista
            # Ajustar umbrales hacia arriba
            oversold = min(oversold + 5, 40)
            overbought = min(overbought + 5, 85)
        elif recent_mean < 40:  # Sesgo bajista
            # Ajustar umbrales hacia abajo
            oversold = max(oversold - 5, 15)
            overbought = max(overbought - 5, 60)
        
        # Calcular umbrales extremos
        extreme_oversold = max(10, p5)
        extreme_overbought = min(90, p95)
        
        # Guardar umbrales calculados
        self.dynamic_thresholds[timeframe] = {
            'oversold': round(oversold, 1),
            'overbought': round(overbought, 1),
            'extreme_oversold': round(extreme_oversold, 1),
            'extreme_overbought': round(extreme_overbought, 1),
            'mean': round(mean_rsi, 1),
            'std': round(std_rsi, 1),
            'volatility': round(rsi_volatility, 3)
        }
        
        logger.debug(f"Umbrales RSI {timeframe}: {self.dynamic_thresholds[timeframe]}")
        
        return self.dynamic_thresholds[timeframe]
    
    def detect_divergence(self, 
                         prices: np.ndarray, 
                         rsi_values: np.ndarray, 
                         window: int = 10) -> Optional[Dict]:
        """
        Detecta divergencias precio-RSI con mayor precisión
        """
        
        if len(prices) < window or len(rsi_values) < window:
            return None
        
        try:
            from scipy.signal import find_peaks
            
            # Obtener ventana de datos
            price_window = prices[-window:]
            rsi_window = rsi_values[-window:]
            
            # Encontrar picos en precio y RSI
            price_peaks, _ = find_peaks(price_window, distance=2)
            rsi_peaks, _ = find_peaks(rsi_window, distance=2)
            
            # Encontrar valles
            price_valleys, _ = find_peaks(-price_window, distance=2)
            rsi_valleys, _ = find_peaks(-rsi_window, distance=2)
            
            # DIVERGENCIA BAJISTA: precio hace nuevo máximo, RSI no
            if len(price_peaks) >= 2 and len(rsi_peaks) >= 2:
                
                # Últimos dos picos
                price_peak1 = price_window[price_peaks[-2]]
                price_peak2 = price_window[price_peaks[-1]]
                rsi_peak1 = rsi_window[rsi_peaks[-2]]
                rsi_peak2 = rsi_window[rsi_peaks[-1]]
                
                # Precio hace nuevo máximo pero RSI no
                if price_peak2 > price_peak1 and rsi_peak2 < rsi_peak1:
                    
                    divergence_strength = abs(rsi_peak1 - rsi_peak2)
                    confidence = min(0.9, 0.5 + divergence_strength / 20)
                    
                    return {
                        'type': 'BEARISH_DIVERGENCE',
                        'pattern': 'REGULAR',
                        'strength': divergence_strength,
                        'confidence': confidence,
                        'price_peaks': [price_peak1, price_peak2],
                        'rsi_peaks': [rsi_peak1, rsi_peak2],
                        'message': f"Divergencia bajista: RSI cae {divergence_strength:.1f} puntos",
                        'action': 'CONSIDER_SHORT'
                    }
                
                # DIVERGENCIA BAJISTA OCULTA: precio hace menor máximo, RSI hace mayor máximo
                elif price_peak2 < price_peak1 and rsi_peak2 > rsi_peak1:
                    
                    divergence_strength = abs(rsi_peak2 - rsi_peak1)
                    confidence = min(0.8, 0.4 + divergence_strength / 20)
                    
                    return {
                        'type': 'BEARISH_DIVERGENCE',
                        'pattern': 'HIDDEN',
                        'strength': divergence_strength,
                        'confidence': confidence,
                        'message': "Divergencia bajista oculta detectada",
                        'action': 'CONTINUATION_DOWN'
                    }
            
            # DIVERGENCIA ALCISTA: precio hace nuevo mínimo, RSI no
            if len(price_valleys) >= 2 and len(rsi_valleys) >= 2:
                
                price_valley1 = price_window[price_valleys[-2]]
                price_valley2 = price_window[price_valleys[-1]]
                rsi_valley1 = rsi_window[rsi_valleys[-2]]
                rsi_valley2 = rsi_window[rsi_valleys[-1]]
                
                # Precio hace nuevo mínimo pero RSI no
                if price_valley2 < price_valley1 and rsi_valley2 > rsi_valley1:
                    
                    divergence_strength = abs(rsi_valley2 - rsi_valley1)
                    confidence = min(0.9, 0.5 + divergence_strength / 20)
                    
                    return {
                        'type': 'BULLISH_DIVERGENCE',
                        'pattern': 'REGULAR',
                        'strength': divergence_strength,
                        'confidence': confidence,
                        'price_valleys': [price_valley1, price_valley2],
                        'rsi_valleys': [rsi_valley1, rsi_valley2],
                        'message': f"Divergencia alcista: RSI sube {divergence_strength:.1f} puntos",
                        'action': 'CONSIDER_LONG'
                    }
                
                # DIVERGENCIA ALCISTA OCULTA
                elif price_valley2 > price_valley1 and rsi_valley2 < rsi_valley1:
                    
                    divergence_strength = abs(rsi_valley1 - rsi_valley2)
                    confidence = min(0.8, 0.4 + divergence_strength / 20)
                    
                    return {
                        'type': 'BULLISH_DIVERGENCE',
                        'pattern': 'HIDDEN',
                        'strength': divergence_strength,
                        'confidence': confidence,
                        'message': "Divergencia alcista oculta detectada",
                        'action': 'CONTINUATION_UP'
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error detectando divergencia: {e}")
            return None
    
    def analyze_multi_timeframe_rsi(self, data_dict: Dict[str, pd.DataFrame]) -> Dict:
        """
        Analiza RSI en múltiples temporalidades y genera señal consolidada
        """
        
        results = {
            'timeframes': {},
            'consensus': None,
            'divergences': [],
            'alerts': []
        }
        
        # Analizar cada temporalidad
        for timeframe, df in data_dict.items():
            if df is not None and len(df) > 14:
                
                # Calcular RSI
                prices = df['close'].values
                rsi = self.calculate_rsi(prices)
                
                # Actualizar histórico
                if timeframe in self.rsi_history:
                    self.rsi_history[timeframe].append(rsi)
                
                # Obtener umbrales adaptativos
                thresholds = self.calculate_adaptive_thresholds(timeframe)
                
                # Determinar condición
                condition = 'NEUTRAL'
                if rsi < thresholds['extreme_oversold']:
                    condition = 'EXTREME_OVERSOLD'
                elif rsi < thresholds['oversold']:
                    condition = 'OVERSOLD'
                elif rsi > thresholds['extreme_overbought']:
                    condition = 'EXTREME_OVERBOUGHT'
                elif rsi > thresholds['overbought']:
                    condition = 'OVERBOUGHT'
                
                # Buscar divergencias
                if len(self.rsi_history[timeframe]) >= 10:
                    rsi_array = np.array(list(self.rsi_history[timeframe])[-10:])
                    divergence = self.detect_divergence(prices[-10:], rsi_array)
                    if divergence:
                        divergence['timeframe'] = timeframe
                        results['divergences'].append(divergence)
                
                # Guardar resultado
                results['timeframes'][timeframe] = {
                    'rsi': rsi,
                    'condition': condition,
                    'thresholds': thresholds,
                    'trend': 'UP' if rsi > 50 else 'DOWN'
                }
        
        # Generar consenso
        results['consensus'] = self._generate_consensus(results['timeframes'])
        
        # Generar alertas si hay condiciones críticas
        results['alerts'] = self._check_critical_conditions(results)
        
        return results
    
    def _generate_consensus(self, timeframe_data: Dict) -> Dict:
        """
        Genera señal de consenso ponderada
        """
        
        if not timeframe_data:
            return {'signal': 'NEUTRAL', 'strength': 0}
        
        # Pesos por temporalidad
        weights = {
            '1min': 0.05,
            '5min': 0.10,
            '15min': 0.15,
            '1h': 0.25,
            '4h': 0.30,
            '1d': 0.15
        }
        
        bullish_score = 0
        bearish_score = 0
        total_weight = 0
        
        for tf, data in timeframe_data.items():
            weight = weights.get(tf, 0.1)
            total_weight += weight
            
            condition = data['condition']
            
            if 'OVERSOLD' in condition:
                bullish_score += weight * (2 if 'EXTREME' in condition else 1)
            elif 'OVERBOUGHT' in condition:
                bearish_score += weight * (2 if 'EXTREME' in condition else 1)
        
        if total_weight == 0:
            return {'signal': 'NEUTRAL', 'strength': 0}
        
        # Normalizar scores
        bullish_score /= total_weight
        bearish_score /= total_weight
        
        # Determinar señal
        if bullish_score > bearish_score * 1.2:
            return {
                'signal': 'BULLISH',
                'strength': bullish_score,
                'confidence': min(0.9, bullish_score / 2)
            }
        elif bearish_score > bullish_score * 1.2:
            return {
                'signal': 'BEARISH',
                'strength': bearish_score,
                'confidence': min(0.9, bearish_score / 2)
            }
        else:
            return {
                'signal': 'NEUTRAL',
                'strength': 0,
                'confidence': 0
            }
    
    def _check_critical_conditions(self, results: Dict) -> List[Dict]:
        """
        Verifica condiciones críticas que requieren alerta inmediata
        """
        
        alerts = []
        
        # Verificar divergencias fuertes
        for div in results.get('divergences', []):
            if div['confidence'] > 0.8:
                alerts.append({
                    'type': 'RSI_DIVERGENCE_ALERT',
                    'severity': 'HIGH',
                    'message': div['message'],
                    'action': div['action']
                })
        
        # Verificar condiciones extremas en múltiples timeframes
        extreme_count = 0
        for tf, data in results.get('timeframes', {}).items():
            if 'EXTREME' in data.get('condition', ''):
                extreme_count += 1
        
        if extreme_count >= 2:
            alerts.append({
                'type': 'MULTIPLE_EXTREME_RSI',
                'severity': 'HIGH',
                'message': f"RSI extremo en {extreme_count} temporalidades",
                'action': 'PREPARE_REVERSAL'
            })
        
        return alerts
    
    def get_symbol_recommendation(self) -> str:
        """
        Obtiene recomendación basada en el tipo de símbolo
        """
        
        return self.symbol_configs.get('description', 'Configuración estándar')