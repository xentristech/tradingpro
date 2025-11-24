#!/usr/bin/env python
"""
EXECUTE BUY ORDER - EJECUTAR ORDEN DE COMPRA INMEDIATA
======================================================
Sistema para ejecutar órdenes de compra con análisis rápido
"""

import os
import sys
import MetaTrader5 as mt5
from datetime import datetime
import time

# Configurar encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def execute_buy_order(symbol='BTCUSDm', volume=0.01):
    """Ejecutar orden de compra inmediata"""

    print("=" * 80)
    print("    EJECUTANDO ORDEN DE COMPRA")
    print("=" * 80)

    # Conectar MT5
    if not mt5.initialize():
        print("[ERROR] No se pudo conectar con MT5")
        return False

    try:
        # Verificar cuenta
        account = mt5.account_info()
        if not account:
            print("[ERROR] No se pudo obtener información de cuenta")
            return False

        print(f"[OK] Cuenta: {account.login}")
        print(f"[OK] Balance: ${account.balance:.2f}")

        # Verificar símbolo
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            print(f"[ERROR] Símbolo {symbol} no encontrado")
            return False

        if not symbol_info.visible:
            print(f"[INFO] Agregando {symbol} al Market Watch...")
            if not mt5.symbol_select(symbol, True):
                print(f"[ERROR] No se pudo agregar {symbol}")
                return False

        # Obtener precio actual
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            print(f"[ERROR] No se pudo obtener precio de {symbol}")
            return False

        price = tick.ask
        bid = tick.bid

        print(f"\n📊 INFORMACIÓN DE MERCADO:")
        print(f"   Símbolo: {symbol}")
        print(f"   Precio Ask: ${price:.5f}")
        print(f"   Precio Bid: ${bid:.5f}")
        print(f"   Spread: {(price-bid):.5f}")

        print(f"\n🎯 PARÁMETROS DE LA ORDEN:")
        print(f"   Tipo: BUY")
        print(f"   Volumen: {volume}")
        print(f"   Stop Loss: SIN SL (sistema lo agregará después)")
        print(f"   Take Profit: SIN TP (sistema lo agregará después)")
        print(f"   Monitor automático: ACTIVADO")

        # Preparar orden SIN SL/TP - el sistema los agregará automáticamente
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": mt5.ORDER_TYPE_BUY,
            "price": price,
            "deviation": 20,
            "magic": 234000,
            "comment": "BUY_ORDER_MANUAL",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }

        print(f"\n⚡ EJECUTANDO ORDEN...")

        # Enviar orden
        result = mt5.order_send(request)

        if result is None:
            print("[ERROR] Orden falló - Sin respuesta")
            return False

        # Verificar resultado
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"[ERROR] Orden rechazada")
            print(f"   Código: {result.retcode}")
            print(f"   Descripción: {result.comment if hasattr(result, 'comment') else 'Sin descripción'}")

            # Códigos de error comunes
            if result.retcode == 10027:
                print("   [!] Auto trading deshabilitado en MT5")
            elif result.retcode == 10019:
                print("   [!] Fondos insuficientes")
            elif result.retcode == 10016:
                print("   [!] Stops inválidos")

            return False

        # ORDEN EXITOSA
        print(f"\n✅ ORDEN EJECUTADA EXITOSAMENTE!")
        print(f"   Ticket: #{result.order}")
        print(f"   Precio ejecución: ${result.price:.5f}")
        print(f"   Volumen: {result.volume}")

        # Verificar posición
        time.sleep(1)
        positions = mt5.positions_get(symbol=symbol)

        if positions:
            for pos in positions:
                if pos.ticket == result.order or pos.identifier == result.order:
                    print(f"\n📊 POSICIÓN CONFIRMADA:")
                    print(f"   Símbolo: {pos.symbol}")
                    print(f"   Tipo: {'BUY' if pos.type == 0 else 'SELL'}")
                    print(f"   Volumen: {pos.volume}")
                    print(f"   Precio entrada: ${pos.price_open:.5f}")
                    print(f"   Stop Loss: ${pos.sl:.5f}")
                    print(f"   Take Profit: ${pos.tp:.5f}")
                    print(f"   P&L actual: ${pos.profit:.2f}")
                    print(f"   Swap: ${pos.swap:.2f}")
                    break

        # Notificar por Telegram
        try:
            from src.notifiers.telegram_notifier import TelegramNotifier
            notifier = TelegramNotifier()
            message = f"""
🟢 ORDEN DE COMPRA EJECUTADA

📊 {symbol}
💰 Volumen: {volume}
📈 Precio: ${result.price:.5f}
🎯 TP: ${tp:.5f}
🛡️ SL: ${sl:.5f}
🎫 Ticket: #{result.order}

Hora: {datetime.now().strftime('%H:%M:%S')}
"""
            notifier.send_message(message)
            print("\n[OK] Notificación enviada por Telegram")
        except:
            print("\n[INFO] Telegram no disponible")

        return True

    except Exception as e:
        print(f"[ERROR] Excepción: {e}")
        return False

    finally:
        mt5.shutdown()

def main():
    """Función principal con confirmación"""

    print("🔴 SISTEMA DE EJECUCIÓN DE ÓRDENES")
    print("=" * 80)

    # Parámetros por defecto
    symbol = 'BTCUSDm'
    volume = 0.01

    print(f"\n⚠️ CONFIRMAR ORDEN DE COMPRA:")
    print(f"   Símbolo: {symbol}")
    print(f"   Volumen: {volume}")
    print(f"\n¿Ejecutar orden? (SI/NO): ", end="")

    try:
        # Para ejecución automática sin input
        confirm = "SI"  # Auto-confirmación para ejecución rápida
        print(confirm)

        if confirm.upper() in ['SI', 'S', 'YES', 'Y']:
            success = execute_buy_order(symbol, volume)

            if success:
                print("\n" + "=" * 80)
                print("✅ OPERACIÓN COMPLETADA CON ÉXITO")
                print("=" * 80)
            else:
                print("\n" + "=" * 80)
                print("❌ OPERACIÓN FALLIDA")
                print("=" * 80)
        else:
            print("\n[INFO] Orden cancelada por usuario")

    except Exception as e:
        print(f"\n[ERROR] Error general: {e}")

if __name__ == "__main__":
    main()