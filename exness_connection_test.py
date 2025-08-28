#!/usr/bin/env python3
"""
EXNESS CONNECTION TEST - Conectar específicamente a la cuenta Exness
Usuario: 197678662
Servidor: Exness-MT5Trial11
"""
import MetaTrader5 as mt5
import os
from dotenv import load_dotenv

# Cargar configuración
load_dotenv('.env')

def connect_exness():
    """Conectar específicamente a la cuenta Exness"""
    
    # Credenciales específicas
    login = int(os.getenv('MT5_LOGIN', '197678662'))
    password = os.getenv('MT5_PASSWORD', 'Badboy930218*')
    server = os.getenv('MT5_SERVER', 'Exness-MT5Trial11')
    
    print("=== CONEXION EXNESS ===")
    print(f"Login: {login}")
    print(f"Server: {server}")
    print(f"Password: {'*' * len(password)}")
    
    # Inicializar MT5
    if not mt5.initialize():
        print("ERROR: No se pudo inicializar MT5")
        return False
    
    # Intentar login específico
    if not mt5.login(login, password=password, server=server):
        print("ERROR: No se pudo conectar con las credenciales")
        print(f"Error MT5: {mt5.last_error()}")
        mt5.shutdown()
        return False
    
    # Verificar conexión
    account = mt5.account_info()
    if not account:
        print("ERROR: No se pudo obtener información de cuenta")
        mt5.shutdown()
        return False
    
    print("\n=== CONEXION EXITOSA ===")
    print(f"Cuenta: {account.login}")
    print(f"Nombre: {account.name}")
    print(f"Servidor: {account.server}")
    print(f"Balance: ${account.balance:.2f}")
    print(f"Equity: ${account.equity:.2f}")
    print(f"Margin: ${account.margin:.2f}")
    print(f"Leverage: 1:{account.leverage}")
    
    # Verificar auto trading
    terminal = mt5.terminal_info()
    if terminal:
        print(f"Auto Trading: {'ENABLED' if terminal.trade_allowed else 'DISABLED'}")
        if not terminal.trade_allowed:
            print("⚠️ AUTO TRADING DESHABILITADO - Necesita habilitarse en MT5")
    
    return True

def check_symbols():
    """Verificar símbolos disponibles"""
    print("\n=== SIMBOLOS DISPONIBLES ===")
    symbols = mt5.symbols_get()
    
    if not symbols:
        print("No se encontraron símbolos")
        return []
    
    available = []
    print(f"Total símbolos: {len(symbols)}")
    
    # Buscar símbolos principales
    major_symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD']
    crypto_symbols = ['BTCUSD', 'ETHUSD', 'LTCUSD']
    
    print("\nSímbolos Forex:")
    for symbol_name in major_symbols:
        for symbol in symbols:
            if symbol.name == symbol_name and symbol.visible:
                tick = mt5.symbol_info_tick(symbol.name)
                if tick:
                    print(f"  ✓ {symbol.name}: {tick.bid:.5f}")
                    available.append(symbol.name)
                break
    
    print("\nSímbolos Crypto:")
    for symbol_name in crypto_symbols:
        for symbol in symbols:
            if symbol.name == symbol_name and symbol.visible:
                tick = mt5.symbol_info_tick(symbol.name)
                if tick:
                    print(f"  ✓ {symbol.name}: {tick.bid:.2f}")
                    available.append(symbol.name)
                break
    
    # Si no encuentra los principales, mostrar algunos disponibles
    if not available:
        print("\nPrimeros 10 símbolos disponibles:")
        count = 0
        for symbol in symbols:
            if symbol.visible and count < 10:
                tick = mt5.symbol_info_tick(symbol.name)
                if tick:
                    print(f"  {symbol.name}: {tick.bid}")
                    available.append(symbol.name)
                    count += 1
    
    return available

def test_order_capability():
    """Probar capacidad de órdenes"""
    print("\n=== TEST CAPACIDAD DE ORDENES ===")
    
    # Verificar terminal
    terminal = mt5.terminal_info()
    if not terminal:
        print("❌ No se pudo obtener info del terminal")
        return False
    
    if not terminal.trade_allowed:
        print("❌ AUTO TRADING DESHABILITADO en el terminal")
        print("   Para habilitar:")
        print("   1. Abrir MT5")
        print("   2. Tools → Options → Expert Advisors")
        print("   3. Marcar 'Allow automated trading'")
        print("   4. Marcar 'Allow DLL imports'")
        print("   5. Hacer clic OK")
        return False
    
    print("✓ Auto trading habilitado en terminal")
    
    # Verificar cuenta
    account = mt5.account_info()
    if account.trade_allowed:
        print("✓ Trading permitido en la cuenta")
    else:
        print("❌ Trading no permitido en la cuenta")
        return False
    
    if account.trade_expert:
        print("✓ Expert Advisors permitidos")
    else:
        print("❌ Expert Advisors no permitidos")
    
    return True

def run_exness_validation():
    """Ejecutar validación completa de Exness"""
    
    try:
        # Paso 1: Conectar
        if not connect_exness():
            return False
        
        # Paso 2: Verificar símbolos
        available_symbols = check_symbols()
        
        # Paso 3: Verificar capacidad de trading
        trading_ready = test_order_capability()
        
        print("\n=== RESUMEN VALIDACION ===")
        print(f"✓ Conexión Exness: OK")
        print(f"✓ Símbolos disponibles: {len(available_symbols)}")
        print(f"{'✓' if trading_ready else '❌'} Trading capability: {'OK' if trading_ready else 'DISABLED'}")
        
        if trading_ready and available_symbols:
            print(f"\n🎉 CUENTA EXNESS LISTA PARA TRADING")
            print(f"   Símbolo recomendado: {available_symbols[0]}")
            
            # Telegram notification
            try:
                from notifiers.telegram_notifier import send_telegram_message
                send_telegram_message(f"✅ CUENTA EXNESS VALIDADA:\n- Login: 197678662\n- Server: Exness-MT5Trial11\n- Símbolos: {len(available_symbols)}\n- Trading: {'Habilitado' if trading_ready else 'Deshabilitado'}")
            except Exception as e:
                print(f"Error Telegram: {e}")
                
            return True
        else:
            print(f"\n❌ CUENTA NECESITA CONFIGURACION")
            return False
            
    except Exception as e:
        print(f"Error en validación: {e}")
        return False
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    print("=" * 50)
    print("VALIDACION CUENTA EXNESS")
    print("=" * 50)
    
    success = run_exness_validation()
    
    print("=" * 50)
    if success:
        print("🎉 VALIDACION EXITOSA")
    else:
        print("❌ VALIDACION FALLIDA")
    print("=" * 50)