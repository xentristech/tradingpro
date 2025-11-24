#!/usr/bin/env python
"""
Monitor en Tiempo Real - Quantum Trading System
"""
import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv
import MetaTrader5 as mt5

load_dotenv()

def monitor_system():
    """Monitor en tiempo real del sistema"""
    
    os.system('cls' if os.name == 'nt' else 'clear')
    
    while True:
        try:
            os.system('cls' if os.name == 'nt' else 'clear')
            
            print("=" * 70)
            print("QUANTUM TRADING SYSTEM - MONITOR EN TIEMPO REAL")
            print("=" * 70)
            print(f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print()
            
            # Verificar MT5
            print("=" * 70)
            print("ESTADO MT5")
            print("=" * 70)
            
            if not mt5.initialize(
                login=int(os.getenv('MT5_LOGIN')),
                password=os.getenv('MT5_PASSWORD'),
                server=os.getenv('MT5_SERVER')
            ):
                print("ERROR: MT5 no conectado")
                print(f"Error: {mt5.last_error()}")
                print("\nREVISAR:")
                print("  1. MT5 esta abierto?")
                print("  2. Credenciales correctas en .env?")
                print("  3. AutoTrading habilitado?")
            else:
                print("CONECTADO")
                
                # Info de cuenta
                account = mt5.account_info()
                if account:
                    print(f"\nCuenta: {account.login}")
                    print(f"Servidor: {account.server}")
                    print(f"Balance: ${account.balance:.2f}")
                    print(f"Equity: ${account.equity:.2f}")
                    print(f"Profit: ${account.profit:.2f}")
                    print(f"Margen Libre: ${account.margin_free:.2f}")
                
                # Info terminal
                terminal = mt5.terminal_info()
                if terminal:
                    print(f"\nAutoTrading: {'SI' if terminal.trade_allowed else 'NO'}")
                    print(f"Conectado al servidor: {'SI' if terminal.connected else 'NO'}")
                
                # Posiciones abiertas
                print("\n" + "=" * 70)
                print("POSICIONES ABIERTAS")
                print("=" * 70)
                
                positions = mt5.positions_get()
                if positions:
                    print(f"Total: {len(positions)}")
                    print()
                    for pos in positions:
                        print(f"Ticket #{pos.ticket}")
                        print(f"  Symbol: {pos.symbol}")
                        print(f"  Type: {'BUY' if pos.type == 0 else 'SELL'}")
                        print(f"  Volume: {pos.volume}")
                        print(f"  Open Price: {pos.price_open}")
                        print(f"  Current Price: {pos.price_current}")
                        print(f"  SL: {pos.sl}")
                        print(f"  TP: {pos.tp}")
                        print(f"  Profit: ${pos.profit:.2f}")
                        print(f"  Comment: {pos.comment}")
                        print()
                else:
                    print("No hay posiciones abiertas")
                
                mt5.shutdown()
            
            # Leer últimas líneas del log
            print("\n" + "=" * 70)
            print("ULTIMAS LINEAS DEL LOG (10)")
            print("=" * 70)
            
            log_file = "logs/quantum_trading_system.log"
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    for line in lines[-10:]:
                        print(line.strip())
            else:
                print("Log no encontrado")
            
            print("\n" + "=" * 70)
            print("Actualizando cada 10 segundos... (Ctrl+C para salir)")
            print("=" * 70)
            
            time.sleep(10)
            
        except KeyboardInterrupt:
            print("\n\nMonitor detenido")
            break
        except Exception as e:
            print(f"\nError: {e}")
            time.sleep(10)

if __name__ == "__main__":
    monitor_system()
