"""
DeepSeek-R1:14b Fix Test
Probando diferentes configuraciones para solucionar el problema de respuestas vacias
"""

import requests
import json
import time

def test_deepseek_configurations():
    print("DEEPSEEK-R1:14B CONFIGURATION TEST")
    print("="*50)

    ollama_url = "http://localhost:11434"
    model = "deepseek-r1:14b"

    # Test diferentes configuraciones
    configurations = [
        {
            "name": "Minimal Config",
            "options": {
                "num_predict": 30,
                "temperature": 0.1
            }
        },
        {
            "name": "Standard Config",
            "options": {
                "num_predict": 100,
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 40
            }
        },
        {
            "name": "High Creativity",
            "options": {
                "num_predict": 200,
                "temperature": 0.9,
                "top_p": 0.95,
                "repeat_penalty": 1.1
            }
        },
        {
            "name": "Conservative",
            "options": {
                "num_predict": 50,
                "temperature": 0.3,
                "top_p": 0.8,
                "repeat_penalty": 1.05
            }
        },
        {
            "name": "DeepSeek Optimized",
            "options": {
                "num_predict": 100,
                "temperature": 0.5,
                "top_p": 0.9,
                "top_k": 50,
                "repeat_penalty": 1.1,
                "seed": 42
            }
        }
    ]

    test_prompts = [
        "Hello",
        "What is 2+2?",
        "Explain forex trading briefly.",
        "BUY or SELL EURUSD?",
        "Trading analysis: EURUSD at 1.1625, RSI 60. Decision?"
    ]

    for i, config in enumerate(configurations, 1):
        print(f"\n{i}. Testing {config['name']}...")
        print(f"   Options: {config['options']}")

        for prompt_idx, prompt in enumerate(test_prompts):
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": config['options']
            }

            try:
                start_time = time.time()
                response = requests.post(
                    f"{ollama_url}/api/generate",
                    json=payload,
                    timeout=90
                )
                elapsed = time.time() - start_time

                if response.status_code == 200:
                    result = response.json()
                    response_text = result.get('response', '').strip()

                    if len(response_text) > 0:
                        print(f"   Prompt {prompt_idx+1}: SUCCESS ({len(response_text)} chars, {elapsed:.1f}s)")
                        print(f"   Response: {response_text[:100]}...")

                        # Si encontramos una configuración exitosa, seguir con esta
                        if len(response_text) > 10:
                            print(f"\n*** WORKING CONFIGURATION FOUND: {config['name']} ***")
                            return config['options']
                    else:
                        print(f"   Prompt {prompt_idx+1}: EMPTY ({elapsed:.1f}s)")
                else:
                    print(f"   Prompt {prompt_idx+1}: HTTP {response.status_code}")

            except Exception as e:
                print(f"   Prompt {prompt_idx+1}: ERROR - {str(e)[:50]}...")

        time.sleep(2)  # Pausa entre configuraciones

    # Test del modelo alternativo DeepSeek-R1:8b
    print(f"\n6. Testing alternative deepseek-r1:8b...")
    alt_model = "deepseek-r1:8b"

    payload = {
        "model": alt_model,
        "prompt": "Analyze EURUSD trading signal",
        "stream": False,
        "options": {
            "num_predict": 100,
            "temperature": 0.7,
            "top_p": 0.9
        }
    }

    try:
        response = requests.post(
            f"{ollama_url}/api/generate",
            json=payload,
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            response_text = result.get('response', '').strip()

            if len(response_text) > 0:
                print(f"   deepseek-r1:8b: SUCCESS ({len(response_text)} chars)")
                print(f"   Response: {response_text[:150]}...")
                print(f"\n*** ALTERNATIVE MODEL WORKING: deepseek-r1:8b ***")
            else:
                print(f"   deepseek-r1:8b: EMPTY RESPONSE")
        else:
            print(f"   deepseek-r1:8b: HTTP {response.status_code}")

    except Exception as e:
        print(f"   deepseek-r1:8b: ERROR - {e}")

    print(f"\n*** NO WORKING CONFIGURATION FOUND FOR DEEPSEEK-R1:14B ***")
    print("Recommendation: Use alternative model (gemma3:4b or deepseek-r1:8b)")
    return None

if __name__ == "__main__":
    working_config = test_deepseek_configurations()

    if working_config:
        print(f"\nWorking configuration: {working_config}")
    else:
        print(f"\nNo working configuration found for DeepSeek-R1:14b")