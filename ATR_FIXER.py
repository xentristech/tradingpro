#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Corrector de SL/TP usando ATR - Versión simple que funciona
"""

import MetaTrader5 as mt5
import time
import numpy as np
from datetime import datetime

def calculate_atr_simple(symbol, periods=14):
    """Calcula ATR usando datos de MT5"""
    try:
        # Obtener datos OHLC del timeframe H1
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, periods + 5)
        
        if rates is None or len(rates) < periods:
            print(f"[ERROR] No hay datos para {symbol}")
            return None
            
        # Calcular True Range
        tr_values = []
        for i in range(1, len(rates)):
            high = rates[i]['high']
            low = rates[i]['low']
            prev_close = rates[i-1]['close']
            
            tr1 = high - low
            tr2 = abs(high - prev_close)
            tr3 = abs(low - prev_close)
            
            tr_values.append(max(tr1, tr2, tr3))
        
        if len(tr_values) >= periods:
            atr = sum(tr_values[-periods:]) / periods
            print(f"[ATR] {symbol}: {atr:.5f}")
            return atr
            
    except Exception as e:
        print(f"[ERROR ATR] {symbol}: {e}")
    
    return None

def get_default_atr(symbol):
    """ATR por defecto según símbolo"""
    if "XAU" in symbol.upper() or "GOLD" in symbol.upper():
        return 30.0
    elif "BTC" in symbol.upper():
        return 2000.0
    elif "EUR" in symbol.upper():
        return 0.0015
    elif "GBP" in symbol.upper():
        return 0.0020
    else:
        return 0.001

def fix_position_with_atr(position):
    """Corrige una posición usando ATR"""
    symbol = position.symbol
    
    print(f"\n--- CORRIGIENDO POSICION #{position.ticket} ---")
    print(f"Simbolo: {symbol}")
    print(f"Tipo: {'BUY' if position.type == 0 else 'SELL'}")
    print(f"Volumen: {position.volume}")
    print(f"Precio: {position.price_current:.5f}")
    
    # Calcular ATR
    atr = calculate_atr_simple(symbol)
    if atr is None:
        atr = get_default_atr(symbol)
        print(f"[ATR DEFAULT] {symbol}: {atr:.5f}")
    
    # Multiplicadores
    sl_mult = 2.0  # 2x ATR para SL
    tp_mult = 3.0  # 3x ATR para TP
    
    price = position.price_current
    
    # Calcular SL y TP
    if position.type == 0:  # BUY
        sl_price = price - (atr * sl_mult)
        tp_price = price + (atr * tp_mult)
    else:  # SELL
        sl_price = price + (atr * sl_mult)
        tp_price = price - (atr * tp_mult)
    
    # Obtener info del símbolo para redondear
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info:
        sl_price = round(sl_price, symbol_info.digits)
        tp_price = round(tp_price, symbol_info.digits)
    
    print(f"ATR: {atr:.5f}")
    print(f"SL calculado: {sl_price:.5f} (distancia: {abs(price - sl_price):.5f})")
    print(f"TP calculado: {tp_price:.5f} (distancia: {abs(tp_price - price):.5f})")
    
    # Solo configurar lo que falta
    current_sl = position.sl if position.sl > 0 else sl_price
    current_tp = position.tp if position.tp > 0 else tp_price
    
    # Crear request
    request = {
        "action": mt5.TRADE_ACTION_SLTP,
        "symbol": symbol,
        "position": position.ticket,
        "sl": current_sl,
        "tp": current_tp,
        "magic": 234000,
        "comment": "ATR Fix"
    }
    
    print(f"Configurando SL: {current_sl:.5f} | TP: {current_tp:.5f}")
    
    # Enviar orden
    result = mt5.order_send(request)
    
    if result is None:
        print("[ERROR] order_send() falló")
        return False
    elif result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"[ERROR] Código: {result.retcode}")
        if hasattr(result, 'comment'):
            print(f"Comentario: {result.comment}")
        return False
    else:
        print("[SUCCESS] SL/TP configurados con ATR!")
        return True

def main():
    print("="*60)
    print("     CORRECTOR ATR - STOP LOSS Y TAKE PROFIT")
    print("="*60)
    print(f"Hora: {datetime.now()}")
    
    # Conectar MT5
    if not mt5.initialize():
        print("[ERROR] No se pudo conectar a MT5")
        return
    
    # Info cuenta
    account_info = mt5.account_info()
    if account_info:
        print(f"\nCuenta: {account_info.login}")
        print(f"Balance: ${account_info.balance:.2f}")
        print(f"Servidor: {account_info.server}")
    
    # Obtener posiciones
    positions = mt5.positions_get()
    
    if not positions:
        print("\n[INFO] No hay posiciones abiertas")
        print("Para probar: Abre una posición manual sin SL/TP")
    else:
        print(f"\n[FOUND] {len(positions)} posiciones encontradas")
        
        fixed_count = 0
        for pos in positions:
            needs_sl = pos.sl == 0
            needs_tp = pos.tp == 0
            
            if needs_sl or needs_tp:
                status = []
                if needs_sl: status.append("Sin SL")
                if needs_tp: status.append("Sin TP")
                
                print(f"\n[ALERTA] Posición {pos.ticket}: {' | '.join(status)}")
                
                if fix_position_with_atr(pos):
                    fixed_count += 1
            else:
                print(f"\n[OK] Posición {pos.ticket} ya tiene SL y TP")
        
        print(f"\n{'='*60}")
        print(f"RESULTADO: {fixed_count} posiciones corregidas con ATR")
        print("="*60)
    
    mt5.shutdown()
    print("\nPresiona Enter para continuar...")
    try:
        input()
    except:
        pass

if __name__ == "__main__":
    main()