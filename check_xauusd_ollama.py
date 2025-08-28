#!/usr/bin/env python3
"""
Verificar XAUUSD disponibilidad y sistema Ollama IA
"""
import MetaTrader5 as mt5
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv('.env')

def check_xauusd_availability():
    """Verificar si XAUUSD está disponible en Exness"""
    print("=== VERIFICANDO XAUUSD ===")
    
    if not mt5.initialize():
        print("ERROR: No se pudo conectar a MT5")
        return None
    
    # Buscar variantes de oro
    gold_symbols = ['XAUUSD', 'XAU/USD', 'GOLD', 'GOLDm', 'XAUUSDm']
    found_symbols = []
    
    symbols = mt5.symbols_get()
    
    for gold_name in gold_symbols:
        for symbol in symbols:
            if gold_name.upper() in symbol.name.upper():
                # Intentar activar en Market Watch
                if mt5.symbol_select(symbol.name, True):
                    tick = mt5.symbol_info_tick(symbol.name)
                    if tick and tick.bid > 0:
                        print(f"✓ {symbol.name}: ${tick.bid:.2f}")
                        found_symbols.append(symbol.name)
    
    if not found_symbols:
        print("❌ No se encontró XAUUSD ni variantes de oro")
        
        # Mostrar símbolos disponibles que contengan metal
        print("\nBuscando metales disponibles:")
        metal_count = 0
        for symbol in symbols:
            if any(metal in symbol.name.upper() for metal in ['XAG', 'SILVER', 'PLAT', 'PALL']):
                if mt5.symbol_select(symbol.name, True):
                    tick = mt5.symbol_info_tick(symbol.name)
                    if tick:
                        print(f"  {symbol.name}: ${tick.bid:.2f}")
                        metal_count += 1
        
        if metal_count == 0:
            print("No hay metales disponibles en esta cuenta")
    
    mt5.shutdown()
    return found_symbols

def test_ollama_connection():
    """Probar conexión con Ollama"""
    print("\n=== VERIFICANDO OLLAMA ===")
    
    ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
    ollama_model = os.getenv('OLLAMA_MODEL', 'deepseek-r1:14b')
    
    print(f"Host: {ollama_host}")
    print(f"Modelo: {ollama_model}")
    
    try:
        # Verificar si Ollama está corriendo
        response = requests.get(f"{ollama_host}/api/tags", timeout=5)
        
        if response.status_code == 200:
            models = response.json()
            available_models = [model['name'] for model in models.get('models', [])]
            print(f"✓ Ollama conectado")
            print(f"Modelos disponibles: {available_models}")
            
            if ollama_model in available_models:
                print(f"✓ Modelo {ollama_model} disponible")
                return True
            else:
                print(f"❌ Modelo {ollama_model} no encontrado")
                if available_models:
                    print(f"Usar: {available_models[0]}")
                return False
        else:
            print(f"❌ Error Ollama: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Ollama no está corriendo")
        print("Para iniciar Ollama:")
        print("1. Abrir terminal")
        print("2. Ejecutar: ollama serve")
        print("3. En otra terminal: ollama pull deepseek-r1:14b")
        return False
    except Exception as e:
        print(f"❌ Error conectando Ollama: {e}")
        return False

def test_ai_signal_detection():
    """Probar detección de señales con IA"""
    print("\n=== PROBANDO DETECCIÓN IA ===")
    
    try:
        # Importar el módulo de validación IA
        from ai.ollama_validator import validate_signal
        
        # Crear datos de prueba simulando una señal fuerte
        test_snapshot = {
            "symbol": "XAUUSD",
            "price": 2650.50,
            "rsi": 35.2,
            "macd": 0.15,
            "sma_5": 2648.30,
            "sma_10": 2645.80,
            "sma_20": 2640.20,
            "trend": "alcista",
            "analysis": "Precio por encima de medias móviles, RSI en zona de sobreventa recuperándose, MACD positivo"
        }
        
        print("Enviando datos de prueba a IA:")
        print(f"  Símbolo: {test_snapshot['symbol']}")
        print(f"  Precio: ${test_snapshot['price']}")
        print(f"  RSI: {test_snapshot['rsi']}")
        print(f"  Tendencia: {test_snapshot['trend']}")
        
        # Validar con IA
        ai_result = validate_signal(test_snapshot)
        
        if ai_result:
            print(f"\n🤖 RESPUESTA IA:")
            print(f"  Señal: {ai_result.get('signal', 'N/A')}")
            print(f"  Confianza: {ai_result.get('confidence', 0):.1%}")
            print(f"  Razón: {ai_result.get('reason', 'N/A')}")
            return True
        else:
            print("❌ IA no devolvió respuesta")
            return False
            
    except ImportError:
        print("❌ Módulo de IA no encontrado")
        return False
    except Exception as e:
        print(f"❌ Error en IA: {e}")
        return False

def run_complete_check():
    """Ejecutar verificación completa"""
    print("=" * 60)
    print("VERIFICACIÓN XAUUSD + SISTEMA IA OLLAMA")
    print("=" * 60)
    
    # 1. Verificar XAUUSD
    gold_symbols = check_xauusd_availability()
    
    # 2. Verificar Ollama
    ollama_ok = test_ollama_connection()
    
    # 3. Probar IA
    ai_ok = test_ai_signal_detection()
    
    print("\n" + "=" * 60)
    print("RESUMEN:")
    print(f"✓ XAUUSD disponible: {'SÍ' if gold_symbols else 'NO'}")
    if gold_symbols:
        print(f"  Símbolos oro: {', '.join(gold_symbols)}")
    print(f"✓ Ollama funcionando: {'SÍ' if ollama_ok else 'NO'}")
    print(f"✓ IA detectando señales: {'SÍ' if ai_ok else 'NO'}")
    
    if gold_symbols and ollama_ok and ai_ok:
        print(f"\n🎉 SISTEMA COMPLETO LISTO:")
        print(f"  - Trading con oro disponible")
        print(f"  - IA Ollama operativa")
        print(f"  - Detección de señales fuertes habilitada")
        return True
    else:
        print(f"\n⚠️ SISTEMA NECESITA CONFIGURACIÓN:")
        if not gold_symbols:
            print(f"  - Agregar símbolos de oro a Market Watch")
        if not ollama_ok:
            print(f"  - Iniciar servidor Ollama")
        if not ai_ok:
            print(f"  - Verificar módulo de IA")
        return False

if __name__ == "__main__":
    run_complete_check()