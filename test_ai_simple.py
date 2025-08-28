#!/usr/bin/env python3
import requests
import json

host = 'http://localhost:11434'

# Probemos con un modelo más simple primero
models_to_try = ['gemma3:4b', 'qwen3:8b', 'deepseek-r1:8b']

for model in models_to_try:
    print(f"\n=== PROBANDO {model} ===")
    
    # Prompt muy simple
    prompt = f"""Analiza: XAUUSD precio $2650, RSI 35.2, tendencia alcista.
    
Responde SOLO este JSON (sin texto adicional):
{{"signal": "BUY", "confidence": 80, "reason": "RSI oversold"}}"""

    try:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 80,
                "stop": ["}"]
            }
        }
        
        response = requests.post(f"{host}/api/generate", json=payload, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result.get('response', '').strip()
            
            print(f"Respuesta: {ai_response}")
            
            # Agregar } si falta
            if ai_response.startswith('{') and not ai_response.endswith('}'):
                ai_response += '}'
            
            # Intentar parsear
            try:
                if ai_response.startswith('{'):
                    parsed = json.loads(ai_response)
                    print(f"EXITO! JSON valido:")
                    print(f"  Signal: {parsed.get('signal')}")
                    print(f"  Confidence: {parsed.get('confidence')}")
                    print(f"  Reason: {parsed.get('reason')}")
                    
                    # Este modelo funciona, guardarlo
                    with open('working_model.txt', 'w') as f:
                        f.write(model)
                    
                    print(f"\nModelo {model} FUNCIONA - guardado")
                    break
                    
            except json.JSONDecodeError as e:
                print(f"Error JSON: {e}")
        else:
            print(f"Error HTTP: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")
        continue

else:
    print("\nNingun modelo funciono correctamente")