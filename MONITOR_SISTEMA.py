#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MONITOR DE SISTEMA DE SEÑALES - ALGO TRADER V3
==============================================
Monitorea el estado del sistema y consumo de API en tiempo real
"""

import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path
from colorama import init, Fore, Back, Style

# Inicializar colorama para Windows
init(autoreset=True)

# Añadir path del proyecto
sys.path.insert(0, str(Path(__file__).parent))

try:
    from src.data.twelvedata_client_optimized import TwelveDataClientOptimized
    CLIENT_AVAILABLE = True
except ImportError:
    CLIENT_AVAILABLE = False
    
def clear_screen():
    """Limpia la pantalla"""
    os.system('cls' if os.name == 'nt' else 'clear')
    
def print_header():
    """Imprime el header del monitor"""
    print(Fore.CYAN + "="*60)
    print(Fore.CYAN + " "*15 + "MONITOR DE SISTEMA - ALGO TRADER V3")
    print(Fore.CYAN + "="*60)
    print()
    
def check_api_key():
    """Verifica si la API key está configurada"""
    api_key = os.getenv('TWELVEDATA_API_KEY')
    
    if not api_key:
        return False, "NO CONFIGURADA"
    elif api_key == '23d17ce5b7044ad5aef9766770a6252b':
        return False, "USANDO KEY HARDCODEADA (INSEGURO)"
    else:
        return True, f"Configurada ({api_key[:8]}...)"
        
def check_client_status():
    """Verifica el estado del cliente TwelveData"""
    if not CLIENT_AVAILABLE:
        return {
            'status': 'ERROR',
            'message': 'Cliente no disponible',
            'api_calls': 0,
            'remaining': 0
        }
        
    try:
        client = TwelveDataClientOptimized(use_cache=True)
        status = client.get_status()
        
        return {
            'status': 'OK',
            'message': 'Cliente funcionando',
            'api_calls': status['api_calls_used'],
            'remaining': status['api_calls_remaining'],
            'cache_enabled': status['cache_enabled'],
            'cache_size': status['memory_cache_size']
        }
    except Exception as e:
        return {
            'status': 'ERROR',
            'message': str(e),
            'api_calls': 0,
            'remaining': 0
        }
        
def check_processes():
    """Verifica qué procesos están ejecutándose"""
    import psutil
    
    processes = {
        'telegram_notifier.py': False,
        'realtime_signal_generator.py': False,
        'twelvedata_client': False,
        'MetaTrader': False
    }
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = ' '.join(proc.info['cmdline'] or [])
            for process_name in processes.keys():
                if process_name in cmdline or process_name in proc.info['name']:
                    processes[process_name] = True
        except:
            pass
            
    return processes
    
def calculate_projections(api_calls, remaining):
    """Calcula proyecciones de uso"""
    if api_calls == 0:
        return {
            'time_to_limit': 'N/A',
            'can_run_hours': 'N/A',
            'optimal_interval': 5
        }
        
    # Asumiendo 8 llamadas por ciclo con optimización
    calls_per_cycle = 8
    
    # Calcular tiempo hasta límite
    cycles_remaining = remaining // calls_per_cycle
    
    # Con intervalo de 5 minutos
    hours_at_5min = (cycles_remaining * 5) / 60
    
    # Intervalo óptimo para 24 horas
    if remaining > 0:
        optimal_interval = (24 * 60) / (remaining / calls_per_cycle)
    else:
        optimal_interval = 60
        
    return {
        'time_to_limit': f"{hours_at_5min:.1f} horas",
        'cycles_remaining': cycles_remaining,
        'optimal_interval': min(60, max(5, int(optimal_interval)))
    }
    
def print_status_box(title, status, color=Fore.WHITE):
    """Imprime una caja de estado"""
    print(color + "┌" + "─"*40 + "┐")
    print(color + f"│ {title:<38} │")
    print(color + "├" + "─"*40 + "┤")
    
    for key, value in status.items():
        if isinstance(value, bool):
            icon = "✅" if value else "❌"
            print(color + f"│ {key:<20}: {icon:<16} │")
        else:
            print(color + f"│ {key:<20}: {str(value):<16} │")
            
    print(color + "└" + "─"*40 + "┘")
    print()
    
def monitor_loop():
    """Loop principal del monitor"""
    while True:
        clear_screen()
        print_header()
        
        # Timestamp
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 1. Verificar API Key
        api_ok, api_msg = check_api_key()
        api_color = Fore.GREEN if api_ok else Fore.RED
        
        print(api_color + "API KEY STATUS:")
        print(api_color + f"  {api_msg}")
        print()
        
        # 2. Estado del cliente
        client_status = check_client_status()
        
        if client_status['status'] == 'OK':
            print(Fore.GREEN + "CLIENTE TWELVEDATA:")
            print(f"  📞 Llamadas usadas: {client_status['api_calls']}/800")
            print(f"  ⚡ Llamadas restantes: {client_status['remaining']}")
            
            if 'cache_size' in client_status:
                print(f"  💾 Items en caché: {client_status['cache_size']}")
                
            # Proyecciones
            projections = calculate_projections(
                client_status['api_calls'],
                client_status['remaining']
            )
            
            print()
            print(Fore.YELLOW + "PROYECCIONES:")
            print(f"  ⏱️ Tiempo restante: {projections['time_to_limit']}")
            print(f"  🔄 Ciclos posibles: {projections['cycles_remaining']}")
            print(f"  ⚙️ Intervalo óptimo: {projections['optimal_interval']} minutos")
            
            # Advertencias
            if client_status['remaining'] < 100:
                print()
                print(Back.RED + Fore.WHITE + " ⚠️ ADVERTENCIA: Quedan pocas llamadas API! ")
                
        else:
            print(Fore.RED + "CLIENTE TWELVEDATA:")
            print(f"  ❌ Error: {client_status['message']}")
            
        # 3. Procesos activos
        print()
        processes = check_processes()
        
        print(Fore.CYAN + "PROCESOS DEL SISTEMA:")
        for process, running in processes.items():
            icon = "🟢" if running else "🔴"
            status_text = "Ejecutándose" if running else "Detenido"
            print(f"  {icon} {process:<30} {status_text}")
            
        # 4. Recomendaciones
        print()
        print(Fore.MAGENTA + "RECOMENDACIONES:")
        
        if not api_ok:
            print("  1. ⚠️ Configura tu API key en .env")
            print("     Ejecuta: ACTUALIZAR_SEGURIDAD_URGENTE.bat")
            
        if client_status['remaining'] < 200:
            print("  2. ⚠️ Aumenta el intervalo entre análisis")
            print(f"     Recomendado: {projections['optimal_interval']} minutos")
            
        if not processes['realtime_signal_generator.py']:
            print("  3. ℹ️ El generador de señales no está activo")
            print("     Ejecuta: EJECUTAR_TODO_PRO.bat")
            
        # 5. Comandos disponibles
        print()
        print(Fore.WHITE + "="*60)
        print("COMANDOS:")
        print("  [Q] Salir | [C] Limpiar caché | [R] Refrescar")
        print("="*60)
        
        # Esperar input o refrescar
        import select
        import msvcrt
        
        # Check for input (Windows)
        if msvcrt.kbhit():
            key = msvcrt.getch().decode('utf-8').lower()
            
            if key == 'q':
                print("\n👋 Saliendo del monitor...")
                break
            elif key == 'c':
                if CLIENT_AVAILABLE:
                    try:
                        client = TwelveDataClientOptimized()
                        client.clear_cache()
                        print("\n✅ Caché limpiado")
                        time.sleep(2)
                    except:
                        print("\n❌ Error limpiando caché")
                        time.sleep(2)
            elif key == 'r':
                continue
                
        # Refrescar cada 5 segundos
        time.sleep(5)

def main():
    print("""
╔════════════════════════════════════════════════════════════╗
║        MONITOR DE SISTEMA - ALGO TRADER V3                ║
║                                                            ║
║  Monitorea el estado del sistema y consumo de API         ║
║  Presiona Q para salir, R para refrescar                  ║
╚════════════════════════════════════════════════════════════╝
    """)
    
    time.sleep(2)
    
    try:
        monitor_loop()
    except KeyboardInterrupt:
        print("\n\n👋 Monitor detenido")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        
if __name__ == "__main__":
    # Instalar dependencias si no están
    try:
        import colorama
        import psutil
    except ImportError:
        print("Instalando dependencias necesarias...")
        os.system("pip install colorama psutil")
        print("Por favor, ejecuta el script nuevamente")
        sys.exit(1)
        
    main()
