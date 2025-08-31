#!/usr/bin/env python
"""
EJECUTOR PRINCIPAL DE ALGO TRADER V3
=====================================
Script para iniciar todos los componentes del sistema
"""

import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

class AlgoTraderExecutor:
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.processes = []
        
        # Configurar PYTHONPATH
        sys.path.insert(0, str(self.base_path))
        sys.path.insert(0, str(self.base_path / 'src'))
        
        # Configurar encoding UTF-8
        if sys.stdout.encoding != 'utf-8':
            try:
                sys.stdout.reconfigure(encoding='utf-8', errors='replace')
            except:
                pass
    
    def print_banner(self):
        """Muestra el banner del sistema"""
        print("""
╔════════════════════════════════════════════════════════╗
║            ALGO TRADER V3 - SISTEMA PRINCIPAL         ║
║                 Trading Algorítmico con IA            ║
║                      by XentrisTech                   ║
╚════════════════════════════════════════════════════════╝
        """)
    
    def check_python(self):
        """Verifica la versión de Python"""
        print(f"\n🐍 Python {sys.version_info.major}.{sys.version_info.minor} detectado")
        
        if sys.version_info < (3, 8):
            print("❌ Se requiere Python 3.8 o superior")
            return False
        
        print("✅ Versión de Python correcta")
        return True
    
    def check_dependencies(self):
        """Verifica las dependencias principales"""
        print("\n📦 Verificando dependencias...")
        
        dependencies = {
            'MetaTrader5': 'MetaTrader5',
            'pandas': 'pandas',
            'numpy': 'numpy',
            'requests': 'requests',
            'beautifulsoup4': 'bs4'
        }
        
        missing = []
        for name, module in dependencies.items():
            try:
                __import__(module)
                print(f"  ✓ {name}")
            except ImportError:
                print(f"  ✗ {name} - No instalado")
                missing.append(name)
        
        if missing:
            print(f"\n⚠️ Dependencias faltantes: {', '.join(missing)}")
            print("Ejecuta: pip install " + " ".join(missing))
            return False
        
        return True
    
    def start_component(self, name, script_path, port=None):
        """Inicia un componente del sistema"""
        try:
            if not script_path.exists():
                print(f"  ⚠️ {name}: Archivo no encontrado - {script_path}")
                return None
            
            print(f"  🚀 Iniciando {name}...", end="")
            
            # Iniciar proceso
            process = subprocess.Popen(
                [sys.executable, str(script_path)],
                cwd=str(self.base_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
            )
            
            # Esperar un momento para verificar que inició
            time.sleep(1)
            
            if process.poll() is None:
                print(f" ✓")
                if port:
                    print(f"     → http://localhost:{port}")
                self.processes.append((name, process))
                return process
            else:
                print(f" ✗ (Error al iniciar)")
                return None
                
        except Exception as e:
            print(f" ✗ (Error: {e})")
            return None
    
    def start_dashboards(self):
        """Inicia todos los dashboards"""
        print("\n📊 Iniciando Dashboards...")
        
        dashboards = [
            ("Revolutionary Dashboard", 
             self.base_path / 'src' / 'ui' / 'dashboards' / 'revolutionary_dashboard_final.py', 
             8512),
            ("Chart Simulation", 
             self.base_path / 'src' / 'ui' / 'charts' / 'chart_simulation_reviewed.py', 
             8516),
            ("TradingView Professional", 
             self.base_path / 'src' / 'ui' / 'charts' / 'tradingview_professional_chart.py', 
             8517)
        ]
        
        for name, path, port in dashboards:
            self.start_component(name, path, port)
            time.sleep(1)
    
    def start_trading_system(self, mode='demo'):
        """Inicia el sistema de trading"""
        print(f"\n💹 Iniciando Sistema de Trading (Modo: {mode.upper()})...")
        
        # Configurar modo
        os.environ['TRADING_MODE'] = mode.upper()
        
        # Sistema de ticks
        tick_system = self.base_path / 'src' / 'data' / 'TICK_SYSTEM_FINAL.py'
        self.start_component("Sistema de Ticks", tick_system)
        
        # Bot principal
        trading_bot = self.base_path / 'src' / 'trading' / 'main_trader.py'
        if not trading_bot.exists():
            trading_bot = self.base_path / 'main.py'
        
        self.start_component("Bot de Trading", trading_bot)
    
    def open_browsers(self):
        """Abre los dashboards en el navegador"""
        print("\n🌐 Abriendo dashboards en navegador...")
        time.sleep(3)  # Esperar que los servicios estén listos
        
        urls = [
            'http://localhost:8512',  # Revolutionary Dashboard
            'http://localhost:8516',  # Chart Simulation
            'http://localhost:8517'   # TradingView
        ]
        
        for url in urls:
            webbrowser.open(url)
            time.sleep(1)
    
    def run_demo(self):
        """Ejecuta el sistema en modo DEMO"""
        self.print_banner()
        
        if not self.check_python():
            return
        
        print("\n" + "="*60)
        print("         MODO DEMO - Trading Simulado")
        print("="*60)
        
        # Iniciar componentes
        self.start_trading_system('demo')
        self.start_dashboards()
        self.open_browsers()
        
        print("\n" + "="*60)
        print("✅ SISTEMA INICIADO EXITOSAMENTE")
        print("="*60)
        print("""
Componentes activos:
• Sistema de Ticks: Analizando mercado
• Bot de Trading: Modo DEMO
• Revolutionary Dashboard: http://localhost:8512
• Chart Simulation: http://localhost:8516
• TradingView Professional: http://localhost:8517

Para detener: Presiona Ctrl+C o cierra esta ventana
""")
        
        # Mantener el programa ejecutándose
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.shutdown()
    
    def run_dashboards_only(self):
        """Ejecuta solo los dashboards sin trading"""
        self.print_banner()
        
        print("\n" + "="*60)
        print("      MODO DASHBOARDS - Solo Visualización")
        print("="*60)
        
        self.start_dashboards()
        self.open_browsers()
        
        print("\n✅ Dashboards iniciados")
        print("\nPresiona Ctrl+C para detener")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.shutdown()
    
    def shutdown(self):
        """Detiene todos los procesos"""
        print("\n\n⏹️ Deteniendo sistema...")
        
        for name, process in self.processes:
            try:
                process.terminate()
                print(f"  ✓ {name} detenido")
            except:
                pass
        
        print("\n✅ Sistema detenido correctamente")
    
    def run(self):
        """Ejecuta el sistema con menú interactivo"""
        self.print_banner()
        
        if not self.check_python():
            input("\nPresiona Enter para salir...")
            return
        
        # Verificar dependencias básicas
        self.check_dependencies()
        
        print("\n" + "="*60)
        print("         SELECCIONA MODO DE EJECUCIÓN")
        print("="*60)
        print("""
1. DEMO - Trading simulado (Recomendado)
2. PAPER - Trading con datos reales sin dinero
3. LIVE - Trading real (⚠️ DINERO REAL)
4. DASHBOARDS - Solo visualización
5. Salir
""")
        
        try:
            opcion = input("Selecciona opción (1-5): ").strip()
            
            if opcion == '1':
                self.run_demo()
            elif opcion == '2':
                os.environ['TRADING_MODE'] = 'PAPER'
                self.run_demo()  # Usa la misma función pero con modo PAPER
            elif opcion == '3':
                print("\n⚠️ ADVERTENCIA: Modo LIVE usa dinero real")
                confirmar = input("Escribe CONFIRMAR para continuar: ")
                if confirmar == 'CONFIRMAR':
                    os.environ['TRADING_MODE'] = 'LIVE'
                    self.run_demo()  # Usa la misma función pero con modo LIVE
                else:
                    print("Operación cancelada")
            elif opcion == '4':
                self.run_dashboards_only()
            else:
                print("Saliendo...")
                
        except Exception as e:
            print(f"\n❌ Error: {e}")
            input("\nPresiona Enter para salir...")

if __name__ == "__main__":
    # Verificar si se pasaron argumentos
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        executor = AlgoTraderExecutor()
        
        if mode == '--demo':
            executor.run_demo()
        elif mode == '--dashboards':
            executor.run_dashboards_only()
        else:
            executor.run()
    else:
        # Modo interactivo
        executor = AlgoTraderExecutor()
        executor.run()
