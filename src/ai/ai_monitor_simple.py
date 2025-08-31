#!/usr/bin/env python3
"""
AI MONITOR SIMPLE - Monitor IA sin emojis para compatibilidad
"""
import MetaTrader5 as mt5
import requests
import json
import time
import logging
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv('.env')
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleAIMonitor:
    def __init__(self):
        self.api_key = os.getenv('TWELVEDATA_API_KEY', '23d17ce5b7044ad5aef9766770a6252b')
        self.ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        self.ollama_model = 'gemma3:4b'
        
    def get_positions(self):
        """Obtener posiciones actuales"""
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
                    'open_time': datetime.fromtimestamp(pos.time),
                    'duration_hours': (datetime.now() - datetime.fromtimestamp(pos.time)).total_seconds() / 3600
                })
            
            return position_data
            
        except Exception as e:
            logger.error(f"Error obteniendo posiciones: {e}")
            return []
        finally:
            mt5.shutdown()
    
    def get_market_data(self, symbol):
        """Obtener datos de TwelveData"""
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
            
            # Precio actual
            price_url = f"https://api.twelvedata.com/price"
            price_params = {'symbol': td_symbol, 'apikey': self.api_key}
            price_response = requests.get(price_url, params=price_params, timeout=10)
            
            current_price = None
            if price_response.status_code == 200:
                price_data = price_response.json()
                current_price = float(price_data.get('price', 0))
            
            # RSI
            rsi_url = f"https://api.twelvedata.com/rsi"
            rsi_params = {
                'symbol': td_symbol,
                'interval': '15min',
                'time_period': 14,
                'apikey': self.api_key
            }
            rsi_response = requests.get(rsi_url, params=rsi_params, timeout=10)
            
            rsi_value = 50
            if rsi_response.status_code == 200:
                rsi_data = rsi_response.json()
                if 'values' in rsi_data and rsi_data['values']:
                    rsi_value = float(rsi_data['values'][0]['rsi'])
            
            return {
                'symbol': td_symbol,
                'current_price': current_price,
                'rsi': rsi_value,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo datos {symbol}: {e}")
            return None
    
    def ai_analyze_position(self, position, market_data):
        """Análisis IA de posición"""
        try:
            pnl_percent = (position['profit'] / (position['open_price'] * position['volume'] * 100)) * 100
            
            prompt = f"""Analiza esta posición como trader experto:

POSICION:
Ticket: {position['ticket']}
Simbolo: {position['symbol']}
Tipo: {position['type']}
Precio apertura: ${position['open_price']:.2f}
Precio actual: ${position['current_price']:.2f}
Profit: ${position['profit']:.2f} ({pnl_percent:.1f}%)
Horas abierto: {position['duration_hours']:.1f}

MERCADO REAL:
Precio TwelveData: ${market_data['current_price']:.2f}
RSI: {market_data['rsi']:.1f}

Dame tu recomendacion:

Responde SOLO este JSON:
{{"action": "HOLD", "confidence": 75, "reason": "Tu analisis", "risk": "MEDIUM"}}"""

            payload = {
                "model": self.ollama_model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2, "num_predict": 120}
            }
            
            response = requests.post(f"{self.ollama_host}/api/generate", json=payload, timeout=20)
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result.get('response', '').strip()
                
                start = ai_response.find('{')
                end = ai_response.rfind('}') + 1
                
                if start != -1 and end > start:
                    json_str = ai_response[start:end]
                    try:
                        parsed = json.loads(json_str)
                        return {
                            'action': parsed.get('action', 'HOLD'),
                            'confidence': parsed.get('confidence', 50),
                            'reason': parsed.get('reason', 'Sin razon'),
                            'risk': parsed.get('risk', 'MEDIUM'),
                            'pnl_percent': pnl_percent
                        }
                    except:
                        pass
            
            # Fallback
            if pnl_percent > 8:
                return {'action': 'PARTIAL_CLOSE', 'confidence': 80, 'reason': f'Ganancias {pnl_percent:.1f}%', 'risk': 'LOW'}
            elif pnl_percent < -4:
                return {'action': 'CLOSE', 'confidence': 85, 'reason': f'Perdidas {pnl_percent:.1f}%', 'risk': 'HIGH'}
            else:
                return {'action': 'HOLD', 'confidence': 60, 'reason': 'Posicion estable', 'risk': 'MEDIUM'}
                
        except Exception as e:
            logger.error(f"Error analisis IA: {e}")
            return None
    
    def monitor_all(self):
        """Monitor principal"""
        print("=== AI MONITOR INICIADO ===")
        print("Analizando posiciones con IA + TwelveData...")
        
        cycle = 0
        
        try:
            while True:
                cycle += 1
                timestamp = datetime.now().strftime('%H:%M:%S')
                
                print(f"\n[{cycle:03d}] {timestamp} - ANALISIS IA")
                print("=" * 50)
                
                positions = self.get_positions()
                
                if not positions:
                    print("No hay posiciones para analizar")
                    time.sleep(45)
                    continue
                
                for pos in positions:
                    print(f"\nPOSICION #{pos['ticket']}")
                    print(f"  {pos['symbol']} {pos['type']} {pos['volume']}")
                    print(f"  P&L: ${pos['profit']:.2f} | Tiempo: {pos['duration_hours']:.1f}h")
                    
                    # Datos mercado
                    market_data = self.get_market_data(pos['symbol'])
                    
                    if market_data:
                        print(f"  TwelveData: ${market_data['current_price']:.2f}")
                        print(f"  RSI: {market_data['rsi']:.1f}")
                        
                        # Análisis IA
                        ai_result = self.ai_analyze_position(pos, market_data)
                        
                        if ai_result:
                            action = ai_result['action']
                            confidence = ai_result['confidence']
                            reason = ai_result['reason']
                            risk = ai_result['risk']
                            pnl_pct = ai_result['pnl_percent']
                            
                            print(f"  IA RECOMIENDA: {action} ({confidence}%)")
                            print(f"  Razon: {reason}")
                            print(f"  Riesgo: {risk} | P&L%: {pnl_pct:+.1f}%")
                            
                            # Notificación importante
                            if action in ['CLOSE', 'PARTIAL_CLOSE'] and confidence > 75:
                                try:
                                    from notifiers.telegram_notifier import send_telegram_message
                                    msg = f"IA ALERTA:\n#{pos['ticket']} {pos['symbol']} {pos['type']}\nRecomendacion: {action} ({confidence}%)\nRazon: {reason}\nP&L: ${pos['profit']:.2f}"
                                    send_telegram_message(msg)
                                    print(f"  >> Telegram enviado")
                                except Exception as e:
                                    print(f"  >> Error Telegram: {e}")
                        else:
                            print("  Error en analisis IA")
                    else:
                        print("  Error obteniendo datos TwelveData")
                
                print(f"\n[{cycle:03d}] Completado - {len(positions)} posiciones analizadas")
                
                # Esperar 60 segundos
                time.sleep(60)
                
        except KeyboardInterrupt:
            print("\nMonitor detenido por usuario")
        except Exception as e:
            logger.error(f"Error critico: {e}")
        finally:
            print("AI Monitor finalizado")

if __name__ == "__main__":
    monitor = SimpleAIMonitor()
    monitor.monitor_all()