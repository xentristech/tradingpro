#!/usr/bin/env python3
"""
Lanzador del Dashboard Web
Script para iniciar el dashboard de forma sencilla
"""
import subprocess
import sys
import os
from pathlib import Path
import webbrowser
import time

def check_streamlit():
    """Verificar si Streamlit está instalado"""
    try:
        import streamlit
        return True
    except ImportError:
        return False

def install_streamlit():
    """Instalar Streamlit si no está disponible"""
    print(">> Instalando Streamlit...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'streamlit'], 
                      check=True, capture_output=True)
        print(">> Streamlit instalado exitosamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f">> Error instalando Streamlit: {e}")
        return False

def launch_dashboard():
    """Lanzar el dashboard web"""
    
    # Verificar ubicación actual
    dashboard_file = Path("dashboard_web.py")
    if not dashboard_file.exists():
        print(">> Error: dashboard_web.py no encontrado en el directorio actual")
        print(f"   Directorio actual: {os.getcwd()}")
        return False
    
    # Verificar Streamlit
    if not check_streamlit():
        print(">> Streamlit no esta instalado. Instalando...")
        if not install_streamlit():
            return False
    
    print(">> Iniciando AlgoTrader Dashboard...")
    print(">> El dashboard se abrira en tu navegador automaticamente")
    print(">> Auto-refresh cada 30 segundos esta habilitado por defecto")
    print()
    print(">> Caracteristicas del Dashboard:")
    print("   - Estado del sistema en tiempo real")
    print("   - Informacion de cuenta MT5")
    print("   - Posiciones abiertas")
    print("   - Estado del bot de trading")
    print("   - Estado de notificaciones Telegram")
    print("   - Estado de Ollama IA")
    print("   - Graficos de senales")
    print("   - Logs en tiempo real")
    print()
    print(">> URL del dashboard: http://localhost:8501")
    print(">> Presiona Ctrl+C para detener el dashboard")
    print("="*60)
    
    # Esperar un momento antes de abrir el navegador
    def open_browser():
        time.sleep(3)
        webbrowser.open('http://localhost:8501')
    
    # Abrir navegador en segundo plano
    import threading
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    # Lanzar Streamlit
    try:
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', 
            str(dashboard_file),
            '--server.port=8501',
            '--server.address=localhost',
            '--browser.gatherUsageStats=false'
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f">> Error ejecutando Streamlit: {e}")
        return False
    except KeyboardInterrupt:
        print("\n>> Dashboard detenido por el usuario")
        return True
    
    return True

if __name__ == "__main__":
    print("="*60)
    print("ALGOTRADER DASHBOARD LAUNCHER")
    print("   Panel de Control Web v3.0")
    print("="*60)
    print()
    
    success = launch_dashboard()
    
    if success:
        print("\n>> Dashboard cerrado exitosamente")
    else:
        print("\n>> Error al iniciar el dashboard")
        print("\n>> Soluciones posibles:")
        print("   1. Verifica que estes en el directorio correcto")
        print("   2. Ejecuta: pip install streamlit plotly")
        print("   3. Verifica que Python 3.7+ este instalado")
        
    input("\nPresiona Enter para salir...")