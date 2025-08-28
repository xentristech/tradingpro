"""
Telegram Notifier - Sistema de Notificaciones por Telegram
Envía alertas y reportes del bot de trading
Version: 3.0.0
"""
import os
import logging
import asyncio
import aiohttp
from typing import Dict, List, Optional
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class TelegramNotifier:
    """
    Gestor de notificaciones por Telegram
    Soporta mensajes, imágenes y reportes formateados
    """
    
    def __init__(self, token: str = None, chat_id: str = None):
        """
        Inicializa el notificador
        Args:
            token: Token del bot de Telegram
            chat_id: ID del chat/canal
        """
        # Cargar variables de entorno desde .env
        from dotenv import load_dotenv
        load_dotenv('.env')
        
        self.token = token or os.getenv('TELEGRAM_TOKEN')
        self.chat_id = chat_id or os.getenv('TELEGRAM_CHAT_ID')
        
        if not self.token or not self.chat_id:
            logger.warning("Telegram no configurado correctamente")
            self.enabled = False
        else:
            self.enabled = True
            self.base_url = f"https://api.telegram.org/bot{self.token}"
            logger.info(f"TelegramNotifier inicializado para chat {self.chat_id}")
        
        # Cola de mensajes para evitar spam
        self.message_queue = []
        self.last_message_time = None
        self.min_interval = 1  # Segundos entre mensajes
    
    async def send_message(self, text: str, parse_mode: str = 'HTML') -> bool:
        """
        Envía un mensaje de texto
        Args:
            text: Texto a enviar
            parse_mode: Formato del mensaje (HTML/Markdown)
        Returns:
            True si se envió exitosamente
        """
        if not self.enabled:
            logger.debug(f"Telegram deshabilitado: {text[:50]}...")
            return False
        
        try:
            # Formatear mensaje
            formatted_text = self._format_message(text)
            
            # Construir URL y parámetros
            url = f"{self.base_url}/sendMessage"
            params = {
                'chat_id': self.chat_id,
                'text': formatted_text,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True
            }
            
            # Enviar request
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=params) as response:
                    if response.status == 200:
                        logger.debug("Mensaje enviado a Telegram")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Error enviando mensaje: {response.status} - {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"Error enviando mensaje a Telegram: {e}")
            return False
    
    async def send_photo(self, photo_path: str, caption: str = None) -> bool:
        """
        Envía una imagen
        Args:
            photo_path: Ruta a la imagen
            caption: Texto opcional
        Returns:
            True si se envió exitosamente
        """
        if not self.enabled:
            return False
        
        try:
            url = f"{self.base_url}/sendPhoto"
            
            with open(photo_path, 'rb') as photo:
                data = aiohttp.FormData()
                data.add_field('chat_id', self.chat_id)
                data.add_field('photo', photo, filename='image.png')
                if caption:
                    data.add_field('caption', caption)
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, data=data) as response:
                        return response.status == 200
                        
        except Exception as e:
            logger.error(f"Error enviando foto: {e}")
            return False
    
    async def send_trade_alert(self, trade_data: Dict):
        """
        Envía alerta de operación
        Args:
            trade_data: Datos de la operación
        """
        # Determinar emoji según tipo
        if trade_data.get('type') == 'buy':
            emoji = "🟢"
            action = "COMPRA"
        elif trade_data.get('type') == 'sell':
            emoji = "🔴"
            action = "VENTA"
        else:
            emoji = "📊"
            action = "OPERACIÓN"
        
        # Construir mensaje
        message = f"""
{emoji} <b>{action} EJECUTADA</b>

📈 <b>Símbolo:</b> {trade_data.get('symbol', 'N/A')}
💰 <b>Precio:</b> ${trade_data.get('price', 0):.5f}
📊 <b>Volumen:</b> {trade_data.get('volume', 0):.2f} lotes
🎯 <b>Take Profit:</b> ${trade_data.get('tp', 0):.5f}
🛡️ <b>Stop Loss:</b> ${trade_data.get('sl', 0):.5f}

📝 <b>Razón:</b> {trade_data.get('reason', 'Señal de trading')}
⏰ <b>Hora:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        await self.send_message(message)
    
    async def send_position_update(self, position_data: Dict):
        """
        Envía actualización de posición
        Args:
            position_data: Datos de la posición
        """
        # Determinar estado
        pnl = position_data.get('pnl', 0)
        if pnl > 0:
            emoji = "✅"
            status = "GANANCIA"
        elif pnl < 0:
            emoji = "❌"
            status = "PÉRDIDA"
        else:
            emoji = "⏸️"
            status = "NEUTRAL"
        
        message = f"""
{emoji} <b>ACTUALIZACIÓN DE POSICIÓN</b>

📊 <b>Símbolo:</b> {position_data.get('symbol', 'N/A')}
🆔 <b>ID:</b> {position_data.get('id', 'N/A')}
💵 <b>P&L:</b> ${pnl:.2f} ({position_data.get('pnl_pct', 0):.2f}%)
📈 <b>Precio actual:</b> ${position_data.get('current_price', 0):.5f}
📉 <b>Precio entrada:</b> ${position_data.get('entry_price', 0):.5f}

⏰ <b>Duración:</b> {position_data.get('duration', 'N/A')}
"""
        
        await self.send_message(message)
    
    async def send_daily_report(self, report_data: Dict):
        """
        Envía reporte diario
        Args:
            report_data: Datos del reporte
        """
        # Calcular estadísticas
        total_trades = report_data.get('total_trades', 0)
        winning_trades = report_data.get('winning_trades', 0)
        losing_trades = report_data.get('losing_trades', 0)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        message = f"""
📊 <b>REPORTE DIARIO</b>
{'='*30}

📅 <b>Fecha:</b> {datetime.now().strftime('%Y-%m-%d')}

<b>📈 RESUMEN DE TRADING</b>
• Total operaciones: {total_trades}
• Ganadoras: {winning_trades} ✅
• Perdedoras: {losing_trades} ❌
• Win Rate: {win_rate:.1f}%

<b>💰 RENDIMIENTO</b>
• P&L del día: ${report_data.get('daily_pnl', 0):.2f}
• P&L del mes: ${report_data.get('monthly_pnl', 0):.2f}
• Balance actual: ${report_data.get('balance', 0):.2f}

<b>📊 MÉTRICAS</b>
• Sharpe Ratio: {report_data.get('sharpe_ratio', 0):.2f}
• Max Drawdown: {report_data.get('max_drawdown', 0):.1f}%
• Promedio ganancia: ${report_data.get('avg_win', 0):.2f}
• Promedio pérdida: ${report_data.get('avg_loss', 0):.2f}

<b>🎯 MEJORES OPERACIONES</b>
{self._format_top_trades(report_data.get('top_trades', []))}

{'='*30}
🤖 AlgoTrader v3.0
        """
        
        await self.send_message(message)
    
    async def send_signal_alert(self, signal_data: Dict):
        """
        Envía alerta detallada de señal generada
        Args:
            signal_data: Datos completos de la señal
        """
        # Determinar dirección
        direction = signal_data.get('direction', 'NEUTRAL')
        if direction == 'BUY':
            emoji = "🟢📈"
            action = "COMPRA"
        elif direction == 'SELL':
            emoji = "🔴📉" 
            action = "VENTA"
        else:
            emoji = "⚪🔍"
            action = "NEUTRAL"

        # Formatear razones
        reasons = signal_data.get('reasons', [])
        reasons_text = '\n'.join([f"• {reason}" for reason in reasons[:5]])
        
        message = f"""
{emoji} <b>SEÑAL DE TRADING DETECTADA</b>

📊 <b>Símbolo:</b> {signal_data.get('symbol', 'BTCUSDm')}
🎯 <b>Dirección:</b> {action}
💪 <b>Fuerza:</b> {signal_data.get('strength', 0):.2f} / 1.0
🎲 <b>Confianza:</b> {signal_data.get('confidence', 0):.1%}
💰 <b>Precio actual:</b> ${signal_data.get('price', 0):,.2f}

<b>🧠 ANÁLISIS TÉCNICO:</b>
{reasons_text}

<b>📈 NIVELES SUGERIDOS:</b>
• Entrada: ${signal_data.get('entry_price', 0):,.2f}
• Stop Loss: ${signal_data.get('stop_loss', 0):,.2f}
• Take Profit: ${signal_data.get('take_profit', 0):,.2f}

⏰ <b>Hora:</b> {datetime.now().strftime('%H:%M:%S')}
        """
        
        await self.send_message(message)
    
    async def send_execution_result(self, execution_data: Dict):
        """
        Envía resultado de ejecución en MT5
        Args:
            execution_data: Datos del resultado de ejecución
        """
        success = execution_data.get('success', False)
        
        if success:
            emoji = "✅"
            title = "ORDEN EJECUTADA"
            color = "🟢"
        else:
            emoji = "❌"
            title = "ERROR DE EJECUCIÓN"
            color = "🔴"
        
        message = f"""
{emoji} <b>{title}</b>

{color} <b>Estado:</b> {"EXITOSO" if success else "FALLÓ"}
📊 <b>Símbolo:</b> {execution_data.get('symbol', 'N/A')}
🎯 <b>Tipo:</b> {execution_data.get('order_type', 'N/A')}
📦 <b>Volumen:</b> {execution_data.get('volume', 0):.2f} lotes
💰 <b>Precio:</b> ${execution_data.get('price', 0):,.5f}

<b>🆔 Detalles MT5:</b>
• Ticket: {execution_data.get('ticket', 'N/A')}
• Magic: {execution_data.get('magic', 'N/A')}
• Retcode: {execution_data.get('retcode', 'N/A')}

{f"<b>❌ ERROR:</b> {execution_data.get('error_message', '')}" if not success else ""}

⏰ <b>Hora:</b> {datetime.now().strftime('%H:%M:%S')}
        """
        
        await self.send_message(message)

    async def send_error_alert(self, error_data: Dict):
        """
        Envía alerta de error
        Args:
            error_data: Datos del error
        """
        message = f"""
⚠️ <b>ERROR EN EL SISTEMA</b>

🔴 <b>Tipo:</b> {error_data.get('type', 'Unknown')}
📝 <b>Mensaje:</b> {error_data.get('message', 'Sin descripción')}
📍 <b>Ubicación:</b> {error_data.get('location', 'N/A')}
⏰ <b>Hora:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<b>Acción tomada:</b> {error_data.get('action', 'Sistema en pausa')}
        """
        
        await self.send_message(message)
    
    async def send_market_alert(self, alert_data: Dict):
        """
        Envía alerta de mercado
        Args:
            alert_data: Datos de la alerta
        """
        # Determinar nivel de alerta
        level = alert_data.get('level', 'info')
        if level == 'critical':
            emoji = "🚨"
            title = "ALERTA CRÍTICA"
        elif level == 'warning':
            emoji = "⚠️"
            title = "ADVERTENCIA"
        else:
            emoji = "ℹ️"
            title = "INFORMACIÓN"
        
        message = f"""
{emoji} <b>{title}</b>

📊 <b>Mercado:</b> {alert_data.get('market', 'N/A')}
📈 <b>Indicador:</b> {alert_data.get('indicator', 'N/A')}
💡 <b>Señal:</b> {alert_data.get('signal', 'N/A')}

<b>Detalles:</b>
{alert_data.get('details', 'Sin detalles adicionales')}

<b>Recomendación:</b> {alert_data.get('recommendation', 'Monitorear situación')}
        """
        
        await self.send_message(message)
    
    def _format_message(self, text: str) -> str:
        """
        Formatea el mensaje para Telegram
        Args:
            text: Texto original
        Returns:
            Texto formateado
        """
        # Limitar longitud
        max_length = 4096
        if len(text) > max_length:
            text = text[:max_length-3] + "..."
        
        # Escapar caracteres HTML si es necesario
        # (Telegram acepta estos caracteres en HTML)
        
        return text
    
    def _format_top_trades(self, trades: List[Dict]) -> str:
        """
        Formatea las mejores operaciones
        Args:
            trades: Lista de operaciones
        Returns:
            Texto formateado
        """
        if not trades:
            return "• No hay operaciones destacadas"
        
        formatted = []
        for i, trade in enumerate(trades[:3], 1):
            formatted.append(
                f"{i}. {trade.get('symbol', 'N/A')}: "
                f"${trade.get('pnl', 0):.2f} "
                f"({trade.get('pnl_pct', 0):.1f}%)"
            )
        
        return '\n'.join(formatted)
    
    async def send_bulk_messages(self, messages: List[str]):
        """
        Envía múltiples mensajes respetando límites
        Args:
            messages: Lista de mensajes
        """
        for message in messages:
            await self.send_message(message)
            await asyncio.sleep(self.min_interval)
    
    def format_number(self, number: float, decimals: int = 2) -> str:
        """
        Formatea números para mejor legibilidad
        Args:
            number: Número a formatear
            decimals: Decimales a mostrar
        Returns:
            Número formateado
        """
        if abs(number) >= 1_000_000:
            return f"{number/1_000_000:.{decimals}f}M"
        elif abs(number) >= 1_000:
            return f"{number/1_000:.{decimals}f}K"
        else:
            return f"{number:.{decimals}f}"

# Funciones auxiliares para uso sincrónico
def send_telegram_message(text: str) -> bool:
    """
    Función sincrónica para enviar mensaje
    Args:
        text: Texto a enviar
    Returns:
        True si se envió exitosamente
    """
    notifier = TelegramNotifier()
    return asyncio.run(notifier.send_message(text))

def send_trade_notification(trade_data: Dict):
    """
    Función sincrónica para enviar notificación de trade
    Args:
        trade_data: Datos del trade
    """
    notifier = TelegramNotifier()
    asyncio.run(notifier.send_trade_alert(trade_data))

def send_signal_notification(signal_data: Dict):
    """
    Función sincrónica para enviar notificación de señal
    Args:
        signal_data: Datos de la señal
    """
    notifier = TelegramNotifier()
    asyncio.run(notifier.send_signal_alert(signal_data))

def send_execution_notification(execution_data: Dict):
    """
    Función sincrónica para enviar notificación de ejecución
    Args:
        execution_data: Datos del resultado de ejecución
    """
    notifier = TelegramNotifier()
    asyncio.run(notifier.send_execution_result(execution_data))

def send_error_notification(error_data: Dict):
    """
    Función sincrónica para enviar notificación de error
    Args:
        error_data: Datos del error
    """
    notifier = TelegramNotifier()
    asyncio.run(notifier.send_error_alert(error_data))

# Testing
if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Cargar configuración
    load_dotenv('configs/.env')
    
    # Crear notifier
    notifier = TelegramNotifier()
    
    if notifier.enabled:
        # Test: Enviar mensaje simple
        async def test():
            print("📤 Enviando mensaje de prueba...")
            
            # Mensaje simple
            await notifier.send_message("🤖 Test de AlgoTrader v3.0")
            
            # Alerta de trade
            trade_data = {
                'type': 'buy',
                'symbol': 'BTCUSD',
                'price': 43250.50,
                'volume': 0.1,
                'tp': 44000,
                'sl': 42500,
                'reason': 'Señal de cruce de medias'
            }
            await notifier.send_trade_alert(trade_data)
            
            # Reporte diario
            report_data = {
                'total_trades': 15,
                'winning_trades': 10,
                'losing_trades': 5,
                'daily_pnl': 523.45,
                'monthly_pnl': 3456.78,
                'balance': 10523.45,
                'sharpe_ratio': 1.85,
                'max_drawdown': 8.5,
                'avg_win': 125.30,
                'avg_loss': 45.20,
                'top_trades': [
                    {'symbol': 'BTCUSD', 'pnl': 234.56, 'pnl_pct': 2.3},
                    {'symbol': 'ETHUSD', 'pnl': 156.78, 'pnl_pct': 1.5},
                    {'symbol': 'SOLUSD', 'pnl': 98.45, 'pnl_pct': 0.9}
                ]
            }
            await notifier.send_daily_report(report_data)
            
            print("✅ Mensajes enviados!")
        
        asyncio.run(test())
    else:
        print("❌ Telegram no está configurado. Verifica TELEGRAM_TOKEN y TELEGRAM_CHAT_ID en .env")
