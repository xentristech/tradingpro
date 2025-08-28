"""
Run Dynamic System - Launcher para el Sistema de Gráficos Dinámicos
================================================================

Script principal para ejecutar todo el sistema de gráficos dinámicos
"""

import os
import sys
import time
import threading
import subprocess
from pathlib import Path
from datetime import datetime

class DynamicSystemLauncher:
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.processes = {}
        self.is_running = False
        
    def check_dependencies(self):
        """Verificar que todos los archivos necesarios existen"""
        required_files = [
            'dynamic_charts.py',
            'chart_scheduler.py', 
            'charts_dashboard.py'
        ]
        
        missing_files = []
        for file in required_files:
            if not (self.base_path / file).exists():
                missing_files.append(file)
        
        if missing_files:
            print(f"ERROR: Archivos faltantes: {', '.join(missing_files)}")
            return False
        
        print("OK - Todos los archivos necesarios están disponibles")
        return True
    
    def start_charts_dashboard(self, port=8507):
        """Iniciar el Charts Dashboard"""
        try:
            print(f"[INICIO] Iniciando Charts Dashboard en puerto {port}...")
            
            # Ejecutar charts_dashboard.py
            process = subprocess.Popen([
                sys.executable, 
                str(self.base_path / 'charts_dashboard.py')
            ], 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(self.base_path)
            )
            
            self.processes['dashboard'] = process
            
            # Dar tiempo para que se inicie
            time.sleep(2)
            
            if process.poll() is None:  # Proceso sigue ejecutándose
                print(f"[OK] Charts Dashboard iniciado correctamente")
                print(f"[URL] http://localhost:{port}")
                return True
            else:
                print("[ERROR] Error iniciando Charts Dashboard")
                return False
                
        except Exception as e:
            print(f"[ERROR] Error iniciando Charts Dashboard: {e}")
            return False
    
    def start_dynamic_charts(self):
        """Iniciar el sistema de gráficos dinámicos"""
        try:
            print("[INICIO] Iniciando sistema de gráficos dinámicos...")
            
            # Ejecutar chart_scheduler.py
            process = subprocess.Popen([
                sys.executable,
                str(self.base_path / 'chart_scheduler.py'),
                '--interval', '30'  # Actualizar cada 30 segundos
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, 
            text=True,
            cwd=str(self.base_path)
            )
            
            self.processes['scheduler'] = process
            
            # Dar tiempo para que se inicie
            time.sleep(3)
            
            if process.poll() is None:
                print("[OK] Sistema de gráficos dinámicos iniciado")
                print("[INFO] Actualizando cada 30 segundos")
                return True
            else:
                print("[ERROR] Error iniciando sistema dinámico")
                return False
                
        except Exception as e:
            print(f"[ERROR] Error iniciando sistema dinámico: {e}")
            return False
    
    def monitor_processes(self):
        """Monitorear procesos en ejecución"""
        def monitor_loop():
            while self.is_running:
                try:
                    # Verificar dashboard
                    if 'dashboard' in self.processes:
                        if self.processes['dashboard'].poll() is not None:
                            print("[WARNING] Charts Dashboard se ha detenido")
                    
                    # Verificar scheduler
                    if 'scheduler' in self.processes:
                        if self.processes['scheduler'].poll() is not None:
                            print("[WARNING] Sistema dinámico se ha detenido")
                    
                    time.sleep(10)  # Revisar cada 10 segundos
                    
                except Exception as e:
                    print(f"Error en monitoreo: {e}")
                    time.sleep(5)
        
        monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
    
    def stop_all_processes(self):
        """Detener todos los procesos"""
        print("\n[STOP] Deteniendo sistema...")
        self.is_running = False
        
        for name, process in self.processes.items():
            try:
                if process.poll() is None:  # Proceso sigue ejecutándose
                    print(f"[STOP] Deteniendo {name}...")
                    process.terminate()
                    
                    # Esperar terminación
                    try:
                        process.wait(timeout=5)
                        print(f"[OK] {name} detenido")
                    except subprocess.TimeoutExpired:
                        print(f"[FORCE] Forzando cierre de {name}")
                        process.kill()
                        
            except Exception as e:
                print(f"Error deteniendo {name}: {e}")
        
        self.processes.clear()
        print("[OK] Sistema completamente detenido")
    
    def show_status(self):
        """Mostrar estado del sistema"""
        print("\n" + "="*50)
        print(" ESTADO DEL SISTEMA DINÁMICO")
        print("="*50)
        
        if not self.processes:
            print("[INFO] Ningún proceso ejecutándose")
            return
        
        for name, process in self.processes.items():
            if process.poll() is None:
                print(f"[RUNNING] {name}: EJECUTÁNDOSE (PID: {process.pid})")
            else:
                print(f"[STOPPED] {name}: DETENIDO")
        
        print(f"\n[TIME] Estado actual: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("[URL] Charts Dashboard: http://localhost:8507")
        print("[INFO] Gráficos actualizándose cada 30 segundos")
    
    def run_complete_system(self):
        """Ejecutar sistema completo"""
        print("DYNAMIC CHART SYSTEM LAUNCHER")
        print("="*60)
        print("[INICIO] Iniciando sistema completo de gráficos dinámicos...")
        print("="*60)
        
        # Verificar dependencias
        if not self.check_dependencies():
            return False
        
        self.is_running = True
        
        # 1. Iniciar Charts Dashboard
        if not self.start_charts_dashboard():
            return False
        
        # 2. Iniciar sistema dinámico
        if not self.start_dynamic_charts():
            self.stop_all_processes()
            return False
        
        # 3. Iniciar monitoreo
        self.monitor_processes()
        
        print("\n" + "="*60)
        print(" SISTEMA DINÁMICO COMPLETAMENTE ACTIVO")
        print("="*60)
        print("[URL] Charts Dashboard: http://localhost:8507")
        print("[INFO] Auto-refresh: 15 segundos")
        print("[INFO] Gráficos actualizándose: cada 30 segundos")
        print("[INFO] Tipos: Candlestick, Line, OHLC, Bars")
        print("[INFO] Símbolos: BTC/USD, XAU/USD, EUR/USD")
        print("="*60)
        print("Presiona Ctrl+C para detener todo el sistema")
        
        try:
            # Mantener ejecutándose hasta interrumpir
            while self.is_running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n[STOP] Interrupción recibida...")
        
        finally:
            self.stop_all_processes()
        
        return True
    
    def run_test_mode(self):
        """Ejecutar en modo de prueba (una actualización)"""
        print("TEST MODE - DYNAMIC CHART SYSTEM")
        print("="*40)
        
        if not self.check_dependencies():
            return False
        
        try:
            print("[TEST] Ejecutando prueba del sistema dinámico...")
            
            # Ejecutar una actualización de prueba
            result = subprocess.run([
                sys.executable,
                str(self.base_path / 'chart_scheduler.py'),
                '--once'
            ], 
            capture_output=True, 
            text=True,
            timeout=120  # Timeout de 2 minutos
            )
            
            if result.returncode == 0:
                print("[OK] Prueba exitosa!")
                print("[SUCCESS] Gráficos dinámicos generados correctamente")
                
                # Mostrar archivos creados
                charts_dir = self.base_path / "advanced_charts"
                if charts_dir.exists():
                    live_charts = list(charts_dir.glob("*_live.png"))
                    if live_charts:
                        print(f"[INFO] {len(live_charts)} gráficos LIVE encontrados:")
                        for chart in live_charts[-5:]:  # Mostrar últimos 5
                            print(f"  - {chart.name}")
                
                return True
            else:
                print("[ERROR] Error en la prueba:")
                print(result.stderr)
                return False
                
        except subprocess.TimeoutExpired:
            print("[ERROR] Timeout en la prueba (>2 minutos)")
            return False
        except Exception as e:
            print(f"[ERROR] Error en prueba: {e}")
            return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Dynamic Chart System Launcher')
    parser.add_argument('--test', action='store_true', 
                       help='Ejecutar en modo de prueba (una actualización)')
    parser.add_argument('--dashboard-only', action='store_true',
                       help='Solo iniciar Charts Dashboard')
    parser.add_argument('--status', action='store_true',
                       help='Mostrar estado del sistema')
    
    args = parser.parse_args()
    
    launcher = DynamicSystemLauncher()
    
    try:
        if args.test:
            success = launcher.run_test_mode()
            sys.exit(0 if success else 1)
            
        elif args.dashboard_only:
            print("Iniciando solo Charts Dashboard...")
            launcher.is_running = True
            if launcher.start_charts_dashboard():
                print("Dashboard activo. Presiona Ctrl+C para detener.")
                try:
                    while True:
                        time.sleep(1)
                except KeyboardInterrupt:
                    pass
                finally:
                    launcher.stop_all_processes()
            
        elif args.status:
            launcher.show_status()
            
        else:
            # Ejecutar sistema completo
            success = launcher.run_complete_system()
            sys.exit(0 if success else 1)
            
    except Exception as e:
        print(f"[FATAL] Error fatal: {e}")
        launcher.stop_all_processes()
        sys.exit(1)

if __name__ == "__main__":
    main()