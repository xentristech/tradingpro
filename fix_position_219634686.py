#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para corregir posición #219634686 sin SL/TP
"""
import MetaTrader5 as mt5
import os
from dotenv import load_dotenv

# Cargar configuración
load_dotenv('configs/.env')

def fix_position_219634686():
    """Corrige específicamente la posición #219634686"""
    
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
    ticket = 219634686
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
    
    # Calcular SL y TP basado en los valores recomendados
    entry_price = position.price_open  # 108949.48
    
    # Valores recomendados del detector
    sl = 105680.99560
    tp = 113852.20660
    
    print(f"Aplicando niveles recomendados:")
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
        "comment": "Fix SL/TP position 219634686"
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
    success = fix_position_219634686()
    
    if success:
        print("\\n=== VERIFICACION ===")
        # Verificar que se aplicó correctamente
        position = mt5.positions_get(ticket=219634686)
        if position:
            pos = position[0]
            print(f"SL final: {pos.sl}")
            print(f"TP final: {pos.tp}")
            print("Posicion protegida correctamente!")
    
    mt5.shutdown()