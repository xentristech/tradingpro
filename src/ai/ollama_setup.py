"""
SCRIPT COMPLETO DE VERIFICACIÓN Y CONFIGURACIÓN DE OLLAMA
"""
import os
import sys
import subprocess
import time
import json
import platform
from pathlib import Path

def print_header(text):
    print("="*70)
    print(f"   {text}")
    print("="*70)
    print()

def check_command_exists(command):
    """Verifica si un comando existe en el sistema"""
    try:
        subprocess.run([command, "--version"], capture_output=True, timeout=3)
        return True
    except:
        return False

def test_http_connection():
    """Prueba la conexión HTTP a Ollama"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        return response.status_code == 200, response.json() if response.status_code == 200 else None
    except:
        return False, None

def find_ollama_installation():
    """Busca dónde está instalado Ollama"""
    possible_paths = [
        Path.home() / "AppData/Local/Programs/Ollama/ollama.exe",
        Path.home() / "AppData/Local/Ollama/ollama.exe",
        Path("C:/Program Files/Ollama/ollama.exe"),
        Path("C:/ollama/ollama.exe"),
    ]
    
    for path in possible_paths:
        if path.exists():
            return str(path)
    return None

def main():
    print_header("VERIFICACIÓN COMPLETA DE OLLAMA PARA TRADING BOT")
    
    # 1. Sistema Operativo
    print("📋 INFORMACIÓN DEL SISTEMA")
    print(f"   OS: {platform.system()} {platform.release()}")
    print(f"   Python: {sys.version.split()[0]}")
    print()
    
    # 2. Verificar instalación
    print("🔍 VERIFICANDO INSTALACIÓN DE OLLAMA")
    print("-"*40)
    
    ollama_in_path = check_command_exists("ollama")
    ollama_path = find_ollama_installation()
    
    if ollama_in_path:
        print("✅ Ollama está instalado y en el PATH")
        
        # Obtener versión
        try:
            result = subprocess.run(["ollama", "--version"], capture_output=True, text=True)
            print(f"   Versión: {result.stdout.strip()}")
        except:
            pass
            
    elif ollama_path:
        print(f"⚠️ Ollama encontrado pero no en PATH: {ollama_path}")
        print("   Añade Ollama al PATH del sistema para usar desde cualquier lugar")
    else:
        print("❌ Ollama NO está instalado")
        print("\n" + "="*70)
        print("📥 INSTRUCCIONES PARA INSTALAR OLLAMA:")
        print("="*70)
        print("""
1. Abre tu navegador y ve a:
   🌐 https://ollama.ai/download

2. Haz clic en "Download for Windows"

3. Ejecuta el instalador descargado (OllamaSetup.exe)

4. Sigue las instrucciones del instalador

5. Después de instalar:
   - Abre una terminal nueva (CMD o PowerShell)
   - Ejecuta: ollama serve
   
6. Descarga un modelo (en otra terminal):
   - Para trading (8GB): ollama pull deepseek-r1:14b
   - Alternativa ligera (4.7GB): ollama pull llama3
   - Más ligero (2.3GB): ollama pull phi3

7. Vuelve a ejecutar este script
        """)
        return
    
    print()
    
    # 3. Verificar si está ejecutándose
    print("🔌 VERIFICANDO SERVICIO OLLAMA")
    print("-"*40)
    
    is_running, api_data = test_http_connection()
    
    if is_running:
        print("✅ Ollama está EJECUTÁNDOSE en http://localhost:11434")
        
        if api_data and "models" in api_data:
            models = api_data["models"]
            print(f"\n📦 MODELOS INSTALADOS: {len(models)}")
            
            if models:
                print("-"*40)
                for model in models:
                    name = model.get("name", "desconocido")
                    size_gb = model.get("size", 0) / (1024**3)
                    modified = model.get("modified_at", "")[:10]
                    print(f"   • {name}")
                    print(f"     Tamaño: {size_gb:.1f} GB | Modificado: {modified}")
                    
                # Verificar modelos recomendados
                model_names = [m.get("name", "") for m in models]
                
                recommended = {
                    "deepseek-r1:14b": "Mejor para trading (8GB)",
                    "deepseek-r1": "Versión general DeepSeek",
                    "llama3.1": "Buena alternativa (4.7GB)",
                    "llama3": "Alternativa estable",
                    "mistral": "Rápido y eficiente (4.1GB)",
                    "phi3": "Más ligero (2.3GB)"
                }
                
                print("\n🎯 MODELOS RECOMENDADOS PARA TRADING:")
                print("-"*40)
                
                found_recommended = False
                for model_key, description in recommended.items():
                    if any(model_key in name for name in model_names):
                        print(f"   ✅ {model_key}: {description}")
                        found_recommended = True
                        
                if not found_recommended:
                    print("   ⚠️ No tienes ningún modelo recomendado")
                    print("\n   📥 Instala uno con:")
                    print("      ollama pull deepseek-r1:14b  (mejor)")
                    print("      ollama pull llama3  (alternativa)")
                    
            else:
                print("   ⚠️ No hay modelos instalados")
                print("\n📥 INSTALA UN MODELO:")
                print("   ollama pull deepseek-r1:14b  (8GB, mejor para trading)")
                print("   ollama pull llama3  (4.7GB, buena alternativa)")
                print("   ollama pull phi3  (2.3GB, más ligero)")
                
    else:
        print("❌ Ollama NO está ejecutándose")
        print("\n🚀 PARA INICIAR OLLAMA:")
        print("-"*40)
        print("1. Abre una terminal nueva (CMD o PowerShell)")
        print("2. Ejecuta: ollama serve")
        print("3. Deja esa terminal abierta")
        print("4. Vuelve a ejecutar este script")
        
        if ollama_in_path or ollama_path:
            print("\n💡 Intentando iniciar Ollama automáticamente...")
            
            try:
                # Intentar iniciar Ollama
                cmd = "ollama" if ollama_in_path else ollama_path
                subprocess.Popen([cmd, "serve"], 
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
                
                print("   Esperando 5 segundos...")
                time.sleep(5)
                
                # Verificar de nuevo
                is_running, _ = test_http_connection()
                if is_running:
                    print("   ✅ ¡Ollama iniciado correctamente!")
                else:
                    print("   ❌ Ollama no respondió después de iniciar")
                    print("   Intenta iniciarlo manualmente")
            except Exception as e:
                print(f"   ❌ Error al iniciar: {e}")
    
    print()
    
    # 4. Verificar archivo .env
    print("⚙️ VERIFICANDO CONFIGURACIÓN DEL BOT")
    print("-"*40)
    
    env_file = Path("configs/.env")
    if env_file.exists():
        with open(env_file, 'r') as f:
            env_content = f.read()
            
        if "OLLAMA_API_BASE" in env_content:
            print("✅ Configuración de Ollama encontrada en .env")
            
            # Extraer valores
            for line in env_content.split('\n'):
                if line.startswith("OLLAMA_MODEL"):
                    model = line.split('=')[1].strip()
                    print(f"   Modelo configurado: {model}")
                    
                    # Verificar si el modelo está instalado
                    if is_running and api_data:
                        model_names = [m.get("name", "") for m in api_data.get("models", [])]
                        if any(model in name for name in model_names):
                            print(f"   ✅ Modelo {model} está instalado")
                        else:
                            print(f"   ⚠️ Modelo {model} NO está instalado")
                            print(f"      Instálalo con: ollama pull {model}")
        else:
            print("⚠️ No hay configuración de Ollama en .env")
    else:
        print("❌ No existe el archivo configs/.env")
    
    print()
    
    # 5. Resumen final
    print_header("RESUMEN Y RECOMENDACIONES")
    
    if ollama_in_path and is_running:
        print("🎉 ¡OLLAMA ESTÁ LISTO PARA USAR!")
        print("\n✅ Tu bot puede usar IA para tomar decisiones inteligentes")
        print("\n💡 SIGUIENTE PASO:")
        print("   Ejecuta el bot con: .\\EJECUTAR_SISTEMA.bat")
        
    elif ollama_in_path and not is_running:
        print("⚠️ OLLAMA INSTALADO PERO NO EJECUTÁNDOSE")
        print("\n💡 ACCIÓN REQUERIDA:")
        print("   1. Abre una terminal")
        print("   2. Ejecuta: ollama serve")
        print("   3. Deja la terminal abierta")
        print("   4. Ejecuta el bot")
        
    else:
        print("❌ OLLAMA NO ESTÁ INSTALADO")
        print("\n💡 ACCIÓN REQUERIDA:")
        print("   1. Ve a https://ollama.ai/download")
        print("   2. Descarga e instala Ollama")
        print("   3. Ejecuta: ollama serve")
        print("   4. Descarga un modelo: ollama pull llama3")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
    
    print()
    input("Presiona Enter para salir...")
