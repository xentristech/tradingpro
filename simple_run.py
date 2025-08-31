import os
import subprocess
import time
import webbrowser

print("INICIANDO ALGO TRADER V3...")
print("="*50)

# Cambiar al directorio del proyecto
os.chdir(r"C:\Users\user\Desktop\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2")

# Servicios a iniciar
services = [
    ("Sistema de Ticks", r"src\data\TICK_SYSTEM_FINAL.py"),
    ("Revolutionary Dashboard", r"src\ui\dashboards\revolutionary_dashboard_final.py"),
    ("Chart Simulation", r"src\ui\charts\chart_simulation_reviewed.py"),
    ("TradingView Pro", r"src\ui\charts\tradingview_professional_chart.py")
]

# Iniciar cada servicio
for name, script in services:
    if os.path.exists(script):
        print(f"Iniciando {name}...")
        subprocess.Popen(f"start cmd /k python {script}", shell=True)
        time.sleep(2)
    else:
        print(f"ADVERTENCIA: No se encuentra {script}")

# Esperar que los servicios inicien
print("\nEsperando que los servicios inicien...")
time.sleep(5)

# Abrir navegadores
print("\nAbriendo dashboards...")
webbrowser.open("http://localhost:8512")
time.sleep(1)
webbrowser.open("http://localhost:8516")
time.sleep(1)
webbrowser.open("http://localhost:8517")

print("\n" + "="*50)
print("SISTEMA INICIADO")
print("="*50)
print("\nDashboards disponibles:")
print("- Revolutionary Dashboard: http://localhost:8512")
print("- Chart Simulation: http://localhost:8516")
print("- TradingView Pro: http://localhost:8517")
print("\nLos servicios están ejecutándose en ventanas separadas.")
print("Para detener, cierra las ventanas de comandos.")

input("\nPresiona Enter para salir...")
