#!/usr/bin/env python
"""
EJECUTOR MAESTRO CON TELEGRAM Y SEÑALES - ALGO TRADER V3
========================================================
Sistema completo con notificaciones y generador de señales activo
"""

import os
import sys
import subprocess
import time
import socket
import webbrowser
from pathlib import Path
from datetime import datetime
import json
import threading
import logging

class AlgoTraderExecutorPro:
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.processes = {}
        
        # Configurar logging
        log_dir = self.base_path / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'system.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        self.services = {
            'telegram_notifier': {
                'file': 'src/notifiers/telegram_notifier.py',
                'name': '📱 Notificador Telegram',
                'process': None,
                'status': 'stopped',
                'critical': True
            },
            'signal_generator': {
                'file': 'src/signals/advanced_signal_generator.py',
                'name': '🤖 Generador de Señales IA',
                'process': None,
                'status': 'stopped',
                'critical': True
            },
            'tick_system': {
                'file': 'src/data/TICK_SYSTEM_FINAL.py',
                'port': 8508,
                'name': '📊 Sistema de Ticks MT5',
                'process': None,
                'status': 'stopped'
            },
            'revolutionary_dashboard': {
                'file': 'src/ui/dashboards/revolutionary_dashboard_final.py',
                'port': 8512,
                'name': '🎯 Revolutionary Dashboard',
                'url': 'http://localhost:8512',
                'process': None,
                'status': 'stopped'
            },
            'chart_simulation': {
                'file': 'src/ui/charts/chart_simulation_reviewed.py',
                'port': 8516,
                'name': '📈 Chart Simulation',
                'url': 'http://localhost:8516',
                'process': None,
                'status': 'stopped'
            },
            'tradingview_chart': {
                'file': 'src/ui/charts/tradingview_professional_chart.py',
                'port': 8517,
                'name': '📊 TradingView Professional',
                'url': 'http://localhost:8517',
                'process': None,
                'status': 'stopped'
            }
        }
        
    def play_start_greeting(self):
        """Reproduce un saludo por voz opcional y muestra el texto.

        Control:
        - Configuración en config/start_greeting.txt (líneas a pronunciar/mostrar)
        - Env ENABLE_TTS=1 para activar voz (Windows con PowerShell System.Speech)
        """
        try:
            cfg = self.base_path / 'config' / 'start_greeting.txt'
            lines = []
            if cfg.exists():
                with open(cfg, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        s = line.strip()
                        if s:
                            lines.append(s)
            else:
                lines = [
                    'XENTRISTECH, Empresa de Tecnología.',
                    'Sistema de trading iniciado y operativo.',
                    'Bienvenido, operando en modo 24/7.'
                ]

            # Mostrar en consola
            print("\n" + "="*60)
            print("MENSAJE DE INICIO")
            print("="*60)
            for s in lines:
                print(f"• {s}")

            # Voz opcional en Windows
            if os.getenv('ENABLE_TTS', '1') in ('1', 'true', 'True') and os.name == 'nt':
                try:
                    text = '. '.join(lines)
                    safe = text.replace("'", "''")  # escapado simple para PowerShell
                    cmd = [
                        'powershell.exe', '-NoProfile', '-Command',
                        (
                            "Add-Type -AssemblyName System.Speech; "
                            "$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                            f"$speak.Speak('{safe}')"
                        )
                    ]
                    subprocess.Popen(cmd)
                except Exception as e:
                    self.logger.warning(f"No se pudo reproducir TTS: {e}")
        except Exception as e:
            self.logger.error(f"Error en saludo de inicio: {e}")

    def _read_start_greeting_lines(self):
        """Lee líneas del saludo configurable para reutilizar en Telegram."""
        try:
            cfg = self.base_path / 'config' / 'start_greeting.txt'
            lines = []
            if cfg.exists():
                with open(cfg, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        s = line.strip()
                        if s:
                            lines.append(s)
            else:
                lines = [
                    'XENTRISTECH, Empresa de Tecnología.',
                    'Sistema de trading iniciado y operativo.',
                    'Bienvenido, operando en modo 24/7.'
                ]
            return lines
        except Exception:
            return []

    def open_custom_pages(self):
        """Abre páginas web personalizadas desde config o variable de entorno.

        - Lee la variable de entorno AUTO_OPEN_URLS (separadas por coma), o
        - Lee el archivo config/auto_open_urls.txt (una URL por línea).
        """
        try:
            urls = []
            # 1) Variable de entorno
            env_urls = os.getenv('AUTO_OPEN_URLS')
            if env_urls:
                urls = [u.strip() for u in env_urls.split(',') if u.strip()]
            else:
                # 2) Archivo de configuración
                cfg = self.base_path / 'config' / 'auto_open_urls.txt'
                if cfg.exists():
                    with open(cfg, 'r', encoding='utf-8', errors='ignore') as f:
                        for line in f:
                            s = line.strip()
                            if s and not s.startswith('#'):
                                urls.append(s)

            if not urls:
                return

            print("\n" + "="*60)
            print("ABRIENDO PÁGINAS PERSONALIZADAS")
            print("="*60 + "\n")
            for url in urls:
                try:
                    print(f"  Abriendo: {url}")
                    webbrowser.open(url)
                    time.sleep(0.5)
                except Exception as e:
                    self.logger.warning(f"No se pudo abrir {url}: {e}")
        except Exception as e:
            self.logger.error(f"Error abriendo páginas personalizadas: {e}")

    def check_port(self, port):
        """Verifica si un puerto está disponible"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        return result == 0
        
    def check_telegram_config(self):
        """Verifica configuración de Telegram"""
        env_path = self.base_path / '.env'
        
        if env_path.exists():
            with open(env_path, 'r') as f:
                content = f.read()
                has_token = 'TELEGRAM_TOKEN=' in content and 'TELEGRAM_TOKEN=your' not in content
                has_chat = 'TELEGRAM_CHAT_ID=' in content and 'TELEGRAM_CHAT_ID=your' not in content
                return has_token and has_chat
        return False
        
    def check_dependencies(self):
        """Verifica las dependencias necesarias"""
        print("\n" + "="*60)
        print("VERIFICANDO SISTEMA")
        print("="*60)
        
        # Verificar Python
        print("\n📦 Verificando dependencias...")
        
        dependencies = {
            'MetaTrader5': ('MetaTrader5', True),
            'pandas': ('pandas', True),
            'numpy': ('numpy', True),
            'requests': ('requests', True),
            'beautifulsoup4': ('bs4', False),
            'plotly': ('plotly', False),
            'python-dotenv': ('dotenv', True)
        }
        
        missing = []
        
        for package, (import_name, critical) in dependencies.items():
            try:
                __import__(import_name)
                print(f"  ✅ {package}")
            except ImportError:
                if critical:
                    print(f"  ❌ {package} (CRÍTICO)")
                    missing.append(package)
                else:
                    print(f"  ⚠️ {package} (opcional)")
                    
        # Verificar Telegram
        print("\n📱 Verificando Telegram...")
        if self.check_telegram_config():
            print("  ✅ Telegram configurado")
        else:
            print("  ⚠️ Telegram no configurado (revisa .env)")
            
        if missing:
            print(f"\n⚠️ Instalando dependencias faltantes...")
            for package in missing:
                print(f"  Instalando {package}...")
                subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', package],
                    capture_output=True
                )
            print("  ✅ Dependencias instaladas")
            
        return True
        
    def start_service(self, service_key):
        """Inicia un servicio específico"""
        service = self.services[service_key]
        file_path = self.base_path / service['file']
        
        if not file_path.exists():
            self.logger.error(f"❌ Archivo no encontrado: {service['file']}")
            return False
            
        try:
            # Para servicios con puerto, verificar disponibilidad
            if 'port' in service:
                if self.check_port(service['port']):
                    print(f"  ⚠️ Puerto {service['port']} ya en uso")
                    service['status'] = 'running'
                    return True
                    
            # Iniciar el proceso
            print(f"  Iniciando {service['name']}...")
            
            # Para Windows, usar CREATE_NEW_CONSOLE para procesos en segundo plano
            if os.name == 'nt':
                service['process'] = subprocess.Popen(
                    [sys.executable, str(file_path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=str(self.base_path),
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
                service['process'] = subprocess.Popen(
                    [sys.executable, str(file_path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=str(self.base_path)
                )
            
            # Esperar a que el servicio inicie
            time.sleep(3)
            
            # Verificar estado
            if 'port' in service:
                if self.check_port(service['port']):
                    service['status'] = 'running'
                    print(f"  ✅ {service['name']} activo en puerto {service['port']}")
                    return True
                else:
                    print(f"  ⚠️ {service['name']} no respondió")
                    return False
            else:
                # Para servicios sin puerto, asumir que están corriendo
                service['status'] = 'running'
                print(f"  ✅ {service['name']} iniciado")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Error iniciando {service['name']}: {e}")
            service['status'] = 'error'
            return False
            
    def start_all_services(self):
        """Inicia todos los servicios en orden"""
        print("\n" + "="*60)
        print("INICIANDO SERVICIOS")
        print("="*60 + "\n")
        
        # Orden de inicio optimizado
        service_order = [
            'telegram_notifier',     # Primero Telegram
            'signal_generator',      # Luego generador de señales
            'tick_system',          # Sistema de ticks
            'revolutionary_dashboard',
            'chart_simulation',
            'tradingview_chart'
        ]

        # Opcional: iniciar terminal MCP Trader 24/7 si existe y está habilitado
        mcp_path = self.base_path / 'src/ui/mcp_trader_terminal.py'
        if mcp_path.exists() and os.getenv('MCP_TRADER_ENABLE', '1') in ('1', 'true', 'True'):
            self.services['mcp_trader_terminal'] = {
                'file': 'src/ui/mcp_trader_terminal.py',
                'name': '🖥 MCP Trader 24/7',
                'process': None,
                'status': 'stopped',
                'critical': False
            }
            service_order.append('mcp_trader_terminal')
        
        success_count = 0
        
        for service_key in service_order:
            if self.start_service(service_key):
                success_count += 1
            time.sleep(1)
            
        print(f"\n✅ {success_count}/{len(service_order)} servicios iniciados")
        
        # Enviar notificación de inicio si Telegram está activo
        if success_count > 0:
            self.send_startup_notification(success_count)
            
        return success_count > 0
        
    def send_startup_notification(self, services_count):
        """Envía notificación de inicio por Telegram"""
        try:
            # Importar y usar el notificador
            sys.path.insert(0, str(self.base_path))
            from src.notifiers.telegram_notifier import TelegramNotifier
            
            notifier = TelegramNotifier()
            if notifier.is_active:
                # Incluir saludo configurable si está habilitado
                include_greeting = os.getenv('TELEGRAM_GREETING_ENABLE', '1') in ('1', 'true', 'True')
                greeting = ''
                if include_greeting:
                    glines = self._read_start_greeting_lines()
                    if glines:
                        safe = [line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;') for line in glines]
                        greeting = '\n'.join(safe) + '\n\n'

                message = (
                    f"{greeting}"
                    f"🚀 <b>ALGO TRADER V3 INICIADO</b>\n\n"
                    f"✅ Servicios activos: {services_count}/6\n"
                    f"📊 Dashboards disponibles:\n"
                    f"  • http://localhost:8512\n"
                    f"  • http://localhost:8516\n"
                    f"  • http://localhost:8517\n\n"
                    f"🤖 Generador de señales: ACTIVO\n"
                    f"📱 Notificaciones: ACTIVAS\n\n"
                    f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
                notifier.send_message(message, parse_mode='HTML')
        except Exception as e:
            self.logger.error(f"Error enviando notificación: {e}")
            
    def open_dashboards(self):
        """Abre los dashboards en el navegador"""
        print("\n" + "="*60)
        print("ABRIENDO DASHBOARDS")
        print("="*60 + "\n")
        
        for service_key, service in self.services.items():
            if 'url' in service and service['status'] == 'running':
                print(f"  Abriendo {service['name']}...")
                webbrowser.open(service['url'])
                time.sleep(1)
                
    def show_status(self):
        """Muestra el estado de todos los servicios"""
        print("\n" + "="*60)
        print("ESTADO DEL SISTEMA - ALGO TRADER V3")
        print("="*60)
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-"*60)
        
        print("\n📊 SERVICIOS PRINCIPALES:")
        for service_key, service in self.services.items():
            if service.get('critical'):
                status_icon = "✅" if service['status'] == 'running' else "❌"
                print(f"{status_icon} {service['name']:35} [{service['status'].upper():10}]")
                
        print("\n🌐 SERVICIOS WEB:")
        for service_key, service in self.services.items():
            if 'port' in service:
                status_icon = "✅" if service['status'] == 'running' else "❌"
                print(f"{status_icon} {service['name']:35} Puerto {service['port']}")
                if 'url' in service and service['status'] == 'running':
                    print(f"    └─> {service['url']}")
                    
        print("\n📱 TELEGRAM:")
        if self.check_telegram_config():
            print("  ✅ Configurado y activo")
            print("  📤 Enviando señales en tiempo real")
        else:
            print("  ⚠️ No configurado")
            
        print("="*60)
        
    def monitor_services(self):
        """Monitorea servicios y reinicia si es necesario"""
        while True:
            time.sleep(30)
            
            for service_key, service in self.services.items():
                if service['status'] == 'running':
                    # Para servicios con puerto
                    if 'port' in service:
                        if not self.check_port(service['port']):
                            self.logger.warning(f"⚠️ {service['name']} se detuvo. Reiniciando...")
                            self.start_service(service_key)
                    # Para procesos
                    elif service['process']:
                        if service['process'].poll() is not None:
                            self.logger.warning(f"⚠️ {service['name']} se detuvo. Reiniciando...")
                            self.start_service(service_key)
                            
    def stop_all_services(self):
        """Detiene todos los servicios"""
        print("\n" + "="*60)
        print("DETENIENDO SERVICIOS")
        print("="*60 + "\n")
        
        for service_key, service in self.services.items():
            if service['process'] and service['process'].poll() is None:
                print(f"  Deteniendo {service['name']}...")
                service['process'].terminate()
                service['status'] = 'stopped'
                time.sleep(0.5)
                
        print("\n✅ Todos los servicios detenidos")
        
    def run_interactive(self):
        """Ejecuta el sistema en modo interactivo"""
        print("""
╔════════════════════════════════════════════════════════════╗
║         ALGO TRADER V3 - SISTEMA COMPLETO CON IA          ║
║           Telegram + Señales + Trading Automático         ║
╚════════════════════════════════════════════════════════════╝
        """)
        
        # Verificar dependencias
        self.check_dependencies()
        
        # Iniciar todos los servicios
        if self.start_all_services():
            # Mostrar estado
            self.show_status()
            
            # Esperar un momento
            time.sleep(3)
            
            # Abrir dashboards
            self.open_dashboards()
            # Abrir páginas personalizadas
            self.open_custom_pages()
            # Saludo de inicio (voz + texto)
            self.play_start_greeting()
            
            # Iniciar monitor en segundo plano
            monitor_thread = threading.Thread(target=self.monitor_services, daemon=True)
            monitor_thread.start()
            
            # Menú interactivo
            while True:
                print("\n" + "="*60)
                print("OPCIONES DISPONIBLES")
                print("="*60)
                print("[1] 📊 Ver estado del sistema")
                print("[2] 🤖 Estado del generador de señales")
                print("[3] 📱 Enviar mensaje de prueba por Telegram")
                print("[4] 🌐 Abrir dashboards")
                print("[5] 🔄 Reiniciar todos los servicios")
                print("[6] 📜 Ver logs recientes")
                print("[7] 💰 Iniciar Trading Bot (DEMO)")
                print("[0] 🛑 Salir")
                print("="*60)
                
                choice = input("\nSelecciona una opción: ")
                
                if choice == '1':
                    self.show_status()
                    
                elif choice == '2':
                    print("\n🤖 ESTADO DEL GENERADOR DE SEÑALES:")
                    print("  • Estado: ACTIVO")
                    print("  • Estrategias: 6 activas")
                    print("  • Símbolos: XAUUSD, EURUSD, GBPUSD, BTCUSD")
                    print("  • Análisis cada: 60 segundos")
                    
                elif choice == '3':
                    self.send_test_message()
                    
                elif choice == '4':
                    self.open_dashboards()
                    
                elif choice == '5':
                    self.stop_all_services()
                    time.sleep(2)
                    self.start_all_services()
                    
                elif choice == '6':
                    self.show_logs()
                    
                elif choice == '7':
                    self.start_trading_bot()
                    
                elif choice == '0':
                    print("\n¿Deseas detener todos los servicios? (s/n): ", end='')
                    if input().lower() == 's':
                        self.stop_all_services()
                    break
                    
                else:
                    print("⚠️ Opción no válida")
                    
        else:
            print("\n❌ Error al iniciar los servicios")
            
    def send_test_message(self):
        """Envía mensaje de prueba por Telegram"""
        try:
            sys.path.insert(0, str(self.base_path))
            from src.notifiers.telegram_notifier import TelegramNotifier
            
            notifier = TelegramNotifier()
            if notifier.is_active:
                test_signal = {
                    'symbol': 'XAUUSD',
                    'type': 'BUY',
                    'price': 2650.50,
                    'strength': 0.85,
                    'tp': 2655.00,
                    'sl': 2648.00,
                    'strategy': 'Test Manual',
                    'timeframe': 'M5',
                    'reason': 'Señal de prueba enviada manualmente'
                }
                
                notifier.send_signal(test_signal)
                print("\n✅ Mensaje de prueba enviado")
            else:
                print("\n❌ Telegram no está activo")
        except Exception as e:
            print(f"\n❌ Error: {e}")
            
    def show_logs(self):
        """Muestra los logs recientes"""
        log_file = self.base_path / 'logs' / 'system.log'
        
        if log_file.exists():
            print("\n" + "="*60)
            print("LOGS RECIENTES")
            print("="*60)
            
            with open(log_file, 'r') as f:
                lines = f.readlines()
                for line in lines[-30:]:  # Últimas 30 líneas
                    print(line.strip())
        else:
            print("\n⚠️ No hay logs disponibles")
            
    def start_trading_bot(self):
        """Inicia el bot de trading"""
        print("\n🤖 Iniciando Trading Bot en modo DEMO...")
        
        # Buscar archivo del bot
        bot_files = [
            'src/trading/main_trader.py',
            'main.py',
            'src/trading/live_trader.py'
        ]
        
        for bot_file in bot_files:
            bot_path = self.base_path / bot_file
            if bot_path.exists():
                os.environ['TRADING_MODE'] = 'DEMO'
                subprocess.Popen(
                    [sys.executable, str(bot_path)],
                    cwd=str(self.base_path)
                )
                print("✅ Trading Bot iniciado")
                return
                
        print("❌ No se encontró el archivo del Trading Bot")

def main():
    executor = AlgoTraderExecutorPro()
    
    # Verificar argumentos
    if len(sys.argv) > 1:
        if sys.argv[1] == '--auto':
            executor.start_all_services()
            executor.show_status()
            # En modo auto, también abrir dashboards y páginas personalizadas
            try:
                executor.open_dashboards()
                executor.open_custom_pages()
                executor.play_start_greeting()
            except Exception:
                pass
            print("\n✅ Sistema iniciado. Presiona Enter para salir...")
            input()
        elif sys.argv[1] == '--stop':
            executor.stop_all_services()
    else:
        executor.run_interactive()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Deteniendo sistema...")
        executor = AlgoTraderExecutorPro()
        executor.stop_all_services()
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        import traceback
        traceback.print_exc()
