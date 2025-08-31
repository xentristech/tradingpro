#!/usr/bin/env python3
"""
AI SIGNAL MONITOR - Monitor inteligente del generador de señales
Analiza la calidad y precisión de señales generadas vs mercado real
"""
import MetaTrader5 as mt5
import requests
import json
import time
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
from advanced_analysis import AdvancedAnalyzer

load_dotenv('.env')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AISignalMonitor:
    def __init__(self):
        self.api_key = os.getenv('TWELVEDATA_API_KEY', '23d17ce5b7044ad5aef9766770a6252b')
        self.ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        self.ollama_model = 'gemma3:4b'
        self.analyzer = AdvancedAnalyzer()
        self.signal_history = []
        
    def get_current_market_sentiment(self, symbols):
        """Obtener sentimiento general del mercado"""
        try:
            market_data = {}
            
            for symbol in symbols:
                # Normalizar símbolo para TwelveData
                if 'XAU' in symbol or 'GOLD' in symbol:
                    td_symbol = 'XAU/USD'
                elif 'BTC' in symbol:
                    td_symbol = 'BTC/USD'
                elif 'ETH' in symbol:
                    td_symbol = 'ETH/USD'
                else:
                    td_symbol = symbol
                
                # Obtener datos múltiples
                data = {}
                
                # Precio actual
                price_url = f"https://api.twelvedata.com/price"
                price_params = {'symbol': td_symbol, 'apikey': self.api_key}
                price_response = requests.get(price_url, params=price_params, timeout=8)
                
                if price_response.status_code == 200:
                    price_data = price_response.json()
                    data['price'] = float(price_data.get('price', 0))
                
                # RSI
                rsi_url = f"https://api.twelvedata.com/rsi"
                rsi_params = {'symbol': td_symbol, 'interval': '15min', 'time_period': 14, 'apikey': self.api_key}
                rsi_response = requests.get(rsi_url, params=rsi_params, timeout=8)
                
                if rsi_response.status_code == 200:
                    rsi_data = rsi_response.json()
                    if 'values' in rsi_data and rsi_data['values']:
                        data['rsi'] = float(rsi_data['values'][0]['rsi'])
                
                # Volatilidad (usando time series)
                ts_url = f"https://api.twelvedata.com/time_series"
                ts_params = {'symbol': td_symbol, 'interval': '15min', 'outputsize': 20, 'apikey': self.api_key}
                ts_response = requests.get(ts_url, params=ts_params, timeout=10)
                
                if ts_response.status_code == 200:
                    ts_data = ts_response.json()
                    if 'values' in ts_data and ts_data['values']:
                        closes = [float(v['close']) for v in ts_data['values'][:10]]
                        if len(closes) > 1:
                            # Calcular volatilidad simple
                            avg_price = sum(closes) / len(closes)
                            variance = sum((price - avg_price) ** 2 for price in closes) / len(closes)
                            volatility = (variance ** 0.5) / avg_price * 100
                            data['volatility'] = volatility
                
                market_data[symbol] = data
                time.sleep(0.5)  # Evitar rate limiting
            
            return market_data
            
        except Exception as e:
            logger.error(f"Error obteniendo sentimiento mercado: {e}")
            return {}
    
    def ai_evaluate_signal_quality(self, symbol, signal_data, market_data):
        """IA evalúa la calidad de una señal generada"""
        try:
            market_info = market_data.get(symbol, {})
            
            prompt = f"""Evalúa la calidad de esta señal de trading como experto analista:

SEÑAL GENERADA:
- Símbolo: {symbol}
- Señal: {signal_data.get('signal', 'N/A')}
- Confianza: {signal_data.get('confidence', 0):.1%}
- Razones: {', '.join(signal_data.get('reasons', []))}
- Precio señal: ${signal_data.get('price', 0):.2f}

DATOS MERCADO REAL (TwelveData):
- Precio actual: ${market_info.get('price', 0):.2f}
- RSI real: {market_info.get('rsi', 50):.1f}
- Volatilidad: {market_info.get('volatility', 0):.1f}%

CRITERIOS EVALUACIÓN:
- ¿La señal es coherente con datos reales?
- ¿El timing es apropiado?
- ¿La confianza está justificada?
- ¿Hay riesgos no considerados?

Responde SOLO este JSON:
{{"quality_score": 85, "timing": "EXCELLENT/GOOD/FAIR/POOR", "risk_assessment": "LOW/MEDIUM/HIGH", "recommendation": "EXECUTE/WAIT/IGNORE", "analysis": "Tu evaluación aquí"}}"""

            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 200}
            }
            
            response = requests.post(f"{self.ollama_host}/api/generate", json=payload, timeout=25)
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get('response', '').strip()
                
                # Extraer JSON
                start = ai_response.find('{')
                end = ai_response.rfind('}') + 1
                
                if start != -1 and end > start:
                    json_str = ai_response[start:end]
                    try:
                        parsed = json.loads(json_str)
                        return {
                            'quality_score': parsed.get('quality_score', 50),
                            'timing': parsed.get('timing', 'FAIR'),
                            'risk_assessment': parsed.get('risk_assessment', 'MEDIUM'),
                            'recommendation': parsed.get('recommendation', 'WAIT'),
                            'analysis': parsed.get('analysis', 'Sin análisis detallado')
                        }
                    except json.JSONDecodeError:
                        return self._fallback_evaluation(signal_data, market_info)
            
            return self._fallback_evaluation(signal_data, market_info)
            
        except Exception as e:
            logger.error(f"Error evaluación IA señal: {e}")
            return self._fallback_evaluation(signal_data, market_data.get(symbol, {}))
    
    def _fallback_evaluation(self, signal_data, market_info):
        """Evaluación de respaldo"""
        confidence = signal_data.get('confidence', 0)
        
        if confidence > 0.7:
            return {
                'quality_score': 75,
                'timing': 'GOOD',
                'risk_assessment': 'MEDIUM',
                'recommendation': 'EXECUTE',
                'analysis': f'Alta confianza {confidence:.1%}'
            }
        elif confidence > 0.5:
            return {
                'quality_score': 60,
                'timing': 'FAIR', 
                'risk_assessment': 'MEDIUM',
                'recommendation': 'WAIT',
                'analysis': f'Confianza moderada {confidence:.1%}'
            }
        else:
            return {
                'quality_score': 40,
                'timing': 'POOR',
                'risk_assessment': 'HIGH',
                'recommendation': 'IGNORE',
                'analysis': f'Baja confianza {confidence:.1%}'
            }
    
    def monitor_signal_generation(self):
        """Monitor principal del generador de señales"""
        print("=== AI SIGNAL MONITOR INICIADO ===")
        print("Monitoreando generación de señales con IA + TwelveData...")
        
        symbols_to_monitor = ['BTCUSDm', 'ETHUSDm', 'XAUUSDm']
        cycle = 0
        
        try:
            while True:
                cycle += 1
                timestamp = datetime.now().strftime('%H:%M:%S')
                
                print(f"\n[{cycle:03d}] {timestamp} - EVALUACIÓN IA SEÑALES")
                print("=" * 70)
                
                # Conectar MT5
                if not mt5.initialize():
                    print("❌ Error conectando MT5")
                    time.sleep(30)
                    continue
                
                # Obtener sentimiento general del mercado
                print("📊 Obteniendo datos mercado tiempo real...")
                market_data = self.get_current_market_sentiment(symbols_to_monitor)
                
                # Analizar cada símbolo
                signals_generated = 0
                quality_scores = []
                
                for symbol in symbols_to_monitor:
                    print(f"\n🔍 EVALUANDO GENERADOR SEÑALES: {symbol}")
                    
                    # Verificar símbolo disponible en MT5
                    tick = mt5.symbol_info_tick(symbol)
                    if not tick:
                        print(f"   ⚠️ Símbolo {symbol} no disponible en MT5")
                        continue
                    
                    # Generar señal usando sistema actual
                    try:
                        signal_result = self.analyzer.analyze_symbol_advanced(symbol)
                        
                        if signal_result and signal_result['signal'] != 'HOLD':
                            signals_generated += 1
                            signal = signal_result['signal']
                            confidence = signal_result['confidence']
                            
                            print(f"   🎯 SEÑAL DETECTADA: {signal} ({confidence:.1%})")
                            print(f"   📈 Precio MT5: ${tick.bid:.2f}")
                            
                            if symbol in market_data:
                                td_price = market_data[symbol].get('price', 0)
                                print(f"   💹 Precio TwelveData: ${td_price:.2f}")
                            
                            # Evaluación IA de la señal
                            ai_evaluation = self.ai_evaluate_signal_quality(symbol, signal_result, market_data)
                            
                            if ai_evaluation:
                                quality = ai_evaluation['quality_score']
                                timing = ai_evaluation['timing']
                                risk = ai_evaluation['risk_assessment']
                                recommendation = ai_evaluation['recommendation']
                                analysis = ai_evaluation['analysis']
                                
                                quality_scores.append(quality)
                                
                                # Mostrar evaluación IA
                                quality_emoji = "🟢" if quality >= 70 else "🟡" if quality >= 50 else "🔴"
                                timing_emoji = {"EXCELLENT": "⚡", "GOOD": "✅", "FAIR": "⚠️", "POOR": "❌"}.get(timing, "❓")
                                risk_emoji = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}.get(risk, "⚪")
                                rec_emoji = {"EXECUTE": "🚀", "WAIT": "⏳", "IGNORE": "🚫"}.get(recommendation, "❓")
                                
                                print(f"   🤖 EVALUACIÓN IA:")
                                print(f"      {quality_emoji} Calidad: {quality}/100")
                                print(f"      {timing_emoji} Timing: {timing}")
                                print(f"      {risk_emoji} Riesgo: {risk}")
                                print(f"      {rec_emoji} Recomendación: {recommendation}")
                                print(f"      💡 Análisis: {analysis}")
                                
                                # Guardar historial
                                self.signal_history.append({
                                    'timestamp': datetime.now(),
                                    'symbol': symbol,
                                    'signal': signal,
                                    'confidence': confidence,
                                    'quality_score': quality,
                                    'recommendation': recommendation
                                })
                                
                                # Telegram para señales de alta calidad
                                if quality >= 75 and recommendation == 'EXECUTE':
                                    try:
                                        from notifiers.telegram_notifier import send_telegram_message
                                        message = f"🚀 SEÑAL ALTA CALIDAD:\n{symbol} {signal} ({confidence:.1%})\nCalidad IA: {quality}/100\nTiming: {timing}\nRecomendación: {recommendation}"
                                        send_telegram_message(message)
                                    except:
                                        pass
                        else:
                            print(f"   📊 Sin señales fuertes para {symbol}")
                            if symbol in market_data:
                                market_info = market_data[symbol]
                                print(f"   💹 Precio: ${market_info.get('price', 0):.2f} | RSI: {market_info.get('rsi', 50):.1f}")
                    
                    except Exception as e:
                        print(f"   ❌ Error generando señal {symbol}: {e}")
                        continue
                
                # Resumen del ciclo
                mt5.shutdown()
                
                avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
                
                print(f"\n📊 RESUMEN CICLO [{cycle:03d}]:")
                print(f"   Señales generadas: {signals_generated}")
                print(f"   Calidad promedio: {avg_quality:.0f}/100")
                print(f"   Símbolos monitoreados: {len(symbols_to_monitor)}")
                
                # Historial reciente
                if len(self.signal_history) > 10:
                    self.signal_history = self.signal_history[-10:]  # Mantener últimas 10
                
                recent_quality = [s['quality_score'] for s in self.signal_history[-5:]]
                if recent_quality:
                    trend_quality = sum(recent_quality) / len(recent_quality)
                    print(f"   Tendencia calidad (5 últimas): {trend_quality:.0f}/100")
                
                # Esperar 90 segundos (análisis espaciado)
                time.sleep(90)
                
        except KeyboardInterrupt:
            print("\n🛑 Monitor detenido por usuario")
        except Exception as e:
            logger.error(f"Error crítico monitor señales: {e}")
        finally:
            print("📴 AI Signal Monitor finalizado")

if __name__ == "__main__":
    monitor = AISignalMonitor()
    monitor.monitor_signal_generation()