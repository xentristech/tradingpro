#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ADVANCED RISK MANAGER - BREAKEVEN & TRAILING STOP CON IA
=========================================================
Sistema inteligente de gestión de riesgo con breakeven automático
y trailing stop dinámico asistido por IA y datos de TwelveData
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import json
import requests

# Cargar configuración
load_dotenv('configs/.env')

class AdvancedRiskManager:
    """
    Gestor avanzado de riesgo con Breakeven y Trailing Stop inteligente
    """
    
    def __init__(self):
        """Inicializar el gestor de riesgo"""
        # Configuración de funciones (activar/desactivar)
        self.ENABLE_BREAKEVEN = os.getenv('ENABLE_BREAKEVEN', 'true').lower() == 'true'
        self.ENABLE_TRAILING_STOP = os.getenv('ENABLE_TRAILING_STOP', 'true').lower() == 'true'
        self.USE_AI_OPTIMIZATION = os.getenv('USE_AI_RISK_OPTIMIZATION', 'true').lower() == 'true'
        
        # Parámetros de Breakeven
        self.BREAKEVEN_TRIGGER_PIPS = float(os.getenv('BREAKEVEN_TRIGGER_PIPS', '20'))
        self.BREAKEVEN_OFFSET_PIPS = float(os.getenv('BREAKEVEN_OFFSET_PIPS', '2'))
        self.BREAKEVEN_MIN_PROFIT_USD = float(os.getenv('BREAKEVEN_MIN_PROFIT_USD', '10'))
        
        # Parámetros de Trailing Stop
        self.TRAILING_ACTIVATION_PIPS = float(os.getenv('TRAILING_ACTIVATION_PIPS', '30'))
        self.TRAILING_DISTANCE_PIPS = float(os.getenv('TRAILING_DISTANCE_PIPS', '15'))
        self.TRAILING_STEP_PIPS = float(os.getenv('TRAILING_STEP_PIPS', '5'))
        self.USE_ATR_TRAILING = os.getenv('USE_ATR_TRAILING', 'true').lower() == 'true'
        self.ATR_MULTIPLIER = float(os.getenv('ATR_MULTIPLIER', '2.0'))
        
        # Control de frecuencia
        self.CHECK_INTERVAL = int(os.getenv('RISK_CHECK_INTERVAL', '30'))  # segundos
        self.last_check = {}
        
        # APIs
        self.twelvedata_key = os.getenv('TWELVEDATA_API_KEY')
        self.ollama_base = os.getenv('OLLAMA_API_BASE', 'http://localhost:11434/v1')
        self.ollama_model = os.getenv('OLLAMA_MODEL', 'deepseek-r1:14b')
        
        # Estado del sistema
        self.active = True
        self.positions_managed = {}
        self.statistics = {
            'breakeven_applied': 0,
            'trailing_updated': 0,
            'total_pips_saved': 0,
            'ai_suggestions': 0
        }
        
        # Logger
        self.setup_logger()
        
    def setup_logger(self):
        """Configurar logger del sistema"""
        self.logger = logging.getLogger('RiskManager')
        self.logger.setLevel(logging.INFO)
        
        # Crear directorio de logs si no existe
        os.makedirs('logs', exist_ok=True)
        
        # Handler para archivo
        fh = logging.FileHandler('logs/risk_manager.log', encoding='utf-8')
        fh.setLevel(logging.INFO)
        
        # Handler para consola
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formato
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
        
    def start(self):
        """Iniciar el gestor de riesgo"""
        self.logger.info("="*60)
        self.logger.info("ADVANCED RISK MANAGER - INICIANDO")
        self.logger.info("="*60)
        self.logger.info(f"Breakeven: {'ACTIVADO' if self.ENABLE_BREAKEVEN else 'DESACTIVADO'}")
        self.logger.info(f"Trailing Stop: {'ACTIVADO' if self.ENABLE_TRAILING_STOP else 'DESACTIVADO'}")
        self.logger.info(f"IA Optimization: {'ACTIVADO' if self.USE_AI_OPTIMIZATION else 'DESACTIVADO'}")
        self.logger.info(f"Intervalo de verificación: {self.CHECK_INTERVAL} segundos")
        self.logger.info("-"*60)
        
        while self.active:
            try:
                # Verificar conexión MT5
                if not self.verify_mt5_connection():
                    self.logger.warning("MT5 no conectado, esperando...")
                    time.sleep(10)
                    continue
                
                # Obtener posiciones abiertas
                positions = mt5.positions_get()
                if positions:
                    self.logger.info(f"Monitoreando {len(positions)} posiciones...")
                    
                    for position in positions:
                        self.manage_position(position)
                        
                # Mostrar estadísticas
                if self.statistics['breakeven_applied'] > 0 or self.statistics['trailing_updated'] > 0:
                    self.show_statistics()
                    
            except Exception as e:
                self.logger.error(f"Error en ciclo principal: {e}")
                
            # Esperar antes del próximo ciclo
            time.sleep(self.CHECK_INTERVAL)
            
    def verify_mt5_connection(self) -> bool:
        """Verificar conexión con MT5"""
        try:
            if not mt5.terminal_info():
                if not mt5.initialize():
                    return False
            return True
        except:
            return False
            
    def manage_position(self, position):
        """Gestionar una posición individual"""
        ticket = position.ticket
        symbol = position.symbol
        
        # Evitar procesar la misma posición muy seguido
        if ticket in self.last_check:
            if time.time() - self.last_check[ticket] < 10:
                return
                
        self.last_check[ticket] = time.time()
        
        # Obtener información del símbolo
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            return
            
        point = symbol_info.point
        current_price = symbol_info.bid if position.type == mt5.ORDER_TYPE_BUY else symbol_info.ask
        
        # Calcular profit en pips
        if position.type == mt5.ORDER_TYPE_BUY:
            profit_pips = (current_price - position.price_open) / point
        else:
            profit_pips = (position.price_open - current_price) / point
            
        # Obtener recomendaciones de IA si está activado
        ai_params = None
        if self.USE_AI_OPTIMIZATION:
            ai_params = self.get_ai_recommendations(symbol, position, profit_pips)
            
        # Aplicar Breakeven si está activado
        if self.ENABLE_BREAKEVEN:
            self.check_and_apply_breakeven(position, profit_pips, point, ai_params)
            
        # Aplicar Trailing Stop si está activado
        if self.ENABLE_TRAILING_STOP:
            self.check_and_apply_trailing(position, profit_pips, current_price, point, ai_params)
            
    def check_and_apply_breakeven(self, position, profit_pips, point, ai_params=None):
        """Verificar y aplicar breakeven a una posición"""
        ticket = position.ticket
        
        # Verificar si ya se aplicó breakeven
        if ticket in self.positions_managed and self.positions_managed[ticket].get('breakeven_applied'):
            return
            
        # Determinar trigger de breakeven
        trigger_pips = self.BREAKEVEN_TRIGGER_PIPS
        offset_pips = self.BREAKEVEN_OFFSET_PIPS
        
        # Usar parámetros de IA si están disponibles
        if ai_params and 'breakeven_trigger' in ai_params:
            trigger_pips = ai_params['breakeven_trigger']
            self.logger.info(f"IA sugiere breakeven trigger: {trigger_pips} pips")
            
        # Verificar si se alcanzó el trigger
        if profit_pips >= trigger_pips and position.profit >= self.BREAKEVEN_MIN_PROFIT_USD:
            # Calcular nuevo stop loss (breakeven + offset)
            if position.type == mt5.ORDER_TYPE_BUY:
                new_sl = position.price_open + (offset_pips * point)
                # Solo mover si el nuevo SL es mejor que el actual
                if position.sl < new_sl:
                    self.modify_position_sl(position, new_sl, "BREAKEVEN")
            else:  # SELL
                new_sl = position.price_open - (offset_pips * point)
                # Solo mover si el nuevo SL es mejor que el actual
                if position.sl == 0 or position.sl > new_sl:
                    self.modify_position_sl(position, new_sl, "BREAKEVEN")
                    
    def check_and_apply_trailing(self, position, profit_pips, current_price, point, ai_params=None):
        """Verificar y aplicar trailing stop a una posición"""
        ticket = position.ticket
        
        # Verificar si se alcanzó la activación del trailing
        activation_pips = self.TRAILING_ACTIVATION_PIPS
        distance_pips = self.TRAILING_DISTANCE_PIPS
        
        # Usar parámetros de IA si están disponibles
        if ai_params:
            if 'trailing_activation' in ai_params:
                activation_pips = ai_params['trailing_activation']
            if 'trailing_distance' in ai_params:
                distance_pips = ai_params['trailing_distance']
                
        # Verificar activación
        if profit_pips < activation_pips:
            return
            
        # Usar ATR para distancia si está configurado
        if self.USE_ATR_TRAILING:
            atr = self.get_current_atr(position.symbol)
            if atr:
                distance_pips = (atr * self.ATR_MULTIPLIER) / point
                
        # Calcular nuevo trailing stop
        if position.type == mt5.ORDER_TYPE_BUY:
            new_sl = current_price - (distance_pips * point)
            # Solo mover si es mejor que el actual
            if position.sl < new_sl:
                # Verificar step mínimo
                if position.sl == 0 or (new_sl - position.sl) >= (self.TRAILING_STEP_PIPS * point):
                    self.modify_position_sl(position, new_sl, "TRAILING")
        else:  # SELL
            new_sl = current_price + (distance_pips * point)
            # Solo mover si es mejor que el actual
            if position.sl == 0 or position.sl > new_sl:
                # Verificar step mínimo
                if position.sl == 0 or (position.sl - new_sl) >= (self.TRAILING_STEP_PIPS * point):
                    self.modify_position_sl(position, new_sl, "TRAILING")
                    
    def modify_position_sl(self, position, new_sl, reason=""):
        """Modificar el stop loss de una posición"""
        try:
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": position.symbol,
                "position": position.ticket,
                "sl": round(new_sl, mt5.symbol_info(position.symbol).digits),
                "tp": position.tp,
                "magic": int(os.getenv('MT5_MAGIC', 20250817)),
                "comment": f"ARM_{reason}"
            }
            
            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                ticket = position.ticket
                old_sl = position.sl if position.sl > 0 else position.price_open
                
                # Registrar en gestión
                if ticket not in self.positions_managed:
                    self.positions_managed[ticket] = {}
                    
                if reason == "BREAKEVEN":
                    self.positions_managed[ticket]['breakeven_applied'] = True
                    self.statistics['breakeven_applied'] += 1
                elif reason == "TRAILING":
                    self.positions_managed[ticket]['last_trailing'] = new_sl
                    self.statistics['trailing_updated'] += 1
                    
                # Calcular pips salvados
                if position.type == mt5.ORDER_TYPE_BUY:
                    pips_saved = (new_sl - old_sl) / mt5.symbol_info(position.symbol).point
                else:
                    pips_saved = (old_sl - new_sl) / mt5.symbol_info(position.symbol).point
                    
                self.statistics['total_pips_saved'] += max(0, pips_saved)
                
                self.logger.info(f"✅ {reason} aplicado - Ticket: {ticket}, Nuevo SL: {new_sl:.5f}")
                
                # Enviar notificación Telegram
                self.send_telegram_notification(position, new_sl, reason)
                
                return True
            else:
                if result:
                    self.logger.error(f"Error modificando posición: {result.comment}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error en modify_position_sl: {e}")
            return False
            
    def get_current_atr(self, symbol) -> Optional[float]:
        """Obtener el ATR actual del símbolo desde TwelveData"""
        if not self.twelvedata_key:
            return None
            
        try:
            url = "https://api.twelvedata.com/atr"
            params = {
                'symbol': symbol.replace('m', ''),  # Quitar sufijo 'm' si existe
                'interval': '5min',
                'outputsize': 1,
                'apikey': self.twelvedata_key
            }
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if 'values' in data and len(data['values']) > 0:
                    return float(data['values'][0]['atr'])
        except Exception as e:
            self.logger.debug(f"Error obteniendo ATR: {e}")
            
        # Fallback: calcular ATR local con MT5
        return self.calculate_local_atr(symbol)
        
    def calculate_local_atr(self, symbol, period=14) -> Optional[float]:
        """Calcular ATR localmente usando datos de MT5"""
        try:
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, period + 1)
            if rates is None or len(rates) < period:
                return None
                
            df = pd.DataFrame(rates)
            df['hl'] = df['high'] - df['low']
            df['hc'] = abs(df['high'] - df['close'].shift(1))
            df['lc'] = abs(df['low'] - df['close'].shift(1))
            df['tr'] = df[['hl', 'hc', 'lc']].max(axis=1)
            atr = df['tr'].rolling(period).mean().iloc[-1]
            
            return atr
        except Exception as e:
            self.logger.debug(f"Error calculando ATR local: {e}")
            return None
            
    def get_ai_recommendations(self, symbol, position, current_profit_pips) -> Optional[Dict]:
        """Obtener recomendaciones de IA para gestión de riesgo"""
        if not self.USE_AI_OPTIMIZATION:
            return None
            
        try:
            # Obtener datos de mercado
            market_data = self.get_market_context(symbol)
            
            # Preparar prompt para IA
            prompt = f"""Analyze risk management for open position:
Symbol: {symbol}
Type: {'BUY' if position.type == mt5.ORDER_TYPE_BUY else 'SELL'}
Entry: {position.price_open}
Current Profit: {current_profit_pips:.1f} pips
Current SL: {position.sl if position.sl > 0 else 'None'}
Market Context: {json.dumps(market_data, indent=2)}

Suggest optimal parameters:
1. Breakeven trigger (pips)
2. Trailing activation (pips)
3. Trailing distance (pips)
4. Risk level (conservative/moderate/aggressive)

Respond in JSON format only."""
            
            # Llamar a Ollama
            response = requests.post(
                f"{self.ollama_base}/chat/completions",
                json={
                    "model": self.ollama_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 200
                },
                timeout=10
            )
            
            if response.status_code == 200:
                ai_response = response.json()
                if 'choices' in ai_response and len(ai_response['choices']) > 0:
                    content = ai_response['choices'][0]['message']['content']
                    
                    # Intentar parsear JSON de la respuesta
                    try:
                        # Buscar JSON en la respuesta
                        import re
                        json_match = re.search(r'\{[^}]+\}', content)
                        if json_match:
                            params = json.loads(json_match.group())
                            self.statistics['ai_suggestions'] += 1
                            return {
                                'breakeven_trigger': float(params.get('breakeven_trigger', self.BREAKEVEN_TRIGGER_PIPS)),
                                'trailing_activation': float(params.get('trailing_activation', self.TRAILING_ACTIVATION_PIPS)),
                                'trailing_distance': float(params.get('trailing_distance', self.TRAILING_DISTANCE_PIPS)),
                                'risk_level': params.get('risk_level', 'moderate')
                            }
                    except:
                        pass
                        
        except Exception as e:
            self.logger.debug(f"Error obteniendo recomendaciones IA: {e}")
            
        return None
        
    def get_market_context(self, symbol) -> Dict:
        """Obtener contexto del mercado para análisis"""
        context = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'volatility': 'normal',
            'trend': 'neutral'
        }
        
        try:
            # Obtener datos recientes
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 100)
            if rates is not None and len(rates) > 20:
                df = pd.DataFrame(rates)
                
                # Calcular indicadores básicos
                df['sma20'] = df['close'].rolling(20).mean()
                df['sma50'] = df['close'].rolling(50).mean()
                
                # Determinar tendencia
                if len(df) >= 50:
                    current_price = df['close'].iloc[-1]
                    sma20 = df['sma20'].iloc[-1]
                    sma50 = df['sma50'].iloc[-1]
                    
                    if current_price > sma20 > sma50:
                        context['trend'] = 'bullish'
                    elif current_price < sma20 < sma50:
                        context['trend'] = 'bearish'
                        
                # Calcular volatilidad
                returns = df['close'].pct_change().dropna()
                volatility = returns.std()
                
                if volatility > returns.std() * 1.5:
                    context['volatility'] = 'high'
                elif volatility < returns.std() * 0.5:
                    context['volatility'] = 'low'
                    
                # ATR
                atr = self.calculate_local_atr(symbol)
                if atr:
                    context['atr'] = float(atr)
                    
        except Exception as e:
            self.logger.debug(f"Error obteniendo contexto: {e}")
            
        return context
        
    def send_telegram_notification(self, position, new_sl, reason):
        """Enviar notificación por Telegram"""
        try:
            token = os.getenv('TELEGRAM_TOKEN')
            chat_id = os.getenv('TELEGRAM_CHAT_ID')
            
            if not token or token == 'your_telegram_bot_token':
                return
                
            # Construir mensaje
            if reason == "BREAKEVEN":
                emoji = "🔒"
                action = "BREAKEVEN APLICADO"
            else:
                emoji = "📈"
                action = "TRAILING STOP ACTUALIZADO"
                
            message = f"""
{emoji} **{action}** {emoji}

📊 **Detalles:**
• Símbolo: {position.symbol}
• Ticket: #{position.ticket}
• Tipo: {'COMPRA' if position.type == mt5.ORDER_TYPE_BUY else 'VENTA'}
• Entrada: {position.price_open:.5f}
• Nuevo SL: {new_sl:.5f}
• Profit Actual: ${position.profit:.2f}

🛡️ **Protección {'Activada' if reason == 'BREAKEVEN' else 'Actualizada'}**
            """
            
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            requests.post(url, data=data, timeout=5)
            
        except Exception as e:
            self.logger.debug(f"Error enviando notificación Telegram: {e}")
            
    def show_statistics(self):
        """Mostrar estadísticas del sistema"""
        self.logger.info("-" * 50)
        self.logger.info("📊 ESTADÍSTICAS DE GESTIÓN DE RIESGO")
        self.logger.info(f"  Breakeven aplicados: {self.statistics['breakeven_applied']}")
        self.logger.info(f"  Trailing actualizados: {self.statistics['trailing_updated']}")
        self.logger.info(f"  Total pips protegidos: {self.statistics['total_pips_saved']:.1f}")
        if self.USE_AI_OPTIMIZATION:
            self.logger.info(f"  Sugerencias IA: {self.statistics['ai_suggestions']}")
        self.logger.info("-" * 50)
        
    def stop(self):
        """Detener el gestor de riesgo"""
        self.active = False
        self.logger.info("Sistema de gestión de riesgo detenido")
        

def main():
    """Función principal"""
    print("=" * 60)
    print("  ADVANCED RISK MANAGER - ALGO TRADER V3")
    print("  Breakeven & Trailing Stop Inteligente")
    print("=" * 60)
    
    manager = AdvancedRiskManager()
    
    try:
        manager.start()
    except KeyboardInterrupt:
        print("\n\nDeteniendo sistema...")
        manager.stop()
        print("Sistema detenido correctamente")
        

if __name__ == "__main__":
    main()
