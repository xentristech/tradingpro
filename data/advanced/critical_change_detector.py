"""
Sistema de Detección de Cambios Críticos en Tiempo Real
Basado en el análisis del XAU/USD que detectó la caída
Author: XentrisTech
Version: 2.0
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@dataclass
class CriticalAlert:
    """Alerta crítica del mercado"""
    timestamp: datetime
    severity: str  # 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    type: str  # 'DIVERGENCE', 'SUPPORT_BREAK', 'RESISTANCE_REJECT', etc
    message: str
    action: str  # 'CLOSE_LONGS', 'REDUCE_POSITION', 'STOP_TRADING', etc
    price_level: float
    indicators: Dict[str, float]

class CriticalChangeDetector:
    """
    Detector avanzado de cambios críticos en el mercado
    Implementa las técnicas que detectaron la caída del oro
    """
    
    def __init__(self, symbol: str, sensitivity: float = 0.7):
        self.symbol = symbol
        self.sensitivity = sensitivity
        self.alerts_history = []
        self.critical_levels = {}
        
        # Umbrales adaptativos para diferentes activos
        self.configure_thresholds(symbol)
        
    def configure_thresholds(self, symbol: str):
        """Configura umbrales según el activo"""
        if 'XAU' in symbol or 'GOLD' in symbol:
            self.rsi_thresholds = {
                '1min': {'oversold': 25, 'overbought': 75},
                '5min': {'oversold': 28, 'overbought': 72},
                '15min': {'oversold': 30, 'overbought': 70},
                '1h': {'oversold': 30, 'overbought': 70},
                '4h': {'oversold': 35, 'overbought': 65},
                '1d': {'oversold': 40, 'overbought': 60},
                '1M': {'oversold': 45, 'overbought': 85}  # Mensual más conservador
            }
        elif 'BTC' in symbol or 'ETH' in symbol:
            # Crypto más volátil
            self.rsi_thresholds = {
                '1min': {'oversold': 20, 'overbought': 80},
                '5min': {'oversold': 25, 'overbought': 75},
                '15min': {'oversold': 28, 'overbought': 72},
                '1h': {'oversold': 30, 'overbought': 70},
                '4h': {'oversold': 33, 'overbought': 67},
                '1d': {'oversold': 35, 'overbought': 65},
                '1M': {'oversold': 40, 'overbought': 80}
            }
        else:
            # Default para forex y otros
            self.rsi_thresholds = {
                '1min': {'oversold': 30, 'overbought': 70},
                '5min': {'oversold': 30, 'overbought': 70},
                '15min': {'oversold': 30, 'overbought': 70},
                '1h': {'oversold': 30, 'overbought': 70},
                '4h': {'oversold': 35, 'overbought': 65},
                '1d': {'oversold': 40, 'overbought': 60},
                '1M': {'oversold': 45, 'overbought': 55}
            }
    
    def detect_multi_timeframe_divergence(self, 
                                         rsi_data: Dict[str, float],
                                         price_data: Dict[str, pd.DataFrame]) -> Optional[CriticalAlert]:
        """
        Detecta divergencias entre múltiples temporalidades
        Como cuando el RSI 1H cayó 7 puntos mientras el diario se mantenía
        """
        timeframes = ['5min', '15min', '1h', '4h', '1d']
        available_tf = [tf for tf in timeframes if tf in rsi_data]
        
        if len(available_tf) < 2:
            return None
            
        divergences = []
        
        for i, tf in enumerate(available_tf[:-1]):
            for tf2 in available_tf[i+1:]:
                # Calcular cambio de RSI
                rsi_change_tf1 = self._calculate_rsi_momentum(price_data.get(tf, pd.DataFrame()))
                rsi_change_tf2 = self._calculate_rsi_momentum(price_data.get(tf2, pd.DataFrame()))
                
                # Divergencia significativa
                if abs(rsi_change_tf1 - rsi_change_tf2) > 5:
                    divergences.append({
                        'timeframes': (tf, tf2),
                        'delta': abs(rsi_change_tf1 - rsi_change_tf2),
                        'direction': 'bearish' if rsi_change_tf1 < rsi_change_tf2 else 'bullish',
                        'rsi_tf1': rsi_data[tf],
                        'rsi_tf2': rsi_data[tf2]
                    })
        
        # Si hay divergencias críticas
        if divergences:
            max_divergence = max(divergences, key=lambda x: x['delta'])
            
            # Determinar severidad
            if max_divergence['delta'] > 10:
                severity = 'CRITICAL'
                action = 'CLOSE_ALL'
            elif max_divergence['delta'] > 7:  # Como la caída de 7.42 puntos en 1H
                severity = 'HIGH'
                action = 'REDUCE_POSITION'
            elif max_divergence['delta'] > 5:
                severity = 'MEDIUM'
                action = 'TIGHTEN_STOPS'
            else:
                severity = 'LOW'
                action = 'MONITOR'
                
            current_price = price_data[available_tf[0]]['close'].iloc[-1] if available_tf else 0
            
            return CriticalAlert(
                timestamp=datetime.now(),
                severity=severity,
                type='MULTI_TF_DIVERGENCE',
                message=f"⚠️ Divergencia {severity} detectada: {max_divergence['timeframes']} - Delta: {max_divergence['delta']:.2f} | RSI {max_divergence['timeframes'][0]}: {max_divergence['rsi_tf1']:.1f}, RSI {max_divergence['timeframes'][1]}: {max_divergence['rsi_tf2']:.1f}",
                action=action,
                price_level=current_price,
                indicators={
                    'divergence_delta': max_divergence['delta'],
                    'direction': max_divergence['direction'],
                    'rsi_fast': max_divergence['rsi_tf1'],
                    'rsi_slow': max_divergence['rsi_tf2']
                }
            )
        
        return None
    
    def detect_double_top_rejection(self, 
                                   df: pd.DataFrame,
                                   window: int = 20,
                                   tolerance: float = 0.002) -> Optional[CriticalAlert]:
        """
        Detecta doble techo con rechazo como el de $3,390.77
        """
        if len(df) < window:
            return None
            
        recent_highs = df['high'].iloc[-window:]
        
        # Buscar picos locales
        peaks = []
        for i in range(2, len(recent_highs) - 2):
            if (recent_highs.iloc[i] > recent_highs.iloc[i-1] and 
                recent_highs.iloc[i] > recent_highs.iloc[i+1] and
                recent_highs.iloc[i] > recent_highs.iloc[i-2] and
                recent_highs.iloc[i] > recent_highs.iloc[i+2]):
                peaks.append((i, recent_highs.iloc[i]))
        
        # Verificar doble techo
        if len(peaks) >= 2:
            last_two_peaks = peaks[-2:]
            peak1_price = last_two_peaks[0][1]
            peak2_price = last_two_peaks[1][1]
            
            # Si los picos están dentro de la tolerancia
            if abs(peak1_price - peak2_price) / peak1_price < tolerance:
                current_price = df['close'].iloc[-1]
                
                # Si el precio cayó después del segundo pico
                if current_price < peak2_price * (1 - tolerance):
                    
                    # Calcular objetivo de caída
                    neckline = df['low'].iloc[-window:].min()
                    pattern_height = peak2_price - neckline
                    target = neckline - pattern_height * 0.618  # Fibonacci target
                    
                    return CriticalAlert(
                        timestamp=datetime.now(),
                        severity='HIGH',
                        type='DOUBLE_TOP_REJECTION',
                        message=f"🔴 Doble techo confirmado en {peak2_price:.2f} - Precio actual: {current_price:.2f} - Target: {target:.2f}",
                        action='CLOSE_LONGS',
                        price_level=peak2_price,
                        indicators={
                            'rejection_level': peak2_price,
                            'current': current_price,
                            'neckline': neckline,
                            'target': target
                        }
                    )
        
        return None
    
    def detect_double_bottom_reversal(self,
                                    df: pd.DataFrame,
                                    window: int = 20,
                                    tolerance: float = 0.002) -> Optional[CriticalAlert]:
        """
        Detecta doble suelo para reversiones alcistas
        """
        if len(df) < window:
            return None
            
        recent_lows = df['low'].iloc[-window:]
        
        # Buscar valles locales
        valleys = []
        for i in range(2, len(recent_lows) - 2):
            if (recent_lows.iloc[i] < recent_lows.iloc[i-1] and 
                recent_lows.iloc[i] < recent_lows.iloc[i+1] and
                recent_lows.iloc[i] < recent_lows.iloc[i-2] and
                recent_lows.iloc[i] < recent_lows.iloc[i+2]):
                valleys.append((i, recent_lows.iloc[i]))
        
        # Verificar doble suelo
        if len(valleys) >= 2:
            last_two_valleys = valleys[-2:]
            valley1_price = last_two_valleys[0][1]
            valley2_price = last_two_valleys[1][1]
            
            # Si los valles están dentro de la tolerancia
            if abs(valley1_price - valley2_price) / valley1_price < tolerance:
                current_price = df['close'].iloc[-1]
                
                # Si el precio subió después del segundo valle
                if current_price > valley2_price * (1 + tolerance):
                    
                    # Calcular objetivo de subida
                    neckline = df['high'].iloc[-window:].max()
                    pattern_height = neckline - valley2_price
                    target = neckline + pattern_height * 0.618
                    
                    return CriticalAlert(
                        timestamp=datetime.now(),
                        severity='HIGH',
                        type='DOUBLE_BOTTOM_REVERSAL',
                        message=f"🟢 Doble suelo confirmado en {valley2_price:.2f} - Precio actual: {current_price:.2f} - Target: {target:.2f}",
                        action='CLOSE_SHORTS',
                        price_level=valley2_price,
                        indicators={
                            'support_level': valley2_price,
                            'current': current_price,
                            'neckline': neckline,
                            'target': target
                        }
                    )
        
        return None
    
    def detect_support_break(self,
                           df: pd.DataFrame,
                           key_levels: List[float],
                           buffer_pct: float = 0.0005) -> Optional[CriticalAlert]:
        """
        Detecta ruptura de soportes clave
        """
        if len(df) < 2:
            return None
            
        current_price = df['close'].iloc[-1]
        previous_price = df['close'].iloc[-2]
        
        for support in sorted(key_levels, reverse=True):
            # Si cruzó el soporte hacia abajo
            if previous_price > support and current_price < support * (1 - buffer_pct):
                
                # Verificar volumen para confirmar ruptura
                volume_confirmation = False
                if 'volume' in df.columns:
                    avg_volume = df['volume'].iloc[-20:].mean()
                    current_volume = df['volume'].iloc[-1]
                    volume_confirmation = current_volume > avg_volume * 1.5
                
                # Calcular siguiente soporte
                lower_supports = [s for s in key_levels if s < support]
                next_support = max(lower_supports) if lower_supports else support * 0.98
                
                # Determinar severidad
                drop_pct = (support - next_support) / support
                if drop_pct > 0.02:
                    severity = 'HIGH'
                elif drop_pct > 0.01:
                    severity = 'MEDIUM'
                else:
                    severity = 'LOW'
                
                return CriticalAlert(
                    timestamp=datetime.now(),
                    severity=severity,
                    type='SUPPORT_BREAK',
                    message=f"⚠️ Ruptura de soporte en {support:.2f} {'con volumen' if volume_confirmation else ''} - Siguiente: {next_support:.2f}",
                    action='ADJUST_STOPS',
                    price_level=support,
                    indicators={
                        'broken_support': support,
                        'next_target': next_support,
                        'volume_confirmation': volume_confirmation,
                        'drop_potential': drop_pct
                    }
                )
        
        return None
    
    def detect_resistance_break(self,
                              df: pd.DataFrame,
                              key_levels: List[float],
                              buffer_pct: float = 0.0005) -> Optional[CriticalAlert]:
        """
        Detecta ruptura de resistencias clave (señal alcista)
        """
        if len(df) < 2:
            return None
            
        current_price = df['close'].iloc[-1]
        previous_price = df['close'].iloc[-2]
        
        for resistance in sorted(key_levels):
            # Si cruzó la resistencia hacia arriba
            if previous_price < resistance and current_price > resistance * (1 + buffer_pct):
                
                # Verificar volumen
                volume_confirmation = False
                if 'volume' in df.columns:
                    avg_volume = df['volume'].iloc[-20:].mean()
                    current_volume = df['volume'].iloc[-1]
                    volume_confirmation = current_volume > avg_volume * 1.5
                
                # Calcular siguiente resistencia
                higher_resistances = [r for r in key_levels if r > resistance]
                next_resistance = min(higher_resistances) if higher_resistances else resistance * 1.02
                
                return CriticalAlert(
                    timestamp=datetime.now(),
                    severity='MEDIUM',
                    type='RESISTANCE_BREAK',
                    message=f"✅ Ruptura de resistencia en {resistance:.2f} {'con volumen' if volume_confirmation else ''} - Objetivo: {next_resistance:.2f}",
                    action='CONSIDER_LONGS',
                    price_level=resistance,
                    indicators={
                        'broken_resistance': resistance,
                        'next_target': next_resistance,
                        'volume_confirmation': volume_confirmation
                    }
                )
        
        return None
    
    def detect_momentum_exhaustion(self,
                                 df: pd.DataFrame,
                                 rsi: float,
                                 macd_hist: Optional[np.ndarray] = None) -> Optional[CriticalAlert]:
        """
        Detecta agotamiento del momentum
        """
        if len(df) < 5:
            return None
        
        alerts = []
        
        # RSI extremo con divergencia
        if 'rsi' in df.columns:
            rsi_values = df['rsi'].iloc[-5:].values
            price_values = df['close'].iloc[-5:].values
            
            # Calcular velocidad de cambio del RSI
            rsi_velocity = np.gradient(rsi_values)[-1]
            
            # Divergencia bajista: precio sube, RSI baja
            if price_values[-1] > price_values[-3] and rsi_values[-1] < rsi_values[-3] and rsi > 70:
                alerts.append(CriticalAlert(
                    timestamp=datetime.now(),
                    severity='HIGH',
                    type='BEARISH_DIVERGENCE',
                    message=f"📉 Divergencia BAJISTA detectada - RSI: {rsi:.1f} (cayendo a {rsi_velocity:.2f}/período)",
                    action='CLOSE_LONGS',
                    price_level=df['close'].iloc[-1],
                    indicators={'rsi': rsi, 'rsi_velocity': rsi_velocity}
                ))
            
            # Divergencia alcista: precio baja, RSI sube
            elif price_values[-1] < price_values[-3] and rsi_values[-1] > rsi_values[-3] and rsi < 30:
                alerts.append(CriticalAlert(
                    timestamp=datetime.now(),
                    severity='HIGH',
                    type='BULLISH_DIVERGENCE',
                    message=f"📈 Divergencia ALCISTA detectada - RSI: {rsi:.1f} (subiendo a {rsi_velocity:.2f}/período)",
                    action='CLOSE_SHORTS',
                    price_level=df['close'].iloc[-1],
                    indicators={'rsi': rsi, 'rsi_velocity': rsi_velocity}
                ))
        
        # MACD histograma decreciente
        if macd_hist is not None and len(macd_hist) >= 3:
            macd_declining = all(macd_hist[i] < macd_hist[i-1] for i in range(-3, 0))
            
            if macd_declining and rsi > 60:
                alerts.append(CriticalAlert(
                    timestamp=datetime.now(),
                    severity='MEDIUM',
                    type='MOMENTUM_EXHAUSTION',
                    message=f"⚠️ Agotamiento de momentum - MACD declinando, RSI: {rsi:.1f}",
                    action='TIGHTEN_STOPS',
                    price_level=df['close'].iloc[-1],
                    indicators={'rsi': rsi, 'macd_declining': True}
                ))
        
        # Retornar la alerta más severa
        return max(alerts, key=lambda x: ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].index(x.severity)) if alerts else None
    
    def detect_volatility_expansion(self,
                                   df: pd.DataFrame,
                                   lookback: int = 20,
                                   threshold: float = 1.5) -> Optional[CriticalAlert]:
        """
        Detecta expansión súbita de volatilidad
        """
        if len(df) < lookback + 14:
            return None
            
        # ATR actual vs histórico
        current_atr = self._calculate_atr(df.iloc[-14:])
        historical_atr = self._calculate_atr(df.iloc[-lookback-14:-lookback])
        
        if historical_atr == 0:
            return None
            
        volatility_ratio = current_atr / historical_atr
        
        if volatility_ratio > threshold:
            # Determinar severidad
            if volatility_ratio > 2.5:
                severity = 'CRITICAL'
                action = 'CLOSE_ALL'
            elif volatility_ratio > 2.0:
                severity = 'HIGH'
                action = 'REDUCE_SIZE'
            elif volatility_ratio > threshold:
                severity = 'MEDIUM'
                action = 'TIGHTEN_STOPS'
            else:
                return None
            
            return CriticalAlert(
                timestamp=datetime.now(),
                severity=severity,
                type='VOLATILITY_SPIKE',
                message=f"⚡ Expansión de volatilidad {severity}: {(volatility_ratio - 1)*100:.1f}% sobre promedio",
                action=action,
                price_level=df['close'].iloc[-1],
                indicators={
                    'current_atr': current_atr,
                    'historical_atr': historical_atr,
                    'ratio': volatility_ratio
                }
            )
        
        return None
    
    def detect_volume_anomaly(self,
                            df: pd.DataFrame,
                            threshold: float = 2.0) -> Optional[CriticalAlert]:
        """
        Detecta anomalías en el volumen
        """
        if 'volume' not in df.columns or len(df) < 20:
            return None
            
        current_volume = df['volume'].iloc[-1]
        avg_volume = df['volume'].iloc[-20:].mean()
        
        if avg_volume == 0:
            return None
            
        volume_ratio = current_volume / avg_volume
        
        if volume_ratio > threshold:
            # Determinar dirección del movimiento
            price_change = df['close'].iloc[-1] - df['open'].iloc[-1]
            direction = 'BULLISH' if price_change > 0 else 'BEARISH'
            
            return CriticalAlert(
                timestamp=datetime.now(),
                severity='MEDIUM' if volume_ratio < 3 else 'HIGH',
                type=f'VOLUME_SPIKE_{direction}',
                message=f"📊 Volumen anormal {direction}: {volume_ratio:.1f}x promedio",
                action='MONITOR' if volume_ratio < 3 else 'PREPARE_ACTION',
                price_level=df['close'].iloc[-1],
                indicators={
                    'current_volume': current_volume,
                    'avg_volume': avg_volume,
                    'ratio': volume_ratio,
                    'direction': direction
                }
            )
        
        return None
    
    def _calculate_rsi_momentum(self, df: pd.DataFrame) -> float:
        """Calcula el momentum del RSI"""
        if 'rsi' not in df.columns or len(df) < 2:
            return 0
        rsi_values = df['rsi'].iloc[-5:].values
        if len(rsi_values) < 2:
            return 0
        return rsi_values[-1] - rsi_values[-2]
    
    def _calculate_atr(self, df: pd.DataFrame) -> float:
        """Calcula Average True Range"""
        if len(df) < 2:
            return 0
            
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return true_range.mean()
    
    def run_full_scan(self, market_data: Dict[str, pd.DataFrame]) -> List[CriticalAlert]:
        """
        Ejecuta escaneo completo de todas las señales críticas
        """
        alerts = []
        
        try:
            # 1. Divergencias multi-temporales
            rsi_data = {}
            for tf, df in market_data.items():
                if 'rsi' in df.columns and len(df) > 0:
                    rsi_data[tf] = df['rsi'].iloc[-1]
            
            if len(rsi_data) >= 2:
                divergence_alert = self.detect_multi_timeframe_divergence(rsi_data, market_data)
                if divergence_alert:
                    alerts.append(divergence_alert)
            
            # 2. Patrones de precio (usar temporalidad más baja disponible)
            for tf in ['5min', '15min', '1h', '4h']:
                if tf in market_data and len(market_data[tf]) > 20:
                    # Doble techo
                    double_top = self.detect_double_top_rejection(market_data[tf])
                    if double_top:
                        alerts.append(double_top)
                        break  # Solo detectar en una temporalidad
                    
                    # Doble suelo
                    double_bottom = self.detect_double_bottom_reversal(market_data[tf])
                    if double_bottom:
                        alerts.append(double_bottom)
                        break
            
            # 3. Ruptura de niveles (calcular dinámicamente)
            if '15min' in market_data or '5min' in market_data:
                df = market_data.get('15min', market_data.get('5min'))
                if len(df) > 20:
                    key_levels = self._calculate_key_levels(df)
                    
                    support_break = self.detect_support_break(df, key_levels)
                    if support_break:
                        alerts.append(support_break)
                    
                    resistance_break = self.detect_resistance_break(df, key_levels)
                    if resistance_break:
                        alerts.append(resistance_break)
            
            # 4. Agotamiento de momentum
            for tf in ['1h', '4h', '1d']:
                if tf in market_data and 'rsi' in market_data[tf].columns:
                    rsi_val = market_data[tf]['rsi'].iloc[-1] if len(market_data[tf]) > 0 else 50
                    macd_hist = None
                    if 'macd_hist' in market_data[tf].columns:
                        macd_hist = market_data[tf]['macd_hist'].iloc[-5:].values
                    
                    momentum_alert = self.detect_momentum_exhaustion(
                        market_data[tf],
                        rsi_val,
                        macd_hist
                    )
                    if momentum_alert:
                        alerts.append(momentum_alert)
                        break  # Solo una alerta de momentum
            
            # 5. Expansión de volatilidad
            for tf in ['15min', '1h', '4h']:
                if tf in market_data and len(market_data[tf]) > 40:
                    volatility_alert = self.detect_volatility_expansion(market_data[tf])
                    if volatility_alert:
                        alerts.append(volatility_alert)
                        break
            
            # 6. Anomalías de volumen
            for tf in ['5min', '15min', '1h']:
                if tf in market_data and 'volume' in market_data[tf].columns:
                    volume_alert = self.detect_volume_anomaly(market_data[tf])
                    if volume_alert:
                        alerts.append(volume_alert)
                        break
            
            # Filtrar por severidad según sensibilidad
            if self.sensitivity < 0.5:
                alerts = [a for a in alerts if a.severity in ['HIGH', 'CRITICAL']]
            elif self.sensitivity < 0.8:
                alerts = [a for a in alerts if a.severity in ['MEDIUM', 'HIGH', 'CRITICAL']]
            
            # Eliminar duplicados manteniendo la más severa
            unique_alerts = {}
            for alert in alerts:
                key = alert.type
                if key not in unique_alerts or self._severity_score(alert) > self._severity_score(unique_alerts[key]):
                    unique_alerts[key] = alert
            
            alerts = list(unique_alerts.values())
            
            # Ordenar por severidad
            alerts.sort(key=lambda x: self._severity_score(x), reverse=True)
            
            # Guardar historial (mantener últimas 100)
            self.alerts_history.extend(alerts)
            self.alerts_history = self.alerts_history[-100:]
            
        except Exception as e:
            logger.error(f"Error en escaneo completo: {e}", exc_info=True)
        
        return alerts
    
    def _calculate_key_levels(self, df: pd.DataFrame) -> List[float]:
        """Calcula niveles clave de soporte y resistencia"""
        if len(df) < 20:
            return []
            
        levels = []
        
        # Máximos y mínimos del período
        period_high = df['high'].max()
        period_low = df['low'].min()
        levels.extend([period_high, period_low])
        
        # Pivotes clásicos
        last_high = df['high'].iloc[-1]
        last_low = df['low'].iloc[-1]
        last_close = df['close'].iloc[-1]
        
        pivot = (last_high + last_low + last_close) / 3
        r1 = 2 * pivot - last_low
        r2 = pivot + (last_high - last_low)
        s1 = 2 * pivot - last_high
        s2 = pivot - (last_high - last_low)
        
        levels.extend([pivot, r1, r2, s1, s2])
        
        # Máximos y mínimos locales
        for i in range(5, len(df) - 5, 5):
            local_high = df['high'].iloc[i-5:i+5].max()
            local_low = df['low'].iloc[i-5:i+5].min()
            levels.extend([local_high, local_low])
        
        # Niveles psicológicos (números redondos)
        current_price = df['close'].iloc[-1]
        round_factor = 10 ** (len(str(int(current_price))) - 2)  # Ajustar según magnitud
        round_level = round(current_price / round_factor) * round_factor
        
        levels.extend([
            round_level - round_factor,
            round_level,
            round_level + round_factor
        ])
        
        # Limpiar y ordenar
        levels = sorted(list(set([round(l, 2) for l in levels if l > 0])))
        
        # Filtrar niveles muy cercanos (menos del 0.1% de diferencia)
        filtered_levels = []
        for level in levels:
            if not filtered_levels or abs(level - filtered_levels[-1]) / filtered_levels[-1] > 0.001:
                filtered_levels.append(level)
        
        return filtered_levels
    
    def _severity_score(self, alert: CriticalAlert) -> int:
        """Convierte severidad a score numérico"""
        severity_map = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3, 'CRITICAL': 4}
        return severity_map.get(alert.severity, 0)
    
    def get_alert_summary(self) -> Dict[str, any]:
        """Obtiene resumen de alertas recientes"""
        if not self.alerts_history:
            return {
                'total': 0,
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0,
                'last_alert': None
            }
        
        return {
            'total': len(self.alerts_history),
            'critical': sum(1 for a in self.alerts_history if a.severity == 'CRITICAL'),
            'high': sum(1 for a in self.alerts_history if a.severity == 'HIGH'),
            'medium': sum(1 for a in self.alerts_history if a.severity == 'MEDIUM'),
            'low': sum(1 for a in self.alerts_history if a.severity == 'LOW'),
            'last_alert': self.alerts_history[-1].message if self.alerts_history else None,
            'last_time': self.alerts_history[-1].timestamp if self.alerts_history else None
        }
