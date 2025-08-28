"""
Exness Automated Trader - Trading automatizado para cuenta Exness
Ejecuta estrategias de trading en la cuenta 197678662
"""
import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import MetaTrader5 as mt5

# Configurar path del proyecto
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from core.bot_manager import BotManager
from signals.signal_generator import SignalGenerator
from risk.risk_manager import RiskManager
from notifiers.telegram_notifier import TelegramNotifier

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class ExnessAutomatedTrader:
    """Trading automatizado para cuenta Exness"""
    
    def __init__(self):
        """Inicializa el trader automatizado"""
        logger.info("="*60)
        logger.info("EXNESS AUTOMATED TRADER v1.0")
        logger.info("Cuenta: 197678662 - Exness-MT5Trial11")
        logger.info("="*60)
        
        # Cargar configuración
        load_dotenv('configs/.env')
        
        # Configuración específica de Exness
        self.account_login = 197678662
        self.account_server = 'Exness-MT5Trial11'
        self.account_password = os.getenv('MT5_PASSWORD_EXNESS', '')
        self.mt5_path = os.getenv('MT5_PATH_EXNESS', 'C:\\Program Files\\MetaTrader 5 Exness\\terminal64.exe')
        
        # Símbolos a operar
        self.symbols = ['EURUSD', 'GBPUSD', 'USDJPY']
        self.active_symbol = 'EURUSD'
        
        # Componentes del sistema
        self.signal_generator = None
        self.risk_manager = None
        self.telegram = None
        self.bot_manager = None
        
        # Estado
        self.running = False
        self.trades_today = 0
        self.max_trades_per_day = 5
        
    def initialize(self):
        """Inicializa conexión y componentes"""
        try:
            # Conectar a MT5 con cuenta Exness
            logger.info("Conectando a MT5 Exness...")
            
            # Intentar con path específico primero
            if self.mt5_path and os.path.exists(self.mt5_path):
                if not mt5.initialize(path=self.mt5_path):
                    logger.warning("No se pudo inicializar con path específico, intentando default")
                    if not mt5.initialize():
                        logger.error("Error inicializando MT5")
                        return False
            else:
                if not mt5.initialize():
                    logger.error("Error inicializando MT5")
                    return False
            
            # Login a cuenta Exness
            if self.account_password and self.account_server:
                if not mt5.login(self.account_login, self.account_password, self.account_server):
                    logger.warning(f"No se pudo hacer login directo, verificando cuenta actual")
            
            # Verificar cuenta conectada
            account_info = mt5.account_info()
            if not account_info:
                logger.error("No se pudo obtener información de cuenta")
                return False
            
            if account_info.login != self.account_login:
                logger.warning(f"Cuenta incorrecta: {account_info.login}, esperaba {self.account_login}")
                logger.info("Por favor cambie manualmente a la cuenta Exness en MT5")
                return False
            
            logger.info(f"Conectado exitosamente a Exness")
            logger.info(f"Cuenta: {account_info.login}")
            logger.info(f"Balance: ${account_info.balance:.2f}")
            logger.info(f"Equity: ${account_info.equity:.2f}")
            logger.info(f"Leverage: 1:{account_info.leverage}")
            
            # Inicializar componentes
            self._initialize_components()
            
            return True
            
        except Exception as e:
            logger.error(f"Error en inicialización: {e}")
            return False
    
    def _initialize_components(self):
        """Inicializa componentes del sistema"""
        try:
            # Telegram
            if os.getenv('TELEGRAM_TOKEN') and os.getenv('TELEGRAM_CHAT_ID'):
                self.telegram = TelegramNotifier()
                logger.info("Telegram notifier activado")
            
            # Signal Generator
            self.signal_generator = SignalGenerator(
                symbol=self.active_symbol,
                timeframes=['M5', 'M15', 'H1']
            )
            logger.info("Signal Generator inicializado")
            
            # Risk Manager
            self.risk_manager = RiskManager(
                max_risk_per_trade=0.02,  # 2% por operación
                max_daily_loss=0.05,       # 5% pérdida diaria máxima
                max_positions=3
            )
            logger.info("Risk Manager configurado")
            
            # Bot Manager
            self.bot_manager = BotManager(
                mode='LIVE',
                signal_generator=self.signal_generator,
                risk_manager=self.risk_manager,
                telegram_notifier=self.telegram
            )
            logger.info("Bot Manager listo")
            
        except Exception as e:
            logger.error(f"Error inicializando componentes: {e}")
            raise
    
    def run(self):
        """Ejecuta el loop principal de trading"""
        if not self.initialize():
            logger.error("No se pudo inicializar el sistema")
            return
        
        self.running = True
        logger.info("Sistema de trading automatizado iniciado")
        
        # Notificar inicio
        if self.telegram:
            self.telegram.send_sync(
                "EXNESS TRADER INICIADO\\n\\n"
                f"Cuenta: {self.account_login}\\n"
                f"Símbolos: {', '.join(self.symbols)}\\n"
                f"Max trades/día: {self.max_trades_per_day}\\n"
                "\\nSistema automatizado activo"
            )
        
        iteration = 0
        last_analysis_minute = -1
        
        try:
            while self.running:
                iteration += 1
                current_time = datetime.now()
                current_minute = current_time.minute
                
                # Análisis cada minuto nuevo
                if current_minute != last_analysis_minute:
                    last_analysis_minute = current_minute
                    
                    # Verificar límites
                    if self.trades_today >= self.max_trades_per_day:
                        if iteration % 60 == 0:  # Log cada hora
                            logger.info(f"Límite diario alcanzado ({self.trades_today}/{self.max_trades_per_day})")
                    else:
                        # Analizar cada símbolo
                        for symbol in self.symbols:
                            self._analyze_symbol(symbol, iteration)
                    
                    # Estado del sistema cada 5 minutos
                    if current_minute % 5 == 0:
                        self._log_system_status()
                    
                    # Reset contador diario a medianoche
                    if current_time.hour == 0 and current_time.minute == 0:
                        self.trades_today = 0
                        logger.info("Contador de trades diario reseteado")
                
                time.sleep(5)  # Check cada 5 segundos
                
        except KeyboardInterrupt:
            logger.info("Deteniendo por interrupción del usuario...")
        except Exception as e:
            logger.error(f"Error en loop principal: {e}")
        finally:
            self.cleanup()
    
    def _analyze_symbol(self, symbol: str, iteration: int):
        """Analiza un símbolo específico"""
        try:
            # Cambiar símbolo activo
            self.signal_generator.symbol = symbol
            
            # Generar señales
            signals = self.signal_generator.generate_signals()
            
            if signals and signals.get('action') in ['BUY', 'SELL']:
                confidence = signals.get('confidence', 0)
                
                if confidence > 0.7:  # Solo operar con alta confianza
                    logger.info(f"[{iteration:04d}] {symbol} - Señal detectada:")
                    logger.info(f"  Acción: {signals['action']}")
                    logger.info(f"  Confianza: {confidence:.1%}")
                    logger.info(f"  Estrategias: {', '.join(signals.get('strategies', []))}")
                    
                    # Ejecutar trade si pasa validación de riesgo
                    if self._execute_trade(symbol, signals):
                        self.trades_today += 1
                        logger.info(f"Trade ejecutado - Total hoy: {self.trades_today}")
                    
        except Exception as e:
            logger.error(f"Error analizando {symbol}: {e}")
    
    def _execute_trade(self, symbol: str, signals: dict) -> bool:
        """Ejecuta una operación"""
        try:
            account_info = mt5.account_info()
            if not account_info:
                return False
            
            # Validar riesgo
            position_size = self.risk_manager.calculate_position_size(
                account_balance=account_info.balance,
                stop_loss_pips=30  # SL fijo de 30 pips
            )
            
            if position_size <= 0:
                logger.warning("Tamaño de posición inválido")
                return False
            
            # Preparar orden
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info or not symbol_info.visible:
                mt5.symbol_select(symbol, True)
                symbol_info = mt5.symbol_info(symbol)
            
            if not symbol_info:
                logger.error(f"No se pudo obtener info de {symbol}")
                return False
            
            # Precio actual
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return False
            
            # Configurar orden
            action = signals['action']
            if action == 'BUY':
                order_type = mt5.ORDER_TYPE_BUY
                price = tick.ask
                sl = price - (30 * symbol_info.point)
                tp = price + (60 * symbol_info.point)
            else:  # SELL
                order_type = mt5.ORDER_TYPE_SELL
                price = tick.bid
                sl = price + (30 * symbol_info.point)
                tp = price - (60 * symbol_info.point)
            
            # Ajustar volumen
            volume = max(symbol_info.volume_min, min(position_size, symbol_info.volume_max))
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": order_type,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": 20,
                "magic": 234000,
                "comment": f"ExnessAuto_{signals.get('strategies', ['NA'])[0][:10]}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            # Enviar orden
            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(f"Trade ejecutado exitosamente:")
                logger.info(f"  Ticket: {result.order}")
                logger.info(f"  Volumen: {volume}")
                logger.info(f"  Precio: {price}")
                logger.info(f"  SL: {sl:.5f} | TP: {tp:.5f}")
                
                # Notificar
                if self.telegram:
                    self.telegram.send_sync(
                        f"TRADE EJECUTADO - EXNESS\\n\\n"
                        f"Símbolo: {symbol}\\n"
                        f"Acción: {action}\\n"
                        f"Volumen: {volume}\\n"
                        f"Precio: {price:.5f}\\n"
                        f"SL: {sl:.5f}\\n"
                        f"TP: {tp:.5f}\\n"
                        f"Confianza: {signals.get('confidence', 0):.1%}"
                    )
                
                return True
            else:
                logger.warning(f"Trade rechazado: {result.comment if result else 'Unknown error'}")
                return False
                
        except Exception as e:
            logger.error(f"Error ejecutando trade: {e}")
            return False
    
    def _log_system_status(self):
        """Registra el estado del sistema"""
        try:
            account_info = mt5.account_info()
            positions = mt5.positions_get()
            
            if account_info:
                logger.info("-" * 40)
                logger.info("ESTADO DEL SISTEMA")
                logger.info(f"Hora: {datetime.now().strftime('%H:%M:%S')}")
                logger.info(f"Balance: ${account_info.balance:.2f}")
                logger.info(f"Equity: ${account_info.equity:.2f}")
                logger.info(f"Posiciones abiertas: {len(positions) if positions else 0}")
                logger.info(f"Trades hoy: {self.trades_today}/{self.max_trades_per_day}")
                
                if positions:
                    total_profit = sum(p.profit for p in positions)
                    logger.info(f"P&L abierto: ${total_profit:.2f}")
                
                logger.info("-" * 40)
                
        except Exception as e:
            logger.error(f"Error en log de estado: {e}")
    
    def cleanup(self):
        """Limpia recursos y cierra conexiones"""
        logger.info("Limpiando recursos...")
        
        self.running = False
        
        # Cerrar posiciones si es necesario
        positions = mt5.positions_get()
        if positions and len(positions) > 0:
            logger.warning(f"Hay {len(positions)} posiciones abiertas")
        
        # Notificar cierre
        if self.telegram:
            self.telegram.send_sync(
                "EXNESS TRADER DETENIDO\\n\\n"
                f"Trades ejecutados hoy: {self.trades_today}"
            )
        
        # Cerrar MT5
        mt5.shutdown()
        logger.info("Sistema detenido correctamente")

def main():
    """Función principal"""
    trader = ExnessAutomatedTrader()
    trader.run()

if __name__ == "__main__":
    main()