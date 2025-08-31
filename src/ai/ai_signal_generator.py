"""
AI Signal Generator with TwelveData & Ollama
Generador de Señales con Inteligencia Artificial
Version: 4.0.0
"""
import os
import sys
import json
import time
import asyncio
import logging
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import ollama

# Configurar path
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from notifiers.telegram_notifier import TelegramNotifier
from risk.risk_manager import RiskManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.FileHandler('logs/ai_signal_generator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AISignalGenerator:
    """
    Generador de señales usando TwelveData API + Ollama AI
    """
    
    def __init__(self):
        """Inicializa el generador con IA"""
        logger.info("="*60)
        logger.info(" AI SIGNAL GENERATOR - TWELVEDATA + OLLAMA")
        logger.info("="*60)
        
        # Cargar configuración
        load_dotenv('configs/.env')
        
        # API Keys
        self.twelvedata_api_key = os.getenv('TWELVEDATA_API_KEY')
        if not self.twelvedata_api_key:
            logger.error("TWELVEDATA_API_KEY no configurada en .env")
            raise ValueError("TwelveData API key requerida")
        
        # Símbolos principales (incluyendo crypto y oro)
        self.symbols = {
            'forex': ['EUR/USD', 'GBP/USD', 'USD/JPY'],
            'crypto': ['BTC/USD', 'ETH/USD'],
            'commodities': ['XAU/USD']  # Oro
        }
        
        # Configuración de intervals para análisis multi-timeframe
        self.intervals = ['5min', '15min', '1h', '4h']
        
        # Componentes
        self.telegram = None
        self.risk_manager = RiskManager()
        self.ollama_client = None
        
        # Estado
        self.signals_cache = {}
        self.ai_analyses = []
        
        # Inicializar componentes
        self._initialize_components()
    
    def _initialize_components(self):
        """Inicializa componentes del sistema"""
        try:
            # Telegram
            if os.getenv('TELEGRAM_TOKEN') and os.getenv('TELEGRAM_CHAT_ID'):
                self.telegram = TelegramNotifier()
                logger.info("Telegram notifier activado")
            
            # Verificar Ollama
            try:
                self.ollama_client = ollama.Client()
                models = self.ollama_client.list()
                logger.info(f"Ollama conectado - Modelos disponibles: {len(models.get('models', []))}")
            except Exception as e:
                logger.warning(f"Ollama no disponible, usando análisis tradicional: {e}")
                self.ollama_client = None
            
            logger.info("Componentes inicializados correctamente")
            
        except Exception as e:
            logger.error(f"Error inicializando componentes: {e}")
            raise
    
    def get_twelvedata_indicators(self, symbol: str, interval: str = '15min') -> Dict:
        """
        Obtiene indicadores técnicos de TwelveData
        """
        try:
            base_url = "https://api.twelvedata.com"
            
            # Obtener múltiples indicadores en una llamada
            indicators = ['rsi', 'macd', 'bbands', 'stoch', 'adx', 'atr', 'ema']
            results = {}
            
            # Precio actual y OHLCV
            response = requests.get(
                f"{base_url}/time_series",
                params={
                    'symbol': symbol,
                    'interval': interval,
                    'apikey': self.twelvedata_api_key,
                    'outputsize': 100,
                    'format': 'JSON'
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'values' in data:
                    results['price_data'] = data['values']
                    current_price = float(data['values'][0]['close'])
                    results['current_price'] = current_price
                    
                    logger.info(f"{symbol} @ {current_price:.5f}")
            
            # Obtener indicadores técnicos
            for indicator in indicators:
                try:
                    response = requests.get(
                        f"{base_url}/{indicator}",
                        params={
                            'symbol': symbol,
                            'interval': interval,
                            'apikey': self.twelvedata_api_key,
                            'outputsize': 30,
                            'format': 'JSON'
                        },
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if 'values' in data:
                            results[indicator] = data['values']
                            
                except Exception as e:
                    logger.warning(f"Error obteniendo {indicator} para {symbol}: {e}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error en TwelveData API para {symbol}: {e}")
            return {}
    
    async def analyze_with_ollama(self, symbol: str, market_data: Dict) -> Dict:
        """
        Analiza datos del mercado usando Ollama AI
        """
        if not self.ollama_client:
            return self._traditional_analysis(symbol, market_data)
        
        try:
            # Preparar contexto para Ollama
            current_price = market_data.get('current_price', 0)
            
            # Extraer últimos valores de indicadores
            latest_indicators = {}
            if 'rsi' in market_data and market_data['rsi']:
                latest_indicators['RSI'] = market_data['rsi'][0].get('rsi', 'N/A')
            
            if 'macd' in market_data and market_data['macd']:
                macd_data = market_data['macd'][0]
                latest_indicators['MACD'] = macd_data.get('macd', 'N/A')
                latest_indicators['MACD_Signal'] = macd_data.get('macd_signal', 'N/A')
            
            if 'bbands' in market_data and market_data['bbands']:
                bb_data = market_data['bbands'][0]
                latest_indicators['BB_Upper'] = bb_data.get('upper_band', 'N/A')
                latest_indicators['BB_Lower'] = bb_data.get('lower_band', 'N/A')
            
            # Construir prompt para Ollama
            prompt = f"""
            Analiza los siguientes datos del mercado para {symbol} y genera una señal de trading:
            
            Precio actual: {current_price}
            
            Indicadores técnicos:
            {json.dumps(latest_indicators, indent=2)}
            
            Basándote en estos datos, responde en formato JSON:
            {{
                "action": "BUY/SELL/HOLD",
                "confidence": 0.0-1.0,
                "stop_loss": precio_sugerido,
                "take_profit": precio_sugerido,
                "reasoning": "explicación breve"
            }}
            
            Considera:
            1. Condiciones de sobrecompra/sobreventa (RSI)
            2. Momentum y tendencia (MACD)
            3. Volatilidad (Bollinger Bands)
            4. Gestión de riesgo (ratio 1:2 mínimo)
            """
            
            # Consultar Ollama
            response = self.ollama_client.generate(
                model='deepseek-r1:8b',  # Usando DeepSeek R1 8B
                prompt=prompt,
                format='json'
            )
            
            if response and 'response' in response:
                try:
                    ai_analysis = json.loads(response['response'])
                    
                    # Validar y ajustar respuesta
                    ai_analysis['symbol'] = symbol
                    ai_analysis['timestamp'] = datetime.now().isoformat()
                    ai_analysis['ai_model'] = 'ollama-llama2'
                    
                    logger.info(f"[OLLAMA] {symbol}: {ai_analysis['action']} (Confianza: {ai_analysis['confidence']:.1%})")
                    
                    return ai_analysis
                    
                except json.JSONDecodeError:
                    logger.warning("Respuesta de Ollama no es JSON válido, usando análisis tradicional")
                    return self._traditional_analysis(symbol, market_data)
            
        except Exception as e:
            logger.error(f"Error en análisis con Ollama: {e}")
            return self._traditional_analysis(symbol, market_data)
    
    def _traditional_analysis(self, symbol: str, market_data: Dict) -> Dict:
        """
        Análisis tradicional cuando Ollama no está disponible
        """
        try:
            current_price = market_data.get('current_price', 0)
            
            # Inicializar señal
            signal = {
                'action': 'HOLD',
                'confidence': 0.0,
                'stop_loss': None,
                'take_profit': None,
                'reasoning': [],
                'symbol': symbol,
                'timestamp': datetime.now().isoformat(),
                'ai_model': 'traditional'
            }
            
            score = 0
            max_score = 0
            
            # Analizar RSI
            if 'rsi' in market_data and market_data['rsi']:
                rsi_value = float(market_data['rsi'][0].get('rsi', 50))
                max_score += 2
                
                if rsi_value < 30:
                    score += 2
                    signal['reasoning'].append(f"RSI sobreventa ({rsi_value:.1f})")
                    signal['action'] = 'BUY'
                elif rsi_value > 70:
                    score += 2
                    signal['reasoning'].append(f"RSI sobrecompra ({rsi_value:.1f})")
                    signal['action'] = 'SELL'
                elif 40 < rsi_value < 60:
                    score += 1
                    signal['reasoning'].append(f"RSI neutral ({rsi_value:.1f})")
            
            # Analizar MACD
            if 'macd' in market_data and market_data['macd']:
                macd_data = market_data['macd'][0]
                macd = float(macd_data.get('macd', 0))
                macd_signal = float(macd_data.get('macd_signal', 0))
                max_score += 2
                
                if macd > macd_signal and macd > 0:
                    score += 2
                    signal['reasoning'].append("MACD bullish crossover")
                    if signal['action'] == 'HOLD':
                        signal['action'] = 'BUY'
                elif macd < macd_signal and macd < 0:
                    score += 2
                    signal['reasoning'].append("MACD bearish crossover")
                    if signal['action'] == 'HOLD':
                        signal['action'] = 'SELL'
            
            # Analizar Bollinger Bands
            if 'bbands' in market_data and market_data['bbands']:
                bb_data = market_data['bbands'][0]
                upper_band = float(bb_data.get('upper_band', 0))
                lower_band = float(bb_data.get('lower_band', 0))
                max_score += 2
                
                if current_price <= lower_band:
                    score += 2
                    signal['reasoning'].append("Precio en banda inferior de Bollinger")
                    if signal['action'] != 'SELL':
                        signal['action'] = 'BUY'
                elif current_price >= upper_band:
                    score += 2
                    signal['reasoning'].append("Precio en banda superior de Bollinger")
                    if signal['action'] != 'BUY':
                        signal['action'] = 'SELL'
            
            # Calcular confianza
            if max_score > 0:
                signal['confidence'] = score / max_score
            
            # Calcular SL y TP si hay señal
            if signal['action'] in ['BUY', 'SELL']:
                # Usar ATR o 2% del precio si no hay ATR
                atr = 0.02 * current_price
                if 'atr' in market_data and market_data['atr']:
                    atr = float(market_data['atr'][0].get('atr', atr))
                
                if signal['action'] == 'BUY':
                    signal['stop_loss'] = current_price - (atr * 1.5)
                    signal['take_profit'] = current_price + (atr * 3)
                else:  # SELL
                    signal['stop_loss'] = current_price + (atr * 1.5)
                    signal['take_profit'] = current_price - (atr * 3)
            
            return signal
            
        except Exception as e:
            logger.error(f"Error en análisis tradicional: {e}")
            return {
                'action': 'HOLD',
                'confidence': 0.0,
                'reasoning': [f"Error: {str(e)}"],
                'symbol': symbol,
                'timestamp': datetime.now().isoformat()
            }
    
    async def generate_signals(self):
        """
        Genera señales para todos los símbolos configurados
        """
        all_signals = []
        
        logger.info("\n" + "="*60)
        logger.info(" GENERANDO SEÑALES CON IA")
        logger.info("="*60)
        
        # Analizar cada categoría
        for category, symbols in self.symbols.items():
            logger.info(f"\n[{category.upper()}]")
            
            for symbol in symbols:
                try:
                    # Obtener datos de TwelveData
                    logger.info(f"\nAnalizando {symbol}...")
                    market_data = self.get_twelvedata_indicators(symbol, '15min')
                    
                    if not market_data or 'current_price' not in market_data:
                        logger.warning(f"No hay datos disponibles para {symbol}")
                        continue
                    
                    # Analizar con IA
                    signal = await self.analyze_with_ollama(symbol, market_data)
                    
                    # Agregar categoría
                    signal['category'] = category
                    
                    # Guardar señal
                    all_signals.append(signal)
                    
                    # Mostrar resultado
                    if signal['action'] != 'HOLD':
                        logger.info(f"  [SEÑAL] {signal['action']}")
                        logger.info(f"  Confianza: {signal['confidence']:.1%}")
                        logger.info(f"  SL: {signal['stop_loss']:.5f} | TP: {signal['take_profit']:.5f}")
                        logger.info(f"  Razón: {', '.join(signal['reasoning'])}")
                        
                        # Notificar señales fuertes
                        if signal['confidence'] >= 0.7:
                            await self.notify_strong_signal(signal)
                    else:
                        logger.info(f"  [HOLD] Sin señal clara")
                    
                    # Rate limiting para API
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"Error procesando {symbol}: {e}")
        
        return all_signals
    
    async def notify_strong_signal(self, signal: Dict):
        """
        Notifica señales fuertes por Telegram
        """
        if not self.telegram:
            return
        
        try:
            message = f"""
🤖 **SEÑAL IA DETECTADA**

📊 **Símbolo:** {signal['symbol']}
📈 **Acción:** {signal['action']}
💯 **Confianza:** {signal['confidence']:.1%}
🎯 **Precio actual:** {signal.get('current_price', 'N/A')}

🛡️ **Stop Loss:** {signal['stop_loss']:.5f}
🎯 **Take Profit:** {signal['take_profit']:.5f}

📝 **Análisis:**
{chr(10).join('• ' + r for r in signal['reasoning'])}

🤖 **Modelo:** {signal.get('ai_model', 'N/A')}
⏰ **Hora:** {datetime.now().strftime('%H:%M:%S')}
"""
            
            await self.telegram.send_message(message)
            logger.info(f"Notificación enviada para {signal['symbol']}")
            
        except Exception as e:
            logger.error(f"Error enviando notificación: {e}")
    
    async def execute_signal_mt5(self, signal: Dict) -> bool:
        """
        Ejecuta una señal en MetaTrader 5
        """
        try:
            # Mapear símbolo de TwelveData a MT5
            mt5_symbol = signal['symbol'].replace('/', '').replace('BTC', 'BTCUSD').replace('XAU', 'XAUUSD')
            
            # Verificar si el símbolo está disponible en MT5
            symbol_info = mt5.symbol_info(mt5_symbol)
            if not symbol_info or not symbol_info.visible:
                logger.warning(f"{mt5_symbol} no disponible en MT5")
                return False
            
            # Obtener precio actual de MT5
            tick = mt5.symbol_info_tick(mt5_symbol)
            if not tick:
                return False
            
            # Calcular volumen
            account_info = mt5.account_info()
            position_size = self.risk_manager.calculate_position_size(
                account_balance=account_info.balance,
                stop_loss_pips=30
            )
            
            volume = max(symbol_info.volume_min, min(position_size, symbol_info.volume_max))
            
            # Preparar orden
            if signal['action'] == 'BUY':
                order_type = mt5.ORDER_TYPE_BUY
                price = tick.ask
            else:
                order_type = mt5.ORDER_TYPE_SELL
                price = tick.bid
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": mt5_symbol,
                "volume": volume,
                "type": order_type,
                "price": price,
                "sl": signal['stop_loss'],
                "tp": signal['take_profit'],
                "deviation": 20,
                "magic": 999999,
                "comment": f"AI_{signal.get('ai_model', 'signal')[:10]}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Enviar orden
            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(f"✅ Trade ejecutado: {mt5_symbol} {signal['action']} @ {price:.5f}")
                
                if self.telegram:
                    await self.telegram.send_message(
                        f"✅ **TRADE EJECUTADO**\n\n"
                        f"Ticket: #{result.order}\n"
                        f"Símbolo: {mt5_symbol}\n"
                        f"Tipo: {signal['action']}\n"
                        f"Volumen: {volume}\n"
                        f"Precio: {price:.5f}\n"
                        f"SL: {signal['stop_loss']:.5f}\n"
                        f"TP: {signal['take_profit']:.5f}\n\n"
                        f"Confianza IA: {signal['confidence']:.1%}"
                    )
                
                return True
            else:
                logger.warning(f"Trade rechazado: {result.comment if result else 'Unknown'}")
                return False
                
        except Exception as e:
            logger.error(f"Error ejecutando señal: {e}")
            return False
    
    async def run(self):
        """
        Loop principal del generador de señales IA
        """
        logger.info("\n🤖 AI Signal Generator iniciado")
        logger.info(f"📊 Símbolos monitoreados: {sum(len(s) for s in self.symbols.values())}")
        logger.info(f"🔧 TwelveData API: {'✅' if self.twelvedata_api_key else '❌'}")
        logger.info(f"🧠 Ollama AI: {'✅' if self.ollama_client else '❌ (usando análisis tradicional)'}")
        
        # Conectar a MT5
        if not mt5.initialize():
            logger.error("No se pudo conectar a MT5")
            return
        
        account = mt5.account_info()
        if account:
            logger.info(f"💰 Cuenta MT5: {account.login} | Balance: ${account.balance:.2f}")
        
        iteration = 0
        
        try:
            while True:
                iteration += 1
                logger.info(f"\n[Iteración {iteration}] - {datetime.now().strftime('%H:%M:%S')}")
                
                # Generar señales
                signals = await self.generate_signals()
                
                # Filtrar señales fuertes
                strong_signals = [s for s in signals if s['confidence'] >= 0.7 and s['action'] != 'HOLD']
                
                if strong_signals:
                    logger.info(f"\n📊 {len(strong_signals)} señales fuertes detectadas")
                    
                    # Ejecutar la mejor señal
                    best_signal = max(strong_signals, key=lambda x: x['confidence'])
                    
                    logger.info(f"Ejecutando mejor señal: {best_signal['symbol']} {best_signal['action']}")
                    success = await self.execute_signal_mt5(best_signal)
                    
                    if success:
                        logger.info("✅ Señal ejecutada exitosamente")
                else:
                    logger.info("No hay señales fuertes en este momento")
                
                # Esperar antes del próximo análisis
                logger.info(f"Próximo análisis en 5 minutos...")
                await asyncio.sleep(300)  # 5 minutos
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Sistema detenido por usuario")
        except Exception as e:
            logger.error(f"Error en loop principal: {e}")
        finally:
            mt5.shutdown()
            logger.info("Sistema finalizado")

async def main():
    """Función principal"""
    generator = AISignalGenerator()
    await generator.run()

if __name__ == "__main__":
    asyncio.run(main())