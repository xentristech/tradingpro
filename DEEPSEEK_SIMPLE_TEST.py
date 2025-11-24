"""
DeepSeek Simple Test - Replica exacta del curl que funciona
"""

import requests
import json

def test_deepseek_simple():
    print("DEEPSEEK SIMPLE TEST")
    print("="*30)

    url = "http://localhost:11434/api/generate"

    # Exact same payload as working curl
    payload = {
        "model": "deepseek-r1:14b",
        "prompt": "EURUSD trading analysis",
        "stream": False,
        "options": {
            "num_predict": 50,
            "temperature": 0.2
        }
    }

    try:
        print("Sending request...")

        response = requests.post(
            url,
            json=payload,
            timeout=30
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            response_text = result.get('response', '')

            print(f"Response length: {len(response_text)}")

            if response_text:
                print(f"SUCCESS!")
                print(f"Response: {response_text}")
                return True
            else:
                print(f"Empty response")
                print(f"Full result: {result}")
                return False
        else:
            print(f"Failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False

    except Exception as e:
        print(f"Exception: {e}")
        return False

if __name__ == "__main__":
    test_deepseek_simple()