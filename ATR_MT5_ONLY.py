#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Corrector de SL/TP usando SOLO datos de MT5 - Sin APIs externas
"""

import MetaTrader5 as mt5
from datetime import datetime

def calculate_atr_from_mt5(symbol, periods=14):
    """Calcula ATR usando EXCLUSIVAMENTE datos OHLC de MT5"""
    
    print(f"[ATR] Calculando para {symbol}...")
    
    # Obtener datos de diferentes timeframes hasta encontrar suficientes
    timeframes_to_try = [
        (mt5.TIMEFRAME_H1, "H1"),
        (mt5.TIMEFRAME_M30, "M30"),
        (mt5.TIMEFRAME_M15, "M15"),
        (mt5.TIMEFRAME_H4, "H4")
    ]
    
    for tf, tf_name in timeframes_to_try:
        try:
            # Obtener más barras de las necesarias por seguridad
            rates = mt5.copy_rates_from_pos(symbol, tf, 0, periods + 20)
            
            if rates is None or len(rates) < periods + 1:
                print(f"[ATR] {tf_name}: Datos insuficientes ({len(rates) if rates else 0} barras)")
                continue
            
            print(f"[ATR] {tf_name}: {len(rates)} barras obtenidas")
            
            # Calcular True Range
            true_ranges = []
            
            for i in range(1, len(rates)):
                high = rates[i]['high']
                low = rates[i]['low']
                prev_close = rates[i-1]['close']
                
                # True Range = max(H-L, |H-Cprev|, |L-Cprev|)
                tr1 = high - low
                tr2 = abs(high - prev_close)
                tr3 = abs(low - prev_close)
                
                tr = max(tr1, tr2, tr3)
                true_ranges.append(tr)
            
            if len(true_ranges) >= periods:
                # ATR = promedio de los últimos N True Ranges
                atr = sum(true_ranges[-periods:]) / periods
                print(f"[ATR] {symbol}: {atr:.5f} (TF: {tf_name}, {periods} períodos)")
                return atr
                
        except Exception as e:
            print(f"[ERROR] {tf_name}: {e}")
            continue
    
    print(f"[ATR] No se pudo calcular para {symbol}")
    return None

def get_atr_value(symbol):
    """Obtiene ATR con múltiples métodos usando solo MT5"""
    
    # Método 1: Calcular ATR de barras OHLC
    atr = calculate_atr_from_mt5(symbol, 14)
    if atr is not None:
        return atr
    
    # Método 2: Usar datos de tick para estimar volatilidad
    try:
        print(f"[TICKS] Intentando con tick data para {symbol}...")
        ticks = mt5.copy_ticks_from_pos(symbol, 0, 200, mt5.COPY_TICKS_ALL)
        
        if ticks is not None and len(ticks) > 50:
            # Usar bid prices para calcular volatilidad
            prices = [t.bid for t in ticks if t.bid > 0]
            
            if len(prices) > 10:
                # Calcular diferencias absolutas
                changes = []
                for i in range(1, len(prices)):
                    change = abs(prices[i] - prices[i-1])
                    changes.append(change)
                
                if changes:
                    avg_change = sum(changes) / len(changes)
                    # Escalar para aproximar ATR diario
                    estimated_atr = avg_change * 50  # Factor empírico
                    print(f"[TICKS] {symbol}: {estimated_atr:.5f} (de {len(ticks)} ticks)")
                    return estimated_atr
                    
    except Exception as e:
        print(f"[ERROR TICKS] {symbol}: {e}")
    
    # Método 3: Valores por defecto basados en el símbolo
    atr_defaults = {
        'XAU': 20.0,    # Oro
        'GOLD': 20.0,
        'BTC': 2000.0,  # Bitcoin
        'EUR': 0.0010,  # EUR/USD
        'GBP': 0.0012,  # GBP/USD
        'USD': 0.8,     # USD/JPY típico
        'JPY': 0.8
    }
    
    for key, default_atr in atr_defaults.items():
        if key.upper() in symbol.upper():
            print(f"[DEFAULT] {symbol}: {default_atr:.5f}")
            return default_atr
    
    # Último recurso
    fallback_atr = 0.001
    print(f"[FALLBACK] {symbol}: {fallback_atr:.5f}")
    return fallback_atr

def main():
    print("=" * 70)
    print("     CORRECTOR ATR - SOLO METATRADER 5")
    print("=" * 70)
    print("Sin APIs externas - Solo datos locales MT5")
    print(f"Fecha: {datetime.now()}\n")
    
    # Conectar MT5
    if not mt5.initialize():
        print("[ERROR] No se pudo conectar a MT5")
        return
    
    # Info de cuenta
    account = mt5.account_info()
    if account:
        print(f"Cuenta: {account.login}")
        print(f"Balance: ${account.balance:.2f}")
        print(f"Equity: ${account.equity:.2f}")
        print(f"Servidor: {account.server}\n")
    
    # Obtener posiciones
    positions = mt5.positions_get()
    
    if not positions:
        print("[INFO] No hay posiciones abiertas")
        print("Abre una posición manual sin SL/TP para probar")
    else:
        print(f"[SCAN] {len(positions)} posiciones encontradas\n")
        
        corrected = 0
        
        for i, pos in enumerate(positions, 1):
            print(f"--- POSICION {i} ---")
            print(f"Ticket: #{pos.ticket}")
            print(f"Símbolo: {pos.symbol}")
            print(f"Tipo: {'BUY' if pos.type == 0 else 'SELL'}")
            print(f"Volumen: {pos.volume} lotes")
            print(f"Precio actual: {pos.price_current:.5f}")
            print(f"P&L: ${pos.profit:.2f}")
            
            # Verificar SL/TP
            has_sl = pos.sl > 0
            has_tp = pos.tp > 0
            
            if has_sl and has_tp:
                print(f"[OK] SL: {pos.sl:.5f} | TP: {pos.tp:.5f}")
                continue
            
            # Necesita corrección
            missing = []
            if not has_sl: missing.append("SL")
            if not has_tp: missing.append("TP")
            print(f"[ALERTA] Falta: {', '.join(missing)}")
            
            # Calcular ATR
            atr = get_atr_value(pos.symbol)
            
            # Configurar niveles
            price = pos.price_current
            sl_distance = atr * 2.0  # 2 × ATR
            tp_distance = atr * 3.0  # 3 × ATR
            
            if pos.type == 0:  # BUY
                new_sl = price - sl_distance
                new_tp = price + tp_distance
            else:  # SELL
                new_sl = price + sl_distance
                new_tp = price - tp_distance
            
            # Usar decimales del símbolo
            symbol_info = mt5.symbol_info(pos.symbol)
            if symbol_info:
                new_sl = round(new_sl, symbol_info.digits)
                new_tp = round(new_tp, symbol_info.digits)
            
            # Solo modificar lo que falta
            final_sl = new_sl if not has_sl else pos.sl
            final_tp = new_tp if not has_tp else pos.tp
            
            print(f"ATR calculado: {atr:.5f}")
            print(f"Nuevo SL: {final_sl:.5f}")
            print(f"Nuevo TP: {final_tp:.5f}")
            
            # Enviar modificación
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": pos.symbol,
                "position": pos.ticket,
                "sl": final_sl,
                "tp": final_tp,
                "magic": 234000,
                "comment": "ATR MT5"
            }
            
            result = mt5.order_send(request)
            
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                print("[SUCCESS] Posición corregida con ATR!")
                corrected += 1
            else:
                error_code = result.retcode if result else "Sin respuesta"
                print(f"[ERROR] {error_code}")
            
            print()
        
        print("=" * 70)
        print(f"RESUMEN: {corrected} de {len(positions)} posiciones corregidas")
        print("=" * 70)
    
    mt5.shutdown()

if __name__ == "__main__":
    main()
    print("\nPresiona Enter para continuar...")
    try:
        input()
    except:
        pass