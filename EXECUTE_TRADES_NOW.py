#!/usr/bin/env python
"""
EJECUTOR DIRECTO DE TRADES - EJECUTA SEÑALES DETECTADAS
"""

import MetaTrader5 as mt5
import sys
from pathlib import Path

# Añadir path del proyecto
sys.path.insert(0, str(Path(__file__).parent))

def execute_trade(symbol, signal_type, confidence):
    """Ejecutar trade directamente en MT5"""
    
    print(f"\nEjecutando trade para {symbol}...")
    print(f"  Señal: {signal_type} ({confidence:.1f}%)")
    
    # Inicializar MT5
    if not mt5.initialize():
        print("  ERROR: No se pudo conectar a MT5")
        return False
    
    # Obtener información del símbolo
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print(f"  ERROR: Símbolo {symbol} no encontrado")
        return False
    
    if not symbol_info.visible:
        if not mt5.symbol_select(symbol, True):
            print(f"  ERROR: No se pudo seleccionar {symbol}")
            return False
    
    # Obtener precio actual
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        print(f"  ERROR: No se pudo obtener precio para {symbol}")
        return False
    
    # Configurar parámetros del trade
    lot = 0.01  # Tamaño mínimo
    
    if signal_type == "BUY":
        price = tick.ask
        sl = price - 50 * symbol_info.point  # 50 pips SL
        tp = price + 100 * symbol_info.point  # 100 pips TP
        order_type = mt5.ORDER_TYPE_BUY
    else:  # SELL
        price = tick.bid
        sl = price + 50 * symbol_info.point
        tp = price - 100 * symbol_info.point
        order_type = mt5.ORDER_TYPE_SELL
    
    # Preparar solicitud
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 20,
        "magic": 123456,
        "comment": f"AlgoTrader-{signal_type}-{confidence:.0f}%",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    # Enviar orden
    result = mt5.order_send(request)
    
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        print(f"  -> TRADE EJECUTADO EXITOSAMENTE")
        print(f"    Ticket: #{result.order}")
        print(f"    Precio: {price:.5f}")
        print(f"    SL: {sl:.5f}, TP: {tp:.5f}")
        return True
    else:
        print(f"  -> ERROR ejecutando trade: {result.retcode}")
        print(f"    Comentario: {result.comment}")
        return False

def main():
    print("=" * 60)
    print("    EJECUTOR DIRECTO DE TRADES")
    print("=" * 60)
    
    # Señales detectadas del análisis anterior (símbolos corregidos para MT5)
    trades_to_execute = [
        {"symbol": "EURUSDm", "signal": "BUY", "confidence": 70.5},
        {"symbol": "GBPUSDm", "signal": "BUY", "confidence": 78.0}
    ]
    
    print(f"\nSe ejecutarán {len(trades_to_execute)} trades:")
    for trade in trades_to_execute:
        print(f"  - {trade['symbol']}: {trade['signal']} ({trade['confidence']:.1f}%)")
    
    # Inicializar MT5
    if not mt5.initialize():
        print("\nERROR: No se pudo conectar a MT5")
        return
    
    # Información de cuenta
    account = mt5.account_info()
    if account:
        print(f"\nCuenta MT5: {account.login}")
        print(f"Balance: ${account.balance:.2f}")
        print(f"Equity: ${account.equity:.2f}")
    
    # Ejecutar cada trade
    executed = 0
    for trade in trades_to_execute:
        if execute_trade(trade["symbol"], trade["signal"], trade["confidence"]):
            executed += 1
    
    print(f"\n{executed}/{len(trades_to_execute)} trades ejecutados exitosamente")
    
    # Mostrar posiciones actuales
    positions = mt5.positions_get()
    if positions:
        print(f"\nPosiciones abiertas totales: {len(positions)}")
        for pos in positions:
            print(f"  {pos.symbol}: {'BUY' if pos.type == 0 else 'SELL'} | Vol: {pos.volume} | P&L: ${pos.profit:.2f}")
    
    mt5.shutdown()
    print("\nEjecución completada")

if __name__ == "__main__":
    main()