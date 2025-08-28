"""
INICIO TICK SYSTEM - Launcher completo para el sistema de análisis de ticks
=========================================================================

Sistema completo que integra:
- Datos tick reales de MetaTrader 5
- Datos de TwelveData para comparación
- Dashboard visual en tiempo real
- Análisis de spreads y movimientos
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def check_requirements():
    """Verificar requisitos del sistema"""
    print("VERIFICANDO REQUISITOS...")
    print("-" * 40)
    
    requirements = {
        'MetaTrader5': False,
        'twelvedata': False,
        'pandas': False,
        'numpy': False
    }
    
    # Verificar MetaTrader5
    try:
        import MetaTrader5 as mt5
        requirements['MetaTrader5'] = True
        print("OK MetaTrader5: Disponible")
    except ImportError:
        print("ERROR MetaTrader5: No instalado")
        print("   Instalar con: pip install MetaTrader5")
    
    # Verificar TwelveData
    try:
        from twelvedata import TDClient
        requirements['twelvedata'] = True
        print("OK TwelveData: Disponible")
    except ImportError:
        print("ERROR TwelveData: No instalado")
        print("   Instalar con: pip install twelvedata")
    
    # Verificar pandas
    try:
        import pandas as pd
        requirements['pandas'] = True
        print("OK Pandas: Disponible")
    except ImportError:
        print("ERROR Pandas: No instalado")
        print("   Instalar con: pip install pandas")
    
    # Verificar numpy
    try:
        import numpy as np
        requirements['numpy'] = True
        print("OK NumPy: Disponible")
    except ImportError:
        print("ERROR NumPy: No instalado")
        print("   Instalar con: pip install numpy")
    
    return requirements

def check_mt5_connection():
    """Verificar conexión con MetaTrader 5"""
    try:
        import MetaTrader5 as mt5
        
        print("\n[VERIFICANDO] Conexión MetaTrader 5...")
        
        if mt5.initialize():
            account_info = mt5.account_info()
            if account_info:
                print(f"OK MT5 CONECTADO")
                print(f"   Cuenta: {account_info.login}")
                print(f"   Broker: {account_info.company}")
                print(f"   Balance: ${account_info.balance:.2f}")
                return True
            else:
                print("AVISO MT5 conectado pero sin información de cuenta")
                return True  # Aún podemos usarlo
        else:
            print("ERROR No se puede conectar a MetaTrader 5")
            print("   Asegúrate de tener MT5 instalado y ejecutándose")
            return False
            
    except Exception as e:
        print(f"ERROR verificando MT5: {e}")
        return False

def check_twelvedata_api():
    """Verificar API de TwelveData"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('TWELVEDATA_API_KEY')
        
        if not api_key:
            print("AVISO TwelveData API key no encontrada")
            print("   Verifica el archivo .env")
            return False
        
        print(f"OK TwelveData API key encontrada: {api_key[:10]}...")
        return True
            
    except Exception as e:
        print(f"ERROR verificando TwelveData: {e}")
        return False

def main():
    print("="*60)
    print(" TICK SYSTEM LAUNCHER - AlgoTrader MVP v3")
    print("="*60)
    print("Sistema completo de análisis de ticks bid/ask:")
    print("  - Datos reales desde MetaTrader 5")
    print("  - Comparación con TwelveData")
    print("  - Dashboard visual en tiempo real")
    print("  - Análisis de spreads y movimientos")
    print("="*60)
    
    # Cambiar al directorio correcto
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    print(f"Directorio de trabajo: {script_dir}")
    
    # Verificar requisitos
    print("\n[PASO 1] Verificando requisitos...")
    requirements = check_requirements()
    
    # Verificar conexiones
    print("\n[PASO 2] Verificando conexiones...")
    mt5_ok = check_mt5_connection()
    td_ok = check_twelvedata_api()
    
    if not mt5_ok and not td_ok:
        print("\nERROR No hay fuentes de datos disponibles.")
        print("Configura al menos MetaTrader 5 o TwelveData API")
        return False
    
    # Mostrar configuración final
    print("\n" + "="*60)
    print(" CONFIGURACIÓN FINAL")
    print("="*60)
    print(f"MetaTrader 5: {'OK ACTIVO' if mt5_ok else 'ERROR NO DISPONIBLE'}")
    print(f"TwelveData:   {'OK ACTIVO' if td_ok else 'ERROR NO DISPONIBLE'}")
    
    if mt5_ok and td_ok:
        print("\nCONFIGURACIÓN ÓPTIMA: Ambas fuentes disponibles")
        print("   Podrás comparar datos MT5 vs TwelveData en tiempo real")
    elif mt5_ok:
        print("\nMODO MT5: Solo datos de MetaTrader 5")
        print("   Tendrás datos tick reales del broker")
    elif td_ok:
        print("\nMODO TWELVEDATA: Solo datos de TwelveData")
        print("   Tendrás datos de mercado generales")
    
    print("\n[PASO 3] Opciones de ejecución:")
    print("1. Dashboard de Ticks (MT5 + TwelveData) - Puerto 8508")
    print("2. Dashboard de Gráficos Dinámicos - Puerto 8507")
    print("3. Ambos dashboards")
    print("4. Análisis en consola")
    
    print(f"\n[INFO] Para usar el sistema:")
    print("python tick_dashboard.py          # Dashboard ticks (puerto 8508)")
    print("python dashboard_funcional.py     # Dashboard gráficos (puerto 8507)")
    print("python mt5_tick_analyzer.py       # Análisis en consola")
    
    print("\n[FINALIZADO] Sistema configurado correctamente")
    print("Usa los comandos de arriba para ejecutar cada componente")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\nSISTEMA COMPLETADO EXITOSAMENTE")
        else:
            print("\nSISTEMA TERMINÓ CON ERRORES")
            sys.exit(1)
    except Exception as e:
        print(f"\nERROR FATAL: {e}")
        sys.exit(1)