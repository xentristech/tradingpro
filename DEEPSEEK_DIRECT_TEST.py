"""
Test directo para DeepSeek-R1:14b
Diagnostico detallado del problema
"""

import requests
import json
import time

def test_deepseek_direct():
    print("DEEPSEEK-R1:14B DIRECT TEST")
    print("="*50)

    ollama_url = "http://localhost:11434"
    model = "deepseek-r1:14b"

    # Test 1: Lista de modelos
    print("\n1. Testing model availability...")
    try:
        response = requests.get(f"{ollama_url}/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"  Found {len(models)} models:")
            for m in models:
                name = m['name']
                size = m.get('size', 0)
                print(f"    - {name} ({size/1e9:.1f}GB)")

            # Check DeepSeek specifically
            deepseek_models = [m for m in models if 'deepseek' in m['name'].lower()]
            print(f"\n  DeepSeek models: {len(deepseek_models)}")
            for m in deepseek_models:
                print(f"    - {m['name']}")
        else:
            print(f"  Error getting models: {response.status_code}")
            return
    except Exception as e:
        print(f"  Error: {e}")
        return

    # Test 2: Simple prompt
    print("\n2. Testing simple prompt...")
    simple_prompt = "Hello, what is 2+2?"

    payload = {
        "model": model,
        "prompt": simple_prompt,
        "stream": False,
        "options": {
            "num_predict": 50,
            "temperature": 0.1,
            "top_p": 0.9
        }
    }

    try:
        print(f"  Sending request to {model}...")
        start_time = time.time()

        response = requests.post(
            f"{ollama_url}/api/generate",
            json=payload,
            timeout=120
        )

        elapsed = time.time() - start_time
        print(f"  Response time: {elapsed:.2f}s")
        print(f"  Status code: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            response_text = result.get('response', '').strip()

            print(f"  Response length: {len(response_text)} characters")
            print(f"  Response preview: {response_text[:200]}...")

            if len(response_text) > 0:
                print("  ✅ SUCCESS: DeepSeek responded!")
            else:
                print("  ❌ FAIL: Empty response")
                print(f"  Full result: {result}")
        else:
            print(f"  ❌ FAIL: HTTP {response.status_code}")
            print(f"  Error: {response.text}")

    except requests.exceptions.Timeout:
        print("  ❌ FAIL: Request timeout (120s)")
    except Exception as e:
        print(f"  ❌ FAIL: {e}")

    # Test 3: Trading prompt
    print("\n3. Testing trading prompt...")
    trading_prompt = """Analyze EURUSD:
Price: 1.1625
RSI: 60
Action needed: BUY/SELL/HOLD
Give short answer."""

    payload = {
        "model": model,
        "prompt": trading_prompt,
        "stream": False,
        "options": {
            "num_predict": 100,
            "temperature": 0.2,
            "top_p": 0.9
        }
    }

    try:
        print(f"  Sending trading analysis request...")
        start_time = time.time()

        response = requests.post(
            f"{ollama_url}/api/generate",
            json=payload,
            timeout=180  # Longer timeout for complex prompt
        )

        elapsed = time.time() - start_time
        print(f"  Response time: {elapsed:.2f}s")

        if response.status_code == 200:
            result = response.json()
            response_text = result.get('response', '').strip()

            print(f"  Response length: {len(response_text)}")
            if len(response_text) > 0:
                print(f"  Trading response: {response_text}")
                print("  ✅ SUCCESS: Trading analysis received!")
            else:
                print("  ❌ FAIL: Empty trading response")

        else:
            print(f"  ❌ FAIL: HTTP {response.status_code}")

    except Exception as e:
        print(f"  ❌ FAIL: {e}")

    # Test 4: Alternative models comparison
    print("\n4. Testing alternative models for comparison...")
    alternative_models = ["gemma3:4b", "qwen3:8b"]

    for alt_model in alternative_models:
        try:
            payload = {
                "model": alt_model,
                "prompt": "What is 2+2?",
                "stream": False,
                "options": {"num_predict": 30}
            }

            response = requests.post(
                f"{ollama_url}/api/generate",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '').strip()
                status = "✅ Working" if len(response_text) > 0 else "❌ Empty"
                print(f"  {alt_model}: {status} ({len(response_text)} chars)")
            else:
                print(f"  {alt_model}: ❌ HTTP {response.status_code}")

        except Exception as e:
            print(f"  {alt_model}: ❌ Error - {e}")

if __name__ == "__main__":
    test_deepseek_direct()