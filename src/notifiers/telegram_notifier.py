#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NOTIFICADOR DE TELEGRAM - ALGO TRADER V3 (FIXED)
================================================
Sistema de notificaciones en tiempo real por Telegram
"""

import os
import sys
import requests
import json
from datetime import datetime
from typing import Dict, Any, Optional
import time
import logging

# Configurar encoding UTF-8
if sys.platform == 'win32':
    import locale
    locale.setlocale(locale.LC_ALL, '')

class TelegramNotifier:
    def __init__(self):
        self.token = os.getenv('TELEGRAM_TOKEN', '7872232379:AAGXriuQJFww4-HqKm3MxzYwGdfakg5rgO4')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID', '-1002766499765')
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.is_active = False
        
        # Configurar logging con encoding UTF-8
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout)
            ],
            encoding='utf-8'
        )
        self.logger = logging.getLogger(__name__)
        
        # Verificar conexión
        self.verify_connection()
        
    def verify_connection(self):
        """Verifica la conexión con Telegram"""
        try:
            response = requests.get(f"{self.base_url}/getMe", timeout=10)
            if response.status_code == 200:
                bot_info = response.json()
                if bot_info.get('ok'):
                    self.is_active = True
                    bot_name = bot_info['result']['username']
                    self.logger.info(f"Bot de Telegram conectado: @{bot_name}")
                    # Enviar mensaje de inicio
                    self.send_message(
                        "🚀 *ALGO TRADER V3 ACTIVO*\n\n"
                        "Sistema de trading algorítmico iniciado correctamente.\n"
                        f"Bot: @{bot_name}\n"
                        f"Hora: {datetime.now().strftime('%H:%M:%S')}", 
                        parse_mode='Markdown'
                    )
                    return True
        except Exception as e:
            self.logger.error(f"Error conectando con Telegram: {e}")
            self.is_active = False
        return False
        
    def send_message(self, text: str, parse_mode: str = 'HTML', disable_notification: bool = False):
        """Envía un mensaje a Telegram"""
        if not self.is_active:
            return False
            
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                'chat_id': self.chat_id,
                'text': text,
                'parse_mode': parse_mode,
                'disable_notification': disable_notification
            }
            
            response = requests.post(url, json=data, timeout=10)
            if response.status_code == 200:
                return True
            else:
                self.logger.error(f"Error enviando mensaje: {response.text}")
                return False
        except Exception as e:
            self.logger.error(f"Error en send_message: {e}")
            return False
            
    def send_signal(self, signal: Dict[str, Any]):
        """Envía una señal de trading a Telegram"""
        try:
            # Formatear emoji según tipo de señal
            signal_emoji = "🟢" if signal.get('type') == 'BUY' else "🔴"
            strength_emoji = "💪" if signal.get('strength', 0) > 0.7 else "⚡"
            
            # Crear mensaje formateado
            message = f"""
{signal_emoji} <b>SEÑAL DE TRADING</b> {signal_emoji}

📊 <b>Símbolo:</b> {signal.get('symbol', 'N/A')}
📈 <b>Tipo:</b> {signal.get('type', 'N/A')}
💰 <b>Precio:</b> {signal.get('price', 0):.5f}
{strength_emoji} <b>Fuerza:</b> {signal.get('strength', 0):.2%}

🎯 <b>Take Profit:</b> {signal.get('tp', 0):.5f}
🛡️ <b>Stop Loss:</b> {signal.get('sl', 0):.5f}

📝 <b>Estrategia:</b> {signal.get('strategy', 'N/A')}
⏰ <b>Timeframe:</b> {signal.get('timeframe', 'N/A')}

💡 <b>Razón:</b> {signal.get('reason', 'Análisis técnico')}

🤖 <i>Generado por Algo Trader V3</i>
"""
            
            return self.send_message(message, parse_mode='HTML')
            
        except Exception as e:
            self.logger.error(f"Error enviando señal: {e}")
            return False
            
    def send_trade_update(self, trade_info: Dict[str, Any]):
        """Envía actualización de trade"""
        try:
            # Determinar emoji según estado
            if trade_info.get('status') == 'opened':
                emoji = "🆕"
                title = "POSICIÓN ABIERTA"
            elif trade_info.get('status') == 'closed':
                profit = trade_info.get('profit', 0)
                emoji = "✅" if profit > 0 else "❌"
                title = "POSICIÓN CERRADA"
            else:
                emoji = "📊"
                title = "ACTUALIZACIÓN DE TRADE"
                
            message = f"""
{emoji} <b>{title}</b> {emoji}

📊 <b>Símbolo:</b> {trade_info.get('symbol', 'N/A')}
🎫 <b>Ticket:</b> #{trade_info.get('ticket', 'N/A')}
📈 <b>Tipo:</b> {trade_info.get('type', 'N/A')}

💰 <b>Precio Entrada:</b> {trade_info.get('open_price', 0):.5f}
💵 <b>Precio Actual:</b> {trade_info.get('current_price', 0):.5f}
📏 <b>Volumen:</b> {trade_info.get('volume', 0):.2f}

💹 <b>Profit:</b> ${trade_info.get('profit', 0):.2f}
📊 <b>Profit %:</b> {trade_info.get('profit_percent', 0):.2f}%

⏰ <b>Hora:</b> {datetime.now().strftime('%H:%M:%S')}
"""
            
            return self.send_message(message, parse_mode='HTML')
            
        except Exception as e:
            self.logger.error(f"Error enviando actualización de trade: {e}")
            return False
            
    def send_alert(self, alert_type: str, message: str, critical: bool = False):
        """Envía una alerta al chat"""
        try:
            # Determinar emoji según tipo
            emojis = {
                'info': 'ℹ️',
                'warning': '⚠️',
                'error': '🚨',
                'success': '✅',
                'money': '💰',
                'chart': '📈',
                'time': '⏰'
            }
            
            emoji = emojis.get(alert_type, '📢')
            
            formatted_message = f"""
{emoji} <b>ALERTA {alert_type.upper()}</b> {emoji}

{message}

⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            return self.send_message(
                formatted_message, 
                parse_mode='HTML',
                disable_notification=not critical
            )
            
        except Exception as e:
            self.logger.error(f"Error enviando alerta: {e}")
            return False
            
    def send_daily_report(self, report_data: Dict[str, Any]):
        """Envía reporte diario"""
        try:
            message = f"""
📊 <b>REPORTE DIARIO - ALGO TRADER V3</b> 📊

📅 <b>Fecha:</b> {datetime.now().strftime('%Y-%m-%d')}

<b>📈 RESULTADOS DEL DÍA:</b>
• Trades Totales: {report_data.get('total_trades', 0)}
• Trades Ganadores: {report_data.get('winning_trades', 0)}
• Trades Perdedores: {report_data.get('losing_trades', 0)}
• Win Rate: {report_data.get('win_rate', 0):.2f}%

<b>💰 FINANCIERO:</b>
• Profit Total: ${report_data.get('total_profit', 0):.2f}
• Mejor Trade: ${report_data.get('best_trade', 0):.2f}
• Peor Trade: ${report_data.get('worst_trade', 0):.2f}
• Promedio: ${report_data.get('avg_profit', 0):.2f}

<b>📊 MÉTRICAS:</b>
• Balance: ${report_data.get('balance', 0):.2f}
• Equity: ${report_data.get('equity', 0):.2f}
• Margin: ${report_data.get('margin', 0):.2f}
• Drawdown: {report_data.get('drawdown', 0):.2f}%

<b>🎯 SEÑALES:</b>
• Señales Generadas: {report_data.get('signals_generated', 0)}
• Señales Ejecutadas: {report_data.get('signals_executed', 0)}
• Precisión: {report_data.get('signal_accuracy', 0):.2f}%

🤖 <i>Reporte automático generado por Algo Trader V3</i>
"""
            
            return self.send_message(message, parse_mode='HTML')
            
        except Exception as e:
            self.logger.error(f"Error enviando reporte diario: {e}")
            return False
    
    def keep_alive(self):
        """Mantiene el servicio activo"""
        self.logger.info("Servicio de Telegram activo y monitoreando...")
        while True:
            try:
                # Verificar conexión cada 5 minutos
                time.sleep(300)
                if not self.is_active:
                    self.verify_connection()
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.logger.error(f"Error en keep_alive: {e}")
                time.sleep(30)

# Instancia global
telegram_notifier = None

def initialize_telegram():
    """Inicializa el notificador de Telegram"""
    global telegram_notifier
    telegram_notifier = TelegramNotifier()
    return telegram_notifier

def main():
    print("""
╔════════════════════════════════════════════════════════════╗
║          NOTIFICADOR DE TELEGRAM - ALGO TRADER V3         ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    # Inicializar notificador
    notifier = TelegramNotifier()
    
    if notifier.is_active:
        print("\nTelegram conectado correctamente")
        print("Sistema de notificaciones activo")
        print("Presiona Ctrl+C para detener\n")
        
        # Mantener el servicio activo
        notifier.keep_alive()
    else:
        print("\nNo se pudo conectar con Telegram")
        print("Verifica el token y chat_id en el archivo .env")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nServicio detenido")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
