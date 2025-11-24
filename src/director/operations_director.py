#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DIRECTOR DE OPERACIONES INTELIGENTE - ALGO TRADER V3
=====================================================
Sistema avanzado de monitoreo y ajuste dinámico de operaciones
basado en volumen institucional y análisis de mercado en tiempo real
"""

import os
import sys
import time
import json
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import numpy as np
import pandas as pd

# Añadir path del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Importar módulos necesarios
from src.data.twelvedata_client import TwelveDataClient
from src.ai.ollama_client import OllamaClient
from src.broker.mt5_connection import MT5Connection
from src.notifiers.telegram_notifier import TelegramNotifier

logger = logging.getLogger(__name__)

class OperationsDirector:
    """
    Director de Operaciones que monitorea trades activos y ajusta TPs
    basándose en análisis de volumen institucional y condiciones del mercado
    """
    
    def __init__(self):
        """Inicializa el Director de Operaciones"""
        self.name = "Operations_Director_V3"
        self.is_running = False
        
        # Clientes
        self.twelvedata_client = None
        self.ollama_client = None
        self.mt5_connection = None
        self.telegram = None
        
        # Estado de operaciones
        self.monitored_trades = {}  # {ticket: trade_info}
        self.volume_analysis = {}   # {symbol: volume_data}
        self.institutional_levels = {}  # {symbol: levels}
        
        # Configuración
        self.check_interval = 30  # Segundos entre análisis
        self.volume_threshold = 2.0  # RVOL mínimo para considerar institucional
        self.tp_extension_factor = 1.5  # Factor para extender TP
        self.tp_reduction_factor = 0.8  # Factor para reducir TP
        
        # Estadísticas
        self.total_adjustments = 0
        self.successful_extensions = 0
        self.protective_reductions = 0
        
        # Inicializar clientes
        self.initialize_clients()
        
    def initialize_clients(self):
        """Inicializa todos los clientes necesarios"""
        try:
            # TwelveData para datos de mercado
            self.twelvedata_client = TwelveDataClient()
            logger.info("[OK] TwelveData client inicializado")
            
            # Ollama para análisis IA
            self.ollama_client = OllamaClient()
            logger.info("[OK] Ollama client inicializado")
            
            # MT5 para gestión de trades
            self.mt5_connection = MT5Connection()
            if self.mt5_connection.connect():
                logger.info("[OK] MT5 conectado")
            
            # Telegram para notificaciones
            try:
                self.telegram = TelegramNotifier()
                logger.info("[OK] Telegram inicializado")
            except:
                logger.warning("Telegram no disponible")
                
        except Exception as e:
            logger.error(f"Error inicializando clientes: {e}")
    
    def get_volume_indicators(self, symbol: str) -> Dict[str, Any]:
        """
        Obtiene indicadores de volumen para detectar actividad institucional
        
        Indicadores:
        - OBV (On Balance Volume)
        - VWAP (Volume Weighted Average Price)
        - RVOL (Relative Volume)
        - Volume Delta (si disponible)
        """
        try:
            # Mapear símbolo para TwelveData
            td_symbol = self.twelvedata_client.map_symbol(symbol)
            
            indicators = {}
            
            # 1. OBV - On Balance Volume
            try:
                obv_url = f"{self.twelvedata_client.base_url}/obv"
                params = {
                    'symbol': td_symbol,
                    'interval': '5min',
                    'apikey': self.twelvedata_client.api_key
                }
                response = self.twelvedata_client._make_request(obv_url, params)
                if response and 'values' in response:
                    obv_values = [float(v['obv']) for v in response['values'][:10]]
                    indicators['obv'] = obv_values[0] if obv_values else 0
                    indicators['obv_trend'] = 'UP' if len(obv_values) > 1 and obv_values[0] > obv_values[1] else 'DOWN'
                    indicators['obv_strength'] = abs(obv_values[0] - obv_values[1]) if len(obv_values) > 1 else 0
            except:
                pass
            
            # 2. VWAP - Volume Weighted Average Price
            try:
                vwap_url = f"{self.twelvedata_client.base_url}/vwap"
                params = {
                    'symbol': td_symbol,
                    'interval': '5min',
                    'apikey': self.twelvedata_client.api_key
                }
                response = self.twelvedata_client._make_request(vwap_url, params)
                if response and 'values' in response:
                    indicators['vwap'] = float(response['values'][0]['vwap'])
            except:
                pass
            
            # 3. Volumen actual y promedio para RVOL
            try:
                # Obtener datos de volumen recientes
                ts_url = f"{self.twelvedata_client.base_url}/time_series"
                params = {
                    'symbol': td_symbol,
                    'interval': '5min',
                    'outputsize': 50,
                    'apikey': self.twelvedata_client.api_key
                }
                response = self.twelvedata_client._make_request(ts_url, params)
                
                if response and 'values' in response:
                    volumes = [float(v['volume']) for v in response['values']]
                    if volumes:
                        current_volume = volumes[0]
                        avg_volume = np.mean(volumes[1:21]) if len(volumes) > 1 else current_volume
                        
                        # RVOL - Relative Volume
                        indicators['rvol'] = current_volume / avg_volume if avg_volume > 0 else 1.0
                        indicators['current_volume'] = current_volume
                        indicators['avg_volume'] = avg_volume
                        
                        # Detectar picos de volumen anormales
                        indicators['volume_spike'] = indicators['rvol'] > self.volume_threshold
                        
                        # Análisis de distribución de volumen
                        recent_volumes = volumes[:5]
                        indicators['volume_increasing'] = all(recent_volumes[i] >= recent_volumes[i+1] 
                                                              for i in range(len(recent_volumes)-1))
            except:
                pass
            
            # 4. Análisis de Price Action con Volumen
            try:
                if response and 'values' in response:
                    recent_bars = response['values'][:5]
                    
                    # Detectar velas con mechas largas + alto volumen
                    for bar in recent_bars:
                        high = float(bar['high'])
                        low = float(bar['low'])
                        close = float(bar['close'])
                        open_price = float(bar['open'])
                        volume = float(bar['volume'])
                        
                        body = abs(close - open_price)
                        range_total = high - low
                        upper_wick = high - max(close, open_price)
                        lower_wick = min(close, open_price) - low
                        
                        # Absorción institucional (mecha larga + volumen alto)
                        if range_total > 0:
                            wick_ratio = max(upper_wick, lower_wick) / range_total
                            if wick_ratio > 0.6 and volume > avg_volume * 1.5:
                                indicators['institutional_absorption'] = True
                                indicators['absorption_direction'] = 'BUY' if lower_wick > upper_wick else 'SELL'
                                break
            except:
                pass
            
            # 5. Calcular Score Institucional
            institutional_score = 0
            
            if indicators.get('volume_spike'):
                institutional_score += 30
            
            if indicators.get('rvol', 1) > 3:
                institutional_score += 20
            
            if indicators.get('obv_trend') == 'UP' and indicators.get('obv_strength', 0) > 0:
                institutional_score += 20
            
            if indicators.get('institutional_absorption'):
                institutional_score += 30
                
            indicators['institutional_score'] = institutional_score
            indicators['institutional_detected'] = institutional_score >= 50
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error obteniendo indicadores de volumen para {symbol}: {e}")
            return {}
    
    def analyze_market_conditions(self, symbol: str, current_price: float) -> Dict[str, Any]:
        """
        Analiza las condiciones actuales del mercado para un símbolo
        """
        try:
            analysis = {
                'symbol': symbol,
                'current_price': current_price,
                'timestamp': datetime.now()
            }
            
            # Obtener indicadores de volumen
            volume_indicators = self.get_volume_indicators(symbol)
            analysis['volume'] = volume_indicators
            
            # Obtener precio vs VWAP
            if 'vwap' in volume_indicators:
                vwap = volume_indicators['vwap']
                analysis['price_vs_vwap'] = 'ABOVE' if current_price > vwap else 'BELOW'
                analysis['vwap_distance'] = abs(current_price - vwap)
                analysis['vwap_distance_pct'] = (abs(current_price - vwap) / vwap) * 100
            
            # Detectar momentum
            analysis['momentum'] = self.detect_momentum(symbol)
            
            # Detectar niveles clave
            analysis['key_levels'] = self.detect_key_levels(symbol, current_price)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analizando condiciones de mercado: {e}")
            return {}
    
    def detect_momentum(self, symbol: str) -> Dict[str, Any]:
        """Detecta el momentum actual del mercado"""
        try:
            td_symbol = self.twelvedata_client.map_symbol(symbol)
            
            # Obtener RSI
            rsi_url = f"{self.twelvedata_client.base_url}/rsi"
            params = {
                'symbol': td_symbol,
                'interval': '5min',
                'apikey': self.twelvedata_client.api_key
            }
            response = self.twelvedata_client._make_request(rsi_url, params)
            
            momentum = {}
            if response and 'values' in response:
                rsi = float(response['values'][0]['rsi'])
                momentum['rsi'] = rsi
                momentum['rsi_signal'] = 'OVERBOUGHT' if rsi > 70 else 'OVERSOLD' if rsi < 30 else 'NEUTRAL'
            
            # Obtener MACD
            macd_url = f"{self.twelvedata_client.base_url}/macd"
            params = {
                'symbol': td_symbol,
                'interval': '5min',
                'apikey': self.twelvedata_client.api_key
            }
            response = self.twelvedata_client._make_request(macd_url, params)
            
            if response and 'values' in response:
                macd = float(response['values'][0]['macd'])
                signal = float(response['values'][0]['macd_signal'])
                momentum['macd'] = macd
                momentum['macd_signal'] = signal
                momentum['macd_cross'] = 'BULLISH' if macd > signal else 'BEARISH'
            
            return momentum
            
        except Exception as e:
            logger.error(f"Error detectando momentum: {e}")
            return {}
    
    def detect_key_levels(self, symbol: str, current_price: float) -> Dict[str, Any]:
        """Detecta niveles clave de soporte/resistencia"""
        try:
            td_symbol = self.twelvedata_client.map_symbol(symbol)
            
            # Obtener datos históricos para análisis
            ts_url = f"{self.twelvedata_client.base_url}/time_series"
            params = {
                'symbol': td_symbol,
                'interval': '15min',
                'outputsize': 100,
                'apikey': self.twelvedata_client.api_key
            }
            response = self.twelvedata_client._make_request(ts_url, params)
            
            levels = {}
            if response and 'values' in response:
                highs = [float(v['high']) for v in response['values']]
                lows = [float(v['low']) for v in response['values']]
                
                # Niveles psicológicos (números redondos)
                if 'XAU' in symbol:  # Oro
                    psychological = [round(current_price / 50) * 50 + i*50 for i in range(-2, 3)]
                elif 'BTC' in symbol:  # Bitcoin
                    psychological = [round(current_price / 1000) * 1000 + i*1000 for i in range(-2, 3)]
                else:  # Forex
                    psychological = [round(current_price, 3)]
                
                levels['psychological'] = psychological
                
                # Resistencia y soporte basados en máximos/mínimos recientes
                levels['resistance'] = max(highs[:20]) if highs else current_price * 1.01
                levels['support'] = min(lows[:20]) if lows else current_price * 0.99
                
                # Distancia a niveles clave
                levels['distance_to_resistance'] = levels['resistance'] - current_price
                levels['distance_to_support'] = current_price - levels['support']
                
                # Zona actual
                if current_price > levels['resistance'] * 0.998:
                    levels['zone'] = 'RESISTANCE'
                elif current_price < levels['support'] * 1.002:
                    levels['zone'] = 'SUPPORT'
                else:
                    levels['zone'] = 'NEUTRAL'
            
            return levels
            
        except Exception as e:
            logger.error(f"Error detectando niveles clave: {e}")
            return {}
    
    def request_ai_reanalysis(self, trade_info: Dict, market_analysis: Dict) -> Dict[str, Any]:
        """
        Solicita un nuevo análisis a la IA para evaluar si ajustar el TP
        """
        try:
            if not self.ollama_client:
                return {}
            
            prompt = f"""
            Eres un Director de Operaciones analizando un trade activo. Evalúa si el TP debe ajustarse.
            
            TRADE ACTUAL:
            - Símbolo: {trade_info['symbol']}
            - Tipo: {trade_info['type']}
            - Precio entrada: {trade_info['entry_price']}
            - TP actual: {trade_info['tp']}
            - Profit actual: ${trade_info['profit']:.2f}
            
            ANÁLISIS DE VOLUMEN:
            - RVOL: {market_analysis['volume'].get('rvol', 1):.2f}x
            - OBV Trend: {market_analysis['volume'].get('obv_trend', 'N/A')}
            - Volumen institucional: {'DETECTADO' if market_analysis['volume'].get('institutional_detected') else 'NO DETECTADO'}
            - Score institucional: {market_analysis['volume'].get('institutional_score', 0)}/100
            
            CONDICIONES DE MERCADO:
            - Precio vs VWAP: {market_analysis.get('price_vs_vwap', 'N/A')}
            - RSI: {market_analysis.get('momentum', {}).get('rsi', 50):.1f}
            - Zona actual: {market_analysis.get('key_levels', {}).get('zone', 'NEUTRAL')}
            
            DECISIÓN REQUERIDA:
            1. EXTENDER TP: Si hay volumen institucional a favor y momentum fuerte
            2. MANTENER TP: Si las condiciones son neutrales
            3. REDUCIR TP: Si hay señales de reversión o agotamiento
            
            Responde SOLO con:
            ACCION: [EXTENDER/MANTENER/REDUCIR]
            NUEVO_TP: [precio numérico o N/A si mantener]
            RAZON: [explicación breve]
            CONFIANZA: [0-100]%
            """
            
            # Solicitar análisis a la IA
            response = self.ollama_client.analyze_with_simple_prompt(prompt)
            
            if response:
                # Parsear respuesta
                lines = response.strip().split('\n')
                analysis = {}
                
                for line in lines:
                    if 'ACCION:' in line:
                        analysis['action'] = line.split(':')[1].strip()
                    elif 'NUEVO_TP:' in line:
                        try:
                            tp_value = line.split(':')[1].strip()
                            if tp_value != 'N/A':
                                analysis['new_tp'] = float(tp_value)
                        except:
                            pass
                    elif 'RAZON:' in line:
                        analysis['reason'] = line.split(':', 1)[1].strip()
                    elif 'CONFIANZA:' in line:
                        try:
                            conf = line.split(':')[1].strip().replace('%', '')
                            analysis['confidence'] = float(conf) / 100
                        except:
                            analysis['confidence'] = 0.5
                
                return analysis
            
            return {}
            
        except Exception as e:
            logger.error(f"Error en re-análisis IA: {e}")
            return {}
    
    def should_adjust_tp(self, trade_info: Dict, market_analysis: Dict) -> Tuple[bool, float, str]:
        """
        Determina si se debe ajustar el TP basándose en el análisis
        
        Returns:
            (should_adjust, new_tp, reason)
        """
        try:
            current_tp = trade_info['tp']
            entry_price = trade_info['entry_price']
            current_price = trade_info['current_price']
            trade_type = trade_info['type']
            
            # Obtener análisis de IA
            ai_analysis = self.request_ai_reanalysis(trade_info, market_analysis)
            
            if ai_analysis and ai_analysis.get('confidence', 0) > 0.6:
                action = ai_analysis.get('action', 'MANTENER')
                
                if action == 'EXTENDER' and 'new_tp' in ai_analysis:
                    return True, ai_analysis['new_tp'], ai_analysis.get('reason', 'IA recomienda extensión')
                elif action == 'REDUCIR' and 'new_tp' in ai_analysis:
                    return True, ai_analysis['new_tp'], ai_analysis.get('reason', 'IA recomienda reducción')
            
            # Lógica de respaldo sin IA
            volume_data = market_analysis.get('volume', {})
            momentum = market_analysis.get('momentum', {})
            levels = market_analysis.get('key_levels', {})
            
            # CASO 1: Extender TP si hay volumen institucional a favor
            if volume_data.get('institutional_detected'):
                if trade_type == 'BUY':
                    # Para BUY: extender si OBV sube y precio sobre VWAP
                    if (volume_data.get('obv_trend') == 'UP' and 
                        market_analysis.get('price_vs_vwap') == 'ABOVE'):
                        
                        # Calcular nuevo TP extendido
                        tp_distance = current_tp - entry_price
                        new_tp = entry_price + (tp_distance * self.tp_extension_factor)
                        
                        # No extender más allá de la resistencia
                        if 'resistance' in levels:
                            new_tp = min(new_tp, levels['resistance'] * 0.998)
                        
                        if new_tp > current_tp:
                            return True, new_tp, "Volumen institucional detectado - Extensión de TP"
                
                else:  # SELL
                    # Para SELL: extender si OBV baja y precio bajo VWAP
                    if (volume_data.get('obv_trend') == 'DOWN' and 
                        market_analysis.get('price_vs_vwap') == 'BELOW'):
                        
                        tp_distance = entry_price - current_tp
                        new_tp = entry_price - (tp_distance * self.tp_extension_factor)
                        
                        # No extender más allá del soporte
                        if 'support' in levels:
                            new_tp = max(new_tp, levels['support'] * 1.002)
                        
                        if new_tp < current_tp:
                            return True, new_tp, "Volumen institucional detectado - Extensión de TP"
            
            # CASO 2: Reducir TP si hay señales de agotamiento
            if momentum.get('rsi_signal') == 'OVERBOUGHT' and trade_type == 'BUY':
                # Reducir TP para asegurar ganancias
                tp_distance = current_tp - entry_price
                new_tp = entry_price + (tp_distance * self.tp_reduction_factor)
                
                if new_tp < current_tp and new_tp > current_price:
                    return True, new_tp, "RSI sobrecomprado - Reducción protectora de TP"
            
            elif momentum.get('rsi_signal') == 'OVERSOLD' and trade_type == 'SELL':
                tp_distance = entry_price - current_tp
                new_tp = entry_price - (tp_distance * self.tp_reduction_factor)
                
                if new_tp > current_tp and new_tp < current_price:
                    return True, new_tp, "RSI sobrevendido - Reducción protectora de TP"
            
            # CASO 3: Ajustar si está cerca de niveles psicológicos
            if 'psychological' in levels:
                for level in levels['psychological']:
                    distance_to_level = abs(current_tp - level)
                    if distance_to_level < (abs(current_tp - entry_price) * 0.1):
                        # TP está muy cerca de nivel psicológico, ajustar
                        if trade_type == 'BUY':
                            new_tp = level - (level * 0.0002)  # Justo antes del nivel
                        else:
                            new_tp = level + (level * 0.0002)  # Justo después del nivel
                        
                        if abs(new_tp - current_tp) > (current_tp * 0.001):
                            return True, new_tp, f"Ajuste a nivel psicológico {level}"
            
            return False, current_tp, "Mantener TP actual"
            
        except Exception as e:
            logger.error(f"Error evaluando ajuste de TP: {e}")
            return False, trade_info['tp'], "Error en evaluación"
    
    def analyze_single_cycle(self):
        """
        Análisis único de todas las posiciones activas - NO LOOP
        Retorna diccionario con resultados
        """
        logger.info(f"[DIRECTOR] Iniciando monitoreo de operaciones...")
        
        results = {
            'total_positions': 0,
            'tp_adjustments': 0,
            'adjustments_details': [],
            'errors': []
        }
        
        try:
            # Verificar conexión MT5
            if not self.mt5_connection:
                logger.error("[DIRECTOR] MT5Connection no inicializado")
                results['errors'].append("MT5Connection no inicializado")
                return results
                
            if not self.mt5_connection.ensure_connected():
                logger.error("[DIRECTOR] No se pudo conectar a MT5")
                results['errors'].append("No se pudo conectar a MT5")
                return results
            
            # Obtener posiciones abiertas
            positions = self.mt5_connection.get_positions()
            
            if not positions:
                logger.info("[DIRECTOR] No hay posiciones abiertas")
                return results
            
            results['total_positions'] = len(positions)
            logger.info(f"[DIRECTOR] Monitoreando {len(positions)} posiciones")
            
            for position in positions:
                try:
                    # Preparar información del trade
                    trade_info = {
                        'ticket': position.ticket,
                        'symbol': position.symbol,
                        'type': 'BUY' if position.type == 0 else 'SELL',
                        'volume': position.volume,
                        'entry_price': position.price_open,
                        'current_price': position.price_current,
                        'sl': position.sl,
                        'tp': position.tp,
                        'profit': position.profit,
                        'swap': position.swap,
                        'commission': getattr(position, 'commission', 0)
                    }
                    
                    # Solo monitorear trades con TP establecido
                    if trade_info['tp'] == 0:
                        logger.warning(f"[DIRECTOR] Trade {trade_info['ticket']} sin TP, saltando")
                        continue
                    
                    # Analizar condiciones del mercado
                    market_analysis = self.analyze_market_conditions(
                        trade_info['symbol'],
                        trade_info['current_price']
                    )
                    
                    # Evaluar si ajustar TP
                    should_adjust, new_tp, reason = self.should_adjust_tp(trade_info, market_analysis)
                    
                    if should_adjust and new_tp != trade_info['tp']:
                        # Ejecutar ajuste
                        success = self.mt5_connection.modify_position(
                            trade_info['ticket'],
                            sl=trade_info['sl'],
                            tp=new_tp
                        )
                        
                        if success:
                            self.total_adjustments += 1
                            results['tp_adjustments'] += 1
                            
                            # Determinar tipo de ajuste
                            if new_tp > trade_info['tp'] and trade_info['type'] == 'BUY':
                                self.successful_extensions += 1
                                adjustment_type = "EXTENSION"
                            elif new_tp < trade_info['tp'] and trade_info['type'] == 'SELL':
                                self.successful_extensions += 1
                                adjustment_type = "EXTENSION"
                            else:
                                self.protective_reductions += 1
                                adjustment_type = "REDUCTION"
                            
                            # Registrar detalles del ajuste
                            adjustment_detail = {
                                'ticket': trade_info['ticket'],
                                'symbol': trade_info['symbol'],
                                'type': adjustment_type,
                                'old_tp': trade_info['tp'],
                                'new_tp': new_tp,
                                'reason': reason,
                                'current_price': trade_info['current_price'],
                                'market_data': market_analysis
                            }
                            results['adjustments_details'].append(adjustment_detail)
                            
                            logger.info(f"[DIRECTOR] TP ajustado - {adjustment_type}")
                            logger.info(f"  Ticket: {trade_info['ticket']}")
                            logger.info(f"  Símbolo: {trade_info['symbol']}")
                            logger.info(f"  TP anterior: {trade_info['tp']:.5f}")
                            logger.info(f"  TP nuevo: {new_tp:.5f}")
                            logger.info(f"  Razón: {reason}")
                            
                            # Notificar por Telegram
                            self.send_adjustment_notification(
                                trade_info, new_tp, reason, market_analysis
                            )
                        else:
                            logger.error(f"[DIRECTOR] Error ajustando TP para {trade_info['ticket']}")
                            results['errors'].append(f"Error ajustando TP para ticket {trade_info['ticket']}")
                    
                except Exception as e:
                    error_msg = f"Error procesando posición {getattr(position, 'ticket', 'N/A')}: {e}"
                    logger.error(f"[DIRECTOR] {error_msg}")
                    results['errors'].append(error_msg)
                    continue
            
            return results
            
        except Exception as e:
            error_msg = f"Error en análisis general: {e}"
            logger.error(f"[DIRECTOR] {error_msg}")
            results['errors'].append(error_msg)
            return results
    
    def monitor_active_trades(self):
        """
        Ciclo principal de monitoreo de trades activos
        """
        logger.info(f"[DIRECTOR] Iniciando monitoreo de operaciones...")
        
        while self.is_running:
            try:
                # Usar el nuevo método de análisis único
                results = self.analyze_single_cycle()
                
                # Log de resultados
                if results.get('total_positions', 0) > 0:
                    logger.info(f"[DIRECTOR] Análisis completado: {results['total_positions']} posiciones, {results['tp_adjustments']} ajustes")
                
                if results.get('errors'):
                    for error in results['errors']:
                        logger.error(f"[DIRECTOR] {error}")
                
                # Esperar antes del próximo ciclo
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"[DIRECTOR] Error en ciclo de monitoreo: {e}")
                time.sleep(self.check_interval)
    
    def send_adjustment_notification(self, trade_info: Dict, new_tp: float, reason: str, analysis: Dict):
        """Envía notificación de ajuste de TP por Telegram"""
        try:
            if not self.telegram or not self.telegram.is_active:
                return
            
            # Determinar emoji según tipo de ajuste
            if new_tp > trade_info['tp'] and trade_info['type'] == 'BUY':
                emoji = "📈"
                action = "EXTENDIDO"
            elif new_tp < trade_info['tp'] and trade_info['type'] == 'SELL':
                emoji = "📉"
                action = "EXTENDIDO"
            else:
                emoji = "🛡️"
                action = "REDUCIDO"
            
            volume_data = analysis.get('volume', {})
            
            message = f"""
{emoji} **TP {action} - DIRECTOR DE OPERACIONES** {emoji}

**Trade:** #{trade_info['ticket']}
**Símbolo:** {trade_info['symbol']}
**Tipo:** {trade_info['type']}
**Profit actual:** ${trade_info['profit']:.2f}

**Ajuste de TP:**
• Anterior: {trade_info['tp']:.5f}
• Nuevo: {new_tp:.5f}
• Razón: {reason}

**Análisis de Volumen:**
• RVOL: {volume_data.get('rvol', 1):.2f}x
• Volumen institucional: {'✅ DETECTADO' if volume_data.get('institutional_detected') else '❌ NO DETECTADO'}
• Score: {volume_data.get('institutional_score', 0)}/100

**Estadísticas del Director:**
• Total ajustes: {self.total_adjustments}
• Extensiones exitosas: {self.successful_extensions}
• Reducciones protectoras: {self.protective_reductions}

⏰ {datetime.now().strftime('%H:%M:%S')}
"""
            
            self.telegram.send_message(message)
            
        except Exception as e:
            logger.error(f"Error enviando notificación: {e}")
    
    def start(self):
        """Inicia el Director de Operaciones"""
        if self.is_running:
            logger.warning("[DIRECTOR] Ya está en ejecución")
            return
        
        self.is_running = True
        
        # Iniciar monitoreo en hilo separado
        monitor_thread = threading.Thread(target=self.monitor_active_trades, daemon=True)
        monitor_thread.start()
        
        logger.info("[DIRECTOR] Director de Operaciones iniciado")
        
        # Notificar inicio
        if self.telegram and self.telegram.is_active:
            self.telegram.send_message(
                "🎯 **DIRECTOR DE OPERACIONES ACTIVO** 🎯\n\n"
                "Sistema de ajuste dinámico de TP iniciado:\n"
                "• Análisis de volumen institucional\n"
                "• Re-evaluación con IA\n"
                "• Ajuste inteligente de targets\n"
                f"• Intervalo de análisis: {self.check_interval}s"
            )
    
    def stop(self):
        """Detiene el Director de Operaciones"""
        self.is_running = False
        logger.info("[DIRECTOR] Director de Operaciones detenido")
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado actual del Director"""
        return {
            'name': self.name,
            'is_running': self.is_running,
            'monitored_trades': len(self.monitored_trades),
            'total_adjustments': self.total_adjustments,
            'successful_extensions': self.successful_extensions,
            'protective_reductions': self.protective_reductions,
            'check_interval': self.check_interval,
            'volume_threshold': self.volume_threshold,
            'last_analysis': datetime.now()
        }


# Función auxiliar para TwelveData
def _make_request(self, url: str, params: Dict) -> Optional[Dict]:
    """Método auxiliar para hacer requests a TwelveData"""
    try:
        import requests
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        logger.error(f"Error en request: {e}")
        return None

# Agregar método a TwelveDataClient si no existe
if not hasattr(TwelveDataClient, '_make_request'):
    TwelveDataClient._make_request = _make_request


if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Crear y ejecutar Director
    director = OperationsDirector()
    director.start()
    
    print("\n" + "="*60)
    print("DIRECTOR DE OPERACIONES INTELIGENTE")
    print("="*60)
    print("Monitoreando trades activos...")
    print("Análisis de volumen institucional activo")
    print("Re-evaluación con IA habilitada")
    print(f"Intervalo de verificación: {director.check_interval} segundos")
    print("\nPresiona Ctrl+C para detener")
    print("-"*60)
    
    try:
        while True:
            time.sleep(60)
            status = director.get_status()
            print(f"\n[STATUS] Ajustes: {status['total_adjustments']} | "
                  f"Extensiones: {status['successful_extensions']} | "
                  f"Protecciones: {status['protective_reductions']}")
    except KeyboardInterrupt:
        print("\n\nDeteniendo Director...")
        director.stop()
        print("Director detenido.")