"""
AI Trade Monitor - Monitor Inteligente de Operaciones
Supervisa trades, valida con IA y gestiona automáticamente SL/TP
Version: 3.0.0
"""
import os
import sys
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Configurar path del proyecto
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

# Importar módulos del proyecto
from enhanced_modules.trade_validator import TradeValidator
from notifiers.telegram_notifier import TelegramNotifier
import MetaTrader5 as mt5

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.FileHandler('logs/ai_trade_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AITradeMonitor:
    """
    Monitor inteligente de operaciones con validación IA
    """
    
    def __init__(self):
        """Inicializa el monitor"""
        # Cargar configuración
        load_dotenv('configs/.env')
        
        self.running = False
        self.validation_interval = 300  # 5 minutos
        self.last_validation_time = None
        
        # Inicializar componentes
        self.telegram_notifier = self._initialize_telegram()
        self.trade_validator = TradeValidator(
            twelvedata_api_key=os.getenv('TWELVEDATA_API_KEY'),
            telegram_notifier=self.telegram_notifier
        )
        
        # Estado
        self.monitored_positions = set()
        self.validation_history = []
        
        logger.info("AI Trade Monitor inicializado")
    
    def _initialize_telegram(self):
        """Inicializa notificador de Telegram"""
        try:
            if os.getenv('TELEGRAM_TOKEN') and os.getenv('TELEGRAM_CHAT_ID'):
                return TelegramNotifier()
            else:
                logger.warning("Credenciales de Telegram no configuradas")
                return None
        except Exception as e:
            logger.error(f"Error inicializando Telegram: {e}")
            return None
    
    async def start_monitoring(self):
        """Inicia el monitoreo continuo"""
        logger.info("🤖 INICIANDO AI TRADE MONITOR")
        logger.info("="*60)
        
        if not mt5.initialize():
            logger.error("❌ No se pudo inicializar MT5")
            return
        
        self.running = True
        
        # Enviar notificación de inicio
        if self.telegram_notifier:
            await self.telegram_notifier.send_message(
                "🤖 <b>AI TRADE MONITOR INICIADO</b>\n\n"
                "✅ Validación automática de trades\n"
                "✅ Gestión inteligente de SL/TP\n"
                "✅ Notificaciones en tiempo real\n\n"
                "<i>Monitoreando cada 5 minutos...</i>"
            )
        
        # Loop principal
        try:
            while self.running:
                await self._monitoring_cycle()
                await asyncio.sleep(60)  # Check cada minuto
                
        except KeyboardInterrupt:
            logger.info("⚠️ Interrupción por usuario")
        except Exception as e:
            logger.error(f"❌ Error en monitoring loop: {e}")
        finally:
            await self.stop_monitoring()
    
    async def _monitoring_cycle(self):
        """Ejecuta un ciclo de monitoreo"""
        try:
            current_time = datetime.now()
            
            # Verificar si es momento de validar
            should_validate = (
                self.last_validation_time is None or 
                (current_time - self.last_validation_time).seconds >= self.validation_interval
            )
            
            if should_validate:
                logger.info("🔍 Ejecutando validación de trades...")
                await self._validate_all_trades()
                self.last_validation_time = current_time
            
            # Verificar nuevas posiciones
            await self._check_new_positions()
            
            # Procesar comandos pendientes de Telegram
            # (Esto se haría con webhook en producción)
            
        except Exception as e:
            logger.error(f"Error en ciclo de monitoreo: {e}")
    
    async def _validate_all_trades(self):
        """Valida todas las operaciones abiertas"""
        try:
            analyses = await self.trade_validator.validate_all_positions()
            
            if not analyses:
                logger.info("No hay posiciones para validar")
                return
            
            # Procesar cada análisis
            actions_taken = []
            for analysis in analyses:
                logger.info(f"📊 Validando #{analysis.ticket} ({analysis.symbol})")
                logger.info(f"   Viable: {analysis.is_viable} | Confianza: {analysis.confidence:.1%}")
                logger.info(f"   Recomendación: {analysis.recommendation}")
                
                if analysis.reasons:
                    logger.info("   Problemas detectados:")
                    for reason in analysis.reasons:
                        logger.info(f"     • {reason}")
                
                # Guardar en historial
                self.validation_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'ticket': analysis.ticket,
                    'analysis': analysis
                })
                
                # Las acciones se ejecutan automáticamente por el TradeValidator
                # a través de las notificaciones de Telegram
                
                if analysis.recommendation != 'KEEP':
                    actions_taken.append(f"#{analysis.ticket} - {analysis.recommendation}")
            
            # Resumen
            if actions_taken:
                logger.info(f"✅ Validación completada - {len(actions_taken)} acciones requeridas")
            else:
                logger.info("✅ Validación completada - Todos los trades OK")
                
        except Exception as e:
            logger.error(f"Error validando trades: {e}")
    
    async def _check_new_positions(self):
        """Verifica si hay nuevas posiciones abiertas"""
        try:
            positions = mt5.positions_get()
            if not positions:
                return
            
            current_tickets = {pos.ticket for pos in positions}
            new_positions = current_tickets - self.monitored_positions
            closed_positions = self.monitored_positions - current_tickets
            
            # Procesar nuevas posiciones
            for ticket in new_positions:
                position = next(pos for pos in positions if pos.ticket == ticket)
                await self._process_new_position(position)
            
            # Actualizar conjunto de posiciones monitoreadas
            self.monitored_positions = current_tickets
            
            # Log posiciones cerradas
            if closed_positions:
                logger.info(f"📉 Posiciones cerradas: {closed_positions}")
                
        except Exception as e:
            logger.error(f"Error verificando nuevas posiciones: {e}")
    
    async def _process_new_position(self, position):
        """Procesa una nueva posición detectada"""
        try:
            logger.info(f"🆕 Nueva posición detectada: #{position.ticket} {position.symbol}")
            
            # Verificar inmediatamente si tiene SL/TP
            has_sl = position.sl != 0
            has_tp = position.tp != 0
            
            if not has_sl or not has_tp:
                logger.warning(f"⚠️ Posición #{position.ticket} sin SL/TP completos")
                
                # Validación inmediata para posiciones sin protección
                analysis = await self.trade_validator._analyze_position(position)
                await self.trade_validator._send_validation_notification(analysis)
                
            else:
                logger.info(f"✅ Posición #{position.ticket} con SL/TP configurados")
                
                # Notificación informativa
                if self.telegram_notifier:
                    action_emoji = "🟢" if position.type == 0 else "🔴"
                    await self.telegram_notifier.send_message(
                        f"{action_emoji} <b>Nueva operación detectada</b>\n\n"
                        f"🎯 <b>#{position.ticket}</b> - {position.symbol}\n"
                        f"📊 Tipo: {'BUY' if position.type == 0 else 'SELL'}\n"
                        f"💰 Volumen: {position.volume}\n"
                        f"💵 Precio: {position.price_open}\n"
                        f"🛡️ SL: {position.sl if position.sl != 0 else 'N/A'}\n"
                        f"🎯 TP: {position.tp if position.tp != 0 else 'N/A'}\n\n"
                        f"✅ <i>Protecciones configuradas correctamente</i>"
                    )
                
        except Exception as e:
            logger.error(f"Error procesando nueva posición: {e}")
    
    async def process_telegram_message(self, message: str) -> str:
        """
        Procesa mensajes de Telegram para comandos de validación
        """
        try:
            message = message.strip().upper()
            
            # Comandos de validación
            if any(cmd in message for cmd in ['APPROVE', 'CLOSE', 'IGNORE']):
                return await self.trade_validator.process_telegram_command(message)
            
            # Comando de estado
            elif message == 'MONITOR_STATUS':
                return await self._get_monitor_status()
            
            # Comando de validación manual
            elif message == 'VALIDATE_NOW':
                await self._validate_all_trades()
                return "✅ Validación manual ejecutada"
            
            # Comando de pausa/reanudación
            elif message == 'PAUSE_MONITOR':
                self.running = False
                return "⏸️ Monitor pausado"
                
            elif message == 'RESUME_MONITOR':
                if not self.running:
                    self.running = True
                    asyncio.create_task(self.start_monitoring())
                    return "▶️ Monitor reanudado"
                else:
                    return "ℹ️ Monitor ya está ejecutándose"
            
            else:
                return None  # No es un comando de este módulo
                
        except Exception as e:
            logger.error(f"Error procesando mensaje Telegram: {e}")
            return f"❌ Error procesando comando: {str(e)}"
    
    async def _get_monitor_status(self) -> str:
        """Obtiene el estado actual del monitor"""
        try:
            positions = mt5.positions_get()
            position_count = len(positions) if positions else 0
            
            status = f"""
🤖 <b>AI TRADE MONITOR STATUS</b>

📊 <b>Estado:</b> {'🟢 ACTIVO' if self.running else '🔴 PAUSADO'}
📈 <b>Posiciones monitoreadas:</b> {position_count}
⏰ <b>Última validación:</b> {self.last_validation_time.strftime('%H:%M:%S') if self.last_validation_time else 'Nunca'}
📝 <b>Validaciones realizadas:</b> {len(self.validation_history)}

<b>⚙️ CONFIGURACIÓN:</b>
• Intervalo validación: {self.validation_interval//60} minutos
• TwelveData: {'✅' if os.getenv('TWELVEDATA_API_KEY') else '❌'}
• Telegram: {'✅' if self.telegram_notifier else '❌'}

<b>🎮 COMANDOS DISPONIBLES:</b>
• <code>VALIDATE_NOW</code> - Validar ahora
• <code>PAUSE_MONITOR</code> - Pausar monitor
• <code>RESUME_MONITOR</code> - Reanudar monitor
"""
            
            if position_count > 0:
                status += f"\n<b>📈 POSICIONES ACTUALES:</b>\n"
                for pos in positions:
                    action_emoji = "🟢" if pos.type == 0 else "🔴"
                    status += f"{action_emoji} #{pos.ticket} {pos.symbol} P&L: ${pos.profit:.2f}\n"
            
            return status
            
        except Exception as e:
            logger.error(f"Error obteniendo estado: {e}")
            return "❌ Error obteniendo estado del monitor"
    
    async def stop_monitoring(self):
        """Detiene el monitoreo"""
        logger.info("🛑 Deteniendo AI Trade Monitor...")
        
        self.running = False
        
        if self.telegram_notifier:
            await self.telegram_notifier.send_message(
                "🛑 <b>AI TRADE MONITOR DETENIDO</b>\n\n"
                f"📊 Validaciones realizadas: {len(self.validation_history)}\n"
                f"⏰ Tiempo activo: {datetime.now()}\n\n"
                "<i>Monitor desactivado</i>"
            )
        
        logger.info("✅ AI Trade Monitor detenido")

# Función principal
async def main():
    """Función principal del monitor"""
    monitor = AITradeMonitor()
    
    try:
        await monitor.start_monitoring()
    except KeyboardInterrupt:
        logger.info("Deteniendo por interrupción del usuario...")
    finally:
        await monitor.stop_monitoring()

if __name__ == "__main__":
    print("""
    ============================================================
    AI TRADE MONITOR v3.0 - Monitor Inteligente de Operaciones
    ============================================================
    
    - Validacion automatica con IA
    - Gestion inteligente de SL/TP  
    - Notificaciones Telegram
    - Analisis tecnico avanzado
    
    ============================================================
    """)
    
    # Ejecutar monitor
    asyncio.run(main())