#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verificar posiciones abiertas en MT5 - Versión simplificada
"""
import sys
import os

# Instalar librerías si no están
try:
    import MetaTrader5 as mt5
except:
    print("Instalando MetaTrader5...")
    os.system("pip install MetaTrader5")
    import MetaTrader5 as mt5

from datetime import datetime

def main():
    print("="*60)
    print("VERIFICACIÓN DE POSICIONES MT5")
    print("="*60)
    print(f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Conectar a MT5 (ya está abierto)
    print("Conectando a MT5...")
    if not mt5.initialize():
        print(f"ERROR: No se pudo conectar - {mt5.last_error()}")
        return
    
    print("✅ Conectado exitosamente")
    print()
    
    # Obtener información de la cuenta
    account = mt5.account_info()
    if account:
        print("INFORMACIÓN DE LA CUENTA:")
        print(f"  Número: {account.login}")
        print(f"  Servidor: {account.server}")
        print(f"  Balance: ${account.balance:.2f}")
        print(f"  Equity: ${account.equity:.2f}")
        print(f"  Margen libre: ${account.margin_free:.2f}")
        print(f"  Profit actual: ${account.profit:.2f}")
        print()
    
    # Obtener posiciones
    positions = mt5.positions_get()
    
    if not positions or len(positions) == 0:
        print("❌ NO HAY POSICIONES ABIERTAS")
        
        # Verificar historial reciente
        from datetime import timedelta
        desde = datetime.now() - timedelta(days=7)
        deals = mt5.history_deals_get(desde, datetime.now())
        if deals:
            print(f"\nHistorial última semana: {len(deals)} transacciones")
            
    else:
        print(f"✅ POSICIONES ABIERTAS: {len(positions)}")
        print("-"*60)
        
        total_profit = 0
        for i, pos in enumerate(positions, 1):
            print(f"\n[{i}] Posición #{pos.ticket}")
            print(f"  Símbolo: {pos.symbol}")
            print(f"  Tipo: {'COMPRA' if pos.type == 0 else 'VENTA'}")
            print(f"  Volumen: {pos.volume} lotes")
            print(f"  Precio apertura: {pos.price_open:.5f}")
            
            # Obtener precio actual
            tick = mt5.symbol_info_tick(pos.symbol)
            if tick:
                current = tick.bid if pos.type == 0 else tick.ask
                print(f"  Precio actual: {current:.5f}")
                
                # Calcular pips
                if 'JPY' in pos.symbol:
                    pip_value = 0.01
                elif pos.symbol in ['XAUUSD', 'GOLD', 'XAUUSDm']:
                    pip_value = 0.1
                elif pos.symbol.startswith('BTC'):
                    pip_value = 1.0
                else:
                    pip_value = 0.0001
                
                if pos.type == 0:  # BUY
                    pips = (current - pos.price_open) / pip_value
                else:  # SELL
                    pips = (pos.price_open - current) / pip_value
                
                print(f"  Pips: {pips:.1f}")
            
            print(f"  Stop Loss: {pos.sl:.5f}" if pos.sl > 0 else "  Stop Loss: No establecido")
            print(f"  Take Profit: {pos.tp:.5f}" if pos.tp > 0 else "  Take Profit: No establecido")
            print(f"  Profit: ${pos.profit:.2f}")
            print(f"  Comentario: {pos.comment}")
            print(f"  Tiempo abierto: {datetime.fromtimestamp(pos.time)}")
            
            total_profit += pos.profit
        
        print("-"*60)
        print(f"PROFIT TOTAL: ${total_profit:.2f}")
    
    # Verificar símbolos disponibles
    print("\nSÍMBOLOS PRINCIPALES DISPONIBLES:")
    symbols = ['BTCUSDm', 'XAUUSDm', 'EURUSD', 'GBPUSD']
    for symbol in symbols:
        info = mt5.symbol_info(symbol)
        if info and info.visible:
            tick = mt5.symbol_info_tick(symbol)
            if tick:
                print(f"  {symbol}: ${tick.bid:.5f}")
    
    # Cerrar conexión
    mt5.shutdown()
    print()
    print("="*60)
    print("Verificación completada")
    print("="*60)

if __name__ == "__main__":
    main()
