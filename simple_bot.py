#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Bot de Trading Simple - Version ejecutable directa
"""
import os
import time
import sys
from datetime import datetime
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv('configs/.env')

print("="*50)
print("   BOT DE TRADING - EJECUTANDO")
print("   Cuenta:", os.getenv("MT5_LOGIN"))
print("   Servidor:", os.getenv("MT5_SERVER"))
print("   Simbolo:", os.getenv("SYMBOL"))
print("   Modo LIVE:", os.getenv("LIVE_TRADING"))
print("="*50)

try:
    import MetaTrader5 as mt5
    print("✓ MetaTrader5 importado correctamente")
    
    # Configurar MT5
    path = os.getenv("MT5_PATH")
    login = int(os.getenv("MT5_LOGIN"))
    password = os.getenv("MT5_PASSWORD")
    server = os.getenv("MT5_SERVER")
    symbol = os.getenv("SYMBOL")
    
    print(f"\n--- CONECTANDO A MT5 ---")
    print(f"Path: {path}")
    print(f"Login: {login}")
    print(f"Server: {server}")
    
    # Inicializar MT5
    if not mt5.initialize(path=path, login=login, password=password, server=server):
        error = mt5.last_error()
        print(f"✗ Error de inicialización MT5: {error}")
        print("\nVerifique que MetaTrader 5 esté instalado y configurado.")
        sys.exit(1)
    
    print("✓ MT5 conectado exitosamente")
    
    # Información de cuenta
    account = mt5.account_info()
    if account:
        print(f"\n--- INFORMACIÓN DE CUENTA ---")
        print(f"Login: {account.login}")
        print(f"Balance: ${account.balance:.2f}")
        print(f"Equity: ${account.equity:.2f}")
        print(f"Margin: ${account.margin:.2f}")
        print(f"Free Margin: ${account.margin_free:.2f}")
    
    # Verificar símbolo
    print(f"\n--- VERIFICANDO SÍMBOLO {symbol} ---")
    if not mt5.symbol_select(symbol, True):
        print(f"✗ No se pudo seleccionar el símbolo {symbol}")
        sys.exit(1)
    
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info:
        print(f"✓ Símbolo {symbol} disponible")
        print(f"Spread: {symbol_info.spread} puntos")
        print(f"Min Volume: {symbol_info.volume_min}")
        print(f"Max Volume: {symbol_info.volume_max}")
    
    # Obtener precio actual
    tick = mt5.symbol_info_tick(symbol)
    if tick:
        print(f"\n--- PRECIO ACTUAL ---")
        print(f"{symbol}: Bid={tick.bid}, Ask={tick.ask}")
        print(f"Spread: {tick.ask - tick.bid:.5f}")
    
    # Verificar posiciones abiertas
    positions = mt5.positions_get(symbol=symbol)
    print(f"\n--- POSICIONES ---")
    print(f"Posiciones abiertas: {len(positions) if positions else 0}")
    
    if positions:
        for pos in positions:
            print(f"  {pos.type_str} {pos.volume} {pos.symbol} @ {pos.price_open}")
    
    print(f"\n--- BOT INICIADO ---")
    print(f"Hora de inicio: {datetime.now().strftime('%H:%M:%S')}")
    print("Presione Ctrl+C para detener")
    print("-" * 50)
    
    # Loop principal del bot
    ciclo = 0
    while True:
        try:
            ciclo += 1
            tiempo = datetime.now().strftime('%H:%M:%S')
            
            # Obtener precio actual
            tick = mt5.symbol_info_tick(symbol)
            if tick:
                bid = tick.bid
                ask = tick.ask
                spread = ask - bid
                
                # Verificar posiciones
                positions = mt5.positions_get(symbol=symbol)
                num_pos = len(positions) if positions else 0
                
                print(f"[{ciclo:04d}] {tiempo} | {symbol}: {bid:.5f}/{ask:.5f} | Spread: {spread:.5f} | Pos: {num_pos}")
                
                # Aquí iría la lógica de trading
                # Por ahora solo monitoreamos
                
            else:
                print(f"[{ciclo:04d}] {tiempo} | Error obteniendo tick para {symbol}")
            
            # Esperar 30 segundos
            time.sleep(30)
            
        except KeyboardInterrupt:
            print(f"\n--- BOT DETENIDO ---")
            print(f"Detenido por usuario en: {datetime.now().strftime('%H:%M:%S')}")
            print(f"Ciclos ejecutados: {ciclo}")
            break
            
        except Exception as e:
            print(f"[ERROR] {e}")
            time.sleep(10)
    
    # Cerrar MT5
    mt5.shutdown()
    print("✓ Conexión MT5 cerrada")
    
except ImportError:
    print("✗ Error: MetaTrader5 no está instalado")
    print("Instale con: pip install MetaTrader5")
    
except Exception as e:
    print(f"✗ Error: {e}")
    
finally:
    print(f"\nBot finalizado: {datetime.now().strftime('%H:%M:%S')}")
    print("Presione Enter para salir...")
    try:
        input()
    except:
        pass