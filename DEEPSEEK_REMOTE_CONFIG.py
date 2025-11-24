"""
DeepSeek Remote Configuration
Para conectar con Ollama/DeepSeek en PC externa
"""

import requests
import json
import time

class RemoteOllamaConfig:
    def __init__(self):
        # Configuraciones posibles para servidor remoto
        self.possible_configs = [
            "http://localhost:11434",      # Local (actual)
            "http://192.168.1.100:11434",  # IP local común
            "http://192.168.1.101:11434",  # IP local común
            "http://192.168.1.102:11434",  # IP local común
            "http://192.168.0.100:11434",  # Otra red común
            "http://10.0.0.100:11434",     # Red interna
        ]

        self.working_url = None
        self.available_models = []

    def test_ollama_connection(self, url):
        """Test connection to Ollama server"""
        try:
            response = requests.get(f"{url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return True, models
            return False, []
        except:
            return False, []

    def find_ollama_server(self):
        """Find working Ollama server"""
        print("SEARCHING FOR OLLAMA SERVER...")
        print("="*50)

        for url in self.possible_configs:
            print(f"Testing: {url}")

            success, models = self.test_ollama_connection(url)

            if success:
                print(f"  ✓ FOUND! Server responding")
                print(f"  Models available: {len(models)}")

                # Check for DeepSeek models
                deepseek_models = [m for m in models if 'deepseek' in m['name'].lower()]
                if deepseek_models:
                    print(f"  ✓ DeepSeek models found: {len(deepseek_models)}")
                    for model in deepseek_models:
                        print(f"    - {model['name']}")

                self.working_url = url
                self.available_models = models
                return url, models
            else:
                print(f"  ✗ Not responding")

        print(f"\n❌ NO OLLAMA SERVER FOUND")
        return None, []

    def test_deepseek_remote(self, url, model="deepseek-r1:14b"):
        """Test DeepSeek on remote server"""
        try:
            payload = {
                "model": model,
                "prompt": "Hello, are you working?",
                "stream": False,
                "options": {
                    "num_predict": 30,
                    "temperature": 0.1
                }
            }

            print(f"Testing DeepSeek on {url}...")
            response = requests.post(
                f"{url}/api/generate",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '').strip()

                if len(response_text) > 0:
                    print(f"  ✓ SUCCESS: {response_text}")
                    return True, response_text
                else:
                    print(f"  ✗ Empty response")
                    return False, None
            else:
                print(f"  ✗ HTTP {response.status_code}")
                return False, None

        except Exception as e:
            print(f"  ✗ Error: {e}")
            return False, None

    def create_remote_config(self):
        """Create configuration for remote connection"""
        server_url, models = self.find_ollama_server()

        if not server_url:
            print("\n❌ CONFIGURATION FAILED")
            print("Please provide the IP address of the PC running Ollama")
            print("Example: 192.168.1.100")
            return None

        print(f"\n✓ OLLAMA SERVER FOUND: {server_url}")

        # Test DeepSeek specifically
        deepseek_models = [m for m in models if 'deepseek' in m['name'].lower()]

        working_model = None
        for model_info in deepseek_models:
            model_name = model_info['name']
            print(f"\nTesting {model_name}...")

            success, response = self.test_deepseek_remote(server_url, model_name)
            if success:
                working_model = model_name
                break

        if working_model:
            config = {
                "ollama_url": server_url,
                "model": working_model,
                "status": "working",
                "options": {
                    "num_predict": 50,
                    "temperature": 0.2
                }
            }

            print(f"\n🎉 REMOTE DEEPSEEK CONFIGURATION READY!")
            print(f"URL: {server_url}")
            print(f"Model: {working_model}")

            return config
        else:
            print(f"\n❌ DeepSeek models not responding")
            return None

    def save_config(self, config):
        """Save working configuration"""
        if config:
            with open('remote_ollama_config.json', 'w') as f:
                json.dump(config, f, indent=2)
            print(f"Configuration saved to: remote_ollama_config.json")

def main():
    """Main configuration function"""
    print("REMOTE OLLAMA/DEEPSEEK CONFIGURATION")
    print("="*50)

    configurator = RemoteOllamaConfig()
    config = configurator.create_remote_config()

    if config:
        configurator.save_config(config)
        print(f"\n✓ Setup complete! Use this configuration in trading systems.")
    else:
        print(f"\n❌ Setup failed. Please check:")
        print("1. Ollama is running on remote PC")
        print("2. Port 11434 is accessible")
        print("3. Firewall allows connections")
        print("4. DeepSeek model is loaded")

if __name__ == "__main__":
    main()