#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script simple para corregir posición sin SL/TP
"""
import MetaTrader5 as mt5
import os
from dotenv import load_dotenv

# Cargar configuración
load_dotenv('configs/.env')

def fix_position_219624334():
    """Corrige específicamente la posición #219624334"""
    
    # Conectar a MT5
    login = int(os.getenv("MT5_LOGIN"))
    password = os.getenv("MT5_PASSWORD")
    server = os.getenv("MT5_SERVER")
    
    if not mt5.initialize():
        print("Error: No se pudo inicializar MT5")
        return False
    
    # Login
    if not mt5.login(login, password, server):
        print(f"Error: No se pudo hacer login: {mt5.last_error()}")
        return False
    
    print("=== CORRECCION DE POSICION SIN SL/TP ===")
    print(f"Cuenta: {login}")
    print(f"Servidor: {server}")
    
    # Buscar la posición específica
    ticket = 219624334
    position = mt5.positions_get(ticket=ticket)
    
    if not position:
        print(f"Error: Posición #{ticket} no encontrada")
        return False
    
    position = position[0]  # Tomar la primera (y única)
    
    print(f"Posicion encontrada:")
    print(f"  Ticket: #{position.ticket}")
    print(f"  Simbolo: {position.symbol}")
    print(f"  Tipo: {'SELL' if position.type == 1 else 'BUY'}")
    print(f"  Volumen: {position.volume}")
    print(f"  Precio entrada: {position.price_open}")
    print(f"  SL actual: {position.sl}")
    print(f"  TP actual: {position.tp}")
    
    # Calcular SL y TP
    # Para SELL: SL arriba, TP abajo
    entry_price = position.price_open  # 108702.68
    
    # Usar ATR estimado de ~1600 pips para BTCUSD
    atr_pips = 1600
    
    if position.type == 1:  # SELL
        sl = entry_price + atr_pips  # 108702.68 + 1600 = 110302.68
        tp = entry_price - (atr_pips * 1.5)  # 108702.68 - 2400 = 106302.68
    else:  # BUY
        sl = entry_price - atr_pips
        tp = entry_price + (atr_pips * 1.5)
    
    print(f"Calculando niveles:")
    print(f"  Nuevo SL: {sl}")
    print(f"  Nuevo TP: {tp}")
    
    # Preparar solicitud de modificación
    request = {
        "action": mt5.TRADE_ACTION_SLTP,
        "symbol": position.symbol,
        "position": ticket,
        "sl": sl,
        "tp": tp,
        "magic": 20250817,
        "comment": "Fix SL/TP automatically"
    }
    
    print("\\nEnviando solicitud de modificacion...")
    result = mt5.order_send(request)
    
    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
        print("SUCCESS: Posicion corregida exitosamente!")
        print(f"  SL aplicado: {sl}")
        print(f"  TP aplicado: {tp}")
        return True
    else:
        print(f"ERROR: No se pudo corregir la posicion")
        if result:
            print(f"  Codigo: {result.retcode}")
            print(f"  Comentario: {result.comment}")
        else:
            print("  Sin respuesta del servidor")
        return False

if __name__ == "__main__":
    success = fix_position_219624334()
    
    if success:
        print("\\n=== VERIFICACION ===")
        # Verificar que se aplicó correctamente
        position = mt5.positions_get(ticket=219624334)
        if position:
            pos = position[0]
            print(f"SL final: {pos.sl}")
            print(f"TP final: {pos.tp}")
    
    mt5.shutdown()
    input("\\nPresiona Enter para salir...")