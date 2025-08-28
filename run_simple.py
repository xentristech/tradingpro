#!/usr/bin/env python
"""
🤖 ALGO TRADER - EJECUCIÓN SIMPLIFICADA
Bot de trading para cuenta demo de Exness
"""
import os
import sys
import time
from datetime import datetime

# Configurar encoding
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Cargar configuración
from dotenv import load_dotenv
load_dotenv('.env')

print("="*70)
print(" "*20 + "🤖 ALGO TRADER v3.0 - EXNESS DEMO")
print("="*70)
print()

def connect_mt5():
    """Conecta con MT5"""
    import MetaTrader5 as mt5
    
    path = os.getenv('MT5_PATH')
    login = int(os.getenv('MT5_LOGIN'))
    password = os.getenv('MT5_PASSWORD')
    server = os.getenv('MT5_SERVER')
    
    print("🔌 Conectando a MetaTrader 5...")
    print(f"   Cuenta: {login}")
    print(f"   Servidor: {server}")
    
    if mt5.initialize(path=path, login=login, password=password, server=server, timeout=60000):
        account = mt5.account_info()
        if account:
            print(f"✅ Conectado exitosamente")
            print(f"   Balance: ${account.balance:.2f}")
            print(f"   Equity: ${account.equity:.2f}")
            print(f"   Margin libre: ${account.margin_free:.2f}")
            return True
    
    print("❌ Error conectando a MT5")
    return False

def get_market_data(symbol):
    """Obtiene datos del mercado"""
    import MetaTrader5 as mt5
    
    mt5.symbol_select(symbol, True)
    tick = mt5.symbol_info_tick(symbol)
    
    if tick:
        return {
            'bid': tick.bid,
            'ask': tick.ask,
            'spread': tick.ask - tick.bid
        }
    return None

def analyze_market(symbol):
    """Análisis simple del mercado"""
    data = get_market_data(symbol)
    
    if data:
        # Aquí iría la lógica de análisis con indicadores
        # Por ahora solo mostramos los precios
        return {
            'signal': 'HOLD',
            'confidence': 0.5,
            'price': data['bid'],
            'spread': data['spread']
        }
    return None

def main():
    """Loop principal del bot"""
    
    # Conectar a MT5
    if not connect_mt5():
        print("No se pudo conectar a MT5. Abortando...")
        return
    
    import MetaTrader5 as mt5
    
    symbol = os.getenv('TRADING_SYMBOL', 'BTCUSD')
    print(f"\n📊 Monitoreando: {symbol}")
    print("-"*70)
    
    try:
        cycle = 0
        while True:
            cycle += 1
            timestamp = datetime.now().strftime('%H:%M:%S')
            
            # Obtener datos del mercado
            data = get_market_data(symbol)
            
            if data:
                # Análisis
                analysis = analyze_market(symbol)
                
                # Obtener posiciones abiertas
                positions = mt5.positions_get(symbol=symbol)
                num_positions = len(positions) if positions else 0
                
                # Mostrar información
                print(f"[{cycle:04d}] {timestamp} | {symbol}: {data['bid']:.2f}/{data['ask']:.2f} | "
                      f"Spread: {data['spread']:.2f} | Posiciones: {num_positions} | "
                      f"Señal: {analysis['signal']}")
                
                # Aquí iría la lógica de trading
                # - Validación con IA
                # - Gestión de riesgo
                # - Ejecución de órdenes
                # - Gestión de posiciones
                
                # Por ahora solo monitoreamos
                
            else:
                print(f"[{cycle:04d}] {timestamp} | Error obteniendo datos")
            
            # Esperar antes del próximo ciclo
            time.sleep(20)  # 20 segundos
            
    except KeyboardInterrupt:
        print("\n\n⛔ Bot detenido por el usuario")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        mt5.shutdown()
        print("\n✅ Conexión MT5 cerrada")
        print("="*70)

if __name__ == "__main__":
    main()
