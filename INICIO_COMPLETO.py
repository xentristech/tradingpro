"""
INICIO COMPLETO - Script que ejecuta todo el sistema dinámico
===========================================================
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def main():
    print("SISTEMA DINAMICO COMPLETO - AlgoTrader MVP v3")
    print("="*50)
    
    # Cambiar al directorio correcto
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print(f"Directorio: {script_dir}")
    
    # PASO 1: Generar gráficos de ejemplo
    print("\n[PASO 1] Generando graficos de ejemplo...")
    try:
        result = subprocess.run([sys.executable, "test_visual_charts.py"], 
                               capture_output=True, text=True, timeout=60)
        if result.returncode == 0:
            print("[OK] Graficos generados correctamente")
        else:
            print(f"[ERROR] Error generando graficos: {result.stderr}")
            return False
    except Exception as e:
        print(f"[ERROR] Exception generando graficos: {e}")
        return False
    
    # Verificar que se crearon los gráficos
    charts_dir = Path("advanced_charts")
    if charts_dir.exists():
        chart_files = list(charts_dir.glob("*.png"))
        live_charts = [f for f in chart_files if "_live" in f.name]
        print(f"[INFO] Graficos encontrados: {len(chart_files)}")
        print(f"[INFO] Graficos LIVE: {len(live_charts)}")
        
        if len(chart_files) == 0:
            print("[ERROR] No se crearon graficos")
            return False
    else:
        print("[ERROR] Directorio advanced_charts no existe")
        return False
    
    # PASO 2: Mostrar instrucciones
    print("\n" + "="*50)
    print(" SISTEMA LISTO PARA USAR")
    print("="*50)
    print("\nPara ver los graficos dinamicos:")
    print("1. Ejecuta en otra ventana:")
    print("   python dashboard_funcional.py")
    print("\n2. Abre en tu navegador:")
    print("   http://localhost:8507")
    print("\n3. Veras los graficos con indicadores LIVE")
    
    # PASO 3: Opción de iniciar dashboard automáticamente
    print("\n¿Quieres iniciar el dashboard ahora? (s/n): ", end="")
    
    try:
        respuesta = input().lower().strip()
        if respuesta in ['s', 'si', 'y', 'yes']:
            print("\n[INICIANDO] Dashboard...")
            print("URL: http://localhost:8507")
            print("Presiona Ctrl+C para detener")
            print("="*50)
            
            # Ejecutar dashboard
            subprocess.run([sys.executable, "dashboard_funcional.py"])
        else:
            print("\n[INFO] Dashboard no iniciado automaticamente")
            print("Ejecuta manualmente: python dashboard_funcional.py")
    
    except KeyboardInterrupt:
        print("\n[DETENIDO] Por usuario")
    
    print("\n[FINALIZADO] Sistema dinamico configurado correctamente")
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n[EXITO] Sistema dinamico funcional")
        else:
            print("\n[ERROR] Problemas configurando sistema")
            sys.exit(1)
    except Exception as e:
        print(f"\n[FATAL] Error: {e}")
        sys.exit(1)