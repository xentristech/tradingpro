#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para verificar posiciones abiertas en MT5
"""
import sys
import os

try:
    import MetaTrader5 as mt5
    print("✓ MetaTrader5 importado correctamente")
except ImportError as e:
    print(f"✗ Error importando MetaTrader5: {e}")
    print("Instalando MetaTrader5...")
    os.system(f"{sys.executable} -m pip install MetaTrader5")
    try:
        import MetaTrader5 as mt5
        print("✓ MetaTrader5 instalado e importado")
    except:
        print("✗ No se pudo instalar MetaTrader5")
        sys.exit(1)

from datetime import datetime

def main():
    print("\n" + "="*60)
    print("   VERIFICACIÓN DE POSICIONES MT5")
    print("="*60)
    print(f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python: {sys.version}")
    print(f"MT5 Version: {mt5.__version__ if hasattr(mt5, '__version__') else 'Unknown'}")
    print()
    
    # Intentar conectar
    print("Conectando a MT5...")
    try:
        initialized = mt5.initialize()
        if not initialized:
            error = mt5.last_error()
            print(f"✗ No se pudo conectar a MT5")
            print(f"  Error: {error}")
            print("\nPosibles soluciones:")
            print("  1. Verificar que MT5 esté abierto")
            print("  2. Verificar las credenciales")
            print("  3. Reiniciar MT5")
            return
        
        print("✓ Conectado exitosamente a MT5")
        
        # Información de la cuenta
        account = mt5.account_info()
        if account:
            print("\nINFORMACIÓN DE LA CUENTA:")
            print(f"  Número: {account.login}")
            print(f"  Servidor: {account.server}")
            print(f"  Tipo: {'Demo' if 'demo' in account.server.lower() or 'trial' in account.server.lower() else 'Real'}")
            print(f"  Balance: ${account.balance:.2f}")
            print(f"  Equity: ${account.equity:.2f}")
            print(f"  Margen libre: ${account.margin_free:.2f}")
            print(f"  Profit/Loss actual: ${account.profit:.2f}")
            print(f"  Apalancamiento: 1:{account.leverage}")
        else:
            print("✗ No se pudo obtener información de la cuenta")
        
        print("\n" + "-"*60)
        
        # Obtener posiciones
        positions = mt5.positions_get()
        
        if positions is None:
            print("✗ Error al obtener posiciones")
        elif len(positions) == 0:
            print("📊 NO HAY POSICIONES ABIERTAS ACTUALMENTE")
            
            # Mostrar órdenes pendientes
            orders = mt5.orders_get()
            if orders and len(orders) > 0:
                print(f"\n⏳ Órdenes pendientes: {len(orders)}")
                for order in orders:
                    print(f"  - {order.symbol} {order.type_description} @ {order.price_open:.5f}")
        else:
            print(f"📊 POSICIONES ABIERTAS: {len(positions)}")
            print("-"*60)
            
            total_profit = 0
            total_volume = 0
            
            for i, pos in enumerate(positions, 1):
                print(f"\n[{i}] Posición #{pos.ticket}")
                print(f"  Símbolo: {pos.symbol}")
                print(f"  Tipo: {'COMPRA (BUY)' if pos.type == 0 else 'VENTA (SELL)'}")
                print(f"  Volumen: {pos.volume} lotes")
                print(f"  Precio apertura: {pos.price_open:.5f}")
                
                # Precio actual
                tick = mt5.symbol_info_tick(pos.symbol)
                if tick:
                    current = tick.bid if pos.type == 0 else tick.ask
                    print(f"  Precio actual: {current:.5f}")
                    
                    # Calcular diferencia
                    diff = current - pos.price_open if pos.type == 0 else pos.price_open - current
                    
                    # Determinar valor del pip según el símbolo
                    if 'JPY' in pos.symbol:
                        pip_value = 0.01
                    elif pos.symbol in ['XAUUSD', 'GOLD', 'XAUUSDm']:
                        pip_value = 0.1
                    elif 'BTC' in pos.symbol or 'ETH' in pos.symbol:
                        pip_value = 1.0
                    else:
                        pip_value = 0.0001
                    
                    pips = diff / pip_value
                    print(f"  Diferencia: {pips:.1f} pips")
                
                # SL y TP
                if pos.sl > 0:
                    print(f"  Stop Loss: {pos.sl:.5f}")
                else:
                    print(f"  Stop Loss: ⚠️ NO ESTABLECIDO")
                    
                if pos.tp > 0:
                    print(f"  Take Profit: {pos.tp:.5f}")
                else:
                    print(f"  Take Profit: ⚠️ NO ESTABLECIDO")
                
                # Profit
                profit_color = "🟢" if pos.profit >= 0 else "🔴"
                print(f"  Profit/Loss: {profit_color} ${pos.profit:.2f}")
                
                # Tiempo abierto
                time_open = datetime.fromtimestamp(pos.time)
                duration = datetime.now() - time_open
                hours = duration.total_seconds() / 3600
                print(f"  Abierto desde: {time_open.strftime('%Y-%m-%d %H:%M:%S')} ({hours:.1f} horas)")
                
                # Comentario
                if pos.comment:
                    print(f"  Comentario: {pos.comment}")
                
                total_profit += pos.profit
                total_volume += pos.volume
            
            print("\n" + "="*60)
            print("RESUMEN:")
            print(f"  Total posiciones: {len(positions)}")
            print(f"  Volumen total: {total_volume:.2f} lotes")
            profit_emoji = "🟢" if total_profit >= 0 else "🔴"
            print(f"  Profit/Loss total: {profit_emoji} ${total_profit:.2f}")
        
        # Símbolos disponibles
        print("\n" + "-"*60)
        print("SÍMBOLOS PRINCIPALES:")
        symbols = ['BTCUSDm', 'XAUUSDm', 'EURUSD', 'GBPUSD', 'USTECm', 'US30m']
        for symbol in symbols:
            info = mt5.symbol_info(symbol)
            if info and info.visible:
                tick = mt5.symbol_info_tick(symbol)
                if tick:
                    spread = tick.ask - tick.bid
                    print(f"  {symbol}: Bid={tick.bid:.5f} Ask={tick.ask:.5f} Spread={spread:.5f}")
        
    except Exception as e:
        print(f"\n✗ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cerrar conexión
        try:
            mt5.shutdown()
            print("\n✓ Conexión cerrada")
        except:
            pass
    
    print("\n" + "="*60)
    print("Verificación completada")
    print("="*60)

if __name__ == "__main__":
    main()
    input("\nPresiona Enter para salir...")
