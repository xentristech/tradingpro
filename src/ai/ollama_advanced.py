#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OLLAMA ADVANCED AI TRADER - SISTEMA DE IA PROFESIONAL
=====================================================
Análisis avanzado con múltiples modelos y estrategias de consenso
"""

import json
import logging
import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
import re

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

class SignalStrength(Enum):
    """Fuerza de la señal de trading"""
    VERY_STRONG_BUY = 5
    STRONG_BUY = 4
    BUY = 3
    NEUTRAL = 0
    SELL = -3
    STRONG_SELL = -4
    VERY_STRONG_SELL = -5

@dataclass
class TradingSignal:
    """Señal de trading con todos los parámetros"""
    symbol: str
    action: str  # BUY, SELL, NO_TRADE
    entry_price: float
    stop_loss: float
    take_profit_1: float  # TP parcial
    take_profit_2: float  # TP principal
    take_profit_3: float  # TP extendido
    confidence: float
    risk_reward_ratio: float
    position_size: float
    reasoning: str
    strategy: str
    timeframe: str
    expected_duration: str
    market_conditions: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return {
            'symbol': self.symbol,
            'action': self.action,
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profits': [self.take_profit_1, self.take_profit_2, self.take_profit_3],
            'confidence': self.confidence,
            'risk_reward_ratio': self.risk_reward_ratio,
            'position_size': self.position_size,
            'reasoning': self.reasoning,
            'strategy': self.strategy,
            'timeframe': self.timeframe,
            'expected_duration': self.expected_duration,
            'market_conditions': self.market_conditions
        }

class OllamaAdvanced:
    """Sistema avanzado de IA para trading con múltiples modelos"""
    
    def __init__(self, api_base: str = "http://localhost:11434/v1"):
        self.api_base = api_base
        
        # Modelos disponibles con sus especialidades
        self.models = {
            'deepseek-r1:8b': {
                'specialty': 'fast_analysis',
                'weight': 1.0,
                'timeout': 20
            }
        }
        
        # Cliente OpenAI para Ollama
        if OPENAI_AVAILABLE:
            self.client = OpenAI(api_key="none", base_url=api_base)
        else:
            self.client = None
        
        # Executor para análisis paralelo
        self.executor = ThreadPoolExecutor(max_workers=5)
        
        # Cache de análisis recientes
        self.analysis_cache = {}
        self.cache_ttl = 60  # segundos
        
        # Estrategias de trading
        self.strategies = {
            'scalping': self.analyze_scalping,
            'day_trading': self.analyze_day_trading,
            'swing_trading': self.analyze_swing_trading,
            'position_trading': self.analyze_position_trading,
            'breakout': self.analyze_breakout,
            'mean_reversion': self.analyze_mean_reversion,
            'momentum': self.analyze_momentum,
            'arbitrage': self.analyze_arbitrage
        }
        
        logger.info(f"Ollama Advanced initialized with {len(self.models)} models")
    
    def create_advanced_prompt(self, 
                              symbol: str,
                              market_data: Dict[str, Any],
                              strategy_type: str = 'auto') -> str:
        """Crea un prompt avanzado para análisis de trading"""
        
        prompt = f"""
ELITE TRADER AI ANALYSIS - {symbol}
=====================================
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Strategy Mode: {strategy_type}

MARKET DATA:
------------
Current Price: {market_data.get('current_price', 0):.5f}
24h Change: {market_data.get('change_24h', 0):.2f}%
Volume: {market_data.get('volume', 0):,.0f}
Market Cap Rank: {market_data.get('market_cap_rank', 'N/A')}

TECHNICAL INDICATORS:
--------------------
"""
        
        # Agregar indicadores técnicos
        indicators = market_data.get('indicators', {})
        for timeframe, tf_indicators in indicators.items():
            prompt += f"\n[{timeframe}]:\n"
            
            # RSI
            rsi = tf_indicators.get('rsi', 50)
            prompt += f"  RSI: {rsi:.2f} {'(Oversold)' if rsi < 30 else '(Overbought)' if rsi > 70 else ''}\n"
            
            # MACD
            macd = tf_indicators.get('macd', 0)
            macd_signal = tf_indicators.get('macd_signal', 0)
            prompt += f"  MACD: {macd:.4f} | Signal: {macd_signal:.4f} | Histogram: {(macd-macd_signal):.4f}\n"
            
            # Bollinger Bands
            bb_position = tf_indicators.get('bb_position', 0.5)
            prompt += f"  BB Position: {bb_position:.2%} {'(Upper Band)' if bb_position > 0.8 else '(Lower Band)' if bb_position < 0.2 else ''}\n"
            
            # ATR
            atr = tf_indicators.get('atr', 0)
            atr_percent = tf_indicators.get('atr_percent', 0)
            prompt += f"  ATR: {atr:.5f} ({atr_percent:.2f}% volatility)\n"
            
            # ADX
            adx = tf_indicators.get('adx', 0)
            prompt += f"  ADX: {adx:.2f} {'(Strong Trend)' if adx > 25 else '(No Trend)'}\n"
            
            # Volume
            volume_ratio = tf_indicators.get('volume_ratio', 1)
            prompt += f"  Volume Ratio: {volume_ratio:.2f}x average\n"
        
        # Agregar patrones detectados
        prompt += """
PATTERN ANALYSIS:
----------------
"""
        patterns = market_data.get('patterns', {})
        if patterns:
            for pattern_name, pattern_value in patterns.items():
                if pattern_value != 0:
                    prompt += f"  {pattern_name}: {'Bullish' if pattern_value > 0 else 'Bearish'}\n"
        
        # Agregar análisis de sentimiento
        sentiment = market_data.get('sentiment', 'NEUTRAL')
        prompt += f"""
MARKET SENTIMENT: {sentiment}
CORRELATION ANALYSIS: {market_data.get('correlations', {})}

MARKET PROFILE:
--------------
VWAP: {market_data.get('vwap', 0):.5f}
POC (Point of Control): {market_data.get('poc', 0):.5f}
Value Area High: {market_data.get('va_high', 0):.5f}
Value Area Low: {market_data.get('va_low', 0):.5f}

VOLATILITY METRICS:
------------------
14-day Volatility: {market_data.get('vol_14d', 0):.2f}%
30-day Volatility: {market_data.get('vol_30d', 0):.2f}%
Sharpe Ratio: {market_data.get('sharpe', 0):.2f}

TRADING TASK:
============
Analyze all data and provide a professional trading signal.

REQUIRED OUTPUT FORMAT:
----------------------
ACTION: [BUY/SELL/NO_TRADE]
ENTRY: [exact price]
SL: [stop loss price]
TP1: [first take profit - 30% position]
TP2: [second take profit - 50% position]
TP3: [third take profit - 20% position]
CONFIDENCE: [0-100]%
RRR: [risk reward ratio]
POSITION_SIZE: [0.01-0.10] lots
REASONING: [detailed explanation in one line]
STRATEGY: [strategy name]
TIMEFRAME: [recommended timeframe]
DURATION: [expected trade duration]

IMPORTANT RULES:
1. Only trade if confidence > 65%
2. Risk Reward Ratio must be > 1.5
3. Consider market volatility for SL/TP
4. Use ATR for dynamic stop loss
5. Consider support/resistance levels
6. Account for market sentiment
7. Be precise with all numeric values
8. Think step by step before deciding
"""
        
        return prompt
    
    async def analyze_with_model_async(self, 
                                      model_name: str,
                                      prompt: str,
                                      timeout: int = 30) -> Optional[Dict]:
        """Analiza con un modelo específico de forma asíncrona"""
        try:
            if not self.client:
                return None
                
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=model_name,
                    messages=[
                        {"role": "system", "content": "You are an elite quantitative trader with 20 years of experience."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=500
                ),
                timeout=timeout
            )
            
            return self.parse_ai_response(response.choices[0].message.content)
            
        except asyncio.TimeoutError:
            logger.warning(f"Timeout analyzing with {model_name}")
            return None
        except Exception as e:
            logger.error(f"Error with {model_name}: {e}")
            return None
    
    def parse_ai_response(self, response: str) -> Optional[Dict]:
        """Parsea la respuesta de la IA con manejo robusto de errores"""
        try:
            lines = response.strip().split('\n')
            result = {}
            
            # Buscar patrones específicos en la respuesta completa
            response_upper = response.upper()
            
            # Buscar ACTION
            action_patterns = [r'ACTION:\s*([A-Z_]+)', r'SIGNAL:\s*([A-Z_]+)', r'RECOMMENDATION:\s*([A-Z_]+)']
            for pattern in action_patterns:
                match = re.search(pattern, response_upper)
                if match:
                    action = match.group(1)
                    if action in ['BUY', 'SELL', 'NO_TRADE', 'HOLD']:
                        result['action'] = action
                        break
            
            # Si no encuentra acción específica, usar lógica de sentimiento
            if 'action' not in result:
                if any(word in response_upper for word in ['BUY', 'LONG', 'BULLISH']):
                    result['action'] = 'BUY'
                elif any(word in response_upper for word in ['SELL', 'SHORT', 'BEARISH']):
                    result['action'] = 'SELL'
                else:
                    result['action'] = 'NO_TRADE'
            
            # Buscar precios usando patrones más flexibles
            price_patterns = {
                'entry': [r'ENTRY:\s*([\d.]+)', r'PRICE:\s*([\d.]+)', r'ENTER AT:\s*([\d.]+)'],
                'sl': [r'SL:\s*([\d.]+)', r'STOP LOSS:\s*([\d.]+)', r'STOP:\s*([\d.]+)'],
                'tp1': [r'TP1:\s*([\d.]+)', r'TARGET 1:\s*([\d.]+)', r'TAKE PROFIT:\s*([\d.]+)'],
                'tp2': [r'TP2:\s*([\d.]+)', r'TARGET 2:\s*([\d.]+)'],
                'tp3': [r'TP3:\s*([\d.]+)', r'TARGET 3:\s*([\d.]+)']
            }
            
            for field, patterns in price_patterns.items():
                for pattern in patterns:
                    match = re.search(pattern, response_upper)
                    if match:
                        result[field] = float(match.group(1))
                        break
            
            # Buscar confidence
            conf_patterns = [r'CONFIDENCE:\s*([\d.]+)', r'CONFIDENCE:\s*([\d.]+)%']
            for pattern in conf_patterns:
                match = re.search(pattern, response_upper)
                if match:
                    result['confidence'] = float(match.group(1))
                    break
            
            # Buscar RRR
            rrr_patterns = [r'RRR:\s*([\d.]+)', r'RATIO:\s*([\d.]+)', r'RISK REWARD:\s*([\d.]+)']
            for pattern in rrr_patterns:
                match = re.search(pattern, response_upper)
                if match:
                    result['rrr'] = float(match.group(1))
                    break
            
            # Buscar position size
            size_patterns = [r'POSITION_SIZE:\s*([\d.]+)', r'SIZE:\s*([\d.]+)', r'LOTS:\s*([\d.]+)']
            for pattern in size_patterns:
                match = re.search(pattern, response_upper)
                if match:
                    result['position_size'] = float(match.group(1))
                    break
            
            # Valores por defecto si no se encuentran
            if 'confidence' not in result:
                result['confidence'] = 60  # Default confidence
            
            if 'rrr' not in result and 'entry' in result and 'sl' in result and 'tp1' in result:
                # Calcular RRR si tenemos los precios
                if result['action'] == 'BUY':
                    risk = result['entry'] - result['sl']
                    reward = result['tp1'] - result['entry']
                else:
                    risk = result['sl'] - result['entry']
                    reward = result['entry'] - result['tp1']
                
                result['rrr'] = reward / risk if risk > 0 else 1.5
            
            if 'position_size' not in result:
                result['position_size'] = 0.02  # Default 2% position size
            
            # Agregar TPs faltantes basados en TP1
            if 'tp1' in result:
                if 'tp2' not in result:
                    if result['action'] == 'BUY':
                        result['tp2'] = result['tp1'] * 1.5 - result.get('entry', result['tp1'] * 0.8) * 0.5
                    else:
                        result['tp2'] = result['tp1'] * 0.5 + result.get('entry', result['tp1'] * 1.2) * 0.5
                
                if 'tp3' not in result:
                    result['tp3'] = result.get('tp2', result['tp1'])
            
            # Validar campos mínimos requeridos
            required_fields = ['action']
            if all(field in result for field in required_fields):
                # Agregar información adicional
                result['reasoning'] = "AI analysis based on technical indicators"
                result['strategy'] = "hybrid_ai"
                result['timeframe'] = "1h"
                result['expected_duration'] = "2-8 hours"
                
                return result
            else:
                logger.warning(f"Missing required fields in AI response. Found: {list(result.keys())}")
                return None
                
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            return None
    
    async def ensemble_analysis(self, 
                               symbol: str,
                               market_data: Dict[str, Any]) -> Optional[TradingSignal]:
        """Análisis ensemble usando múltiples modelos y estrategias"""
        
        # Verificar cache
        cache_key = f"{symbol}_{market_data.get('current_price', 0)}"
        if cache_key in self.analysis_cache:
            cached_time, cached_signal = self.analysis_cache[cache_key]
            if (datetime.now() - cached_time).seconds < self.cache_ttl:
                logger.info("Using cached analysis")
                return cached_signal
        
        # Crear prompt
        prompt = self.create_advanced_prompt(symbol, market_data)
        
        # Analizar con múltiples modelos en paralelo
        tasks = []
        for model_name, model_config in self.models.items():
            task = self.analyze_with_model_async(
                model_name, 
                prompt, 
                model_config['timeout']
            )
            tasks.append((model_name, model_config['weight'], task))
        
        # Recopilar resultados
        results = []
        weights = []
        
        for model_name, weight, task in tasks:
            try:
                result = await task
                if result:
                    results.append(result)
                    weights.append(weight)
                    logger.info(f"{model_name}: {result.get('action', 'NO_TRADE')} @ {result.get('confidence', 0)}%")
            except Exception as e:
                logger.error(f"Error getting result from {model_name}: {e}")
        
        if not results:
            return None
        
        # Calcular consenso ponderado
        final_signal = self.calculate_weighted_consensus(results, weights, symbol, market_data)
        
        # Guardar en cache
        if final_signal:
            self.analysis_cache[cache_key] = (datetime.now(), final_signal)
        
        return final_signal
    
    def calculate_weighted_consensus(self, 
                                    results: List[Dict],
                                    weights: List[float],
                                    symbol: str,
                                    market_data: Dict) -> Optional[TradingSignal]:
        """Calcula consenso ponderado de múltiples análisis"""
        
        # Normalizar pesos
        total_weight = sum(weights)
        weights = [w/total_weight for w in weights]
        
        # Calcular scores de acción
        action_scores = {'BUY': 0, 'SELL': 0, 'NO_TRADE': 0}
        
        for result, weight in zip(results, weights):
            action = result.get('action', 'NO_TRADE')
            confidence = result.get('confidence', 50) / 100
            action_scores[action] += weight * confidence
        
        # Determinar acción final
        final_action = max(action_scores, key=action_scores.get)
        
        # Si no hay consenso claro, no operar
        if action_scores[final_action] < 0.5:
            return None
        
        # Calcular parámetros promedio ponderados
        avg_entry = sum(r.get('entry', 0) * w for r, w in zip(results, weights))
        avg_sl = sum(r.get('sl', 0) * w for r, w in zip(results, weights))
        avg_tp1 = sum(r.get('tp1', 0) * w for r, w in zip(results, weights))
        avg_tp2 = sum(r.get('tp2', avg_tp1) * w for r, w in zip(results, weights))
        avg_tp3 = sum(r.get('tp3', avg_tp2) * w for r, w in zip(results, weights))
        avg_confidence = sum(r.get('confidence', 50) * w for r, w in zip(results, weights))
        avg_position_size = sum(r.get('position_size', 0.01) * w for r, w in zip(results, weights))
        
        # Calcular RRR
        if final_action == 'BUY':
            risk = avg_entry - avg_sl
            reward = avg_tp2 - avg_entry
        else:
            risk = avg_sl - avg_entry
            reward = avg_entry - avg_tp2
        
        rrr = reward / risk if risk > 0 else 0
        
        # Validaciones finales
        if rrr < 1.5 or avg_confidence < 65:
            return None
        
        # Crear señal final
        return TradingSignal(
            symbol=symbol,
            action=final_action,
            entry_price=round(avg_entry, 5),
            stop_loss=round(avg_sl, 5),
            take_profit_1=round(avg_tp1, 5),
            take_profit_2=round(avg_tp2, 5),
            take_profit_3=round(avg_tp3, 5),
            confidence=round(avg_confidence, 2),
            risk_reward_ratio=round(rrr, 2),
            position_size=round(avg_position_size, 2),
            reasoning=f"Ensemble consensus from {len(results)} models",
            strategy=self.determine_strategy(market_data),
            timeframe=self.determine_timeframe(market_data),
            expected_duration=self.estimate_duration(market_data),
            market_conditions=market_data
        )
    
    def determine_strategy(self, market_data: Dict) -> str:
        """Determina la mejor estrategia basada en condiciones del mercado"""
        indicators = market_data.get('indicators', {}).get('1h', {})
        
        adx = indicators.get('adx', 0)
        atr_percent = indicators.get('atr_percent', 0)
        volume_ratio = indicators.get('volume_ratio', 1)
        
        if adx > 40:
            return 'momentum'
        elif adx < 20 and atr_percent < 2:
            return 'mean_reversion'
        elif volume_ratio > 2:
            return 'breakout'
        elif atr_percent > 4:
            return 'scalping'
        else:
            return 'swing_trading'
    
    def determine_timeframe(self, market_data: Dict) -> str:
        """Determina el mejor timeframe para operar"""
        volatility = market_data.get('vol_14d', 0)
        
        if volatility > 100:
            return 'M5'
        elif volatility > 50:
            return 'M15'
        elif volatility > 25:
            return 'H1'
        else:
            return 'H4'
    
    def estimate_duration(self, market_data: Dict) -> str:
        """Estima la duración esperada del trade"""
        strategy = self.determine_strategy(market_data)
        
        durations = {
            'scalping': '5-30 minutes',
            'day_trading': '1-4 hours',
            'swing_trading': '1-3 days',
            'position_trading': '1-4 weeks',
            'momentum': '2-8 hours',
            'breakout': '4-12 hours',
            'mean_reversion': '6-24 hours',
            'arbitrage': '1-10 minutes'
        }
        
        return durations.get(strategy, '1-4 hours')
    
    # Estrategias específicas
    def analyze_scalping(self, market_data: Dict) -> Dict:
        """Análisis especializado para scalping"""
        return {'strategy': 'scalping', 'timeframe': 'M1', 'sl_pips': 5, 'tp_pips': 10}
    
    def analyze_day_trading(self, market_data: Dict) -> Dict:
        """Análisis especializado para day trading"""
        return {'strategy': 'day_trading', 'timeframe': 'M15', 'sl_pips': 20, 'tp_pips': 40}
    
    def analyze_swing_trading(self, market_data: Dict) -> Dict:
        """Análisis especializado para swing trading"""
        return {'strategy': 'swing_trading', 'timeframe': 'H4', 'sl_pips': 50, 'tp_pips': 150}
    
    def analyze_position_trading(self, market_data: Dict) -> Dict:
        """Análisis especializado para position trading"""
        return {'strategy': 'position_trading', 'timeframe': 'D1', 'sl_pips': 100, 'tp_pips': 300}
    
    def analyze_breakout(self, market_data: Dict) -> Dict:
        """Análisis especializado para breakout trading"""
        return {'strategy': 'breakout', 'timeframe': 'H1', 'sl_pips': 30, 'tp_pips': 60}
    
    def analyze_mean_reversion(self, market_data: Dict) -> Dict:
        """Análisis especializado para mean reversion"""
        return {'strategy': 'mean_reversion', 'timeframe': 'H1', 'sl_pips': 25, 'tp_pips': 25}
    
    def analyze_momentum(self, market_data: Dict) -> Dict:
        """Análisis especializado para momentum trading"""
        return {'strategy': 'momentum', 'timeframe': 'M30', 'sl_pips': 35, 'tp_pips': 70}
    
    def analyze_arbitrage(self, market_data: Dict) -> Dict:
        """Análisis especializado para arbitrage"""
        return {'strategy': 'arbitrage', 'timeframe': 'M1', 'sl_pips': 3, 'tp_pips': 5}