"""
MONITOR EN TIEMPO REAL DEL BOT
Muestra el estado actual del bot y las operaciones
"""
import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Configurar encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Cargar configuración
load_dotenv('configs/.env')

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_latest_logs():
    """Obtiene los logs más recientes"""
    logs_dir = Path("logs")
    if not logs_dir.exists():
        return None, None
    
    # Buscar archivos de log
    run_logs = list(logs_dir.glob("run_*.out.log"))
    pos_logs = list(logs_dir.glob("positions_*.out.log"))
    
    latest_run = max(run_logs, key=lambda p: p.stat().st_mtime) if run_logs else None
    latest_pos = max(pos_logs, key=lambda p: p.stat().st_mtime) if pos_logs else None
    
    return latest_run, latest_pos

def check_mt5_status():
    """Verifica el estado de MT5"""
    try:
        import MetaTrader5 as mt5
        
        if mt5.initialize():
            account = mt5.account_info()
            positions = mt5.positions_get()
            symbol = os.getenv("SYMBOL", "BTCUSDm")
            tick = mt5.symbol_info_tick(symbol)
            
            mt5.shutdown()
            
            return {
                "connected": True,
                "balance": account.balance if account else 0,
                "equity": account.equity if account else 0,
                "positions": len(positions) if positions else 0,
                "price": tick.bid if tick else 0
            }
    except:
        return {"connected": False}

def monitor_bot():
    """Monitor principal"""
    print("🔍 MONITOR DEL BOT - Actualizando cada 5 segundos")
    print("Presiona Ctrl+C para salir")
    print("="*60)
    
    while True:
        try:
            clear_screen()
            
            # Header
            print("╔" + "═"*58 + "╗")
            print("║" + "ALGO TRADER BOT - MONITOR EN TIEMPO REAL".center(58) + "║")
            print("╚" + "═"*58 + "╝")
            print(f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("-"*60)
            
            # Configuración
            print("\n📋 CONFIGURACIÓN:")
            print(f"   Símbolo: {os.getenv('SYMBOL')}")
            print(f"   Modo: {'🔴 LIVE' if os.getenv('LIVE_TRADING') == 'true' else '🟢 DEMO'}")
            print(f"   SL Default: ${os.getenv('DEF_SL_USD')}")
            print(f"   TP Default: ${os.getenv('DEF_TP_USD')}")
            
            # Estado MT5
            mt5_status = check_mt5_status()
            print("\n💹 METATRADER 5:")
            if mt5_status["connected"]:
                print(f"   Estado: ✅ Conectado")
                print(f"   Balance: ${mt5_status['balance']:.2f}")
                print(f"   Equity: ${mt5_status['equity']:.2f}")
                print(f"   Posiciones: {mt5_status['positions']}")
                print(f"   Precio {os.getenv('SYMBOL')}: {mt5_status['price']:.2f}")
            else:
                print(f"   Estado: ❌ Desconectado")
            
            # Procesos Python
            print("\n🖥️ PROCESOS:")
            import subprocess
            result = subprocess.run(
                ["powershell", "Get-Process", "python*", "-ErrorAction", "SilentlyContinue", 
                 "|", "Select-Object", "ProcessName,CPU", "|", "Format-Table", "-HideTableHeaders"],
                capture_output=True,
                text=True
            )
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                print(f"   Procesos Python activos: {len(lines)}")
            else:
                print("   No hay procesos Python activos")
            
            # Logs
            run_log, pos_log = get_latest_logs()
            print("\n📄 ÚLTIMOS LOGS:")
            if run_log:
                print(f"   Run: {run_log.name} ({run_log.stat().st_size / 1024:.1f} KB)")
                # Mostrar últimas líneas
                try:
                    with open(run_log, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        if lines:
                            print("   Últimas entradas:")
                            for line in lines[-3:]:
                                print(f"     {line.strip()[:80]}")
                except:
                    pass
            
            if pos_log:
                print(f"   Positions: {pos_log.name} ({pos_log.stat().st_size / 1024:.1f} KB)")
            
            # Esperar
            print("\n" + "-"*60)
            print("Actualizando en 5 segundos...")
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("\n\n⛔ Monitor detenido")
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor_bot()
