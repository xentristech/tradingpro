"""
Actualizar LIVE - Script para actualizar gráficos cada 30 segundos
===============================================================
"""

import time
import subprocess
import sys
from datetime import datetime
from pathlib import Path

def actualizar_graficos():
    """Actualizar todos los gráficos LIVE"""
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Actualizando graficos LIVE...")
        
        result = subprocess.run([sys.executable, "test_visual_charts.py"], 
                               capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Graficos actualizados correctamente")
            
            # Contar archivos LIVE
            charts_dir = Path("advanced_charts")
            if charts_dir.exists():
                live_charts = list(charts_dir.glob("*_live.png"))
                print(f"[INFO] {len(live_charts)} graficos LIVE actualizados")
            
            return True
        else:
            print(f"[ERROR] Error actualizando: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Exception: {e}")
        return False

def main():
    print("ACTUALIZADOR DE GRAFICOS LIVE")
    print("="*40)
    print("Este script actualiza los graficos cada 30 segundos")
    print("Mantén el dashboard abierto en: http://localhost:8507")
    print("Veras como los graficos cambian automaticamente")
    print("="*40)
    
    contador = 1
    
    try:
        while True:
            print(f"\n[CICLO {contador}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Actualizar gráficos
            success = actualizar_graficos()
            
            if success:
                print(f"[OK] Ciclo {contador} completado")
                print("[INFO] Revisa el dashboard para ver los cambios")
                print(f"[INFO] Proximo update en 30 segundos...")
            else:
                print(f"[ERROR] Error en ciclo {contador}")
            
            contador += 1
            
            # Esperar 30 segundos
            time.sleep(30)
            
    except KeyboardInterrupt:
        print(f"\n[DETENIDO] Sistema detenido por usuario")
        print(f"Total ciclos ejecutados: {contador - 1}")
    except Exception as e:
        print(f"\n[ERROR FATAL] {e}")

if __name__ == "__main__":
    # Verificar que el directorio existe
    script_dir = Path(__file__).parent
    import os
    os.chdir(script_dir)
    
    main()