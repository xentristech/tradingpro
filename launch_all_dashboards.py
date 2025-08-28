"""
Launch All Dashboards - Lanzador de Múltiples Dashboards
Ejecuta todos los dashboards en puertos diferentes simultáneamente
"""
import subprocess
import threading
import time
import webbrowser
import os
from pathlib import Path

class DashboardLauncher:
    def __init__(self):
        self.dashboards = {
            'Simple Dashboard': {
                'file': 'simple_dashboard.py',
                'port': 8502,
                'description': 'Dashboard principal con información general',
                'process': None
            },
            'Monitoring Dashboard': {
                'file': 'monitoring_dashboard.py', 
                'port': 8503,
                'description': 'Monitoreo multi-cuenta MT5',
                'process': None
            },
            'Trading Dashboard': {
                'file': 'trading_dashboard.py',
                'port': 8504,
                'description': 'Operaciones en vivo y precios',
                'process': None
            },
            'AI Dashboard': {
                'file': 'ai_dashboard.py',
                'port': 8505,
                'description': 'Análisis con IA y Ollama',
                'process': None
            },
            'Signals Dashboard': {
                'file': 'signals_dashboard.py',
                'port': 8506,
                'description': 'Señales técnicas y TwelveData',
                'process': None
            },
            'Charts Dashboard': {
                'file': 'charts_dashboard.py',
                'port': 8507,
                'description': 'Gráficas de TwelveData',
                'process': None
            }
        }
        
        self.running_processes = []
    
    def launch_dashboard(self, name, config):
        """Lanzar un dashboard específico"""
        try:
            file_path = Path(config['file'])
            if not file_path.exists():
                print(f"[ERROR] {name}: Archivo {config['file']} no encontrado")
                return False
            
            print(f"[LAUNCHING] {name} en puerto {config['port']}...")
            
            # Lanzar proceso
            process = subprocess.Popen(
                ['python', config['file']],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
            
            config['process'] = process
            self.running_processes.append(process)
            
            print(f"[OK] {name} iniciado (PID: {process.pid})")
            return True
            
        except Exception as e:
            print(f"[ERROR] {name}: {str(e)}")
            return False
    
    def check_dashboard_status(self, name, config):
        """Verificar si un dashboard está funcionando"""
        if config['process'] and config['process'].poll() is None:
            return True
        return False
    
    def launch_all(self):
        """Lanzar todos los dashboards"""
        print("="*60)
        print(" MULTI-DASHBOARD LAUNCHER")
        print(" Lanzando todos los dashboards simultáneamente")
        print("="*60)
        print()
        
        successful_launches = 0
        
        # Lanzar cada dashboard
        for name, config in self.dashboards.items():
            if self.launch_dashboard(name, config):
                successful_launches += 1
                time.sleep(2)  # Esperar entre lanzamientos
        
        print()
        print("="*60)
        print(f" RESUMEN: {successful_launches}/{len(self.dashboards)} dashboards iniciados")
        print("="*60)
        
        # Mostrar información de acceso
        print()
        print("DASHBOARDS DISPONIBLES:")
        print("-" * 40)
        
        for name, config in self.dashboards.items():
            if self.check_dashboard_status(name, config):
                print(f"✓ {name}")
                print(f"  URL: http://localhost:{config['port']}")
                print(f"  Descripción: {config['description']}")
                print()
            else:
                print(f"✗ {name} - FALLÓ AL INICIAR")
                print()
        
        # Abrir navegadores automáticamente
        if successful_launches > 0:
            print("Abriendo navegadores automáticamente en 5 segundos...")
            threading.Timer(5.0, self.open_browsers).start()
        
        return successful_launches > 0
    
    def open_browsers(self):
        """Abrir todos los dashboards en el navegador"""
        for name, config in self.dashboards.items():
            if self.check_dashboard_status(name, config):
                try:
                    webbrowser.open_new_tab(f'http://localhost:{config["port"]}')
                    time.sleep(1)  # Esperar entre abrir tabs
                except:
                    pass
    
    def monitor_dashboards(self):
        """Monitorear el estado de los dashboards"""
        print("="*60)
        print(" MONITOREANDO DASHBOARDS")
        print(" Presiona Ctrl+C para detener todos")
        print("="*60)
        
        try:
            while True:
                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Estado de dashboards:")
                
                active_count = 0
                for name, config in self.dashboards.items():
                    if self.check_dashboard_status(name, config):
                        print(f"  ✓ {name} - Puerto {config['port']} - ACTIVO")
                        active_count += 1
                    else:
                        print(f"  ✗ {name} - Puerto {config['port']} - INACTIVO")
                
                print(f"\nDashboards activos: {active_count}/{len(self.dashboards)}")
                
                if active_count == 0:
                    print("\n[WARNING] Todos los dashboards han sido detenidos")
                    break
                
                time.sleep(30)  # Revisar cada 30 segundos
                
        except KeyboardInterrupt:
            print("\n\n[USER] Deteniendo todos los dashboards...")
            self.stop_all()
    
    def stop_all(self):
        """Detener todos los dashboards"""
        print("\nDeteniendo dashboards...")
        
        for name, config in self.dashboards.items():
            if config['process'] and config['process'].poll() is None:
                try:
                    config['process'].terminate()
                    config['process'].wait(timeout=5)
                    print(f"✓ {name} detenido")
                except:
                    try:
                        config['process'].kill()
                        print(f"✓ {name} forzado a detenerse")
                    except:
                        print(f"✗ {name} no se pudo detener")
        
        print("\nTodos los dashboards han sido detenidos.")
    
    def show_menu(self):
        """Mostrar menú interactivo"""
        while True:
            print("\n" + "="*50)
            print(" MULTI-DASHBOARD CONTROL PANEL")
            print("="*50)
            print("1. Lanzar todos los dashboards")
            print("2. Ver estado de dashboards")
            print("3. Abrir dashboards en navegador")
            print("4. Detener todos los dashboards")
            print("5. Mostrar URLs de acceso")
            print("0. Salir")
            print("="*50)
            
            choice = input("Selecciona una opción: ").strip()
            
            if choice == '1':
                if self.launch_all():
                    self.monitor_dashboards()
                else:
                    print("No se pudo lanzar ningún dashboard")
            
            elif choice == '2':
                self.show_status()
            
            elif choice == '3':
                self.open_browsers()
                print("Dashboards abiertos en el navegador")
            
            elif choice == '4':
                self.stop_all()
            
            elif choice == '5':
                self.show_urls()
            
            elif choice == '0':
                self.stop_all()
                break
            
            else:
                print("Opción inválida")
    
    def show_status(self):
        """Mostrar estado actual de dashboards"""
        print("\n" + "="*50)
        print(" ESTADO DE DASHBOARDS")
        print("="*50)
        
        for name, config in self.dashboards.items():
            status = "ACTIVO" if self.check_dashboard_status(name, config) else "INACTIVO"
            print(f"{name:<20} | Puerto {config['port']} | {status}")
    
    def show_urls(self):
        """Mostrar URLs de acceso"""
        print("\n" + "="*60)
        print(" URLS DE ACCESO A DASHBOARDS")
        print("="*60)
        
        for name, config in self.dashboards.items():
            status = "✓" if self.check_dashboard_status(name, config) else "✗"
            print(f"{status} {name}")
            print(f"   URL: http://localhost:{config['port']}")
            print(f"   Descripción: {config['description']}")
            print()

def main():
    launcher = DashboardLauncher()
    
    # Verificar archivos
    missing_files = []
    for name, config in launcher.dashboards.items():
        if not Path(config['file']).exists():
            missing_files.append(config['file'])
    
    if missing_files:
        print("ERROR: Los siguientes archivos no existen:")
        for file in missing_files:
            print(f"  - {file}")
        print("\nPor favor, asegúrate de que todos los dashboards estén creados.")
        return
    
    try:
        launcher.show_menu()
    except KeyboardInterrupt:
        print("\nDeteniendo...")
        launcher.stop_all()

if __name__ == "__main__":
    from datetime import datetime
    main()