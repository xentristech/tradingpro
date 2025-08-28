"""
VERIFICACIÓN RÁPIDA DE OLLAMA
"""
import subprocess
import requests
import json
import time

print("="*60)
print("   VERIFICACIÓN RÁPIDA DE OLLAMA")
print("="*60)
print()

# 1. Verificar si Ollama está instalado
print("1️⃣ VERIFICANDO INSTALACIÓN...")
try:
    result = subprocess.run(["ollama", "--version"], capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        print(f"✅ Ollama instalado: {result.stdout.strip()}")
        ollama_installed = True
    else:
        print("❌ Ollama no encontrado")
        ollama_installed = False
except:
    print("❌ Ollama NO está instalado")
    print("\n📥 INSTALAR OLLAMA:")
    print("   1. Ve a: https://ollama.ai/download")
    print("   2. Descarga e instala Ollama para Windows")
    ollama_installed = False

print()

# 2. Verificar si está ejecutándose
print("2️⃣ VERIFICANDO SERVICIO...")
try:
    response = requests.get("http://localhost:11434/api/tags", timeout=3)
    if response.status_code == 200:
        print("✅ Ollama está EJECUTÁNDOSE")
        data = response.json()
        models = data.get("models", [])
        
        print(f"\n📦 Modelos disponibles: {len(models)}")
        for model in models[:5]:  # Mostrar máx 5
            name = model.get("name", "")
            size_gb = model.get("size", 0) / (1024**3)
            print(f"   • {name} ({size_gb:.1f} GB)")
            
        # Buscar DeepSeek
        has_deepseek = any("deepseek" in m.get("name", "").lower() for m in models)
        if has_deepseek:
            print("\n✅ DeepSeek-R1 está disponible")
        else:
            print("\n⚠️ DeepSeek-R1 NO está instalado")
            print("   Para instalarlo: ollama pull deepseek-r1:14b")
            
        ollama_running = True
    else:
        print("❌ Ollama responde pero con error")
        ollama_running = False
        
except requests.ConnectionError:
    print("❌ Ollama NO está ejecutándose")
    
    if ollama_installed:
        print("\n🚀 Intentando iniciar Ollama...")
        try:
            # Intentar iniciar
            subprocess.Popen(["ollama", "serve"], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL,
                           creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0)
            
            print("   Esperando 5 segundos...")
            for i in range(5, 0, -1):
                print(f"   {i}...", end='\r')
                time.sleep(1)
                
            # Verificar de nuevo
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=3)
                if response.status_code == 200:
                    print("\n✅ Ollama iniciado correctamente!")
                    ollama_running = True
                else:
                    print("\n❌ Ollama no respondió después de iniciar")
                    ollama_running = False
            except:
                print("\n❌ No se pudo conectar a Ollama")
                ollama_running = False
                
        except Exception as e:
            print(f"\n❌ Error iniciando Ollama: {e}")
            ollama_running = False
    else:
        print("   Primero instala Ollama")
        ollama_running = False

print()

# 3. Test rápido si está funcionando
if ollama_running:
    print("3️⃣ PROBANDO RESPUESTA DE IA...")
    
    try:
        # Buscar qué modelo usar
        response = requests.get("http://localhost:11434/api/tags")
        models = response.json().get("models", [])
        
        # Prioridad de modelos
        model_priority = ["deepseek-r1:14b", "deepseek-r1", "llama3.1", "llama3", "mistral", "phi3"]
        selected_model = None
        
        for priority_model in model_priority:
            if any(priority_model in m.get("name", "") for m in models):
                selected_model = priority_model
                break
                
        if selected_model:
            print(f"   Usando modelo: {selected_model}")
            
            # Hacer una prueba simple
            test_data = {
                "model": selected_model,
                "prompt": "Responde solo 'OK' si funcionas",
                "stream": False
            }
            
            response = requests.post(
                "http://localhost:11434/api/generate",
                json=test_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("response"):
                    print(f"✅ IA respondió: {result['response'][:50]}")
                    print("\n🎉 ¡OLLAMA ESTÁ LISTO PARA EL BOT!")
                else:
                    print("⚠️ IA respondió pero sin contenido")
            else:
                print(f"❌ Error en respuesta: {response.status_code}")
        else:
            print("❌ No hay modelos instalados")
            print("\n📥 INSTALAR UN MODELO:")
            print("   ollama pull llama3  (más ligero, 4.7GB)")
            print("   ollama pull deepseek-r1:14b  (mejor para trading, 8GB)")
            
    except Exception as e:
        print(f"❌ Error probando IA: {e}")

print()
print("="*60)
print("   RESUMEN")
print("="*60)

# Resumen final
if ollama_installed and ollama_running:
    print("✅ OLLAMA FUNCIONA CORRECTAMENTE")
    print("\n✨ Tu bot puede usar IA para tomar decisiones")
elif ollama_installed and not ollama_running:
    print("⚠️ Ollama instalado pero NO ejecutándose")
    print("\n💡 Ejecuta en terminal: ollama serve")
else:
    print("❌ OLLAMA NO ESTÁ INSTALADO")
    print("\n📥 Descarga desde: https://ollama.ai/download")

print()
input("Presiona Enter para salir...")
