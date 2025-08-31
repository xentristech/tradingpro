#!/usr/bin/env python
"""
🤖 ALGO TRADER - PUNTO DE ENTRADA UNIFICADO
Sistema profesional de trading algorítmico con IA
Version: 3.0.0
"""
import os
import sys
import time
import signal
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

# Configurar encoding UTF-8
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Cambiar al directorio del proyecto
PROJECT_ROOT = Path(__file__).parent
os.chdir(PROJECT_ROOT)
sys.path.insert(0, str(PROJECT_ROOT))

# Configurar logging
from utils.logger_config import setup_logging

# Estado del sistema
class SystemState(Enum):
    """Estados posibles del sistema"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    SHUTTING_DOWN = "shutting_down"

class AlgoTrader:
    """
    Clase principal del sistema de trading
    Unifica toda la funcionalidad del bot
    """
    
    def __init__(self, mode: str = "demo", config_path: str = "configs/.env", check_only: bool = False):
        """
        Inicializa el sistema de trading
        
        Args:
            mode: 'demo', 'paper', 'live'
            config_path: Ruta al archivo de configuración
        """
        self.mode = mode
        self.config_path = config_path
        self.state = SystemState.STOPPED
        self.logger = None
        self.components = {}
        self.start_time = None
        self.shutdown_requested = False
        self.check_only = check_only
        
        # Configurar signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Maneja señales del sistema para shutdown graceful"""
        self.logger.info(f"Señal {signum} recibida. Iniciando shutdown...")
        self.shutdown_requested = True
        self.shutdown()
        
    def initialize(self) -> bool:
        """
        Inicializa todos los componentes del sistema
        
        Returns:
            bool: True si la inicialización fue exitosa
        """
        try:
            self.state = SystemState.STARTING
            print("\n" + "="*70)
            print(" "*20 + "🤖 ALGO TRADER v3.0")
            print("="*70)
            
            # 1. Cargar configuración
            print("\n📁 Cargando configuración...")
            from dotenv import load_dotenv
            load_dotenv(self.config_path)
            # Advertir si existe .env en raíz y no es el seleccionado
            root_env = Path('.env')
            if root_env.exists() and str(root_env) != str(self.config_path):
                print("  ⚠️ Detectado .env en raíz del proyecto. Se usará solo:", self.config_path)
            
            # 2. Configurar logging
            log_level = os.getenv("LOG_LEVEL", "INFO")
            self.logger = setup_logging(log_level)
            self.logger.info("Sistema iniciando...")
            
            # 2.1 Cargar settings.yaml válidos
            try:
                from configs.settings_loader import load_settings
                settings = load_settings('configs/settings.yaml')
                self.components['settings'] = settings
                self.logger.info("Settings cargados y validados")
            except Exception as e:
                self.logger.warning(f"No se pudieron cargar settings.yaml: {e}")

            # 3. Validar modo de operación
            live_trading = os.getenv("LIVE_TRADING", "false").lower() == "true"
            if self.mode == "live" and not live_trading:
                self.logger.warning("⚠️ Modo LIVE solicitado pero LIVE_TRADING=false en config")
                response = input("¿Activar modo LIVE? (SI/no): ")
                if response.upper() != "SI":
                    self.logger.info("Continuando en modo DEMO")
                    self.mode = "demo"
                else:
                    os.environ["LIVE_TRADING"] = "true"
            
            # 4. Mostrar configuración
            self._print_config()
            
            # 5. Verificar dependencias antes de inicializar componentes
            if not self._check_dependencies():
                raise Exception("Faltan dependencias críticas")

            # 6. Inicializar componentes
            print("\n🔧 Inicializando componentes...")
            
            # Cargar State Manager
            from utils.state_manager import StateManager
            self.components['state_manager'] = StateManager()
            # Guardar settings en estado
            if 'settings' in self.components:
                try:
                    self.components['state_manager'].update_config(self.components['settings'].dict())
                except Exception:
                    pass
            print("  ✅ State Manager")
            
            # Cargar Rate Limiter
            from utils.rate_limiter import RateLimiter
            self.components['rate_limiter'] = RateLimiter()
            print("  ✅ Rate Limiter")
            
            # Cargar MT5 Connection Manager
            from utils.mt5_connection import MT5ConnectionManager
            self.components['mt5_manager'] = MT5ConnectionManager()
            if not self.check_only:
                if not self.components['mt5_manager'].connect():
                    raise Exception("No se pudo conectar a MT5")
                print("  ✅ MT5 Connection Manager")
            else:
                print("  ⏭️ MT5 Connection Manager (omitido por --check)")
            
            # Cargar Risk Manager
            from risk.advanced_risk import AdvancedRiskManager
            self.components['risk_manager'] = AdvancedRiskManager(
                initial_capital=float(os.getenv("INITIAL_CAPITAL", "10000")),
                max_risk_per_trade=float(os.getenv("MAX_RISK_PER_TRADE", "0.02")),
                max_portfolio_risk=float(os.getenv("MAX_PORTFOLIO_RISK", "0.06"))
            )
            print("  ✅ Risk Manager")
            
            # Cargar Signal Generator
            from signals.llm_validator import validate_signal
            self.components['signal_validator'] = validate_signal
            print("  ✅ Signal Validator")
            
            # Cargar Telegram Notifier
            if os.getenv("TELEGRAM_TOKEN"):
                from notifiers.telegram import TelegramNotifier
                self.components['notifier'] = TelegramNotifier()
                print("  ✅ Telegram Notifier")
            
            self.state = SystemState.RUNNING
            self.start_time = datetime.now()
            
            print("\n✅ Sistema inicializado correctamente")
            print(f"📊 Modo: {self.mode.upper()}")
            print(f"⏰ Hora de inicio: {self.start_time.strftime('%H:%M:%S')}")
            print("-"*70)
            
            return True
            
        except Exception as e:
            self.state = SystemState.ERROR
            print(f"\n❌ Error durante inicialización: {e}")
            if self.logger:
                self.logger.error(f"Error de inicialización: {e}", exc_info=True)
            return False
    
    def _print_config(self):
        """Muestra la configuración actual"""
        config = {
            "Modo": self.mode.upper(),
            "Live Trading": os.getenv("LIVE_TRADING", "false"),
            "Symbol": os.getenv("SYMBOL", "BTCUSD"),
            "MT5 Login": os.getenv("MT5_LOGIN", "N/A"),
            "MT5 Server": os.getenv("MT5_SERVER", "N/A"),
            "LLM Model": os.getenv("OLLAMA_MODEL", "N/A"),
            "Min Confidence": os.getenv("MIN_CONFIDENCE", "0.75"),
            "Max Risk/Trade": os.getenv("MAX_RISK_PER_TRADE", "0.02"),
        }
        
        print("\n📋 Configuración:")
        for key, value in config.items():
            # Ocultar datos sensibles
            if "login" in key.lower() and value != "N/A":
                value = value[:3] + "***"
            print(f"   {key}: {value}")
    
    def _check_dependencies(self) -> bool:
        """Verifica que todas las dependencias estén disponibles"""
        dependencies = {
            "MetaTrader5": "MetaTrader5",
            "pandas": "pandas",
            "numpy": "numpy",
            "requests": "requests",
            "openai": "openai",
            "streamlit": "streamlit"
        }
        
        missing = []
        for name, module in dependencies.items():
            try:
                __import__(module)
            except ImportError:
                missing.append(name)
        
        if missing:
            print(f"\n⚠️ Dependencias faltantes: {', '.join(missing)}")
            print("Instala con: pip install -r requirements.txt")
            return False
        
        return True
    
    def run(self):
        """
        Loop principal del sistema de trading
        """
        if self.state != SystemState.RUNNING:
            self.logger.error("Sistema no está en estado RUNNING")
            return
        
        try:
            # Importar el orchestrator principal
            from orchestrator.run import main_loop
            
            self.logger.info("Iniciando loop principal de trading...")
            
            # Notificar inicio
            if 'notifier' in self.components:
                self.components['notifier'].send_startup_message(self.mode)
            
            # Variables de control
            cycle = 0
            last_health_check = time.time()
            
            while not self.shutdown_requested:
                try:
                    cycle += 1
                    
                    # Health check cada 60 segundos
                    if time.time() - last_health_check > 60:
                        self._perform_health_check()
                        last_health_check = time.time()
                    
                    # Actualizar estado
                    self.components['state_manager'].update_cycle(cycle)
                    
                    # Ejecutar ciclo de trading
                    main_loop(
                        components=self.components,
                        state_manager=self.components['state_manager'],
                        rate_limiter=self.components['rate_limiter']
                    )
                    
                    # Esperar antes del próximo ciclo
                    poll_seconds = int(os.getenv("POLL_SECONDS", "20"))
                    time.sleep(poll_seconds)
                    
                except KeyboardInterrupt:
                    self.logger.info("Interrupción de teclado detectada")
                    break
                    
                except Exception as e:
                    self.logger.error(f"Error en ciclo {cycle}: {e}", exc_info=True)
                    
                    # Notificar error crítico
                    if 'notifier' in self.components:
                        self.components['notifier'].send_error_message(str(e))
                    
                    # Esperar antes de reintentar
                    time.sleep(30)
                    
        except Exception as e:
            self.state = SystemState.ERROR
            self.logger.critical(f"Error crítico en run(): {e}", exc_info=True)
        finally:
            self.shutdown()
    
    def _perform_health_check(self):
        """Realiza verificación de salud del sistema"""
        try:
            # Verificar conexión MT5
            if 'mt5_manager' in self.components:
                if not self.components['mt5_manager'].is_connected():
                    self.logger.warning("MT5 desconectado, intentando reconectar...")
                    self.components['mt5_manager'].reconnect()
            
            # Verificar memoria
            import psutil
            memory_percent = psutil.virtual_memory().percent
            if memory_percent > 90:
                self.logger.warning(f"Uso de memoria alto: {memory_percent}%")
            
            # Verificar estado
            state = self.components['state_manager'].get_health_status()
            if state['errors'] > 10:
                self.logger.warning(f"Muchos errores detectados: {state['errors']}")
                
        except Exception as e:
            self.logger.error(f"Error en health check: {e}")
    
    def pause(self):
        """Pausa el sistema de trading"""
        if self.state == SystemState.RUNNING:
            self.state = SystemState.PAUSED
            self.logger.info("Sistema pausado")
    
    def resume(self):
        """Resume el sistema de trading"""
        if self.state == SystemState.PAUSED:
            self.state = SystemState.RUNNING
            self.logger.info("Sistema resumido")
    
    def shutdown(self):
        """
        Apaga el sistema de forma segura
        """
        if self.state == SystemState.SHUTTING_DOWN:
            return
            
        self.state = SystemState.SHUTTING_DOWN
        print("\n" + "="*70)
        print("🛑 Iniciando shutdown del sistema...")
        
        try:
            # Guardar estado
            if 'state_manager' in self.components:
                self.components['state_manager'].save_state()
                print("  ✅ Estado guardado")
            
            # Cerrar posiciones si está en modo paper/live
            if self.mode in ["paper", "live"] and 'mt5_manager' in self.components:
                positions = self.components['mt5_manager'].get_open_positions()
                if positions:
                    print(f"  ⚠️ Cerrando {len(positions)} posiciones abiertas...")
                    # Aquí iría la lógica para cerrar posiciones
            
            # Desconectar MT5
            if 'mt5_manager' in self.components:
                self.components['mt5_manager'].disconnect()
                print("  ✅ MT5 desconectado")
            
            # Notificar shutdown
            if 'notifier' in self.components:
                self.components['notifier'].send_shutdown_message()
                print("  ✅ Notificación enviada")
            
            # Calcular estadísticas de sesión
            if self.start_time:
                duration = datetime.now() - self.start_time
                print(f"\n📊 Estadísticas de sesión:")
                print(f"   Duración: {duration}")
                if 'state_manager' in self.components:
                    stats = self.components['state_manager'].get_session_stats()
                    print(f"   Ciclos: {stats.get('cycles', 0)}")
                    print(f"   Trades: {stats.get('trades', 0)}")
                    print(f"   Errores: {stats.get('errors', 0)}")
            
        except Exception as e:
            print(f"❌ Error durante shutdown: {e}")
        finally:
            self.state = SystemState.STOPPED
            print("\n✅ Sistema detenido correctamente")
            print("="*70)


def main():
    """Función principal con argumentos CLI"""
    parser = argparse.ArgumentParser(
        description="🤖 Algo Trader - Sistema de Trading Algorítmico con IA",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python main_trader.py --mode demo           # Modo demo (por defecto)
  python main_trader.py --mode paper          # Paper trading
  python main_trader.py --mode live           # Trading real (¡CUIDADO!)
  python main_trader.py --config custom.env   # Usar config personalizada
  python main_trader.py --check               # Solo verificar sistema
        """
    )
    
    parser.add_argument(
        "--mode",
        choices=["demo", "paper", "live"],
        default="demo",
        help="Modo de operación del bot"
    )
    
    parser.add_argument(
        "--config",
        default="configs/.env",
        help="Ruta al archivo de configuración"
    )
    
    parser.add_argument(
        "--check",
        action="store_true",
        help="Solo verificar el sistema sin ejecutar"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 3.0.0"
    )
    
    args = parser.parse_args()
    
    # Crear instancia del trader
    trader = AlgoTrader(mode=args.mode, config_path=args.config, check_only=args.check)
    
    # Inicializar sistema
    if not trader.initialize():
        print("\n❌ Fallo en la inicialización del sistema")
        sys.exit(1)
    
    # Si es solo verificación, salir
    if args.check:
        print("\n✅ Verificación completada exitosamente")
        return
        trader.shutdown()
        sys.exit(0)
    
    # Ejecutar el sistema
    try:
        trader.run()
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        trader.shutdown()
        sys.exit(1)


if __name__ == "__main__":
    main()
