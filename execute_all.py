#!/usr/bin/env python
"""
EJECUTOR MAESTRO DE ALGO TRADER V3
===================================
Sistema completo de inicio con verificación y monitoreo
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

class AlgoTraderExecutor:
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.processes = {}
        self.services = {
            'tick_system': {
                'file': 'src/data/TICK_SYSTEM_FINAL.py',
                'port': 8508,
                'name': 'Sistema de Ticks MT5',
                'process': None,
                'status': 'stopped'
            },
            'revolutionary_dashboard': {
                'file': 'src/ui/dashboards/revolutionary_dashboard_final.py',
                'port': 8512,
                'name': 'Revolutionary Dashboard',
                'url': 'http://localhost:8512',
                'process': None,
                'status': 'stopped'
            },
            'chart_simulation': {
                'file': 'src/ui/charts/chart_simulation_reviewed.py',
                'port': 8516,
                'name': 'Chart Simulation',
                'url': 'http://localhost:8516',
                'process': None,
                'status': 'stopped'
            },
            'tradingview_chart': {
                'file': 'src/ui/charts/tradingview_professional_chart.py',
                'port': 8517,
                'name': 'TradingView Professional',
                'url': 'http://localhost:8517',
                'process': None,
                'status': 'stopped'
            }
        }
        
    def check_port(self, port):
        """Verifica si un puerto está disponible"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', port))
        sock.close()
        return result == 0
        
    def check_dependencies(self):
        """Verifica las dependencias necesarias"""
        print("\n" + "="*60)
        print("VERIFICANDO DEPENDENCIAS")
        print("="*60)
        
        dependencies = {
            'MetaTrader5': 'MetaTrader5',
            'pandas': 'pandas',
            'numpy': 'numpy',
            'requests': 'requests',
            'beautifulsoup4': 'bs4',
            'plotly': 'plotly',
            'streamlit': 'streamlit'
        }
        
        missing = []
        
        for package, import_name in dependencies.items():
            try:
                __import__(import_name)
                print(f"✓ {package} instalado")
            except ImportError:
                print(f"✗ {package} NO instalado")
                missing.append(package)
                
        if missing:
            print(f"\n⚠️ Dependencias faltantes: {', '.join(missing)}")
            response = input("\n¿Deseas instalarlas ahora? (s/n): ")
            if response.lower() == 's':
                for package in missing:
                    print(f"Instalando {package}...")
                    subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                                 capture_output=True)
                print("✓ Dependencias instaladas")
        
        return len(missing) == 0
        
    def start_service(self, service_key):
        """Inicia un servicio específico"""
        service = self.services[service_key]
        file_path = self.base_path / service['file']
        
        if not file_path.exists():
            print(f"✗ Archivo no encontrado: {service['file']}")
            return False
            
        try:
            # Verificar si el puerto está ocupado
            if self.check_port(service['port']):
                print(f"⚠️ Puerto {service['port']} ya está en uso")
                service['status'] = 'running'
                return True
                
            # Iniciar el proceso
            print(f"Iniciando {service['name']}...")
            service['process'] = subprocess.Popen(
                [sys.executable, str(file_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.base_path)
            )
            
            # Esperar a que el servicio inicie
            time.sleep(2)
            
            # Verificar que el servicio esté activo
            if self.check_port(service['port']):
                service['status'] = 'running'
                print(f"✓ {service['name']} iniciado en puerto {service['port']}")
                return True
            else:
                print(f"⚠️ {service['name']} no respondió en puerto {service['port']}")
                service['status'] = 'failed'
                return False
                
        except Exception as e:
            print(f"✗ Error iniciando {service['name']}: {e}")
            service['status'] = 'error'
            return False
            
    def start_all_services(self):
        """Inicia todos los servicios"""
        print("\n" + "="*60)
        print("INICIANDO SERVICIOS")
        print("="*60 + "\n")
        
        success_count = 0
        
        for service_key in self.services:
            if self.start_service(service_key):
                success_count += 1
            time.sleep(1)
            
        print(f"\n✓ {success_count}/{len(self.services)} servicios iniciados")
        return success_count > 0
        
    def open_dashboards(self):
        """Abre los dashboards en el navegador"""
        print("\n" + "="*60)
        print("ABRIENDO DASHBOARDS")
        print("="*60 + "\n")
        
        for service_key, service in self.services.items():
            if 'url' in service and service['status'] == 'running':
                print(f"Abriendo {service['name']}...")
                webbrowser.open(service['url'])
                time.sleep(1)
                
    def show_status(self):
        """Muestra el estado de todos los servicios"""
        print("\n" + "="*60)
        print("ESTADO DEL SISTEMA")
        print("="*60)
        print(f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-"*60)
        
        for service_key, service in self.services.items():
            status_icon = "✓" if service['status'] == 'running' else "✗"
            status_text = "ACTIVO" if service['status'] == 'running' else "DETENIDO"
            
            print(f"{status_icon} {service['name']:30} [{status_text:10}] Puerto: {service['port']}")
            
            if 'url' in service and service['status'] == 'running':
                print(f"  └─> {service['url']}")
                
        print("="*60)
        
    def monitor_services(self):
        """Monitorea los servicios en segundo plano"""
        while True:
            time.sleep(30)  # Verificar cada 30 segundos
            for service_key, service in self.services.items():
                if service['status'] == 'running':
                    if not self.check_port(service['port']):
                        print(f"\n⚠️ {service['name']} se ha detenido. Reiniciando...")
                        self.start_service(service_key)
                        
    def stop_all_services(self):
        """Detiene todos los servicios"""
        print("\n" + "="*60)
        print("DETENIENDO SERVICIOS")
        print("="*60 + "\n")
        
        for service_key, service in self.services.items():
            if service['process'] and service['process'].poll() is None:
                print(f"Deteniendo {service['name']}...")
                service['process'].terminate()
                service['status'] = 'stopped'
                time.sleep(1)
                
        print("✓ Todos los servicios detenidos")
        
    def start_trading_bot(self, mode='demo'):
        """Inicia el bot de trading"""
        print(f"\n🤖 Iniciando Trading Bot en modo {mode.upper()}...")
        
        bot_path = self.base_path / 'src' / 'trading' / 'main_trader.py'
        
        if not bot_path.exists():
            # Intentar con el archivo en la raíz
            bot_path = self.base_path / 'main.py'
            
        if bot_path.exists():
            os.environ['TRADING_MODE'] = mode.upper()
            subprocess.Popen([sys.executable, str(bot_path)], cwd=str(self.base_path))
            print("✓ Trading Bot iniciado")
        else:
            print("✗ No se encontró el archivo del Trading Bot")
            
    def run_interactive(self):
        """Ejecuta el sistema en modo interactivo"""
        print("""
╔════════════════════════════════════════════════════════════╗
║           ALGO TRADER V3 - SISTEMA DE EJECUCIÓN           ║
║                    Modo Interactivo                       ║
╚════════════════════════════════════════════════════════════╝
        """)
        
        # Verificar dependencias
        if not self.check_dependencies():
            print("\n⚠️ Algunas dependencias faltan. El sistema puede no funcionar correctamente.")
            
        # Iniciar servicios
        if self.start_all_services():
            # Mostrar estado
            self.show_status()
            
            # Abrir dashboards
            time.sleep(2)
            self.open_dashboards()
            
            # Iniciar monitor en segundo plano
            monitor_thread = threading.Thread(target=self.monitor_services, daemon=True)
            monitor_thread.start()
            
            # Menú interactivo
            while True:
                print("\n" + "="*60)
                print("OPCIONES DISPONIBLES")
                print("="*60)
                print("[1] Ver estado del sistema")
                print("[2] Iniciar Trading Bot (DEMO)")
                print("[3] Iniciar Trading Bot (PAPER)")
                print("[4] Abrir dashboards en navegador")
                print("[5] Reiniciar servicios")
                print("[6] Ver logs")
                print("[0] Salir")
                print("="*60)
                
                choice = input("\nSelecciona una opción: ")
                
                if choice == '1':
                    self.show_status()
                elif choice == '2':
                    self.start_trading_bot('demo')
                elif choice == '3':
                    self.start_trading_bot('paper')
                elif choice == '4':
                    self.open_dashboards()
                elif choice == '5':
                    self.stop_all_services()
                    time.sleep(2)
                    self.start_all_services()
                elif choice == '6':
                    log_file = self.base_path / 'logs' / 'algo_trader.log'
                    if log_file.exists():
                        print("\n" + "="*60)
                        print("ÚLTIMAS LÍNEAS DEL LOG")
                        print("="*60)
                        with open(log_file, 'r') as f:
                            lines = f.readlines()
                            for line in lines[-20:]:
                                print(line.strip())
                    else:
                        print("No hay logs disponibles")
                elif choice == '0':
                    print("\n¿Deseas detener todos los servicios? (s/n): ", end='')
                    if input().lower() == 's':
                        self.stop_all_services()
                    break
                else:
                    print("Opción no válida")
                    
        else:
            print("\n✗ Error al iniciar los servicios")
            print("Verifica que los archivos estén en las ubicaciones correctas")
            
    def run_automatic(self):
        """Ejecuta el sistema automáticamente"""
        print("""
╔════════════════════════════════════════════════════════════╗
║           ALGO TRADER V3 - INICIO AUTOMÁTICO              ║
╚════════════════════════════════════════════════════════════╝
        """)
        
        # Iniciar todo automáticamente
        if self.start_all_services():
            self.show_status()
            time.sleep(3)
            self.open_dashboards()
            
            print("\n✓ Sistema iniciado correctamente")
            print("\nLos servicios están ejecutándose en segundo plano.")
            print("Puedes cerrar esta ventana. Los servicios continuarán activos.")
            print("\nDashboards disponibles:")
            
            for service_key, service in self.services.items():
                if 'url' in service and service['status'] == 'running':
                    print(f"  • {service['name']}: {service['url']}")
                    
            print("\nPresiona Enter para salir...")
            input()
        else:
            print("\n✗ Error al iniciar los servicios")
            input("\nPresiona Enter para salir...")

def main():
    executor = AlgoTraderExecutor()
    
    # Verificar argumentos de línea de comandos
    if len(sys.argv) > 1:
        if sys.argv[1] == '--auto':
            executor.run_automatic()
        elif sys.argv[1] == '--stop':
            executor.stop_all_services()
        else:
            executor.run_interactive()
    else:
        executor.run_interactive()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupción detectada. Deteniendo servicios...")
        executor = AlgoTraderExecutor()
        executor.stop_all_services()
    except Exception as e:
        print(f"\n✗ Error crítico: {e}")
        import traceback
        traceback.print_exc()
        input("\nPresiona Enter para salir...")
