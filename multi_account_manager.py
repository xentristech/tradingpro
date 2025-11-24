"""
Multi Account Manager - Gestor de Múltiples Cuentas MT5
Maneja y valida operaciones en todas las cuentas configuradas
Version: 3.0.0
"""
import os
import sys
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv
import MetaTrader5 as mt5

# Configurar path del proyecto
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from enhanced_modules.trade_validator import TradeValidator
from notifiers.telegram_notifier import TelegramNotifier

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.FileHandler('logs/multi_account.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MultiAccountManager:
    """
    Gestor de múltiples cuentas MT5 con validación IA
    """
    
    def __init__(self):
        """Inicializa el gestor multi-cuenta"""
        # Cargar configuración
        load_dotenv('configs/.env')
        
        # Configurar cuenta EXNESS únicamente
        self.accounts = {
            'exness_trial': {
                'login': int(os.getenv('MT5_LOGIN', 197678662)),
                'server': os.getenv('MT5_SERVER', 'Exness-MT5Trial11'),
                'password': os.getenv('MT5_PASSWORD', ''),
                'path': os.getenv('MT5_PATH', 'C:\\Program Files\\MetaTrader 5 EXNESS\\terminal64.exe'),
                'active': True,
                'monitor_only': False,  # Automatización completa habilitada
                'auto_trade': True
            }
        }
        
        # Inicializar componentes
        self.telegram_notifier = self._initialize_telegram()
        self.trade_validator = TradeValidator(
            twelvedata_api_key=os.getenv('TWELVEDATA_API_KEY'),
            telegram_notifier=self.telegram_notifier
        )
        
        # Estado
        self.running = False
        self.account_status = {}
        
        logger.info("ExnessAccountManager inicializado")
    
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
        """Inicia el monitoreo de todas las cuentas"""
        logger.info("=" * 60)
        logger.info("INICIANDO EXNESS ACCOUNT MANAGER")
        logger.info("=" * 60)
        
        self.running = True
        
        # Notificar inicio
        if self.telegram_notifier:
            await self.telegram_notifier.send_message(
                "🏦 <b>EXNESS ACCOUNT MANAGER INICIADO</b>\n\n"
                "✅ Monitoreando cuenta EXNESS MT5\n"
                "✅ Validación automática con IA\n"
                "✅ Gestión de SL/TP inteligente\n\n"
                "<i>Verificando conexión...</i>"
            )
        
        # Loop principal
        try:
            while self.running:
                await self._monitoring_cycle()
                await asyncio.sleep(120)  # Check cada 2 minutos
                
        except KeyboardInterrupt:
            logger.info("Interrupción por usuario")
        except Exception as e:
            logger.error(f"Error en monitoring loop: {e}")
        finally:
            await self.stop_monitoring()
    
    async def _monitoring_cycle(self):
        """Ejecuta un ciclo de monitoreo de todas las cuentas"""
        try:
            logger.info(f"Iniciando ciclo de monitoreo - {datetime.now().strftime('%H:%M:%S')}")
            
            total_positions = 0
            total_problems = 0
            account_summary = []
            
            # Verificar cada cuenta
            for account_name, account_config in self.accounts.items():
                if not account_config['active']:
                    continue
                
                try:
                    logger.info(f"Verificando cuenta: {account_name}")
                    
                    # Conectar a la cuenta
                    connected = await self._connect_to_account(account_config)
                    
                    if connected:
                        # Analizar posiciones
                        positions = mt5.positions_get()
                        account_info = mt5.account_info()
                        
                        if account_info and positions is not None:
                            position_count = len(positions)
                            total_positions += position_count
                            
                            problems_found = 0
                            
                            # Verificar cada posición
                            for pos in positions:
                                if pos.sl == 0 or pos.tp == 0:
                                    problems_found += 1
                                    total_problems += 1
                                    
                                    # Validar con IA
                                    logger.warning(f"Posición sin protección: #{pos.ticket} en {account_name}")
                                    
                                    try:
                                        analysis = await self.trade_validator._analyze_position(pos)
                                        await self.trade_validator._send_validation_notification(analysis)
                                        logger.info(f"Notificación enviada para #{pos.ticket}")
                                    except Exception as e:
                                        logger.error(f"Error validando posición #{pos.ticket}: {e}")
                            
                            # Resumen de cuenta
                            account_summary.append({
                                'name': account_name,
                                'login': account_info.login,
                                'balance': account_info.balance,
                                'equity': account_info.equity,
                                'positions': position_count,
                                'problems': problems_found,
                                'status': 'CONNECTED'
                            })
                            
                            logger.info(f"Cuenta {account_name}: {position_count} posiciones, {problems_found} problemas")
                        
                        else:
                            logger.error(f"Error obteniendo datos de {account_name}")
                            account_summary.append({
                                'name': account_name,
                                'login': account_config['login'],
                                'status': 'ERROR'
                            })
                    
                    else:
                        logger.error(f"No se pudo conectar a {account_name}")
                        account_summary.append({
                            'name': account_name,
                            'login': account_config['login'],
                            'status': 'DISCONNECTED'
                        })
                
                except Exception as e:
                    logger.error(f"Error procesando cuenta {account_name}: {e}")
                    account_summary.append({
                        'name': account_name,
                        'login': account_config.get('login', 'Unknown'),
                        'status': 'ERROR'
                    })
            
            # Enviar resumen por Telegram
            if total_problems > 0:
                await self._send_summary_notification(account_summary, total_positions, total_problems)
            
            logger.info(f"Ciclo completado - {total_positions} posiciones, {total_problems} problemas")
            
        except Exception as e:
            logger.error(f"Error en ciclo de monitoreo: {e}")
    
    async def _connect_to_account(self, account_config: Dict) -> bool:
        """
        Conecta a una cuenta específica de MT5
        Args:
            account_config: Configuración de la cuenta
        Returns:
            True si la conexión fue exitosa
        """
        try:
            # Cerrar conexión anterior
            mt5.shutdown()
            
            # Inicializar MT5 con path específico si está configurado
            mt5_path = account_config.get('path')
            if mt5_path and os.path.exists(mt5_path):
                if not mt5.initialize(path=mt5_path):
                    logger.warning(f"Error inicializando con path específico, usando default")
                    if not mt5.initialize():
                        return False
            else:
                if not mt5.initialize():
                    return False
            
            # Intentar login si hay credenciales
            login = account_config.get('login')
            password = account_config.get('password')
            server = account_config.get('server')
            
            if login and password and server:
                if not mt5.login(login, password, server):
                    logger.warning(f"Login fallido para cuenta {login}, usando conexión actual")
            
            # Verificar conexión
            account_info = mt5.account_info()
            if account_info:
                logger.info(f"Conectado a cuenta {account_info.login} - Balance: ${account_info.balance:.2f}")
                return True
            else:
                return False
                
        except Exception as e:
            logger.error(f"Error conectando a cuenta: {e}")
            return False
    
    async def _send_summary_notification(self, account_summary: List[Dict], total_positions: int, total_problems: int):
        """
        Envía notificación de resumen por Telegram
        """
        if not self.telegram_notifier:
            return
        
        try:
            message = f"""
🏦 <b>RESUMEN CUENTA EXNESS</b>

📊 <b>ESTADO GENERAL:</b>
• Total posiciones: {total_positions}
• Problemas detectados: {total_problems}
• Hora: {datetime.now().strftime('%H:%M:%S')}

<b>📈 CUENTAS:</b>
"""
            
            for account in account_summary:
                status_emoji = {
                    'CONNECTED': '🟢',
                    'DISCONNECTED': '🔴', 
                    'ERROR': '⚠️'
                }.get(account['status'], '❓')
                
                message += f"{status_emoji} <b>{account['name'].upper()}</b>\n"
                message += f"   Login: {account['login']}\n"
                
                if account['status'] == 'CONNECTED':
                    message += f"   Balance: ${account['balance']:.2f}\n"
                    message += f"   Posiciones: {account['positions']}\n"
                    if account['problems'] > 0:
                        message += f"   ⚠️ Sin protección: {account['problems']}\n"
                else:
                    message += f"   Estado: {account['status']}\n"
                
                message += "\n"
            
            if total_problems > 0:
                message += f"⚠️ <b>ACCIÓN REQUERIDA:</b> {total_problems} posiciones sin SL/TP\n"
                message += "💡 Revisa los mensajes de validación anteriores"
            
            await self.telegram_notifier.send_message(message)
            
        except Exception as e:
            logger.error(f"Error enviando resumen: {e}")
    
    async def stop_monitoring(self):
        """Detiene el monitoreo"""
        logger.info("Deteniendo Exness Account Manager...")
        
        self.running = False
        
        if self.telegram_notifier:
            await self.telegram_notifier.send_message(
                "🛑 <b>EXNESS ACCOUNT MANAGER DETENIDO</b>\n\n"
                "<i>Monitoreo de cuenta desactivado</i>"
            )
        
        mt5.shutdown()
        logger.info("Exness Account Manager detenido")
    
    def get_status(self) -> Dict:
        """Obtiene el estado del gestor"""
        return {
            'running': self.running,
            'accounts': len(self.accounts),
            'account_status': self.account_status,
            'telegram_enabled': self.telegram_notifier is not None
        }

# Función principal
async def main():
    """Función principal del gestor multi-cuenta"""
    manager = MultiAccountManager()
    
    try:
        await manager.start_monitoring()
    except KeyboardInterrupt:
        logger.info("Deteniendo por interrupción del usuario...")
    finally:
        await manager.stop_monitoring()

if __name__ == "__main__":
    print("""
    ============================================================
    EXNESS ACCOUNT MANAGER v3.0 - Gestor de Cuenta EXNESS
    ============================================================
    
    - Monitoreo de cuenta EXNESS MT5
    - Configuración desde variables de entorno
    - Validación automática con IA
    - Gestión inteligente de SL/TP
    - Notificaciones por Telegram
    
    ============================================================
    """)
    
    # Ejecutar gestor
    asyncio.run(main())