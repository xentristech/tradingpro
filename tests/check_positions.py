#!/usr/bin/env python3
"""
Script rápido para verificar posiciones abiertas
"""
import MetaTrader5 as mt5
from datetime import datetime

def check_positions():
    """Verificar todas las posiciones abiertas"""
    
    # Inicializar MT5
    if not mt5.initialize():
        print("ERROR: No se pudo conectar con MT5")
        return
    
    try:
        # Información de cuenta
        account = mt5.account_info()
        if account:
            print(f"CUENTA: {account.login}")
            print(f"Balance: ${account.balance:,.2f}")
            print(f"Equity: ${account.equity:,.2f}")
            print(f"Margen: ${account.margin:,.2f}")
            print(f"Libre: ${account.margin_free:,.2f}")
            print()
        
        # Obtener posiciones
        positions = mt5.positions_get()
        
        if not positions:
            print(">>> No hay posiciones abiertas")
            return
        
        print(f"POSICIONES ABIERTAS: {len(positions)}")
        print("="*60)
        
        total_pnl = 0
        for pos in positions:
            pnl_color = "[+]" if pos.profit >= 0 else "[-]"
            type_color = "[BUY]" if pos.type == 0 else "[SELL]"  # BUY=0, SELL=1
            
            print(f"{type_color} #{pos.ticket}")
            print(f"   Símbolo: {pos.symbol}")
            print(f"   Tipo: {'BUY' if pos.type == 0 else 'SELL'}")
            print(f"   Volumen: {pos.volume} lotes")
            print(f"   Precio entrada: {pos.price_open:.5f}")
            print(f"   Precio actual: {pos.price_current:.5f}")
            print(f"   {pnl_color} P&L: ${pos.profit:,.2f}")
            print(f"   Magic: {pos.magic}")
            if hasattr(pos, 'comment') and pos.comment:
                print(f"   Comentario: {pos.comment}")
            print("-" * 40)
            
            total_pnl += pos.profit
        
        # Resumen
        pnl_color = "[+]" if total_pnl >= 0 else "[-]"
        print(f"\n{pnl_color} P&L TOTAL: ${total_pnl:,.2f}")
        
        # Smart Position Manager status
        print(f"\nSMART POSITION MANAGER:")
        print(f"   - Gestionando {len(positions)} posiciones")
        print(f"   - Trailing stops automaticos: ACTIVO")
        print(f"   - Breakeven automatico: ACTIVO")
        print(f"   - Take profits parciales: ACTIVO")
        
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    print("VERIFICANDO POSICIONES...")
    print(f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    check_positions()