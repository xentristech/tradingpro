"""
Control de Pausa para el Sistema de Trading
Permite pausar y reanudar el monitoreo
"""
import os
import signal
import psutil
import time
from datetime import datetime

def find_trading_processes():
    """Encuentra procesos relacionados con el trading bot"""
    trading_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            # Buscar procesos Python con palabras clave del bot
            if proc.info['name'] == 'python.exe':
                cmdline = ' '.join(proc.info['cmdline'] or [])
                keywords = ['multi_account', 'trading_bot', 'monitor', 'dashboard']
                
                if any(keyword in cmdline.lower() for keyword in keywords):
                    trading_processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cmd': cmdline[:100]  # Primeros 100 caracteres
                    })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    return trading_processes

def pause_processes(processes):
    """Pausa los procesos especificados"""
    paused = []
    
    for proc_info in processes:
        try:
            proc = psutil.Process(proc_info['pid'])
            proc.suspend()
            paused.append(proc_info['pid'])
            print(f"⏸️ Pausado PID {proc_info['pid']}: {proc_info['cmd'][:50]}...")
        except Exception as e:
            print(f"❌ No se pudo pausar PID {proc_info['pid']}: {e}")
    
    return paused

def resume_processes(pids):
    """Reanuda los procesos pausados"""
    for pid in pids:
        try:
            proc = psutil.Process(pid)
            proc.resume()
            print(f"▶️ Reanudado PID {pid}")
        except Exception as e:
            print(f"❌ No se pudo reanudar PID {pid}: {e}")

def main():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║           CONTROL DE PAUSA - SISTEMA DE TRADING           ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    while True:
        print("\n" + "="*60)
        print("OPCIONES:")
        print("="*60)
        print("1. Ver procesos activos del bot")
        print("2. Pausar todos los procesos")
        print("3. Reanudar procesos pausados")
        print("4. Detener todos los procesos")
        print("5. Salir")
        print("="*60)
        
        choice = input("\nSelecciona una opción (1-5): ").strip()
        
        if choice == '1':
            # Ver procesos
            print("\n🔍 Buscando procesos del bot...")
            processes = find_trading_processes()
            
            if processes:
                print(f"\n📊 Procesos encontrados: {len(processes)}")
                for proc in processes:
                    print(f"   PID {proc['pid']}: {proc['cmd'][:80]}...")
            else:
                print("❌ No se encontraron procesos del bot activos")
        
        elif choice == '2':
            # Pausar
            print("\n⏸️ Pausando procesos...")
            processes = find_trading_processes()
            
            if processes:
                paused_pids = pause_processes(processes)
                if paused_pids:
                    print(f"\n✅ {len(paused_pids)} procesos pausados")
                    print("Los procesos están suspendidos. Usa opción 3 para reanudar.")
                    
                    # Guardar PIDs pausados
                    with open('paused_pids.txt', 'w') as f:
                        for pid in paused_pids:
                            f.write(f"{pid}\n")
            else:
                print("❌ No hay procesos para pausar")
        
        elif choice == '3':
            # Reanudar
            print("\n▶️ Reanudando procesos...")
            
            try:
                with open('paused_pids.txt', 'r') as f:
                    paused_pids = [int(line.strip()) for line in f]
                
                if paused_pids:
                    resume_processes(paused_pids)
                    print(f"\n✅ {len(paused_pids)} procesos reanudados")
                    os.remove('paused_pids.txt')
                else:
                    print("❌ No hay procesos pausados")
            except FileNotFoundError:
                print("❌ No hay procesos pausados guardados")
        
        elif choice == '4':
            # Detener
            confirm = input("\n⚠️ ¿Seguro que quieres detener todos los procesos? (s/n): ")
            
            if confirm.lower() == 's':
                print("\n🛑 Deteniendo procesos...")
                processes = find_trading_processes()
                
                terminated = 0
                for proc_info in processes:
                    try:
                        proc = psutil.Process(proc_info['pid'])
                        proc.terminate()
                        terminated += 1
                        print(f"❌ Terminado PID {proc_info['pid']}")
                    except:
                        pass
                
                if terminated > 0:
                    print(f"\n✅ {terminated} procesos detenidos")
                else:
                    print("❌ No había procesos para detener")
        
        elif choice == '5':
            print("\n👋 Saliendo del control de pausa...")
            break
        
        else:
            print("❌ Opción no válida")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Control de pausa cerrado")
