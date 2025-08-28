"""
📊 ANALIZADOR DE FLUJO DE VOLUMEN PROFESIONAL
Análisis de Order Flow, Delta Volume, y POC (Point of Control)
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from collections import deque
import logging

logger = logging.getLogger(__name__)

class VolumeFlowAnalyzer:
    """
    Análisis profesional de flujo de órdenes y volumen
    Técnicas usadas por traders institucionales
    """
    
    def __init__(self, symbol: str):
        """
        Args:
            symbol: Símbolo a analizar
        """
        self.symbol = symbol
        
        # Históricos para análisis
        self.volume_history = deque(maxlen=500)
        self.delta_history = deque(maxlen=500)
        self.cvd_history = deque(maxlen=500)  # Cumulative Volume Delta
        
        # Configuración
        self.volume_profile_bins = 50
        self.significant_volume_multiplier = 2.0
        
        logger.info(f"Volume Flow Analyzer inicializado para {symbol}")
    
    def analyze_complete_volume(self, df: pd.DataFrame) -> Dict:
        """
        Análisis completo de volumen con múltiples métricas
        """
        
        if df is None or df.empty:
            return {}
        
        results = {
            'delta_volume': self.calculate_delta_volume(df),
            'volume_profile': self.calculate_volume_profile(df),
            'vwap_analysis': self.calculate_vwap_analysis(df),
            'order_flow': self.analyze_order_flow(df),
            'volume_divergence': self.detect_volume_divergence(df),
            'liquidity_analysis': self.analyze_liquidity(df),
            'institutional_activity': self.detect_institutional_activity(df)
        }
        
        # Generar señales basadas en el análisis
        results['signals'] = self._generate_volume_signals(results)
        
        return results
    
    def calculate_delta_volume(self, df: pd.DataFrame) -> Dict:
        """
        Calcula Delta Volume (Volumen Comprador - Volumen Vendedor)
        """
        
        if len(df) < 2:
            return {'delta': 0, 'cumulative': 0, 'trend': 'NEUTRAL'}
        
        try:
            delta_values = []
            
            for i in range(1, len(df)):
                close = df.iloc[i]['close']
                prev_close = df.iloc[i-1]['close']
                volume = df.iloc[i]['volume']
                
                # Método 1: Basado en dirección del precio
                if close > prev_close:
                    # Precio subió - estimar más volumen comprador
                    buy_volume = volume * 0.65
                    sell_volume = volume * 0.35
                elif close < prev_close:
                    # Precio bajó - estimar más volumen vendedor
                    buy_volume = volume * 0.35
                    sell_volume = volume * 0.65
                else:
                    # Sin cambio - 50/50
                    buy_volume = volume * 0.5
                    sell_volume = volume * 0.5
                
                # Método 2: Usar high, low, close para mejor estimación
                if 'high' in df.columns and 'low' in df.columns:
                    high = df.iloc[i]['high']
                    low = df.iloc[i]['low']
                    
                    if high != low:
                        # Calcular presión compradora/vendedora
                        buy_pressure = (close - low) / (high - low)
                        sell_pressure = (high - close) / (high - low)
                        
                        # Ajustar estimaciones
                        buy_volume = volume * buy_pressure
                        sell_volume = volume * sell_pressure
                
                delta = buy_volume - sell_volume
                delta_values.append(delta)
            
            # Calcular métricas
            current_delta = delta_values[-1] if delta_values else 0
            cumulative_delta = sum(delta_values)
            
            # Determinar tendencia del delta
            if len(delta_values) >= 5:
                recent_delta = sum(delta_values[-5:])
                older_delta = sum(delta_values[-10:-5]) if len(delta_values) >= 10 else 0
                
                if recent_delta > older_delta * 1.2:
                    trend = 'BULLISH'
                elif recent_delta < older_delta * 0.8:
                    trend = 'BEARISH'
                else:
                    trend = 'NEUTRAL'
            else:
                trend = 'NEUTRAL'
            
            # Actualizar histórico
            self.delta_history.append(current_delta)
            self.cvd_history.append(cumulative_delta)
            
            return {
                'current': current_delta,
                'cumulative': cumulative_delta,
                'trend': trend,
                'history': list(self.delta_history)[-20:],
                'strength': abs(cumulative_delta) / (sum(df['volume']) + 1)
            }
            
        except Exception as e:
            logger.error(f"Error calculando delta volume: {e}")
            return {'delta': 0, 'cumulative': 0, 'trend': 'NEUTRAL'}
    
    def calculate_volume_profile(self, df: pd.DataFrame, bins: int = None) -> Dict:
        """
        Calcula el perfil de volumen (Volume Profile)
        Identifica POC, VAH, VAL
        """
        
        if len(df) < 10:
            return {}
        
        if bins is None:
            bins = self.volume_profile_bins
        
        try:
            prices = df['close'].values
            volumes = df['volume'].values
            
            # Crear bins de precio
            price_min = prices.min()
            price_max = prices.max()
            price_bins = np.linspace(price_min, price_max, bins)
            
            # Acumular volumen por nivel de precio
            volume_profile = {}
            
            for i, price in enumerate(prices):
                # Encontrar el bin correspondiente
                bin_index = np.digitize(price, price_bins) - 1
                bin_index = max(0, min(bin_index, len(price_bins) - 2))
                
                bin_price = (price_bins[bin_index] + price_bins[bin_index + 1]) / 2
                
                if bin_price not in volume_profile:
                    volume_profile[bin_price] = 0
                
                volume_profile[bin_price] += volumes[i]
            
            if not volume_profile:
                return {}
            
            # Ordenar por volumen
            sorted_profile = sorted(volume_profile.items(), key=lambda x: x[1], reverse=True)
            
            # Calcular POC (Point of Control) - precio con más volumen
            poc = sorted_profile[0][0] if sorted_profile else 0
            
            # Calcular Value Area (70% del volumen)
            total_volume = sum(v for _, v in sorted_profile)
            value_area_volume = total_volume * 0.7
            
            accumulated_volume = 0
            value_area_prices = []
            
            for price, vol in sorted_profile:
                accumulated_volume += vol
                value_area_prices.append(price)
                if accumulated_volume >= value_area_volume:
                    break
            
            # VAH (Value Area High) y VAL (Value Area Low)
            vah = max(value_area_prices) if value_area_prices else price_max
            val = min(value_area_prices) if value_area_prices else price_min
            
            # Calcular nivel de balance
            current_price = prices[-1]
            position_in_profile = 'NEUTRAL'
            
            if current_price > vah:
                position_in_profile = 'ABOVE_VALUE'
            elif current_price < val:
                position_in_profile = 'BELOW_VALUE'
            else:
                position_in_profile = 'IN_VALUE'
            
            # Identificar niveles de alto volumen (HVN) y bajo volumen (LVN)
            avg_volume = total_volume / len(volume_profile)
            hvn_levels = [p for p, v in volume_profile.items() if v > avg_volume * 1.5]
            lvn_levels = [p for p, v in volume_profile.items() if v < avg_volume * 0.5]
            
            return {
                'poc': poc,
                'vah': vah,
                'val': val,
                'value_area_range': vah - val,
                'position': position_in_profile,
                'current_price': current_price,
                'hvn_levels': sorted(hvn_levels),
                'lvn_levels': sorted(lvn_levels),
                'profile': dict(sorted_profile[:10])  # Top 10 niveles
            }
            
        except Exception as e:
            logger.error(f"Error calculando volume profile: {e}")
            return {}
    
    def calculate_vwap_analysis(self, df: pd.DataFrame) -> Dict:
        """
        Análisis completo de VWAP con bandas de desviación
        """
        
        if len(df) < 2:
            return {}
        
        try:
            # VWAP básico
            typical_price = (df['high'] + df['low'] + df['close']) / 3
            cumulative_tpv = (typical_price * df['volume']).cumsum()
            cumulative_volume = df['volume'].cumsum()
            
            vwap = cumulative_tpv / cumulative_volume
            
            # Calcular desviación estándar para bandas
            squared_diff = ((typical_price - vwap) ** 2 * df['volume'])
            variance = squared_diff.cumsum() / cumulative_volume
            std_dev = np.sqrt(variance)
            
            # Bandas VWAP (1, 2, 3 desviaciones estándar)
            upper_band_1 = vwap + std_dev
            upper_band_2 = vwap + (std_dev * 2)
            upper_band_3 = vwap + (std_dev * 3)
            
            lower_band_1 = vwap - std_dev
            lower_band_2 = vwap - (std_dev * 2)
            lower_band_3 = vwap - (std_dev * 3)
            
            current_price = df['close'].iloc[-1]
            current_vwap = vwap.iloc[-1]
            current_std = std_dev.iloc[-1]
            
            # Determinar posición relativa a VWAP
            distance_from_vwap = current_price - current_vwap
            stds_from_vwap = distance_from_vwap / current_std if current_std > 0 else 0
            
            # Señal basada en posición
            if stds_from_vwap > 2:
                signal = 'EXTREME_OVERBOUGHT'
            elif stds_from_vwap > 1:
                signal = 'OVERBOUGHT'
            elif stds_from_vwap < -2:
                signal = 'EXTREME_OVERSOLD'
            elif stds_from_vwap < -1:
                signal = 'OVERSOLD'
            else:
                signal = 'NEUTRAL'
            
            # Calcular pendiente de VWAP para tendencia
            if len(vwap) >= 10:
                vwap_slope = (vwap.iloc[-1] - vwap.iloc[-10]) / vwap.iloc[-10]
                trend = 'BULLISH' if vwap_slope > 0.001 else 'BEARISH' if vwap_slope < -0.001 else 'NEUTRAL'
            else:
                trend = 'NEUTRAL'
            
            return {
                'vwap': current_vwap,
                'price': current_price,
                'distance': distance_from_vwap,
                'stds_from_vwap': stds_from_vwap,
                'signal': signal,
                'trend': trend,
                'upper_band_1': upper_band_1.iloc[-1],
                'upper_band_2': upper_band_2.iloc[-1],
                'upper_band_3': upper_band_3.iloc[-1],
                'lower_band_1': lower_band_1.iloc[-1],
                'lower_band_2': lower_band_2.iloc[-1],
                'lower_band_3': lower_band_3.iloc[-1]
            }
            
        except Exception as e:
            logger.error(f"Error en análisis VWAP: {e}")
            return {}
    
    def analyze_order_flow(self, df: pd.DataFrame) -> Dict:
        """
        Analiza el flujo de órdenes para detectar presión compradora/vendedora
        """
        
        if len(df) < 5:
            return {}
        
        try:
            # Calcular Order Flow Imbalance
            imbalances = []
            
            for i in range(1, len(df)):
                # Calcular desequilibrio entre compras y ventas
                close = df.iloc[i]['close']
                open_price = df.iloc[i]['open']
                high = df.iloc[i]['high']
                low = df.iloc[i]['low']
                volume = df.iloc[i]['volume']
                
                # Estimar agresividad compradora vs vendedora
                if close > open_price:
                    # Vela alcista - más agresividad compradora
                    buy_aggression = (close - open_price) / (high - low + 0.0001)
                    imbalance = buy_aggression * volume
                else:
                    # Vela bajista - más agresividad vendedora
                    sell_aggression = (open_price - close) / (high - low + 0.0001)
                    imbalance = -sell_aggression * volume
                
                imbalances.append(imbalance)
            
            # Calcular métricas de flujo
            recent_flow = sum(imbalances[-5:]) if len(imbalances) >= 5 else 0
            total_flow = sum(imbalances)
            
            # Detectar absorción (volumen alto sin movimiento de precio)
            recent_volume = df['volume'].iloc[-5:].mean()
            historical_volume = df['volume'].iloc[:-5].mean() if len(df) > 5 else recent_volume
            
            price_change = abs(df['close'].iloc[-1] - df['close'].iloc[-5]) if len(df) >= 5 else 0
            price_range = df['close'].iloc[-5:].max() - df['close'].iloc[-5:].min() if len(df) >= 5 else 0
            
            absorption_detected = False
            if recent_volume > historical_volume * 1.5 and price_range < df['close'].iloc[-1] * 0.002:
                absorption_detected = True
            
            # Detectar momentum del flujo
            if len(imbalances) >= 10:
                recent_momentum = sum(imbalances[-5:])
                older_momentum = sum(imbalances[-10:-5])
                
                if recent_momentum > older_momentum * 1.5:
                    flow_momentum = 'ACCELERATING_UP'
                elif recent_momentum < older_momentum * 0.5:
                    flow_momentum = 'ACCELERATING_DOWN'
                else:
                    flow_momentum = 'STABLE'
            else:
                flow_momentum = 'INSUFFICIENT_DATA'
            
            return {
                'recent_flow': recent_flow,
                'total_flow': total_flow,
                'flow_momentum': flow_momentum,
                'absorption_detected': absorption_detected,
                'buy_pressure': sum(i for i in imbalances if i > 0),
                'sell_pressure': abs(sum(i for i in imbalances if i < 0)),
                'flow_direction': 'BULLISH' if recent_flow > 0 else 'BEARISH' if recent_flow < 0 else 'NEUTRAL'
            }
            
        except Exception as e:
            logger.error(f"Error analizando order flow: {e}")
            return {}
    
    def detect_volume_divergence(self, df: pd.DataFrame, window: int = 20) -> Dict:
        """
        Detecta divergencias entre precio y volumen
        """
        
        if len(df) < window:
            return {}
        
        try:
            prices = df['close'].values[-window:]
            volumes = df['volume'].values[-window:]
            
            # Calcular correlación precio-volumen
            correlation = np.corrcoef(prices, volumes)[0, 1]
            
            # Calcular tendencias
            x = np.arange(len(prices))
            price_slope, _ = np.polyfit(x, prices, 1)
            volume_slope, _ = np.polyfit(x, volumes, 1)
            
            # Normalizar pendientes
            price_trend = price_slope / np.mean(prices)
            volume_trend = volume_slope / np.mean(volumes)
            
            divergence_type = None
            divergence_strength = 0
            
            # Detectar tipos de divergencia
            if price_trend > 0.001 and volume_trend < -0.001:
                # Precio sube, volumen baja = Divergencia bajista
                divergence_type = 'BEARISH_DIVERGENCE'
                divergence_strength = abs(price_trend) + abs(volume_trend)
                message = "Precio sube sin soporte de volumen"
                
            elif price_trend < -0.001 and volume_trend > 0.001:
                # Precio baja, volumen sube = Posible capitulación o acumulación
                divergence_type = 'BULLISH_DIVERGENCE'
                divergence_strength = abs(price_trend) + abs(volume_trend)
                message = "Alto volumen en caída - Posible piso"
                
            elif price_trend > 0.001 and volume_trend > 0.001:
                # Precio y volumen suben = Confirmación alcista
                divergence_type = 'BULLISH_CONFIRMATION'
                divergence_strength = min(price_trend, volume_trend)
                message = "Subida con volumen creciente"
                
            elif price_trend < -0.001 and volume_trend < -0.001:
                # Precio y volumen bajan = Desinterés
                divergence_type = 'BEARISH_EXHAUSTION'
                divergence_strength = min(abs(price_trend), abs(volume_trend))
                message = "Caída con volumen decreciente"
                
            else:
                divergence_type = 'NO_DIVERGENCE'
                message = "Sin divergencia significativa"
            
            return {
                'type': divergence_type,
                'strength': divergence_strength,
                'correlation': correlation,
                'price_trend': price_trend,
                'volume_trend': volume_trend,
                'message': message,
                'significant': divergence_strength > 0.01
            }
            
        except Exception as e:
            logger.error(f"Error detectando divergencia de volumen: {e}")
            return {}
    
    def analyze_liquidity(self, df: pd.DataFrame) -> Dict:
        """
        Analiza la liquidez del mercado
        """
        
        if len(df) < 10:
            return {}
        
        try:
            volumes = df['volume'].values
            prices = df['close'].values
            
            # Calcular métricas de liquidez
            avg_volume = np.mean(volumes)
            std_volume = np.std(volumes)
            cv_volume = std_volume / avg_volume if avg_volume > 0 else 0  # Coeficiente de variación
            
            # Calcular spread estimado (usando high-low como proxy)
            if 'high' in df.columns and 'low' in df.columns:
                spreads = (df['high'] - df['low']) / df['close']
                avg_spread = spreads.mean()
                current_spread = spreads.iloc[-1]
            else:
                avg_spread = 0
                current_spread = 0
            
            # Detectar condiciones de liquidez
            recent_volume = np.mean(volumes[-5:])
            
            if recent_volume > avg_volume * 1.5:
                liquidity_state = 'HIGH'
            elif recent_volume < avg_volume * 0.5:
                liquidity_state = 'LOW'
            else:
                liquidity_state = 'NORMAL'
            
            # Calcular profundidad de mercado estimada
            price_impact = std_volume / avg_volume if avg_volume > 0 else 1
            
            return {
                'state': liquidity_state,
                'avg_volume': avg_volume,
                'recent_volume': recent_volume,
                'volume_cv': cv_volume,
                'avg_spread': avg_spread,
                'current_spread': current_spread,
                'price_impact': price_impact,
                'liquidity_score': 1 / (1 + price_impact)  # 0-1, mayor = más líquido
            }
            
        except Exception as e:
            logger.error(f"Error analizando liquidez: {e}")
            return {}
    
    def detect_institutional_activity(self, df: pd.DataFrame) -> Dict:
        """
        Detecta posible actividad institucional
        """
        
        if len(df) < 20:
            return {}
        
        try:
            volumes = df['volume'].values
            prices = df['close'].values
            
            # Detectar bloques grandes (volumen anormalmente alto)
            avg_volume = np.mean(volumes)
            std_volume = np.std(volumes)
            
            # Umbral para considerar volumen institucional
            institutional_threshold = avg_volume + (std_volume * 2)
            
            # Encontrar velas con volumen institucional
            institutional_bars = []
            for i in range(len(volumes)):
                if volumes[i] > institutional_threshold:
                    institutional_bars.append({
                        'index': i,
                        'volume': volumes[i],
                        'price': prices[i],
                        'ratio': volumes[i] / avg_volume
                    })
            
            # Analizar patrones de acumulación/distribución
            recent_institutional = [b for b in institutional_bars if b['index'] >= len(volumes) - 10]
            
            if len(recent_institutional) >= 3:
                # Múltiples barras institucionales recientes
                avg_inst_price = np.mean([b['price'] for b in recent_institutional])
                
                if prices[-1] > avg_inst_price:
                    pattern = 'ACCUMULATION'
                else:
                    pattern = 'DISTRIBUTION'
            elif len(recent_institutional) > 0:
                pattern = 'SPORADIC'
            else:
                pattern = 'NONE'
            
            # Calcular score de actividad institucional
            institutional_score = len(recent_institutional) / 10  # Normalizado 0-1
            
            return {
                'pattern': pattern,
                'score': institutional_score,
                'recent_blocks': len(recent_institutional),
                'total_blocks': len(institutional_bars),
                'avg_block_size': np.mean([b['volume'] for b in institutional_bars]) if institutional_bars else 0,
                'last_block': institutional_bars[-1] if institutional_bars else None,
                'likely_direction': 'BULLISH' if pattern == 'ACCUMULATION' else 'BEARISH' if pattern == 'DISTRIBUTION' else 'NEUTRAL'
            }
            
        except Exception as e:
            logger.error(f"Error detectando actividad institucional: {e}")
            return {}
    
    def _generate_volume_signals(self, analysis: Dict) -> List[Dict]:
        """
        Genera señales de trading basadas en el análisis de volumen
        """
        
        signals = []
        
        # Señal de Delta Volume
        if 'delta_volume' in analysis:
            delta = analysis['delta_volume']
            if delta.get('trend') == 'BULLISH' and delta.get('strength', 0) > 0.3:
                signals.append({
                    'type': 'DELTA_BUY',
                    'strength': delta['strength'],
                    'message': 'Delta volume fuertemente alcista'
                })
            elif delta.get('trend') == 'BEARISH' and delta.get('strength', 0) > 0.3:
                signals.append({
                    'type': 'DELTA_SELL',
                    'strength': delta['strength'],
                    'message': 'Delta volume fuertemente bajista'
                })
        
        # Señal de Volume Profile
        if 'volume_profile' in analysis:
            vp = analysis['volume_profile']
            if vp.get('position') == 'ABOVE_VALUE':
                signals.append({
                    'type': 'VP_BREAKOUT',
                    'target': vp.get('poc'),
                    'message': f"Precio sobre área de valor - POC: {vp.get('poc', 0):.2f}"
                })
            elif vp.get('position') == 'BELOW_VALUE':
                signals.append({
                    'type': 'VP_BREAKDOWN',
                    'target': vp.get('poc'),
                    'message': f"Precio bajo área de valor - POC: {vp.get('poc', 0):.2f}"
                })
        
        # Señal de VWAP
        if 'vwap_analysis' in analysis:
            vwap = analysis['vwap_analysis']
            if vwap.get('signal') == 'EXTREME_OVERSOLD':
                signals.append({
                    'type': 'VWAP_BOUNCE',
                    'strength': 0.8,
                    'message': 'Extremadamente sobrevendido vs VWAP'
                })
            elif vwap.get('signal') == 'EXTREME_OVERBOUGHT':
                signals.append({
                    'type': 'VWAP_REVERSAL',
                    'strength': 0.8,
                    'message': 'Extremadamente sobrecomprado vs VWAP'
                })
        
        # Señal de Divergencia
        if 'volume_divergence' in analysis:
            div = analysis['volume_divergence']
            if div.get('type') == 'BEARISH_DIVERGENCE' and div.get('significant'):
                signals.append({
                    'type': 'VOLUME_DIVERGENCE_SELL',
                    'strength': div.get('strength', 0),
                    'message': div.get('message', '')
                })
            elif div.get('type') == 'BULLISH_DIVERGENCE' and div.get('significant'):
                signals.append({
                    'type': 'VOLUME_DIVERGENCE_BUY',
                    'strength': div.get('strength', 0),
                    'message': div.get('message', '')
                })
        
        # Señal Institucional
        if 'institutional_activity' in analysis:
            inst = analysis['institutional_activity']
            if inst.get('pattern') == 'ACCUMULATION' and inst.get('score', 0) > 0.3:
                signals.append({
                    'type': 'INSTITUTIONAL_BUY',
                    'strength': inst['score'],
                    'message': 'Detectada acumulación institucional'
                })
            elif inst.get('pattern') == 'DISTRIBUTION' and inst.get('score', 0) > 0.3:
                signals.append({
                    'type': 'INSTITUTIONAL_SELL',
                    'strength': inst['score'],
                    'message': 'Detectada distribución institucional'
                })
        
        return signals