#!/usr/bin/env python
"""
EJECUTOR DIRECTO - ALGO TRADER V3
==================================
Ejecuta todos los servicios inmediatamente
"""

import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

def main():
    base_path = Path(__file__).parent
    os.chdir(base_path)
    
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║           ALGO TRADER V3 - INICIANDO SISTEMA              ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    # Lista de servicios a iniciar
    services = [
        ('src/data/TICK_SYSTEM_FINAL.py', 'Sistema de Ticks', 8508),
        ('src/ui/dashboards/revolutionary_dashboard_final.py', 'Revolutionary Dashboard', 8512),
        ('src/ui/charts/chart_simulation_reviewed.py', 'Chart Simulation', 8516),
        ('src/ui/charts/tradingview_professional_chart.py', 'TradingView Professional', 8517)
    ]
    
    processes = []
    
    # Iniciar cada servicio
    for script, name, port in services:
        script_path = base_path / script
        
        if script_path.exists():
            print(f"\n🚀 Iniciando {name} en puerto {port}...")
            try:
                # Iniciar proceso en segundo plano
                process = subprocess.Popen(
                    [sys.executable, str(script_path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=str(base_path),
                    creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
                )
                processes.append((name, process))
                print(f"✅ {name} iniciado")
                time.sleep(2)  # Esperar entre servicios
            except Exception as e:
                print(f"❌ Error iniciando {name}: {e}")
        else:
            print(f"❌ No se encuentra: {script}")
    
    # Esperar un poco para que los servicios inicien
    print("\n⏳ Esperando que los servicios se estabilicen...")
    time.sleep(5)
    
    # Abrir navegadores
    print("\n🌐 Abriendo dashboards en el navegador...")
    
    urls = [
        ('http://localhost:8512', 'Revolutionary Dashboard'),
        ('http://localhost:8516', 'Chart Simulation'),
        ('http://localhost:8517', 'TradingView Professional')
    ]
    
    for url, name in urls:
        print(f"   Abriendo {name}...")
        webbrowser.open(url)
        time.sleep(1)
    
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║                  SISTEMA INICIADO                         ║
    ╚════════════════════════════════════════════════════════════╝
    
    ✅ SERVICIOS ACTIVOS:
    
       • Sistema de Ticks MT5    - Puerto 8508
       • Revolutionary Dashboard  - http://localhost:8512
       • Chart Simulation        - http://localhost:8516
       • TradingView Pro         - http://localhost:8517
    
    Los servicios están ejecutándose en segundo plano.
    Puedes cerrar esta ventana, los servicios continuarán activos.
    
    Para detener los servicios, cierra las ventanas de consola
    o ejecuta: taskkill /F /IM python.exe
    
    ════════════════════════════════════════════════════════════
    """)
    
    # Mantener el script activo
    try:
        input("\nPresiona Enter para salir (los servicios continuarán)...")
    except KeyboardInterrupt:
        print("\n\n⚠️ Deteniendo servicios...")
        for name, process in processes:
            if process.poll() is None:
                process.terminate()
                print(f"   {name} detenido")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        input("\nPresiona Enter para salir...")
