#!/usr/bin/env python3
import requests
import json

# Probar Ollama directamente
host = 'http://localhost:11434'
model = 'deepseek-r1:14b'

prompt = """Eres un experto analista de trading. Analiza estos datos del mercado:

- Símbolo: XAUUSD  
- Precio: $2650.50
- RSI: 35.2
- Tendencia: alcista

Dame tu recomendación en este formato JSON exacto:
{"signal": "BUY", "confidence": 85, "reason": "RSI oversold recovering"}

Solo responde el JSON, nada más."""

print("Enviando prompt a IA...")
print("Prompt:", prompt[:100] + "...")

try:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 100
        }
    }
    
    response = requests.post(f"{host}/api/generate", json=payload, timeout=20)
    
    if response.status_code == 200:
        result = response.json()
        ai_response = result.get('response', '')
        
        print("\nRespuesta completa de IA:")
        print("=" * 50)
        print(ai_response)
        print("=" * 50)
        
        # Intentar extraer JSON
        try:
            start = ai_response.find('{')
            end = ai_response.rfind('}') + 1
            
            if start != -1 and end > start:
                json_str = ai_response[start:end]
                print(f"\nJSON extraido: {json_str}")
                
                parsed = json.loads(json_str)
                print(f"JSON parseado exitosamente:")
                print(f"  Signal: {parsed.get('signal')}")
                print(f"  Confidence: {parsed.get('confidence')}")
                print(f"  Reason: {parsed.get('reason')}")
            else:
                print("No se encontro JSON en la respuesta")
                
        except json.JSONDecodeError as e:
            print(f"Error parseando JSON: {e}")
    else:
        print(f"Error HTTP: {response.status_code}")
        
except Exception as e:
    print(f"Error: {e}")