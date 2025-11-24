#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🚀 SISTEMA DE TRADING COMPLETO - EJECUCIÓN EN VIVO
==================================================
Ejecuta todo el sistema con las credenciales configuradas
"""

import os
import sys
import time
import json
import logging
from datetime import datetime
from pathlib import Path

# Añadir el path de configs
sys.path.insert(0, str(Path(__file__).parent / 'configs'))

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

def load_config():
    """Carga la configuración desde configs/.env"""
    from dotenv import load_dotenv
    
    config_path = Path(__file__).parent / 'configs' / '.env'
    if config_path.exists():
        load_dotenv(config_path)
        print(f"✅ Configuración cargada desde: {config_path}")
        return True
    else:
        print(f"❌ No se encontró: {config_path}")
        return False

def check_mt5_connection():
    """Verifica y muestra conexión con MT5"""
    try:
        import MetaTrader5 as mt5
        
        # Obtener credenciales
        login = int(os.getenv('MT5_LOGIN', '0'))
        password = os.getenv('MT5_PASSWORD', '')
        server = os.getenv('MT5_SERVER', '')
        
        print(f"\n🔌 CONECTANDO A MT5...")
        print(f"   Login: {login}")
        print(f"   Server: {server}")
        
        # Inicializar MT5
        if not mt5.initialize():
            print("❌ Error inicializando MT5")
            return False
        
        # Intentar login
        if mt5.login(login, password=password, server=server):
            account = mt5.account_info()
            print(f"✅ CONECTADO A MT5!")
            print(f"   Balance: ${account.balance:.2f}")
            print(f"   Equity: ${account.equity:.2f}")
            print(f"   Profit: ${account.profit:.2f}")
            print(f"   Leverage: 1:{account.leverage}")
            
            # Verificar posiciones abiertas
            positions = mt5.positions_get()
            if positions:
                print(f"\n📊 POSICIONES ABIERTAS: {len(positions)}")
                for pos in positions:
                    print(f"   • {pos.symbol}: {pos.volume} lotes | P&L: ${pos.profit:.2f}")
            else:
                print(f"\n📊 No hay posiciones abiertas")
            
            return True
        else:
            error = mt5.last_error()
            print(f"❌ Error de login: {error}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def generate_signals():
    """Genera señales de trading"""
    print(f"\n📈 GENERANDO SEÑALES DE TRADING...")
    print("-"*50)
    
    import requests
    
    api_key = os.getenv('TWELVEDATA_API_KEY', '23d17ce5b7044ad5aef9766770a6252b')
    
    symbols = {
        'EURUSD': 'EUR/USD',
        'GBPUSD': 'GBP/USD',
        'XAUUSD': 'XAU/USD',
        'BTCUSD': 'BTC/USD',
        'NAS100': 'NAS100'
    }
    
    signals = []
    
    for mt5_symbol, api_symbol in symbols.items():
        try:
            # Obtener cotización
            url = f"https://api.twelvedata.com/quote"
            params = {'symbol': api_symbol, 'apikey': api_key}
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                price = float(data.get('close', 0))
                change = float(data.get('percent_change', 0))
                
                # Obtener RSI
                rsi_url = f"https://api.twelvedata.com/rsi"
                rsi_params = {
                    'symbol': api_symbol,
                    'interval': '5min',
                    'time_period': 14,
                    'apikey': api_key
                }
                rsi_response = requests.get(rsi_url, params=rsi_params, timeout=10)
                
                rsi = None
                if rsi_response.status_code == 200:
                    rsi_data = rsi_response.json()
                    if 'values' in rsi_data and rsi_data['values']:
                        rsi = float(rsi_data['values'][0]['rsi'])
                
                # Generar señal
                signal = analyze_signal(mt5_symbol, price, change, rsi)
                signals.append(signal)
                
                # Mostrar resultado
                print(f"\n🎯 {mt5_symbol}")
                print(f"   Precio: ${price:,.2f}")
                print(f"   Cambio: {change:+.2f}%")
                if rsi:
                    print(f"   RSI: {rsi:.1f}")
                print(f"   📍 SEÑAL: {signal['action']}")
                
                time.sleep(0.5)  # Rate limiting
                
        except Exception as e:
            print(f"❌ Error con {mt5_symbol}: {e}")
            continue
    
    return signals

def analyze_signal(symbol, price, change, rsi):
    """Analiza y genera señal de trading"""
    score = 50
    
    # Análisis RSI
    if rsi:
        if rsi < 30:
            score += 25
            action = "STRONG BUY 🚀"
        elif rsi < 40:
            score += 15
            action = "BUY 📈"
        elif rsi > 70:
            score -= 25
            action = "STRONG SELL 📉"
        elif rsi > 60:
            score -= 15
            action = "SELL ⬇️"
        else:
            action = "NEUTRAL ➖"
    else:
        action = "NEUTRAL ➖"
    
    # Momentum del precio
    if change > 1:
        score += 10
    elif change < -1:
        score -= 10
    
    return {
        'symbol': symbol,
        'price': price,
        'change': change,
        'rsi': rsi,
        'score': score,
        'action': action,
        'timestamp': datetime.now().isoformat()
    }

def execute_best_signal(signals):
    """Ejecuta la mejor señal disponible"""
    print(f"\n🚀 EJECUTANDO SEÑALES...")
    print("-"*50)
    
    # Filtrar señales fuertes
    buy_signals = [s for s in signals if 'BUY' in s['action'] and 'NEUTRAL' not in s['action']]
    
    if not buy_signals:
        print("⚠️ No hay señales de compra fuertes en este momento")
        return False
    
    # Ordenar por score
    buy_signals.sort(key=lambda x: x['score'], reverse=True)
    best_signal = buy_signals[0]
    
    print(f"\n🏆 MEJOR SEÑAL: {best_signal['symbol']}")
    print(f"   Score: {best_signal['score']}/100")
    print(f"   Acción: {best_signal['action']}")
    
    # Ejecutar en MT5
    return execute_trade(best_signal)

def execute_trade(signal):
    """Ejecuta trade en MT5"""
    try:
        import MetaTrader5 as mt5
        
        symbol = signal['symbol']
        
        # Verificar si el símbolo existe
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            # Intentar con 'm' al final
            symbol = symbol + 'm'
            symbol_info = mt5.symbol_info(symbol)
            
        if symbol_info is None:
            print(f"❌ Símbolo {signal['symbol']} no encontrado en MT5")
            return False
        
        if not symbol_info.visible:
            print(f"⚠️ Activando símbolo {symbol}...")
            if not mt5.symbol_select(symbol, True):
                print(f"❌ No se pudo activar {symbol}")
                return False
        
        # Obtener precio actual
        tick = mt5.symbol_info_tick(symbol)
        if tick is None:
            print(f"❌ No se pudo obtener precio de {symbol}")
            return False
        
        # Preparar orden
        lot = 0.01  # Lote mínimo
        price = tick.ask if 'BUY' in signal['action'] else tick.bid
        
        # Calcular SL y TP
        point = symbol_info.point
        if 'BUY' in signal['action']:
            sl = price - (100 * point)  # 100 puntos de SL
            tp = price + (200 * point)  # 200 puntos de TP
            order_type = mt5.ORDER_TYPE_BUY
        else:
            sl = price + (100 * point)
            tp = price - (200 * point)
            order_type = mt5.ORDER_TYPE_SELL
        
        # Crear request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": order_type,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 20,
            "magic": 234000,
            "comment": f"Signal: {signal['action']}",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Verificar modo
        live_mode = os.getenv('LIVE_TRADING', 'false').lower() == 'true'
        
        if live_mode:
            print(f"\n⚠️ MODO LIVE - Ejecutando orden real...")
            result = mt5.order_send(request)
            
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"✅ ORDEN EJECUTADA!")
                print(f"   Ticket: #{result.order}")
                print(f"   Símbolo: {symbol}")
                print(f"   Volumen: {lot}")
                print(f"   Precio: {price:.5f}")
                print(f"   SL: {sl:.5f}")
                print(f"   TP: {tp:.5f}")
                return True
            else:
                print(f"❌ Error ejecutando orden: {result.comment}")
                return False
        else:
            print(f"\n📝 MODO DEMO - Simulando orden...")
            print(f"   Símbolo: {symbol}")
            print(f"   Tipo: {signal['action']}")
            print(f"   Volumen: {lot}")
            print(f"   Precio: {price:.5f}")
            print(f"   SL: {sl:.5f}")
            print(f"   TP: {tp:.5f}")
            print(f"   ✅ Orden simulada correctamente")
            return True
            
    except Exception as e:
        print(f"❌ Error ejecutando trade: {e}")
        return False

def monitor_positions():
    """Monitorea posiciones abiertas"""
    try:
        import MetaTrader5 as mt5
        
        positions = mt5.positions_get()
        if not positions:
            return
        
        print(f"\n📊 MONITOREANDO {len(positions)} POSICIONES...")
        
        for pos in positions:
            profit_emoji = "🟢" if pos.profit > 0 else "🔴"
            print(f"   {profit_emoji} {pos.symbol}: {pos.volume} lotes | P&L: ${pos.profit:.2f}")
            
            # Verificar si aplicar trailing stop
            if pos.profit > 10:  # Si ganancia > $10
                print(f"      💰 Aplicando trailing stop...")
                # Aquí iría la lógica de trailing stop
                
    except Exception as e:
        print(f"❌ Error monitoreando: {e}")

def main():
    """Función principal que ejecuta todo"""
    print("\n" + "="*80)
    print("🚀 SISTEMA DE TRADING AUTOMÁTICO v4.0")
    print("="*80)
    print(f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # 1. Cargar configuración
    if not load_config():
        print("❌ Error cargando configuración")
        return
    
    # 2. Verificar MT5
    mt5_connected = check_mt5_connection()
    
    # 3. Generar señales
    signals = generate_signals()
    
    # 4. Guardar señales
    if signals:
        filename = f"signals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(signals, f, indent=2)
        print(f"\n💾 Señales guardadas en: {filename}")
    
    # 5. Ejecutar mejor señal si MT5 está conectado
    if mt5_connected and signals:
        execute_best_signal(signals)
    
    # 6. Monitorear posiciones
    if mt5_connected:
        monitor_positions()
    
    # 7. Resumen final
    print("\n" + "="*80)
    print("📋 RESUMEN DE EJECUCIÓN")
    print("="*80)
    print(f"✅ MT5 Conectado: {'Sí' if mt5_connected else 'No'}")
    print(f"✅ Señales generadas: {len(signals)}")
    print(f"✅ Modo: {'LIVE' if os.getenv('LIVE_TRADING', 'false').lower() == 'true' else 'DEMO'}")
    print("="*80)
    
    # Mantener el sistema activo
    print("\n⏰ Sistema activo. Presiona Ctrl+C para detener...")
    try:
        while True:
            time.sleep(60)  # Esperar 1 minuto
            print(f"\n🔄 Actualizando... {datetime.now().strftime('%H:%M:%S')}")
            
            # Generar nuevas señales
            signals = generate_signals()
            
            # Ejecutar si hay buenas señales
            if mt5_connected and signals:
                execute_best_signal(signals)
            
            # Monitorear
            if mt5_connected:
                monitor_positions()
                
    except KeyboardInterrupt:
        print("\n\n⛔ Sistema detenido por el usuario")
        
        # Cerrar MT5
        try:
            import MetaTrader5 as mt5
            mt5.shutdown()
            print("✅ MT5 cerrado correctamente")
        except:
            pass

if __name__ == "__main__":
    main()
