"""
VERIFICACIÓN Y CONFIGURACIÓN DE OLLAMA
Script para verificar que la IA esté funcionando
"""
import os
import sys
import json
import time
import subprocess
import requests
from pathlib import Path

print("="*70)
print(" "*20 + "VERIFICACIÓN DE IA (OLLAMA)")
print("="*70)
print()

# ========== PASO 1: VERIFICAR SI OLLAMA ESTÁ INSTALADO ==========
print("[1] VERIFICANDO INSTALACIÓN DE OLLAMA")
print("-"*40)

ollama_installed = False
try:
    result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
    if result.returncode == 0:
        print(f"✅ Ollama instalado: {result.stdout.strip()}")
        ollama_installed = True
    else:
        print("❌ Ollama no está instalado")
except FileNotFoundError:
    print("❌ Ollama no está instalado")
except Exception as e:
    print(f"❌ Error verificando Ollama: {e}")

if not ollama_installed:
    print("\n📥 INSTRUCCIONES PARA INSTALAR OLLAMA:")
    print("   1. Ve a: https://ollama.ai/download")
    print("   2. Descarga Ollama para Windows")
    print("   3. Instala y ejecuta Ollama")
    print("   4. En una terminal, ejecuta: ollama pull deepseek-r1:14b")
    print("\n⚠️ Sin Ollama, el bot NO podrá tomar decisiones inteligentes")
    
print()

# ========== PASO 2: VERIFICAR SI OLLAMA ESTÁ EJECUTÁNDOSE ==========
print("[2] VERIFICANDO SERVICIO OLLAMA")
print("-"*40)

ollama_running = False
try:
    response = requests.get("http://localhost:11434/api/tags", timeout=2)
    if response.status_code == 200:
        print("✅ Ollama está ejecutándose")
        ollama_running = True
        
        # Listar modelos disponibles
        data = response.json()
        models = data.get("models", [])
        if models:
            print("\n📦 MODELOS DISPONIBLES:")
            for model in models:
                name = model.get("name", "")
                size = model.get("size", 0) / (1024**3)  # Convertir a GB
                print(f"   - {name} ({size:.1f} GB)")
        else:
            print("⚠️ No hay modelos descargados")
            
    else:
        print("❌ Ollama responde pero con error")
        
except requests.ConnectionError:
    print("❌ Ollama NO está ejecutándose")
    print("\n🚀 INTENTANDO INICIAR OLLAMA...")
    
    try:
        # Intentar iniciar Ollama
        subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("   Esperando 5 segundos...")
        time.sleep(5)
        
        # Verificar de nuevo
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            print("✅ Ollama iniciado correctamente")
            ollama_running = True
        else:
            print("❌ No se pudo iniciar Ollama")
            
    except Exception as e:
        print(f"❌ Error iniciando Ollama: {e}")
        
except Exception as e:
    print(f"❌ Error conectando a Ollama: {e}")

print()

# ========== PASO 3: VERIFICAR MODELO DEEPSEEK ==========
print("[3] VERIFICANDO MODELO DEEPSEEK-R1:14B")
print("-"*40)

model_available = False
if ollama_running:
    try:
        response = requests.get("http://localhost:11434/api/tags")
        data = response.json()
        models = [m.get("name", "") for m in data.get("models", [])]
        
        if "deepseek-r1:14b" in models:
            print("✅ Modelo deepseek-r1:14b disponible")
            model_available = True
        else:
            print("❌ Modelo deepseek-r1:14b NO está descargado")
            
            # Verificar modelos alternativos
            alt_models = ["llama3.1", "llama3", "mistral", "phi3", "gemma"]
            available_alt = [m for m in alt_models if any(m in model for model in models)]
            
            if available_alt:
                print(f"\n📦 MODELOS ALTERNATIVOS DISPONIBLES:")
                for model in available_alt:
                    print(f"   - {model}")
                print("\n💡 Puedes usar uno de estos modelos cambiando OLLAMA_MODEL en configs/.env")
            
            print("\n📥 PARA DESCARGAR DEEPSEEK:")
            print("   Ejecuta en terminal: ollama pull deepseek-r1:14b")
            print("   Nota: El modelo pesa ~8GB")
            
    except Exception as e:
        print(f"❌ Error verificando modelos: {e}")
        
print()

# ========== PASO 4: PROBAR LA IA ==========
print("[4] PROBANDO LA IA CON UNA SEÑAL REAL")
print("-"*40)

if ollama_running:
    from dotenv import load_dotenv
    load_dotenv('configs/.env')
    
    # Configurar cliente
    from openai import OpenAI
    
    api_base = os.getenv("OLLAMA_API_BASE", "http://localhost:11434/v1")
    model = os.getenv("OLLAMA_MODEL", "deepseek-r1:14b")
    
    print(f"Usando modelo: {model}")
    print("Enviando consulta de prueba...")
    
    try:
        client = OpenAI(base_url=api_base, api_key="ollama")
        
        # Prompt de prueba
        test_prompt = {
            "symbol": "BTCUSDm",
            "precio": 118000,
            "tabla": [
                {"tf": "5m", "rsi": 35, "macd_hist": -30, "rvol": 1.5},
                {"tf": "15m", "rsi": 38, "macd_hist": -25, "rvol": 1.3},
                {"tf": "1h", "rsi": 42, "macd_hist": -10, "rvol": 1.1}
            ]
        }
        
        response = client.chat.completions.create(
            model=model,
            temperature=0.2,
            messages=[
                {"role": "system", "content": "Eres un trader. Responde con JSON: {\"senal_final\":\"COMPRA/VENTA/NO OPERAR\", \"confianza\":0.0-1.0, \"razon\":\"texto\"}"},
                {"role": "user", "content": json.dumps(test_prompt)}
            ],
            max_tokens=200
        )
        
        if response and response.choices:
            ai_response = response.choices[0].message.content
            print("\n✅ IA RESPONDIÓ:")
            print("-"*40)
            
            try:
                # Intentar parsear JSON
                json_response = json.loads(ai_response)
                print(f"Señal: {json_response.get('senal_final', 'N/A')}")
                print(f"Confianza: {json_response.get('confianza', 0):.1%}")
                print(f"Razón: {json_response.get('razon', 'N/A')}")
            except:
                # Si no es JSON, mostrar respuesta cruda
                print(ai_response[:200])
                
            print("\n🎉 ¡LA IA ESTÁ FUNCIONANDO CORRECTAMENTE!")
            
        else:
            print("❌ La IA no respondió")
            
    except Exception as e:
        print(f"❌ Error al probar la IA: {e}")
        
        # Verificar si es problema del modelo
        if "model" in str(e).lower():
            print("\n💡 SOLUCIÓN:")
            print("   1. Descarga el modelo: ollama pull deepseek-r1:14b")
            print("   2. O usa otro modelo disponible")
            
else:
    print("⚠️ No se puede probar la IA porque Ollama no está ejecutándose")

print()

# ========== RESUMEN FINAL ==========
print("="*70)
print(" "*20 + "RESUMEN DE ESTADO")
print("="*70)
print()

status = {
    "Ollama instalado": ollama_installed,
    "Ollama ejecutándose": ollama_running,
    "Modelo disponible": model_available,
    "IA funcionando": ollama_running and model_available
}

all_ok = True
for item, ok in status.items():
    icon = "✅" if ok else "❌"
    print(f"   {icon} {item}")
    if not ok:
        all_ok = False

print()

if all_ok:
    print("🎉 ¡TODO LISTO! La IA puede generar señales de trading")
else:
    print("⚠️ Hay problemas con la IA que necesitan resolverse")
    print("\n📝 PASOS PARA SOLUCIONAR:")
    
    if not ollama_installed:
        print("   1. Instalar Ollama desde https://ollama.ai/download")
        
    if not ollama_running:
        print("   2. Ejecutar Ollama: ollama serve")
        
    if not model_available:
        print("   3. Descargar modelo: ollama pull deepseek-r1:14b")

print()
print("💡 NOTA: El bot puede funcionar sin IA, pero NO tomará decisiones inteligentes")
print()

input("Presiona Enter para salir...")
