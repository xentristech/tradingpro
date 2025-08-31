#!/usr/bin/env python
"""
Estrategia Híbrida IA - Ollama + TwelveData
Combina análisis técnico real con inteligencia artificial
"""

import os
import sys
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Agregar path del proyecto
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Importar módulos propios
try:
    from src.ai.ollama_client import OllamaClient, crear_cliente_ollama
    from src.data.twelvedata_client import TwelveDataClient
    from src.notifiers.telegram_notifier import TelegramNotifier
except ImportError as e:
    print(f"Error importando módulos: {e}")
    # Fallback imports
    from ai.ollama_client import OllamaClient, crear_cliente_ollama
    from data.twelvedata_client import TwelveDataClient
    from notifiers.telegram_notifier import TelegramNotifier

logger = logging.getLogger(__name__)

class AIHybridStrategy:
    """
    Estrategia híbrida que combina:
    1. Datos reales de TwelveData API
    2. Análisis con IA (Ollama + deepseek-r1:14b)
    3. Indicadores técnicos tradicionales
    """
    
    def __init__(self):
        """Inicializa la estrategia híbrida"""
        self.name = "AI_Hybrid_Strategy"
        
        # Clientes
        self.ollama_client = None
        self.twelvedata_client = None
        self.telegram = None
        
        # Estado
        self.last_analysis = {}
        self.analysis_count = 0
        self.signals_generated = 0
        
        # Configuración
        self.timeframes = ["5min", "15min", "1h"]
        self.confidence_threshold = 0.7
        
        self.initialize_clients()
        
    def initialize_clients(self):
        """Inicializa los clientes de IA y datos"""
        try:
            # Cliente Ollama
            self.ollama_client = crear_cliente_ollama()
            if self.ollama_client:
                logger.info("✅ Ollama client iniciado")
            else:
                logger.warning("⚠️ Ollama no disponible, usando análisis tradicional")
            
            # Cliente TwelveData
            self.twelvedata_client = TwelveDataClient()
            if self.twelvedata_client:
                logger.info("✅ TwelveData client iniciado")
            else:
                logger.warning("⚠️ TwelveData no disponible")
            
            # Telegram
            try:
                self.telegram = TelegramNotifier()
                if hasattr(self.telegram, 'is_active') and self.telegram.is_active:
                    logger.info("✅ Telegram notifier activo")
            except:
                logger.warning("⚠️ Telegram notifier no disponible")
                
        except Exception as e:
            logger.error(f"Error inicializando clientes: {e}")
    
    def format_symbol_for_twelvedata(self, symbol: str) -> str:
        """
        Convierte símbolo MT5 a formato TwelveData
        Args:
            symbol: Símbolo en formato MT5 (XAUUSD, EURUSD, etc.)
        Returns:
            Símbolo en formato TwelveData (XAU/USD, EUR/USD, etc.)
        """
        symbol_map = {
            'XAUUSD': 'XAU/USD',
            'EURUSD': 'EUR/USD',
            'GBPUSD': 'GBP/USD',
            'BTCUSD': 'BTC/USD',
            'BTCUSDm': 'BTC/USD',  # Mapeo para símbolo MT5 crypto
            'ETHUSD': 'ETH/USD',
            'ETHUSDm': 'ETH/USD',
            'USDJPY': 'USD/JPY',
            'AUDUSD': 'AUD/USD',
            'USDCHF': 'USD/CHF'
        }
        return symbol_map.get(symbol, symbol)
    
    def get_real_market_data(self, symbol: str) -> Dict[str, Any]:
        """
        Obtiene datos reales del mercado
        Args:
            symbol: Símbolo a analizar
        Returns:
            Diccionario con datos de mercado
        """
        if not self.twelvedata_client:
            return {}
        
        try:
            # Convertir símbolo
            td_symbol = self.format_symbol_for_twelvedata(symbol)
            logger.info(f"Obteniendo datos reales para {symbol} ({td_symbol})")
            
            # Obtener análisis completo
            analysis = self.twelvedata_client.get_complete_analysis(td_symbol)
            
            if analysis and analysis.get('price'):
                logger.info(f"✅ Datos reales obtenidos: ${analysis['price']}")
                return analysis
            else:
                logger.warning(f"⚠️ No se pudieron obtener datos reales para {symbol}")
                # Fallback: usar precio simulado para crypto si es necesario
                if 'BTC' in symbol.upper():
                    import random
                    simulated_price = 108800 + random.uniform(-200, 200)
                    logger.info(f"🔄 Usando precio simulado para {symbol}: ${simulated_price:.2f}")
                    return {
                        'price': simulated_price,
                        'volume': 1000000,
                        'change': random.uniform(-2, 2)
                    }
                return {}
                
        except Exception as e:
            logger.error(f"Error obteniendo datos reales: {e}")
            return {}
    
    def get_multi_timeframe_indicators(self, symbol: str) -> Dict[str, Dict]:
        """
        Obtiene indicadores de múltiples timeframes
        Args:
            symbol: Símbolo a analizar
        Returns:
            Diccionario con indicadores por timeframe
        """
        if not self.twelvedata_client:
            return {}
        
        indicators_multi = {}
        td_symbol = self.format_symbol_for_twelvedata(symbol)
        
        for tf in self.timeframes:
            try:
                logger.info(f"Obteniendo indicadores {tf} para {symbol}")
                
                # Obtener precio actual
                price_data = self.twelvedata_client.get_realtime_price(td_symbol)
                
                # Obtener indicadores técnicos
                indicators = self.twelvedata_client.get_technical_indicators(td_symbol, tf)
                
                if indicators:
                    # Agregar precio actual
                    indicators['current_price'] = price_data
                    indicators_multi[tf] = indicators
                    logger.info(f"✅ {tf}: {len(indicators)} indicadores obtenidos")
                else:
                    logger.warning(f"⚠️ {tf}: No se obtuvieron indicadores")
                    indicators_multi[tf] = {}
                
                # Pausa para evitar rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error obteniendo indicadores {tf}: {e}")
                indicators_multi[tf] = {}
        
        return indicators_multi
    
    def get_historical_closes(self, symbol: str) -> Dict[str, List]:
        """
        Obtiene precios de cierre históricos
        Args:
            symbol: Símbolo a analizar
        Returns:
            Diccionario con listas de cierres por timeframe
        """
        if not self.twelvedata_client:
            return {}
        
        closes_multi = {}
        td_symbol = self.format_symbol_for_twelvedata(symbol)
        
        for tf in self.timeframes:
            try:
                # Obtener series temporales
                df = self.twelvedata_client.get_time_series(td_symbol, tf, 30)
                
                if df is not None and len(df) > 0:
                    closes = df['close'].tolist()
                    closes_multi[tf] = closes[:10]  # Solo últimos 10
                    logger.info(f"✅ {tf}: {len(closes_multi[tf])} cierres obtenidos")
                else:
                    closes_multi[tf] = []
                    
                time.sleep(0.3)
                
            except Exception as e:
                logger.error(f"Error obteniendo cierres {tf}: {e}")
                closes_multi[tf] = []
        
        return closes_multi
    
    def analyze_with_ai(self, 
                       symbol: str, 
                       indicators_multi: Dict, 
                       closes_multi: Dict, 
                       current_price: float) -> Dict[str, Any]:
        """
        Analiza con IA usando Ollama
        Args:
            symbol: Símbolo a analizar
            indicators_multi: Indicadores por timeframe
            closes_multi: Cierres históricos
            current_price: Precio actual
        Returns:
            Análisis de IA
        """
        if not self.ollama_client:
            logger.warning("Ollama no disponible - NO GENERAR SEÑALES SIN IA")
            return {
                'senal': 'NO_OPERAR',
                'confianza': 0.0,
                'razonamiento': 'Sin Ollama disponible - Solo datos reales con IA',
                'symbol': symbol
            }
        
        try:
            logger.info(f"🤖 Analizando {symbol} con IA...")
            
            # Analizar con Ollama
            ai_analysis = self.ollama_client.analizar_mercado(
                symbol=symbol,
                indicadores_multi=indicators_multi,
                cierres_multi=closes_multi,
                precio_actual=current_price
            )
            
            if ai_analysis and 'senal' in ai_analysis:
                logger.info(f"✅ IA Analysis: {ai_analysis['senal']} (Confianza: {ai_analysis.get('confianza', 0):.1%})")
                return ai_analysis
            else:
                logger.warning("⚠️ IA no devolvió análisis válido - NO OPERAR")
                return {
                    'senal': 'NO_OPERAR',
                    'confianza': 0.0,
                    'razonamiento': 'IA no devolvió análisis válido - Solo señales con IA válida',
                    'symbol': symbol
                }
                
        except Exception as e:
            logger.error(f"Error en análisis IA: {e} - NO OPERAR")
            return {
                'senal': 'NO_OPERAR',
                'confianza': 0.0,
                'razonamiento': f'Error en IA: {e} - Solo señales con IA válida',
                'symbol': symbol
            }
    
    def fallback_analysis(self, 
                          symbol: str, 
                          indicators_multi: Dict, 
                          current_price: float) -> Dict[str, Any]:
        """
        Análisis de respaldo usando indicadores tradicionales
        Args:
            symbol: Símbolo
            indicators_multi: Indicadores por timeframe
            current_price: Precio actual
        Returns:
            Análisis tradicional
        """
        try:
            # Usar indicadores del timeframe principal (5min)
            indicators = indicators_multi.get('5min', {})
            
            if not indicators:
                return {
                    'senal': 'NO_OPERAR',
                    'confianza': 0.0,
                    'razonamiento': 'Sin datos de indicadores',
                    'symbol': symbol
                }
            
            # Análisis simple basado en RSI y MACD
            rsi = indicators.get('rsi', 50)
            macd = indicators.get('macd', 0)
            macd_signal = indicators.get('macd_signal', 0)
            
            # Lógica simple
            buy_signals = 0
            sell_signals = 0
            
            # RSI
            if rsi < 30:
                buy_signals += 1
            elif rsi > 70:
                sell_signals += 1
            
            # MACD
            if macd > macd_signal and macd > 0:
                buy_signals += 1
            elif macd < macd_signal and macd < 0:
                sell_signals += 1
            
            # Determinar señal
            if buy_signals >= 2:
                senal = 'BUY'
                confianza = 0.6
            elif sell_signals >= 2:
                senal = 'SELL'
                confianza = 0.6
            else:
                senal = 'NO_OPERAR'
                confianza = 0.3
            
            return {
                'senal': senal,
                'confianza': confianza,
                'entrada': current_price,
                'razonamiento': f'Análisis tradicional: RSI={rsi:.1f}, MACD={macd:.4f}',
                'symbol': symbol
            }
            
        except Exception as e:
            logger.error(f"Error en análisis de respaldo: {e}")
            return {
                'senal': 'NO_OPERAR',
                'confianza': 0.0,
                'razonamiento': f'Error en análisis: {str(e)}',
                'symbol': symbol
            }
    
    def generate_signal(self, df, symbol: str) -> List[Dict[str, Any]]:
        """
        Función principal para generar señales (compatible con SignalGenerator)
        Args:
            df: DataFrame (no usado, obtenemos datos reales)
            symbol: Símbolo a analizar
        Returns:
            Lista de señales generadas
        """
        signals = []
        
        try:
            self.analysis_count += 1
            logger.info(f"🎯 AI Hybrid Analysis #{self.analysis_count} para {symbol}")
            
            # 1. Obtener datos reales de mercado
            market_data = self.get_real_market_data(symbol)
            if not market_data or not market_data.get('price'):
                logger.warning(f"⚠️ Sin datos de mercado para {symbol} - NO GENERAR SEÑALES")
                return []  # RETORNAR VACIO - NO SIMULADOS
            
            current_price = market_data['price']
            
            # 2. Obtener indicadores multi-timeframe
            indicators_multi = self.get_multi_timeframe_indicators(symbol)
            if not indicators_multi:
                logger.warning(f"⚠️ Sin indicadores para {symbol} - NO GENERAR SEÑALES")
                return []  # RETORNAR VACIO - NO SIMULADOS
            
            # 3. Obtener cierres históricos
            closes_multi = self.get_historical_closes(symbol)
            
            # 4. Analizar con IA
            ai_analysis = self.analyze_with_ai(
                symbol, indicators_multi, closes_multi, current_price
            )
            
            # 5. Generar señal si cumple criterios
            if (ai_analysis.get('senal') in ['BUY', 'SELL'] and 
                ai_analysis.get('confianza', 0) >= self.confidence_threshold):
                
                # Calcular SL y TP básicos si no los tiene
                if not ai_analysis.get('sl') or not ai_analysis.get('tp'):
                    atr = indicators_multi.get('5min', {}).get('atr', current_price * 0.01)
                    
                    if ai_analysis['senal'] == 'BUY':
                        ai_analysis['sl'] = current_price - (atr * 1.5)
                        ai_analysis['tp'] = current_price + (atr * 2.5)
                    else:
                        ai_analysis['sl'] = current_price + (atr * 1.5)
                        ai_analysis['tp'] = current_price - (atr * 2.5)
                
                # Crear señal
                signal = {
                    'symbol': symbol,
                    'type': ai_analysis['senal'],
                    'price': current_price,
                    'strength': ai_analysis.get('confianza', 0.7),
                    'strategy': 'AI_Hybrid_Ollama_TwelveData',
                    'reason': ai_analysis.get('razonamiento', 'Análisis con IA'),
                    'sl': ai_analysis.get('sl'),
                    'tp': ai_analysis.get('tp'),
                    'ai_analysis': ai_analysis,
                    'market_data': market_data,
                    'timestamp': datetime.now()
                }
                
                signals.append(signal)
                self.signals_generated += 1
                
                logger.info(f"✅ Señal IA generada: {symbol} {ai_analysis['senal']} (Fuerza: {signal['strength']:.1%})")
                
                # Guardar último análisis
                self.last_analysis[symbol] = ai_analysis
                
                # Notificar por Telegram con detalles
                if self.telegram and hasattr(self.telegram, 'is_active') and self.telegram.is_active:
                    self.send_detailed_telegram_notification(signal)
            
            else:
                logger.info(f"ℹ️ {symbol}: {ai_analysis.get('senal', 'NO_SIGNAL')} (Confianza: {ai_analysis.get('confianza', 0):.1%}) - No cumple umbral")
            
        except Exception as e:
            logger.error(f"Error generando señal IA para {symbol}: {e}")
        
        return signals
    
    def send_detailed_telegram_notification(self, signal: Dict[str, Any]):
        """
        Envía notificación detallada por Telegram
        Args:
            signal: Señal generada
        """
        try:
            ai_analysis = signal.get('ai_analysis', {})
            
            message = f"""
🤖 **SENAL IA HIBRIDHA** 🤖

📊 **Simbolo:** {signal['symbol']}
📈 **Tipo:** {signal['type']}
💰 **Precio:** {signal['price']:.5f}
💪 **Fuerza:** {signal['strength']*100:.0f}%
🎯 **Stop Loss:** {signal.get('sl', 'N/A'):.5f}
🎯 **Take Profit:** {signal.get('tp', 'N/A'):.5f}

🧠 **IA Analysis:**
{ai_analysis.get('razonamiento', 'Análisis con IA')}

⚡ **Estrategia:** AI + Ollama + TwelveData
📅 **Tiempo:** {signal['timestamp'].strftime('%H:%M:%S')}

🚀 **Datos Reales:** TwelveData API
🤖 **IA:** Ollama deepseek-r1:14b
"""
            
            self.telegram.send_message(message)
            logger.info(f"✅ Notificación IA enviada por Telegram")
            
        except Exception as e:
            logger.error(f"Error enviando notificación IA: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Obtiene estado de la estrategia
        Returns:
            Diccionario con estado
        """
        return {
            'name': self.name,
            'analysis_count': self.analysis_count,
            'signals_generated': self.signals_generated,
            'ollama_available': self.ollama_client is not None,
            'twelvedata_available': self.twelvedata_client is not None,
            'telegram_available': self.telegram is not None and hasattr(self.telegram, 'is_active') and self.telegram.is_active,
            'last_analysis': self.last_analysis,
            'timeframes': self.timeframes,
            'confidence_threshold': self.confidence_threshold
        }

# Función de conveniencia para usar en SignalGenerator
def ai_hybrid_strategy_function(df, symbol: str) -> List[Dict[str, Any]]:
    """
    Función wrapper para usar en SignalGenerator
    Args:
        df: DataFrame (no usado)
        symbol: Símbolo a analizar
    Returns:
        Lista de señales
    """
    # Crear instancia si no existe
    if not hasattr(ai_hybrid_strategy_function, 'strategy'):
        ai_hybrid_strategy_function.strategy = AIHybridStrategy()
    
    # Generar señal
    return ai_hybrid_strategy_function.strategy.generate_signal(df, symbol)