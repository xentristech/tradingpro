import MetaTrader5 as mt5
import requests
import os
from dotenv import load_dotenv

load_dotenv('.env')

print("=== VERIFICACION XAUUSD + OLLAMA ===")

# 1. Verificar XAUUSD
print("\n1. VERIFICANDO XAUUSD:")
mt5.initialize()

symbols = mt5.symbols_get()
gold_found = False

# Buscar oro
for symbol in symbols:
    if 'XAU' in symbol.name.upper() or 'GOLD' in symbol.name.upper():
        if mt5.symbol_select(symbol.name, True):
            tick = mt5.symbol_info_tick(symbol.name)
            if tick and tick.bid > 0:
                print(f"ENCONTRADO: {symbol.name} = ${tick.bid:.2f}")
                gold_found = True

if not gold_found:
    print("NO SE ENCONTRO XAUUSD - probando agregar manualmente...")
    
    # Intentar agregar XAUUSD manualmente
    gold_variants = ['XAUUSD', 'XAU/USD', 'GOLD', 'GOLDm']
    for variant in gold_variants:
        if mt5.symbol_select(variant, True):
            tick = mt5.symbol_info_tick(variant)
            if tick:
                print(f"AGREGADO: {variant} = ${tick.bid:.2f}")
                gold_found = True
                break

mt5.shutdown()

# 2. Verificar Ollama
print("\n2. VERIFICANDO OLLAMA:")
ollama_host = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
ollama_model = os.getenv('OLLAMA_MODEL', 'deepseek-r1:14b')

print(f"Host: {ollama_host}")
print(f"Modelo: {ollama_model}")

ollama_ok = False
try:
    response = requests.get(f"{ollama_host}/api/tags", timeout=5)
    if response.status_code == 200:
        models = response.json()
        available = [m['name'] for m in models.get('models', [])]
        print(f"Ollama CONECTADO")
        print(f"Modelos: {available}")
        
        if ollama_model in available:
            print(f"Modelo {ollama_model} DISPONIBLE")
            ollama_ok = True
        else:
            print(f"Modelo {ollama_model} NO ENCONTRADO")
    else:
        print(f"Error Ollama: {response.status_code}")
        
except Exception as e:
    print(f"Ollama NO CONECTADO: {e}")
    print("Para iniciar Ollama:")
    print("1. Abrir terminal: ollama serve")
    print("2. Instalar modelo: ollama pull deepseek-r1:14b")

# 3. Probar sistema IA
print("\n3. PROBANDO SISTEMA IA:")
ai_ok = False

try:
    from ai.ollama_validator import validate_signal
    
    test_data = {
        "symbol": "XAUUSD",
        "price": 2650.50,
        "rsi": 35.2,
        "analysis": "RSI sobreventa recuperandose, tendencia alcista"
    }
    
    print("Enviando datos prueba a IA...")
    result = validate_signal(test_data)
    
    if result:
        print(f"IA RESPONDE:")
        print(f"  Signal: {result.get('signal', 'N/A')}")
        print(f"  Confidence: {result.get('confidence', 0):.1%}")
        print(f"  Reason: {result.get('reason', 'N/A')}")
        ai_ok = True
    else:
        print("IA no respondio")
        
except Exception as e:
    print(f"Error IA: {e}")

# RESUMEN
print("\n=== RESUMEN ===")
print(f"XAUUSD: {'OK' if gold_found else 'NO'}")
print(f"Ollama: {'OK' if ollama_ok else 'NO'}")  
print(f"IA Signals: {'OK' if ai_ok else 'NO'}")

if gold_found and ollama_ok and ai_ok:
    print("\nSISTEMA COMPLETO LISTO!")
else:
    print("\nNECESITA CONFIGURACION")