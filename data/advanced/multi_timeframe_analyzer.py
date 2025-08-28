"""
Análisis Multi-Temporal Profesional
Implementa la estrategia que usamos para detectar la divergencia
Author: XentrisTech
Version: 2.0
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class TimeframeSignal:
    """Señal por temporalidad"""
    timeframe: str
    direction: str  # 'BULLISH', 'BEARISH', 'NEUTRAL'
    strength: float  # 0-100
    rsi: float
    macd_signal: float
    volume_ratio: float
    key_levels: List[float]
    trend_quality: float  # Calidad de la tendencia 0-100

class MultiTimeframeAnalyzer:
    """
    Análisis profesional multi-temporal
    """
    
    # Mapeo de timeframes de TwelveData a nombres estándar
    TIMEFRAME_MAPPING = {
        '1min': '1min',
        '5min': '5min', 
        '15min': '15min',
        '30min': '30min',
        '1h': '1h',
        '2h': '2h',
        '4h': '4h',
        '1day': '1d',
        '1week': '1week',
        '1month': '1month'
    }
    
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.configure_weights(symbol)
        
    def configure_weights(self, symbol: str):
        """Configura pesos según el activo"""
        if 'XAU' in symbol or 'GOLD' in symbol:
            # Oro - más peso a temporalidades medianas
            self.timeframe_weights = {
                '1min': 0.02,
                '5min': 0.08,
                '15min': 0.15,
                '30min': 0.15,
                '1h': 0.25,
                '4h': 0.20,
                '1d': 0.10,
                '1week': 0.05,
                '1month': 0.00  # Solo contexto
            }
        elif 'BTC' in symbol or 'ETH' in symbol:
            # Crypto - más peso a corto plazo por volatilidad
            self.timeframe_weights = {
                '1min': 0.05,
                '5min': 0.15,
                '15min': 0.20,
                '30min': 0.20,
                '1h': 0.20,
                '4h': 0.10,
                '1d': 0.08,
                '1week': 0.02,
                '1month': 0.00
            }
        else:
            # Default forex
            self.timeframe_weights = {
                '1min': 0.05,
                '5min': 0.10,
                '15min': 0.15,
                '30min': 0.15,
                '1h': 0.20,
                '4h': 0.20,
                '1d': 0.10,
                '1week': 0.05,
                '1month': 0.00
            }
    
    def analyze_all_timeframes(self, 
                              data_dict: Dict[str, pd.DataFrame]) -> Dict[str, TimeframeSignal]:
        """
        Analiza todas las temporalidades disponibles
        """
        signals = {}
        
        for tf_raw, df in data_dict.items():
            if df is not None and not df.empty and len(df) >= 20:
                # Mapear timeframe
                tf = self.TIMEFRAME_MAPPING.get(tf_raw, tf_raw)
                
                try:
                    signal = self._analyze_timeframe(tf, df)
                    signals[tf] = signal
                    logger.debug(f"Señal {tf}: {signal.direction} ({signal.strength:.1f}%)")
                except Exception as e:
                    logger.error(f"Error analizando {tf}: {e}")
                    
        return signals
    
    def _analyze_timeframe(self, timeframe: str, df: pd.DataFrame) -> TimeframeSignal:
        """
        Analiza una temporalidad específica
        """
        # Calcular indicadores si no existen
        if 'rsi' not in df.columns:
            df['rsi'] = self._calculate_rsi(df['close'])
        
        if 'macd' not in df.columns:
            df = self._calculate_macd(df)
        
        if 'bb_upper' not in df.columns:
            df = self._calculate_bollinger_bands(df)
        
        # Análisis de tendencia con múltiples EMAs
        trend = self._determine_advanced_trend(df)
        
        # Análisis de momentum mejorado
        momentum = self._analyze_momentum(df)
        
        # Análisis de estructura de mercado
        structure = self._analyze_market_structure(df)
        
        # Niveles clave
        key_levels = self._find_key_levels(df)
        
        # Calidad de la tendencia
        trend_quality = self._calculate_trend_quality(df, trend, momentum)
        
        # Determinar dirección y fuerza final
        if trend['direction'] == 'up' and momentum['strength'] > 60:
            direction = 'BULLISH'
            strength = (trend['strength'] * 0.6 + momentum['strength'] * 0.4)
        elif trend['direction'] == 'down' and momentum['strength'] > 60:
            direction = 'BEARISH'
            strength = (trend['strength'] * 0.6 + momentum['strength'] * 0.4)
        else:
            direction = 'NEUTRAL'
            
            # En neutral, evaluar si hay sesgo
            if trend['direction'] == 'up':
                strength = 50 + (trend['strength'] - 50) * 0.5
            elif trend['direction'] == 'down':
                strength = 50 - (trend['strength'] - 50) * 0.5
            else:
                strength = 50.0
        
        # Ajustar por estructura de mercado
        if structure['pattern'] == 'ranging':
            strength *= 0.7  # Reducir confianza en rangos
        elif structure['pattern'] == 'breakout':
            strength *= 1.2  # Aumentar en breakouts
        
        # Limitar strength
        strength = min(100, max(0, strength))
        
        return TimeframeSignal(
            timeframe=timeframe,
            direction=direction,
            strength=strength,
            rsi=df['rsi'].iloc[-1] if 'rsi' in df else 50,
            macd_signal=df['macd'].iloc[-1] if 'macd' in df else 0,
            volume_ratio=self._calculate_volume_ratio(df),
            key_levels=key_levels,
            trend_quality=trend_quality
        )
    
    def get_consensus_signal(self, signals: Dict[str, TimeframeSignal]) -> Dict[str, any]:
        """
        Obtiene señal de consenso ponderada mejorada
        """
        if not signals:
            return {
                'direction': 'NEUTRAL',
                'strength': 0,
                'confidence': 0,
                'alignment': 0,
                'quality': 0
            }
        
        bullish_weight = 0
        bearish_weight = 0
        neutral_weight = 0
        total_weight = 0
        quality_sum = 0
        
        for tf, signal in signals.items():
            weight = self.timeframe_weights.get(tf, 0.1)
            
            # Ajustar peso por calidad de la señal
            adjusted_weight = weight * (signal.trend_quality / 100)
            
            if signal.direction == 'BULLISH':
                bullish_weight += adjusted_weight * signal.strength
            elif signal.direction == 'BEARISH':
                bearish_weight += adjusted_weight * signal.strength
            else:
                neutral_weight += adjusted_weight * 50
            
            total_weight += adjusted_weight
            quality_sum += signal.trend_quality * weight
        
        if total_weight == 0:
            return {
                'direction': 'NEUTRAL',
                'strength': 0,
                'confidence': 0,
                'alignment': 0,
                'quality': 0
            }
        
        # Normalizar scores
        bullish_score = bullish_weight / total_weight
        bearish_score = bearish_weight / total_weight
        neutral_score = neutral_weight / total_weight
        
        # Calcular calidad promedio ponderada
        avg_quality = quality_sum / sum(self.timeframe_weights.get(tf, 0.1) for tf in signals.keys())
        
        # Determinar dirección final con umbrales dinámicos
        threshold = 55 if avg_quality > 70 else 60  # Menor umbral si alta calidad
        
        if bullish_score > bearish_score and bullish_score > threshold:
            direction = 'BULLISH'
            strength = bullish_score
        elif bearish_score > bullish_score and bearish_score > threshold:
            direction = 'BEARISH'
            strength = bearish_score
        else:
            direction = 'NEUTRAL'
            strength = 50
        
        # Calcular confianza mejorada
        alignment = self._calculate_alignment(signals)
        confidence = self._calculate_confidence(signals, alignment, avg_quality)
        
        # Análisis adicional de contexto
        context = self._analyze_context(signals)
        
        return {
            'direction': direction,
            'strength': min(100, strength),
            'confidence': confidence,
            'alignment': alignment,
            'quality': avg_quality,
            'bullish_score': bullish_score,
            'bearish_score': bearish_score,
            'neutral_score': neutral_score,
            'context': context,
            'timeframes_analyzed': len(signals),
            'dominant_timeframe': self._get_dominant_timeframe(signals)
        }
    
    def _calculate_alignment(self, signals: Dict[str, TimeframeSignal]) -> float:
        """
        Calcula qué tan alineadas están las señales con peso por temporalidad
        100 = perfectamente alineadas, 0 = completamente opuestas
        """
        if len(signals) < 2:
            return 50
        
        weighted_alignment = 0
        total_weight = 0
        
        # Obtener dirección dominante
        direction_scores = {'BULLISH': 0, 'BEARISH': 0, 'NEUTRAL': 0}
        
        for tf, signal in signals.items():
            weight = self.timeframe_weights.get(tf, 0.1)
            direction_scores[signal.direction] += weight
            total_weight += weight
        
        # Dirección dominante
        dominant = max(direction_scores, key=direction_scores.get)
        
        # Calcular alineación ponderada
        for tf, signal in signals.items():
            weight = self.timeframe_weights.get(tf, 0.1)
            if signal.direction == dominant:
                weighted_alignment += weight * 100
            elif signal.direction == 'NEUTRAL':
                weighted_alignment += weight * 50
            # Si es opuesto, contribuye 0
        
        return weighted_alignment / total_weight if total_weight > 0 else 50
    
    def _calculate_confidence(self, 
                            signals: Dict[str, TimeframeSignal],
                            alignment: float,
                            quality: float) -> float:
        """
        Calcula confianza basada en múltiples factores
        """
        confidence = 50  # Base
        
        # Factor de alineación (hasta +25)
        confidence += (alignment - 50) * 0.5
        
        # Factor de calidad (hasta +15)
        confidence += (quality - 50) * 0.3
        
        # Factor de número de timeframes (hasta +10)
        tf_factor = min(10, len(signals) * 2)
        confidence += tf_factor
        
        # Penalización por señales mixtas
        directions = [s.direction for s in signals.values()]
        if 'BULLISH' in directions and 'BEARISH' in directions:
            confidence -= 20  # Señales contradictorias
        
        # Bonus por confirmación de timeframes mayores
        if '1d' in signals and '4h' in signals:
            if signals['1d'].direction == signals['4h'].direction:
                confidence += 10
        
        return min(100, max(0, confidence))
    
    def _determine_advanced_trend(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        Determina la tendencia con múltiples EMAs y ADX
        """
        if len(df) < 50:
            return {'direction': 'neutral', 'strength': 50, 'quality': 0}
        
        # EMAs múltiples
        ema_short = df['close'].ewm(span=9).mean()
        ema_medium = df['close'].ewm(span=21).mean()
        ema_long = df['close'].ewm(span=50).mean()
        ema_very_long = df['close'].ewm(span=200, min_periods=50).mean() if len(df) >= 200 else ema_long
        
        current_price = df['close'].iloc[-1]
        
        # Sistema de puntuación
        trend_score = 0
        
        # Precio vs EMAs
        if current_price > ema_short.iloc[-1]:
            trend_score += 2
        if current_price > ema_medium.iloc[-1]:
            trend_score += 2
        if current_price > ema_long.iloc[-1]:
            trend_score += 3
        if current_price > ema_very_long.iloc[-1]:
            trend_score += 3
        
        # Alineación de EMAs
        if ema_short.iloc[-1] > ema_medium.iloc[-1]:
            trend_score += 2
        if ema_medium.iloc[-1] > ema_long.iloc[-1]:
            trend_score += 3
        
        # Pendiente de EMAs (momentum)
        if len(df) >= 5:
            ema_short_slope = (ema_short.iloc[-1] - ema_short.iloc[-5]) / ema_short.iloc[-5]
            ema_medium_slope = (ema_medium.iloc[-1] - ema_medium.iloc[-5]) / ema_medium.iloc[-5]
            
            if ema_short_slope > 0:
                trend_score += 1
            if ema_medium_slope > 0:
                trend_score += 2
        
        # Determinar dirección y fuerza
        max_score = 18
        
        if trend_score > 12:
            direction = 'up'
            strength = 70 + (trend_score - 12) * 5
        elif trend_score > 9:
            direction = 'up'
            strength = 60 + (trend_score - 9) * 3
        elif trend_score < 6:
            direction = 'down'
            strength = 70 + (6 - trend_score) * 5
        elif trend_score < 9:
            direction = 'down'
            strength = 60 + (9 - trend_score) * 3
        else:
            direction = 'neutral'
            strength = 50
        
        # Calcular calidad de la tendencia
        quality = 0
        
        # Consistencia de la tendencia
        if direction != 'neutral':
            # Verificar cuántas velas siguen la tendencia
            trend_candles = 0
            for i in range(1, min(10, len(df))):
                if direction == 'up':
                    if df['close'].iloc[-i] > df['close'].iloc[-i-1]:
                        trend_candles += 1
                else:
                    if df['close'].iloc[-i] < df['close'].iloc[-i-1]:
                        trend_candles += 1
            
            quality = (trend_candles / 9) * 100
        
        return {
            'direction': direction,
            'strength': min(100, strength),
            'quality': quality,
            'score': trend_score,
            'ema_alignment': ema_short.iloc[-1] > ema_medium.iloc[-1] > ema_long.iloc[-1]
        }
    
    def _analyze_momentum(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Analiza el momentum con múltiples indicadores
        """
        if len(df) < 14:
            return {'strength': 50, 'direction': 0}
        
        momentum_score = 0
        
        # RSI momentum
        if 'rsi' in df.columns:
            rsi = df['rsi'].iloc[-1]
            rsi_prev = df['rsi'].iloc[-5] if len(df) >= 5 else rsi
            
            # RSI absoluto
            if rsi > 70:
                momentum_score += 3
            elif rsi > 60:
                momentum_score += 2
            elif rsi > 50:
                momentum_score += 1
            elif rsi < 30:
                momentum_score -= 3
            elif rsi < 40:
                momentum_score -= 2
            elif rsi < 50:
                momentum_score -= 1
            
            # Cambio de RSI
            rsi_change = rsi - rsi_prev
            if abs(rsi_change) > 10:
                momentum_score += 3 if rsi_change > 0 else -3
            elif abs(rsi_change) > 5:
                momentum_score += 2 if rsi_change > 0 else -2
        
        # MACD momentum
        if 'macd_hist' in df.columns and len(df) >= 5:
            macd_hist = df['macd_hist'].iloc[-1]
            macd_hist_prev = df['macd_hist'].iloc[-5]
            
            if macd_hist > 0:
                momentum_score += 2
            else:
                momentum_score -= 2
            
            # Cambio en histograma
            if macd_hist > macd_hist_prev:
                momentum_score += 2
            else:
                momentum_score -= 2
        
        # Price momentum (ROC)
        if len(df) >= 10:
            roc = (df['close'].iloc[-1] - df['close'].iloc[-10]) / df['close'].iloc[-10] * 100
            
            if abs(roc) > 5:
                momentum_score += 3 if roc > 0 else -3
            elif abs(roc) > 2:
                momentum_score += 2 if roc > 0 else -2
            elif abs(roc) > 0.5:
                momentum_score += 1 if roc > 0 else -1
        
        # Convertir score a strength (0-100)
        max_score = 15
        if momentum_score > 0:
            strength = 50 + (momentum_score / max_score) * 50
        else:
            strength = 50 - (abs(momentum_score) / max_score) * 50
        
        return {
            'strength': min(100, max(0, strength)),
            'direction': 1 if momentum_score > 0 else -1 if momentum_score < 0 else 0,
            'score': momentum_score
        }
    
    def _analyze_market_structure(self, df: pd.DataFrame) -> Dict[str, any]:
        """
        Analiza la estructura del mercado
        """
        if len(df) < 20:
            return {'pattern': 'unknown', 'strength': 0}
        
        highs = df['high'].iloc[-20:]
        lows = df['low'].iloc[-20:]
        closes = df['close'].iloc[-20:]
        
        # Detectar tendencia estructural
        higher_highs = 0
        higher_lows = 0
        lower_highs = 0
        lower_lows = 0
        
        for i in range(1, len(highs)):
            if highs.iloc[i] > highs.iloc[i-1]:
                higher_highs += 1
            else:
                lower_highs += 1
                
            if lows.iloc[i] > lows.iloc[i-1]:
                higher_lows += 1
            else:
                lower_lows += 1
        
        # Detectar rango
        price_range = highs.max() - lows.min()
        avg_range = (highs - lows).mean()
        current_position = (closes.iloc[-1] - lows.min()) / price_range if price_range > 0 else 0.5
        
        # Detectar breakout
        is_breakout = False
        if closes.iloc[-1] > highs.iloc[:-1].max():
            is_breakout = True
            pattern = 'breakout_up'
        elif closes.iloc[-1] < lows.iloc[:-1].min():
            is_breakout = True
            pattern = 'breakout_down'
        elif higher_highs > 12 and higher_lows > 12:
            pattern = 'trending_up'
        elif lower_highs > 12 and lower_lows > 12:
            pattern = 'trending_down'
        elif price_range < avg_range * 3:
            pattern = 'ranging'
        else:
            pattern = 'choppy'
        
        return {
            'pattern': pattern,
            'strength': abs(higher_highs - lower_highs) / 19 * 100,
            'position_in_range': current_position,
            'is_breakout': is_breakout
        }
    
    def _calculate_trend_quality(self, 
                                df: pd.DataFrame,
                                trend: Dict,
                                momentum: Dict) -> float:
        """
        Calcula la calidad de la tendencia (0-100)
        """
        quality = 50  # Base
        
        # Factor de alineación de tendencia y momentum
        if trend['direction'] == 'up' and momentum['direction'] > 0:
            quality += 20
        elif trend['direction'] == 'down' and momentum['direction'] < 0:
            quality += 20
        elif trend['direction'] == 'neutral':
            quality -= 10
        
        # Factor de fuerza
        quality += (trend['strength'] - 50) * 0.3
        quality += (momentum['strength'] - 50) * 0.2
        
        # Factor de volatilidad (menor volatilidad = mejor calidad)
        if 'atr' in df.columns and len(df) >= 14:
            atr = df['atr'].iloc[-1]
            price = df['close'].iloc[-1]
            atr_pct = (atr / price) * 100
            
            if atr_pct < 1:  # Baja volatilidad
                quality += 10
            elif atr_pct > 3:  # Alta volatilidad
                quality -= 10
        
        # Factor de consistencia (menos cambios de dirección)
        if len(df) >= 10:
            direction_changes = 0
            for i in range(1, 10):
                if (df['close'].iloc[-i] - df['open'].iloc[-i]) * (df['close'].iloc[-i-1] - df['open'].iloc[-i-1]) < 0:
                    direction_changes += 1
            
            quality -= direction_changes * 3
        
        return min(100, max(0, quality))
    
    def _find_key_levels(self, df: pd.DataFrame, num_levels: int = 5) -> List[float]:
        """
        Encuentra niveles clave de precio mejorados
        """
        if len(df) < 20:
            return []
        
        levels = []
        current_price = df['close'].iloc[-1]
        
        # 1. Pivotes diarios
        last_high = df['high'].iloc[-1]
        last_low = df['low'].iloc[-1]
        last_close = df['close'].iloc[-1]
        
        pivot = (last_high + last_low + last_close) / 3
        r1 = 2 * pivot - last_low
        r2 = pivot + (last_high - last_low)
        s1 = 2 * pivot - last_high
        s2 = pivot - (last_high - last_low)
        
        levels.extend([s2, s1, pivot, r1, r2])
        
        # 2. Máximos y mínimos significativos
        for period in [20, 50, 100]:
            if len(df) >= period:
                period_high = df['high'].iloc[-period:].max()
                period_low = df['low'].iloc[-period:].min()
                levels.extend([period_high, period_low])
        
        # 3. Niveles de Fibonacci del último swing
        if len(df) >= 50:
            recent_high = df['high'].iloc[-50:].max()
            recent_low = df['low'].iloc[-50:].min()
            fib_range = recent_high - recent_low
            
            fib_levels = [
                recent_low + fib_range * 0.236,
                recent_low + fib_range * 0.382,
                recent_low + fib_range * 0.5,
                recent_low + fib_range * 0.618,
                recent_low + fib_range * 0.786
            ]
            levels.extend(fib_levels)
        
        # 4. Niveles psicológicos
        round_factor = 10 ** (len(str(int(current_price))) - 3)
        round_level = round(current_price / round_factor) * round_factor
        levels.extend([
            round_level - round_factor * 2,
            round_level - round_factor,
            round_level,
            round_level + round_factor,
            round_level + round_factor * 2
        ])
        
        # 5. VWAP si hay volumen
        if 'volume' in df.columns and df['volume'].sum() > 0:
            vwap = (df['close'] * df['volume']).sum() / df['volume'].sum()
            levels.append(vwap)
        
        # Limpiar y ordenar
        levels = list(set([round(l, 2) for l in levels if l > 0]))
        
        # Filtrar niveles muy cercanos
        filtered_levels = []
        for level in sorted(levels):
            if not filtered_levels or abs(level - filtered_levels[-1]) / filtered_levels[-1] > 0.002:
                filtered_levels.append(level)
        
        # Retornar los más cercanos al precio actual
        return sorted(filtered_levels, key=lambda x: abs(x - current_price))[:num_levels]
    
    def _calculate_volume_ratio(self, df: pd.DataFrame) -> float:
        """
        Calcula ratio de volumen actual vs promedio
        """
        if 'volume' not in df.columns or len(df) < 20:
            return 1.0
        
        current_vol = df['volume'].iloc[-1]
        avg_vol = df['volume'].iloc[-20:].mean()
        
        return current_vol / avg_vol if avg_vol > 0 else 1.0
    
    def _calculate_bollinger_bands(self, df: pd.DataFrame, period: int = 20, std_dev: int = 2) -> pd.DataFrame:
        """
        Calcula Bandas de Bollinger
        """
        df['bb_middle'] = df['close'].rolling(window=period).mean()
        bb_std = df['close'].rolling(window=period).std()
        df['bb_upper'] = df['bb_middle'] + (bb_std * std_dev)
        df['bb_lower'] = df['bb_middle'] - (bb_std * std_dev)
        df['bb_width'] = df['bb_upper'] - df['bb_lower']
        df['bb_pct'] = (df['close'] - df['bb_lower']) / df['bb_width']
        
        return df
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Calcula RSI
        """
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _calculate_macd(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calcula MACD
        """
        exp1 = df['close'].ewm(span=12).mean()
        exp2 = df['close'].ewm(span=26).mean()
        
        df['macd'] = exp1 - exp2
        df['macd_signal'] = df['macd'].ewm(span=9).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        return df
    
    def _analyze_context(self, signals: Dict[str, TimeframeSignal]) -> Dict[str, any]:
        """
        Analiza el contexto del mercado
        """
        context = {
            'session': self._get_trading_session(),
            'volatility_state': 'normal',
            'trend_consistency': 0,
            'key_levels_nearby': []
        }
        
        # Analizar consistencia de tendencia
        directions = [s.direction for s in signals.values()]
        if directions:
            most_common = max(set(directions), key=directions.count)
            context['trend_consistency'] = directions.count(most_common) / len(directions) * 100
        
        # Identificar niveles clave cercanos
        all_levels = []
        for signal in signals.values():
            all_levels.extend(signal.key_levels)
        
        if all_levels:
            # Eliminar duplicados cercanos
            unique_levels = []
            for level in sorted(all_levels):
                if not unique_levels or abs(level - unique_levels[-1]) / unique_levels[-1] > 0.001:
                    unique_levels.append(level)
            context['key_levels_nearby'] = unique_levels[:3]
        
        # Estado de volatilidad basado en timeframes menores
        for tf in ['5min', '15min', '1h']:
            if tf in signals:
                if signals[tf].strength > 80:
                    context['volatility_state'] = 'high'
                    break
                elif signals[tf].strength < 30:
                    context['volatility_state'] = 'low'
        
        return context
    
    def _get_trading_session(self) -> str:
        """
        Determina la sesión de trading actual
        """
        from datetime import datetime
        import pytz
        
        try:
            # Obtener hora UTC
            utc_now = datetime.now(pytz.UTC)
            hour = utc_now.hour
            
            # Sesiones principales en UTC
            if 22 <= hour or hour < 7:  # 22:00 - 07:00 UTC
                return 'ASIA'
            elif 7 <= hour < 12:  # 07:00 - 12:00 UTC
                return 'LONDON'
            elif 12 <= hour < 21:  # 12:00 - 21:00 UTC
                return 'NEWYORK'
            else:  # 21:00 - 22:00 UTC
                return 'OVERLAP'
        except:
            return 'UNKNOWN'
    
    def _get_dominant_timeframe(self, signals: Dict[str, TimeframeSignal]) -> str:
        """
        Determina qué temporalidad tiene la señal más fuerte
        """
        if not signals:
            return 'NONE'
        
        max_strength = 0
        dominant_tf = 'NONE'
        
        for tf, signal in signals.items():
            weighted_strength = signal.strength * self.timeframe_weights.get(tf, 0.1)
            if weighted_strength > max_strength:
                max_strength = weighted_strength
                dominant_tf = tf
        
        return dominant_tf
