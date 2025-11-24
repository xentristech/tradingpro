"""
Multi Account Manager FIXED v3.2 - Con credenciales correctas
Gestor de Múltiples Cuentas MT5 sin duplicación
Version: 3.2.0
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
import time

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
        logging.FileHandler('logs/multi_account_fixed.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MultiAccountManagerFixed:
    """
    Gestor CORREGIDO de múltiples cuentas MT5 con validación IA
    """
    
    def __init__(self):
        """Inicializa el gestor multi-cuenta"""
        # Cargar configuración
        load_dotenv('configs/.env')
        
        # CONFIGURACIÓN SOLO EXNESS
        self.accounts = {
            'exness_trial': {
                'login': int(os.getenv('MT5_LOGIN', 197678662)),  # EXNESS TRIAL
                'password': os.getenv('MT5_PASSWORD', 'Badboy930218*'),  # Password Exness
                'server': os.getenv('MT5_SERVER', 'Exness-MT5Trial11'),  # Servidor Exness
                'path': os.getenv('MT5_PATH', 'C:\\Program Files\\MetaTrader 5 EXNESS\\terminal64.exe'),
                'active': True,
                'monitor_only': False,  # Puede hacer trading
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
        self.account_data = {}  # Almacenar datos de cada cuenta
        
        logger.info("MultiAccountManager v3.2 inicializado para EXNESS únicamente")
    
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
    
    async def get_account_data(self, account_name: str, account_config: Dict) -> Dict:
        """
        Obtiene datos de una cuenta específica con reconexión completa
        
        Args:
            account_name: Nombre de la cuenta
            account_config: Configuración de la cuenta
            
        Returns:
            Diccionario con datos de la cuenta
        """
        result = {
            'name': account_name,
            'login': account_config['login'],
            'status': 'DISCONNECTED',
            'balance': 0,
            'equity': 0,
            'positions': 0,
            'problems': 0,
            'position_details': []
        }
        
        try:
            # IMPORTANTE: Cerrar completamente la conexión anterior
            mt5.shutdown()
            time.sleep(1)  # Esperar un momento para asegurar cierre completo
            
            # Inicializar MT5 con el path específico
            mt5_path = account_config.get('path')
            
            if mt5_path and os.path.exists(mt5_path):
                logger.info(f"Inicializando MT5 con path: {mt5_path}")
                if not mt5.initialize(path=mt5_path):
                    logger.error(f"No se pudo inicializar MT5 con path {mt5_path}")
                    return result
            else:
                logger.info("Inicializando MT5 con path por defecto")
                if not mt5.initialize():
                    logger.error("No se pudo inicializar MT5")
                    return result
            
            # Hacer login con las credenciales específicas
            login = account_config.get('login')
            password = account_config.get('password')
            server = account_config.get('server')
            
            if login and password and server:
                logger.info(f"Intentando login: {login} en {server}")
                authorized = mt5.login(login, password=password, server=server)
                
                if not authorized:
                    error = mt5.last_error()
                    logger.error(f"Login fallido para {login}: {error}")
                    return result
            else:
                logger.warning(f"Credenciales incompletas para {account_name}")
            
            # Verificar que estamos en la cuenta correcta
            account_info = mt5.account_info()
            if not account_info:
                logger.error(f"No se pudo obtener información de cuenta para {account_name}")
                return result
            
            # VERIFICACIÓN IMPORTANTE: Asegurar que estamos en la cuenta correcta
            if account_info.login != login:
                logger.warning(f"Cuenta incorrecta: esperaba {login}, obtuvo {account_info.login}")
                # Intentar reconectar
                mt5.shutdown()
                time.sleep(1)
                if not mt5.initialize(path=mt5_path):
                    return result
                if not mt5.login(login, password=password, server=server):
                    return result
                account_info = mt5.account_info()
                if not account_info or account_info.login != login:
                    logger.error(f"No se pudo conectar a la cuenta correcta {login}")
                    return result
            
            # Obtener posiciones
            positions = mt5.positions_get()
            if positions is None:
                positions = []
            
            # Actualizar resultado con datos reales
            result['status'] = 'CONNECTED'
            result['balance'] = account_info.balance
            result['equity'] = account_info.equity
            result['positions'] = len(positions)
            result['server'] = account_info.server
            result['company'] = account_info.company
            
            # Verificar problemas en posiciones
            problems_found = 0
            for pos in positions:
                if pos.sl == 0 or pos.tp == 0:
                    problems_found += 1
                
                result['position_details'].append({
                    'ticket': pos.ticket,
                    'symbol': pos.symbol,
                    'volume': pos.volume,
                    'profit': pos.profit,
                    'has_sl': pos.sl != 0,
                    'has_tp': pos.tp != 0
                })
            
            result['problems'] = problems_found
            
            logger.info(f"Cuenta {account_name} ({login}): {len(positions)} posiciones, Balance: ${account_info.balance:.2f}")
            
        except Exception as e:
            logger.error(f"Error obteniendo datos de {account_name}: {e}")
            result['status'] = 'ERROR'
        
        finally:
            # Cerrar conexión después de obtener datos
            mt5.shutdown()
        
        return result
    
    async def start_monitoring(self):
        """Inicia el monitoreo de todas las cuentas"""
        logger.info("=" * 60)
        logger.info("INICIANDO EXNESS ACCOUNT MANAGER v3.2")
        logger.info("Configurado para cuenta EXNESS únicamente")
        logger.info("=" * 60)
        
        self.running = True
        
        # Notificar inicio
        if self.telegram_notifier:
            await self.telegram_notifier.send_message(
                "🏦 <b>EXNESS ACCOUNT MANAGER v3.2</b>\n\n"
                "✅ Monitoreando cuenta EXNESS MT5\n"
                "✅ EXNESS TRIAL: 197678662\n"
                "✅ Configurado desde variables de entorno\n"
                "✅ Validación automática con IA\n\n"
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
            logger.info(f"\n{'='*60}")
            logger.info(f"Iniciando ciclo de monitoreo - {datetime.now().strftime('%H:%M:%S')}")
            logger.info(f"{'='*60}")
            
            total_positions = 0
            total_problems = 0
            account_summary = []
            
            # Verificar cada cuenta INDEPENDIENTEMENTE
            for account_name, account_config in self.accounts.items():
                if not account_config['active']:
                    continue
                
                logger.info(f"\nVerificando cuenta: {account_name}")
                logger.info(f"Login configurado: {account_config['login']}")
                logger.info(f"Servidor: {account_config['server']}")
                
                # Obtener datos de la cuenta con reconexión completa
                account_data = await self.get_account_data(account_name, account_config)
                
                # Almacenar datos
                self.account_data[account_name] = account_data
                
                # Actualizar totales
                if account_data['status'] == 'CONNECTED':
                    total_positions += account_data['positions']
                    total_problems += account_data['problems']
                    
                    # Procesar problemas si hay
                    if account_data['problems'] > 0:
                        for pos_detail in account_data['position_details']:
                            if not pos_detail['has_sl'] or not pos_detail['has_tp']:
                                logger.warning(f"Posición #{pos_detail['ticket']} sin protección en {account_name}")
                
                # Agregar al resumen
                account_summary.append(account_data)
            
            # Mostrar resumen en consola
            self._print_summary(account_summary, total_positions, total_problems)
            
            # Enviar resumen por Telegram
            if total_problems > 0 or (datetime.now().minute % 30 == 0):  # Cada 30 minutos o si hay problemas
                await self._send_summary_notification(account_summary, total_positions, total_problems)
            
            logger.info(f"\nCiclo completado - {total_positions} posiciones totales, {total_problems} problemas detectados")
            
        except Exception as e:
            logger.error(f"Error en ciclo de monitoreo: {e}")
    
    def _print_summary(self, account_summary: List[Dict], total_positions: int, total_problems: int):
        """Imprime resumen en consola"""
        print("\n" + "="*60)
        print("📊 RESUMEN CUENTA EXNESS v3.2")
        print("="*60)
        print(f"\n📈 ESTADO GENERAL:")
        print(f"• Total posiciones: {total_positions}")
        print(f"• Problemas detectados: {total_problems}")
        print(f"• Hora: {datetime.now().strftime('%H:%M:%S')}")
        print(f"\n📋 CUENTAS:")
        
        for account in account_summary:
            status_char = {
                'CONNECTED': '✅',
                'DISCONNECTED': '❌', 
                'ERROR': '⚠️'
            }.get(account['status'], '❓')
            
            print(f"\n{status_char} {account['name'].upper()}")
            print(f"   Login configurado: {account['login']}")
            
            if account['status'] == 'CONNECTED':
                print(f"   Balance: ${account['balance']:.2f}")
                print(f"   Equity: ${account['equity']:.2f}")
                print(f"   Posiciones: {account['positions']}")
                if account['problems'] > 0:
                    print(f"   ⚠️ Sin protección: {account['problems']}")
            else:
                print(f"   Estado: {account['status']}")
        
        if total_problems > 0:
            print(f"\n⚠️ ACCIÓN REQUERIDA: {total_problems} posiciones sin SL/TP")
            print("💡 Revisa los mensajes de validación anteriores")
        
        print("="*60 + "\n")
    
    async def _send_summary_notification(self, account_summary: List[Dict], total_positions: int, total_problems: int):
        """Envía notificación de resumen por Telegram"""
        if not self.telegram_notifier:
            return
        
        try:
            message = f"""
🏦 <b>RESUMEN CUENTA EXNESS v3.2</b>

📊 <b>ESTADO GENERAL:</b>
• Total posiciones: {total_positions}
• Problemas detectados: {total_problems}
• Hora: {datetime.now().strftime('%H:%M:%S')}

📈 <b>CUENTAS:</b>
"""
            
            for account in account_summary:
                status_emoji = {
                    'CONNECTED': '🟢',
                    'DISCONNECTED': '🔴', 
                    'ERROR': '⚠️'
                }.get(account['status'], '❓')
                
                message += f"\n{status_emoji} <b>{account['name'].upper()}</b>\n"
                message += f"   Login: {account['login']}\n"
                
                if account['status'] == 'CONNECTED':
                    message += f"   Balance: ${account['balance']:.2f}\n"
                    message += f"   Equity: ${account['equity']:.2f}\n"
                    message += f"   Posiciones: {account['positions']}\n"
                    if account['problems'] > 0:
                        message += f"   ⚠️ Sin protección: {account['problems']}\n"
                else:
                    message += f"   Estado: {account['status']}\n"
            
            if total_problems > 0:
                message += f"\n⚠️ <b>ACCIÓN REQUERIDA:</b> {total_problems} posiciones sin SL/TP\n"
                message += "💡 Revisa los mensajes de validación anteriores"
            
            await self.telegram_notifier.send_message(message)
            
        except Exception as e:
            logger.error(f"Error enviando resumen: {e}")
    
    async def stop_monitoring(self):
        """Detiene el monitoreo"""
        logger.info("Deteniendo Multi Account Manager...")
        
        self.running = False
        
        if self.telegram_notifier:
            await self.telegram_notifier.send_message(
                "🛑 <b>EXNESS ACCOUNT MANAGER DETENIDO</b>\n\n"
                "<i>Monitoreo de cuenta desactivado</i>"
            )
        
        mt5.shutdown()
        logger.info("Multi Account Manager detenido")
    
    def get_status(self) -> Dict:
        """Obtiene el estado del gestor"""
        return {
            'running': self.running,
            'accounts': len(self.accounts),
            'account_data': self.account_data,
            'telegram_enabled': self.telegram_notifier is not None
        }

# Función principal
async def main():
    """Función principal del gestor multi-cuenta"""
    manager = MultiAccountManagerFixed()
    
    try:
        await manager.start_monitoring()
    except KeyboardInterrupt:
        logger.info("Deteniendo por interrupción del usuario...")
    finally:
        await manager.stop_monitoring()

if __name__ == "__main__":
    print("""
    ============================================================
    EXNESS ACCOUNT MANAGER v3.2 - Gestor de Cuenta EXNESS
    ============================================================
    
    CREDENCIALES CONFIGURADAS:
    
    EXNESS TRIAL (única cuenta activa):
    - Login: 197678662
    - Password: ********* (desde .env)
    - Servidor: Exness-MT5Trial11
    - Path: Configurado desde MT5_PATH
    
    CARACTERÍSTICAS:
    - Conexión exclusiva a EXNESS
    - Configuración desde variables de entorno
    - Prevención de múltiples instancias MT5
    - Monitoreo de cuenta EXNESS MT5
    - Validación automática con IA
    - Gestión inteligente de SL/TP
    - Notificaciones por Telegram
    
    ============================================================
    """)
    
    # Ejecutar gestor
    asyncio.run(main())
