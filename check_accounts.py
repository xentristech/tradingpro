"""
Verificador de Cuentas MT5 - Analiza qué cuentas están activas
"""
import MetaTrader5 as mt5

def analyze_mt5_accounts():
    print("=" * 60)
    print(" ANALISIS DE CUENTAS MT5")
    print("=" * 60)
    
    if not mt5.initialize():
        print("[ERROR] Error inicializando MT5")
        return
    
    try:
        # Información de cuenta actual
        account = mt5.account_info()
        if account:
            print("CUENTA ACTUALMENTE CONECTADA:")
            print(f"  Numero: {account.login}")
            print(f"  Servidor: {account.server}")
            print(f"  Balance: ${account.balance:.2f}")
            print(f"  Equity: ${account.equity:.2f}")
            print(f"  Compania: {account.company}")
            print(f"  Moneda: {account.currency}")
            print()
            
            # Verificar posiciones
            positions = mt5.positions_get()
            print(f"POSICIONES EN CUENTA {account.login}:")
            if positions:
                total_profit = 0
                for i, pos in enumerate(positions, 1):
                    sl_status = "SL: OK" if pos.sl != 0 else "SL: NO"
                    tp_status = "TP: OK" if pos.tp != 0 else "TP: NO"
                    
                    print(f"  [{i}] #{pos.ticket}: {pos.symbol}")
                    print(f"      Tipo: {'BUY' if pos.type == 0 else 'SELL'}")
                    print(f"      Volumen: {pos.volume}")
                    print(f"      P&L: ${pos.profit:.2f}")
                    print(f"      Proteccion: {sl_status} | {tp_status}")
                    total_profit += pos.profit
                    print()
                
                print(f"TOTAL P&L: ${total_profit:.2f}")
            else:
                print("  No hay posiciones abiertas")
        else:
            print("[ERROR] Error obteniendo informacion de cuenta")
            
    except Exception as e:
        print(f"[ERROR] Error: {e}")
    finally:
        mt5.shutdown()
    
    print("=" * 60)

if __name__ == "__main__":
    analyze_mt5_accounts()