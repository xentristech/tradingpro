#!/usr/bin/env python3
"""
AI POSITION MONITOR - Monitoreo inteligente de posiciones abiertas
Analiza posiciones con IA + TwelveData en tiempo real
"""
import MetaTrader5 as mt5
import requests
import json
import time
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os

load_dotenv('.env')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIPositionMonitor:
    def __init__(self):
        self.api_key = os.getenv('TWELVEDATA_API_KEY', '23d17ce5b7044ad5aef9766770a6252b')
        self.ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        self.ollama_model = 'gemma3:4b'  # Modelo más confiable para JSON
        
    def get_live_positions(self):
        """Obtener posiciones actuales de MT5"""
        try:
            if not mt5.initialize():
                return []
            
            positions = mt5.positions_get()
            if not positions:
                return []
            
            position_data = []
            for pos in positions:
                position_data.append({
                    'ticket': pos.ticket,
                    'symbol': pos.symbol,
                    'type': 'BUY' if pos.type == 0 else 'SELL',
                    'volume': pos.volume,
                    'open_price': pos.price_open,
                    'current_price': pos.price_current,
                    'profit': pos.profit,
                    'swap': getattr(pos, 'swap', 0),
                    'commission': getattr(pos, 'commission', 0),
                    'open_time': datetime.fromtimestamp(pos.time),
                    'duration_hours': (datetime.now() - datetime.fromtimestamp(pos.time)).total_seconds() / 3600
                })
            
            return position_data
            
        except Exception as e:
            logger.error(f"Error obteniendo posiciones: {e}")
            return []
        finally:
            mt5.shutdown()
    
    def get_realtime_market_data(self, symbol):
        """Obtener datos de mercado en tiempo real de TwelveData"""
        try:
            # Normalizar símbolo
            if 'XAU' in symbol or 'GOLD' in symbol:
                td_symbol = 'XAU/USD'
            elif 'BTC' in symbol:
                td_symbol = 'BTC/USD'  
            elif 'ETH' in symbol:
                td_symbol = 'ETH/USD'
            else:
                td_symbol = symbol
            
            # Precio en tiempo real
            price_url = f"https://api.twelvedata.com/price"
            price_params = {'symbol': td_symbol, 'apikey': self.api_key}
            price_response = requests.get(price_url, params=price_params, timeout=10)
            
            current_price = None
            if price_response.status_code == 200:
                price_data = price_response.json()
                current_price = float(price_data.get('price', 0))
            
            # RSI en tiempo real
            rsi_url = f"https://api.twelvedata.com/rsi"
            rsi_params = {
                'symbol': td_symbol,
                'interval': '5min',
                'time_period': 14,
                'apikey': self.api_key
            }
            rsi_response = requests.get(rsi_url, params=rsi_params, timeout=10)
            
            rsi_value = 50  # Default
            if rsi_response.status_code == 200:
                rsi_data = rsi_response.json()
                if 'values' in rsi_data and rsi_data['values']:
                    rsi_value = float(rsi_data['values'][0]['rsi'])
            
            # MACD en tiempo real
            macd_url = f"https://api.twelvedata.com/macd"
            macd_params = {
                'symbol': td_symbol,
                'interval': '5min',
                'apikey': self.api_key
            }
            macd_response = requests.get(macd_url, params=macd_params, timeout=10)
            
            macd_value = 0
            macd_signal = 0
            if macd_response.status_code == 200:
                macd_data = macd_response.json()
                if 'values' in macd_data and macd_data['values']:
                    macd_value = float(macd_data['values'][0]['macd'])
                    macd_signal = float(macd_data['values'][0]['macd_signal'])
            
            return {
                'symbol': td_symbol,
                'current_price': current_price,
                'rsi': rsi_value,
                'macd': macd_value,
                'macd_signal': macd_signal,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo datos tiempo real {symbol}: {e}")
            return None
    
    def ai_analyze_position(self, position, market_data):
        """Análisis IA de una posición específica"""
        try:
            # Calcular métricas
            pnl_percent = (position['profit'] / (position['open_price'] * position['volume'] * 100)) * 100
            price_movement = ((position['current_price'] - position['open_price']) / position['open_price']) * 100
            
            if position['type'] == 'SELL':
                price_movement *= -1  # Invertir para SELL
            
            # Crear prompt para IA
            prompt = f"""Analiza esta posición de trading abierta:

POSICIÓN:
- Ticket: {position['ticket']}
- Símbolo: {position['symbol']} 
- Tipo: {position['type']}
- Precio apertura: ${position['open_price']:.2f}
- Precio actual: ${position['current_price']:.2f}
- P&L: ${position['profit']:.2f} ({pnl_percent:.1f}%)
- Tiempo abierto: {position['duration_hours']:.1f} horas

DATOS MERCADO TIEMPO REAL:
- Precio TwelveData: ${market_data['current_price']:.2f}
- RSI: {market_data['rsi']:.1f}
- MACD: {market_data['macd']:.4f}
- MACD Signal: {market_data['macd_signal']:.4f}

Dame tu recomendación como experto trader:

Responde SOLO este JSON:
{{"action": "HOLD/CLOSE/PARTIAL_CLOSE", "confidence": 75, "reason": "Tu análisis aquí", "risk_level": "LOW/MEDIUM/HIGH"}}"""

            # Llamar IA
            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2, "num_predict": 150}
            }
            
            response = requests.post(f"{self.ollama_host}/api/generate", json=payload, timeout=20)
            
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
                            'action': parsed.get('action', 'HOLD'),
                            'confidence': parsed.get('confidence', 50),
                            'reason': parsed.get('reason', 'Sin análisis'),
                            'risk_level': parsed.get('risk_level', 'MEDIUM'),
                            'pnl_percent': pnl_percent,
                            'price_movement': price_movement
                        }
                    except json.JSONDecodeError:
                        return self._fallback_analysis(position, market_data)
                        
            return self._fallback_analysis(position, market_data)
            
        except Exception as e:
            logger.error(f"Error análisis IA posición {position['ticket']}: {e}")
            return self._fallback_analysis(position, market_data)
    
    def _fallback_analysis(self, position, market_data):
        """Análisis de respaldo si falla IA"""
        pnl_percent = (position['profit'] / (position['open_price'] * position['volume'] * 100)) * 100
        
        # Lógica simple basada en reglas
        if pnl_percent > 10:
            return {
                'action': 'PARTIAL_CLOSE',
                'confidence': 70,
                'reason': f'Ganancias altas {pnl_percent:.1f}%',
                'risk_level': 'LOW',
                'pnl_percent': pnl_percent
            }
        elif pnl_percent < -5:
            return {
                'action': 'CLOSE',
                'confidence': 80,
                'reason': f'Pérdidas {pnl_percent:.1f}%',
                'risk_level': 'HIGH',
                'pnl_percent': pnl_percent
            }
        else:
            return {
                'action': 'HOLD',
                'confidence': 60,
                'reason': 'Posición estable',
                'risk_level': 'MEDIUM',
                'pnl_percent': pnl_percent
            }
    
    def monitor_positions_realtime(self):
        """Monitor principal de posiciones en tiempo real"""
        print("=== AI POSITION MONITOR INICIADO ===")
        print("Monitoreando posiciones con IA + TwelveData en tiempo real...")
        
        cycle = 0
        
        try:
            while True:
                cycle += 1
                timestamp = datetime.now().strftime('%H:%M:%S')
                
                print(f"\n[{cycle:03d}] {timestamp} - ANÁLISIS IA POSICIONES")
                print("=" * 60)
                
                # Obtener posiciones actuales
                positions = self.get_live_positions()
                
                if not positions:
                    print("No hay posiciones abiertas para analizar")
                    time.sleep(30)
                    continue
                
                # Analizar cada posición
                for pos in positions:
                    print(f"\n📊 ANALIZANDO POSICIÓN #{pos['ticket']}")
                    print(f"   {pos['symbol']} {pos['type']} {pos['volume']}")
                    print(f"   P&L: ${pos['profit']:.2f} | Abierto: {pos['duration_hours']:.1f}h")
                    
                    # Obtener datos de mercado en tiempo real
                    market_data = self.get_realtime_market_data(pos['symbol'])
                    
                    if market_data:
                        print(f"   💹 TwelveData: ${market_data['current_price']:.2f}")
                        print(f"   📈 RSI: {market_data['rsi']:.1f} | MACD: {market_data['macd']:.4f}")
                        
                        # Análisis IA
                        ai_analysis = self.ai_analyze_position(pos, market_data)
                        
                        if ai_analysis:
                            action = ai_analysis['action']
                            confidence = ai_analysis['confidence']
                            reason = ai_analysis['reason']
                            risk = ai_analysis['risk_level']
                            pnl_pct = ai_analysis['pnl_percent']
                            
                            # Mostrar recomendación IA
                            action_emoji = {"HOLD": "🤝", "CLOSE": "❌", "PARTIAL_CLOSE": "⚡"}.get(action, "🤖")
                            risk_emoji = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}.get(risk, "⚪")
                            
                            print(f"   🤖 IA RECOMIENDA: {action_emoji} {action} ({confidence}%)")
                            print(f"   💡 Razón: {reason}")
                            print(f"   ⚠️ Riesgo: {risk_emoji} {risk} | P&L%: {pnl_pct:+.1f}%")
                            
                            # Telegram notification para acciones importantes
                            if action in ['CLOSE', 'PARTIAL_CLOSE'] and confidence > 70:
                                try:
                                    from notifiers.telegram_notifier import send_telegram_message
                                    message = f"🤖 ALERTA IA:\n#{pos['ticket']} {pos['symbol']} {pos['type']}\nRecomendación: {action} ({confidence}%)\nRazón: {reason}\nP&L: ${pos['profit']:.2f} ({pnl_pct:+.1f}%)"
                                    send_telegram_message(message)
                                except:
                                    pass
                        else:
                            print("   ⚠️ Error en análisis IA")
                    else:
                        print("   ❌ Error obteniendo datos TwelveData")
                
                print(f"\n[{cycle:03d}] Completado - {len(positions)} posiciones analizadas")
                
                # Esperar 60 segundos (análisis más espaciado por uso de API)
                time.sleep(60)
                
        except KeyboardInterrupt:
            print("\n🛑 Monitor detenido por usuario")
        except Exception as e:
            logger.error(f"Error crítico en monitor: {e}")
        finally:
            print("📴 AI Position Monitor finalizado")

if __name__ == "__main__":
    monitor = AIPositionMonitor()
    monitor.monitor_positions_realtime()