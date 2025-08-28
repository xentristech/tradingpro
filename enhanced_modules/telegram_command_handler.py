"""
Telegram Command Handler - Manejador de Comandos de Telegram
Integra validación IA con comandos de Telegram
Version: 3.0.0
"""
import logging
import asyncio
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class TelegramCommandHandler:
    """
    Manejador de comandos de Telegram con validación IA
    """
    
    def __init__(self, ai_trade_monitor=None):
        """
        Inicializa el manejador
        Args:
            ai_trade_monitor: Instancia del monitor IA
        """
        self.ai_monitor = ai_trade_monitor
        self.commands = {
            # Comandos de validación
            'APPROVE': self._handle_approve,
            'CLOSE': self._handle_close,
            'IGNORE': self._handle_ignore,
            
            # Comandos de monitor
            'VALIDATE_NOW': self._handle_validate_now,
            'MONITOR_STATUS': self._handle_monitor_status,
            'PAUSE_MONITOR': self._handle_pause_monitor,
            'RESUME_MONITOR': self._handle_resume_monitor,
            
            # Comandos tradicionales del bot
            'STATUS': self._handle_status,
            'PAUSE': self._handle_pause,
            'RESUME': self._handle_resume,
            'STOP': self._handle_stop,
        }
        
        logger.info("TelegramCommandHandler inicializado")
    
    async def process_message(self, message: str) -> Optional[str]:
        """
        Procesa un mensaje de Telegram
        Args:
            message: Mensaje recibido
        Returns:
            Respuesta para enviar o None si no se reconoce el comando
        """
        try:
            message = message.strip()
            
            # Extraer comando y parámetros
            parts = message.split()
            if not parts:
                return None
            
            command = parts[0].upper()
            params = parts[1:] if len(parts) > 1 else []
            
            # Comandos con parámetros (validación)
            if command in ['APPROVE', 'CLOSE', 'IGNORE'] and params:
                full_command = f"{command} {params[0]}"
                if self.ai_monitor:
                    return await self.ai_monitor.process_telegram_message(full_command)
                else:
                    return "❌ Monitor IA no disponible"
            
            # Comandos simples
            elif command in self.commands:
                handler = self.commands[command]
                return await handler()
            
            # Comando no reconocido
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error procesando mensaje: {e}")
            return f"❌ Error procesando comando: {str(e)}"
    
    async def _handle_approve(self) -> str:
        """Maneja comando APPROVE"""
        return "ℹ️ Uso: APPROVE CÓDIGO\nEjemplo: APPROVE VAL12345"
    
    async def _handle_close(self) -> str:
        """Maneja comando CLOSE"""
        return "ℹ️ Uso: CLOSE CÓDIGO\nEjemplo: CLOSE VAL12345"
    
    async def _handle_ignore(self) -> str:
        """Maneja comando IGNORE"""
        return "ℹ️ Uso: IGNORE CÓDIGO\nEjemplo: IGNORE VAL12345"
    
    async def _handle_validate_now(self) -> str:
        """Maneja comando VALIDATE_NOW"""
        if self.ai_monitor:
            return await self.ai_monitor.process_telegram_message('VALIDATE_NOW')
        return "❌ Monitor IA no disponible"
    
    async def _handle_monitor_status(self) -> str:
        """Maneja comando MONITOR_STATUS"""
        if self.ai_monitor:
            return await self.ai_monitor.process_telegram_message('MONITOR_STATUS')
        return "❌ Monitor IA no disponible"
    
    async def _handle_pause_monitor(self) -> str:
        """Maneja comando PAUSE_MONITOR"""
        if self.ai_monitor:
            return await self.ai_monitor.process_telegram_message('PAUSE_MONITOR')
        return "❌ Monitor IA no disponible"
    
    async def _handle_resume_monitor(self) -> str:
        """Maneja comando RESUME_MONITOR"""
        if self.ai_monitor:
            return await self.ai_monitor.process_telegram_message('RESUME_MONITOR')
        return "❌ Monitor IA no disponible"
    
    async def _handle_status(self) -> str:
        """Maneja comando STATUS tradicional"""
        try:
            import MetaTrader5 as mt5
            
            if not mt5.initialize():
                return "❌ Error conectando a MT5"
            
            # Información básica de cuenta
            account_info = mt5.account_info()
            if not account_info:
                return "❌ Error obteniendo información de cuenta"
            
            positions = mt5.positions_get()
            position_count = len(positions) if positions else 0
            
            total_profit = sum(pos.profit for pos in positions) if positions else 0
            
            status_msg = f"""
📊 <b>ESTADO DEL SISTEMA</b>

💰 <b>Cuenta:</b> {account_info.login}
💵 <b>Balance:</b> ${account_info.balance:.2f}
💲 <b>Equity:</b> ${account_info.equity:.2f}
📈 <b>Posiciones:</b> {position_count}
💹 <b>P&L Total:</b> ${total_profit:.2f}

⏰ <b>Actualizado:</b> {datetime.now().strftime('%H:%M:%S')}
"""
            
            if positions:
                status_msg += "\n<b>📈 POSICIONES ACTIVAS:</b>\n"
                for pos in positions[:5]:  # Máximo 5 posiciones
                    action_emoji = "🟢" if pos.type == 0 else "🔴"
                    sl_status = "✅" if pos.sl != 0 else "❌"
                    tp_status = "✅" if pos.tp != 0 else "❌"
                    
                    status_msg += (
                        f"{action_emoji} <code>#{pos.ticket}</code> {pos.symbol}\n"
                        f"   💰 P&L: <b>${pos.profit:.2f}</b> | "
                        f"SL: {sl_status} | TP: {tp_status}\n"
                    )
                
                if len(positions) > 5:
                    status_msg += f"... y {len(positions) - 5} más\n"
            
            return status_msg
            
        except Exception as e:
            logger.error(f"Error en comando STATUS: {e}")
            return f"❌ Error obteniendo estado: {str(e)}"
    
    async def _handle_pause(self) -> str:
        """Maneja comando PAUSE tradicional"""
        # Aquí se integraría con el bot principal
        return "⏸️ Comando PAUSE recibido\n(Integrar con bot principal)"
    
    async def _handle_resume(self) -> str:
        """Maneja comando RESUME tradicional"""
        # Aquí se integraría con el bot principal
        return "▶️ Comando RESUME recibido\n(Integrar con bot principal)"
    
    async def _handle_stop(self) -> str:
        """Maneja comando STOP tradicional"""
        # Aquí se integraría con el bot principal
        return "🛑 Comando STOP recibido\n(Integrar con bot principal)"
    
    def get_help_message(self) -> str:
        """Obtiene mensaje de ayuda con todos los comandos"""
        return """
🤖 <b>COMANDOS DISPONIBLES</b>

<b>📊 INFORMACIÓN:</b>
• <code>STATUS</code> - Estado general del sistema
• <code>MONITOR_STATUS</code> - Estado del monitor IA

<b>🔍 VALIDACIÓN IA:</b>
• <code>VALIDATE_NOW</code> - Validar trades ahora
• <code>APPROVE CÓDIGO</code> - Aprobar acción sugerida
• <code>CLOSE CÓDIGO</code> - Cerrar posición
• <code>IGNORE CÓDIGO</code> - Ignorar validación

<b>⚙️ CONTROL:</b>
• <code>PAUSE</code> - Pausar trading
• <code>RESUME</code> - Reanudar trading
• <code>STOP</code> - Detener sistema
• <code>PAUSE_MONITOR</code> - Pausar monitor IA
• <code>RESUME_MONITOR</code> - Reanudar monitor IA

<i>💡 El sistema validará automáticamente trades sin SL/TP cada 5 minutos</i>
"""

# Testing
if __name__ == "__main__":
    import asyncio
    
    async def test_handler():
        handler = TelegramCommandHandler()
        
        # Probar comandos
        test_commands = [
            "STATUS",
            "VALIDATE_NOW", 
            "APPROVE VAL123",
            "INVALID_COMMAND"
        ]
        
        for cmd in test_commands:
            print(f"\n> {cmd}")
            response = await handler.process_message(cmd)
            print(f"< {response}")
    
    asyncio.run(test_handler())