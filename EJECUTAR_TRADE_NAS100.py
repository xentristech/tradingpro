#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 EJECUTOR DE TRADES - NAS100 STRONG BUY
=========================================
Ejecuta el trade de NAS100 inmediatamente
"""

import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'configs'))

def ejecutar_trade_nas100():
    """Ejecuta el trade de NAS100 ahora"""
    print("\n" + "="*70)
    print("🚀 EJECUTANDO TRADE NAS100 - STRONG BUY")
    print("="*70)
    
    try:
        # Cargar configuración
        from dotenv import load_dotenv
        load_dotenv('configs/.env')
        
        import MetaTrader5 as mt5
        
        # Credenciales
        login = int(os.getenv('MT5_LOGIN', '197678662'))
        password = os.getenv('MT5_PASSWORD', 'Badboy930218*')
        server = os.getenv('MT5_SERVER', 'Exness-MT5Trial11')
        
        print(f"\n📡 Conectando a MT5...")
        print(f"   Login: {login}")
        print(f"   Server: {server}")
        
        # Inicializar MT5
        if not mt5.initialize():
            print("❌ Error: MT5 no se pudo inicializar")
            print("\n🔧 SOLUCIÓN:")
            print("1. Asegúrate que MetaTrader 5 esté instalado")
            print("2. Descarga desde: https://www.metatrader5.com/")
            return False
        
        # Login
        if not mt5.login(login, password=password, server=server):
            error = mt5.last_error()
            print(f"❌ Error de login: {error}")
            print("\n🔧 SOLUCIÓN:")
            print("1. Verifica las credenciales en configs/.env")
            print("2. Asegúrate que la cuenta esté activa")
            return False
        
        # Cuenta conectada
        account = mt5.account_info()
        print(f"✅ Conectado exitosamente!")
        print(f"   Balance: ${account.balance:.2f}")
        print(f"   Equity: ${account.equity:.2f}")
        
        # Buscar símbolo NAS100
        print(f"\n🔍 Buscando símbolo NAS100...")
        
        # Intentar diferentes variaciones
        symbol_variations = ['NAS100', 'NAS100m', 'NASDAQ100', 'US100', 'USTEC', 'NDX']
        symbol_found = None
        
        for symbol in symbol_variations:
            info = mt5.symbol_info(symbol)
            if info is not None:
                symbol_found = symbol
                print(f"✅ Símbolo encontrado: {symbol}")
                break
        
        if not symbol_found:
            print("❌ No se encontró el símbolo NAS100")
            print("\n📋 Símbolos disponibles similares:")
            symbols = mt5.symbols_get()
            nas_symbols = [s.name for s in symbols if 'NAS' in s.name.upper() or 'NDX' in s.name.upper() or '100' in s.name]
            for s in nas_symbols[:10]:
                print(f"   • {s}")
            return False
        
        # Activar símbolo
        symbol = symbol_found
        if not mt5.symbol_select(symbol, True):
            print(f"⚠️ Activando símbolo {symbol}...")
            mt5.symbol_select(symbol, True)
        
        # Obtener información del símbolo
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            print(f"❌ No se pudo obtener info de {symbol}")
            return False
        
        # Obtener precio actual
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            print(f"❌ No se pudo obtener precio de {symbol}")
            return False
        
        print(f"\n📊 Información del mercado:")
        print(f"   Símbolo: {symbol}")
        print(f"   Bid: {tick.bid:.2f}")
        print(f"   Ask: {tick.ask:.2f}")
        print(f"   Spread: {(tick.ask - tick.bid)/symbol_info.point:.0f} puntos")
        
        # Preparar orden de COMPRA
        lot = symbol_info.volume_min  # Lote mínimo
        price = tick.ask
        point = symbol_info.point
        
        # Calcular SL y TP
        sl_points = 200  # 200 puntos de stop loss
        tp_points = 400  # 400 puntos de take profit (R:R 1:2)
        
        sl = price - (sl_points * point)
        tp = price + (tp_points * point)
        
        print(f"\n📝 Preparando orden BUY:")
        print(f"   Volumen: {lot} lotes")
        print(f"   Precio entrada: {price:.2f}")
        print(f"   Stop Loss: {sl:.2f} (-{sl_points} puntos)")
        print(f"   Take Profit: {tp:.2f} (+{tp_points} puntos)")
        print(f"   Risk/Reward: 1:2")
        
        # Crear request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": mt5.ORDER_TYPE_BUY,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 20,
            "magic": 234000,
            "comment": "NAS100 STRONG BUY Signal",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Verificar modo
        live_mode = os.getenv('LIVE_TRADING', 'false').lower() == 'true'
        
        print(f"\n🚀 Ejecutando orden...")
        print(f"   Modo: {'LIVE' if live_mode else 'DEMO'}")
        
        # Ejecutar orden
        result = mt5.order_send(request)
        
        if result is None:
            print("❌ Error: No se recibió respuesta del servidor")
            return False
        
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"\n✅ ¡ORDEN EJECUTADA EXITOSAMENTE!")
            print(f"   Ticket: #{result.order}")
            print(f"   Volumen: {result.volume}")
            print(f"   Precio: {result.price:.2f}")
            print(f"   Símbolo: {symbol}")
            
            # Verificar posición
            positions = mt5.positions_get(symbol=symbol)
            if positions:
                pos = positions[0]
                print(f"\n📊 Posición abierta:")
                print(f"   P&L actual: ${pos.profit:.2f}")
                print(f"   Swap: ${pos.swap:.2f}")
            
            return True
        else:
            print(f"❌ Error ejecutando orden: {result.comment}")
            print(f"   Código: {result.retcode}")
            
            # Diagnóstico del error
            if result.retcode == 10004:
                print("   Problema: Requote - el precio cambió")
                print("   Solución: Intentar de nuevo")
            elif result.retcode == 10006:
                print("   Problema: Orden rechazada")
                print("   Solución: Verificar parámetros")
            elif result.retcode == 10014:
                print("   Problema: Volumen inválido")
                print(f"   Solución: Usar volumen entre {symbol_info.volume_min} y {symbol_info.volume_max}")
            elif result.retcode == 10016:
                print("   Problema: Stops inválidos")
                print("   Solución: Verificar niveles de SL/TP")
            elif result.retcode == 10019:
                print("   Problema: No hay suficiente dinero")
                print("   Solución: Reducir el tamaño del lote")
            
            return False
            
    except ImportError as e:
        print(f"❌ Error: {e}")
        print("\n🔧 SOLUCIÓN:")
        print("Instalar MetaTrader5:")
        print("pip install MetaTrader5")
        return False
        
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        try:
            mt5.shutdown()
            print("\n✅ MT5 cerrado correctamente")
        except:
            pass

def main():
    """Función principal"""
    success = ejecutar_trade_nas100()
    
    if success:
        print("\n" + "="*70)
        print("🎉 TRADE EJECUTADO CON ÉXITO")
        print("="*70)
        print("\n💡 Próximos pasos:")
        print("1. Monitorear la posición")
        print("2. El sistema aplicará trailing stop automáticamente")
        print("3. Recibirás notificaciones de cambios importantes")
    else:
        print("\n" + "="*70)
        print("⚠️ NO SE PUDO EJECUTAR EL TRADE")
        print("="*70)
        print("\n🔧 Acciones recomendadas:")
        print("1. Verificar que MetaTrader 5 esté instalado")
        print("2. Verificar las credenciales en configs/.env")
        print("3. Asegurarse que el mercado esté abierto")
        print("4. Intentar de nuevo con: python EJECUTAR_TRADE_NAS100.py")

if __name__ == "__main__":
    main()
