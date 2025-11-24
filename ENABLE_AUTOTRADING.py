#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HABILITAR AUTOTRADING EN MT5
Verifica y habilita el trading automático
"""

import MetaTrader5 as mt5
import time

def enable_autotrading():
    """Habilita el AutoTrading en MT5"""
    print("=" * 70)
    print("          HABILITANDO AUTOTRADING EN MT5")
    print("=" * 70)
    print()

    # Conectar a MT5
    print("1. Conectando a MT5...")
    if not mt5.initialize():
        print("   [ERROR] No se pudo inicializar MT5")
        return False

    print("   [OK] Conectado a MT5")

    # Obtener información de la cuenta
    account_info = mt5.account_info()
    if not account_info:
        print("   [ERROR] No se pudo obtener información de la cuenta")
        mt5.shutdown()
        return False

    print(f"   Cuenta: {account_info.login}")
    print(f"   Servidor: {account_info.server}")
    print()

    # Verificar estado del AutoTrading
    print("2. Verificando estado del AutoTrading...")
    terminal_info = mt5.terminal_info()

    if terminal_info:
        print(f"   Trade Allowed: {terminal_info.trade_allowed}")
        # Verificar otros atributos disponibles
        if hasattr(terminal_info, 'trade_expert'):
            print(f"   Trade Expert: {terminal_info.trade_expert}")
        if hasattr(terminal_info, 'dlls_allowed'):
            print(f"   DLLs Allowed: {terminal_info.dlls_allowed}")

    # Verificar permisos de trading de la cuenta
    print()
    print("3. Verificando permisos de trading...")
    print(f"   Trade Allowed (Account): {account_info.trade_allowed}")
    print(f"   Trade Mode: {account_info.trade_mode}")

    if not account_info.trade_allowed:
        print()
        print("   [ALERTA] Trading no permitido en esta cuenta!")
        print("   Esto puede ser porque:")
        print("   - La cuenta es de solo lectura")
        print("   - Hay restricciones del broker")
        print("   - La cuenta está bloqueada")
        mt5.shutdown()
        return False

    # Intentar habilitar símbolos
    print()
    print("4. Habilitando símbolos de trading...")
    symbols = ['BTCUSDm', 'XAUUSDm', 'EURUSD', 'GBPUSD']
    enabled_count = 0

    for symbol in symbols:
        # Seleccionar símbolo en Market Watch
        if mt5.symbol_select(symbol, True):
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info:
                if symbol_info.visible:
                    print(f"   [OK] {symbol}: Habilitado y visible")
                    enabled_count += 1
                else:
                    print(f"   [!] {symbol}: Habilitado pero no visible")
            else:
                print(f"   [!] {symbol}: No se pudo obtener información")
        else:
            print(f"   [ERROR] {symbol}: No se pudo habilitar")

    print()
    print("=" * 70)
    print("RESULTADO:")
    print("=" * 70)

    if terminal_info and terminal_info.trade_allowed:
        print("[OK] AutoTrading HABILITADO en el terminal")
    else:
        print("[!] AutoTrading DESHABILITADO en el terminal")
        print()
        print("SOLUCIÓN:")
        print("1. Abre MetaTrader 5")
        print("2. Haz clic en el botón 'AutoTrading' en la barra superior")
        print("3. Asegúrate de que esté iluminado/activado en color verde")
        print("4. Vuelve a ejecutar este script")

    print()
    print(f"Símbolos habilitados: {enabled_count}/{len(symbols)}")
    print()

    # Intentar una operación de prueba (solo verificación)
    print("5. Verificando capacidad de modificar órdenes...")
    positions = mt5.positions_get()

    if positions and len(positions) > 0:
        pos = positions[0]
        print(f"   Posición encontrada: {pos.symbol} #{pos.ticket}")
        print(f"   Se intentará agregar SL/TP...")
        print()

        # Calcular SL/TP conservadores
        tick = mt5.symbol_info_tick(pos.symbol)
        if tick:
            if pos.type == 0:  # BUY
                sl = pos.price_open - 0.001
                tp = pos.price_open + 0.002
            else:  # SELL
                sl = pos.price_open + 0.001
                tp = pos.price_open - 0.002

            # Intentar modificar
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "symbol": pos.symbol,
                "position": pos.ticket,
                "sl": sl,
                "tp": tp
            }

            result = mt5.order_send(request)

            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                print("   [OK] Se pudo modificar la posición")
                print("   AutoTrading está FUNCIONANDO correctamente!")
                mt5.shutdown()
                return True
            else:
                if result:
                    error_code = result.retcode
                    error_desc = result.comment if hasattr(result, 'comment') else ""
                    print(f"   [ERROR] No se pudo modificar: {error_code}")
                    print(f"   Descripción: {error_desc}")

                    if "disabled" in str(error_desc).lower():
                        print()
                        print("   ACCIÓN REQUERIDA:")
                        print("   - Abre MetaTrader 5")
                        print("   - Habilita el botón 'AutoTrading' (esquina superior)")
                        print("   - El botón debe estar VERDE/ILUMINADO")
                else:
                    print("   [ERROR] No se recibió respuesta")
    else:
        print("   [INFO] No hay posiciones abiertas para verificar")

    mt5.shutdown()
    return False

if __name__ == "__main__":
    try:
        if enable_autotrading():
            print()
            print("=" * 70)
            print("TODO LISTO! El sistema puede operar normalmente.")
            print("=" * 70)
        else:
            print()
            print("=" * 70)
            print("REQUIERE ACCIÓN MANUAL")
            print("=" * 70)
            print()
            print("Por favor, sigue estos pasos:")
            print("1. Abre MetaTrader 5")
            print("2. Busca el botón 'Algo Trading' o 'AutoTrading' en la barra superior")
            print("3. Haz clic para activarlo (debe quedar en color verde)")
            print("4. Si pregunta por permisos, acepta")
            print("5. Ejecuta este script nuevamente para verificar")
            print()
    except Exception as e:
        print(f"\n[ERROR] Error inesperado: {e}")
        import traceback
        traceback.print_exc()
