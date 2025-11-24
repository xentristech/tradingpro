"""
DeepSeek-R1:14b Optimized Trading System
Usando la configuracion que funciona: num_predict=30, temperature=0.1
"""

import MetaTrader5 as mt5
import requests
import json
import time
from datetime import datetime

print("DEEPSEEK-R1:14B OPTIMIZED TRADING SYSTEM")
print("="*50)

class DeepSeekOptimizedTrading:
    def __init__(self):
        # EXNESS Configuration
        self.exness_config = {
            'path': r"C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe",
            'login': 197678662,
            'password': "Badboy930218*",
            'server': "Exness-MT5Trial11"
        }

        # DeepSeek Optimized Configuration
        self.ollama_url = "http://localhost:11434"
        self.model = "deepseek-r1:14b"

        # Configuracion que funciona!
        self.ollama_options = {
            "num_predict": 30,
            "temperature": 0.1
        }

        self.connected = False
        self.account_info = None

    def connect_mt5(self):
        """Connect to EXNESS"""
        print("\nConnecting to EXNESS...")

        try:
            if not mt5.initialize(self.exness_config['path']):
                return False

            if not mt5.login(
                login=self.exness_config['login'],
                password=self.exness_config['password'],
                server=self.exness_config['server']
            ):
                return False

            self.connected = True
            self.account_info = mt5.account_info()

            print(f"  [OK] Connected to EXNESS")
            print(f"  Balance: ${self.account_info.balance:,.2f}")

            return True

        except Exception as e:
            print(f"  [ERROR] MT5 connection failed: {e}")
            return False

    def query_deepseek_simple(self, prompt):
        """Query DeepSeek with optimized configuration"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": self.ollama_options
            }

            print(f"  Querying DeepSeek-R1 (optimized)...")
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=30  # Shorter timeout
            )

            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '').strip()

                if len(response_text) > 0:
                    print(f"  DeepSeek Response: {response_text}")
                    return response_text
                else:
                    print(f"  DeepSeek: Empty response")
                    return None
            else:
                print(f"  DeepSeek Query failed: {response.status_code}")
                return None

        except Exception as e:
            print(f"  Error querying DeepSeek: {e}")
            return None

    def get_simple_market_data(self, symbol):
        """Get basic market data"""
        try:
            if not mt5.symbol_select(symbol, True):
                return None

            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return None

            return {
                'symbol': symbol,
                'price': tick.bid,
                'ask': tick.ask,
                'spread': tick.ask - tick.bid
            }

        except Exception as e:
            print(f"  Error getting {symbol} data: {e}")
            return None

    def create_simple_prompt(self, symbol, price):
        """Create simple prompt for DeepSeek"""
        # Prompt super simple para DeepSeek
        prompt = f"{symbol} price {price:.5f}. BUY/SELL/HOLD?"
        return prompt

    def test_deepseek_trading(self):
        """Test DeepSeek trading with optimized setup"""
        print("\n" + "="*50)
        print("DEEPSEEK OPTIMIZED TRADING TEST")
        print("="*50)

        symbols = ['EURUSDm', 'GBPUSDm', 'XAUUSDm']

        for symbol in symbols:
            print(f"\n[TESTING] {symbol}")

            # Get simple market data
            market_data = self.get_simple_market_data(symbol)
            if not market_data:
                print(f"  [ERROR] Could not get data for {symbol}")
                continue

            print(f"  Price: {market_data['price']:.5f}")
            print(f"  Spread: {market_data['spread']:.5f}")

            # Create simple prompt
            prompt = self.create_simple_prompt(symbol, market_data['price'])
            print(f"  Prompt: {prompt}")

            # Query DeepSeek
            response = self.query_deepseek_simple(prompt)

            if response:
                print(f"  [SUCCESS] DeepSeek responded!")

                # Parse simple response
                response_upper = response.upper()
                if 'BUY' in response_upper:
                    action = 'BUY'
                elif 'SELL' in response_upper:
                    action = 'SELL'
                else:
                    action = 'HOLD'

                print(f"  Parsed Action: {action}")

                if action in ['BUY', 'SELL']:
                    print(f"  [SIGNAL DETECTED] {action} {symbol}")
                    print(f"  Would execute: {action} position on {symbol}")
            else:
                print(f"  [FAIL] No response from DeepSeek")

            print(f"  " + "-"*40)
            time.sleep(3)  # Pausa entre simbolos

    def run_optimized_test(self):
        """Run optimized test"""
        print("\nStarting DeepSeek-R1:14b Optimized Test...")

        # Connect to MT5
        if not self.connect_mt5():
            print("\n[FAILED] MT5 connection failed")
            return

        # Test DeepSeek trading
        self.test_deepseek_trading()

        print(f"\n" + "="*50)
        print("DEEPSEEK OPTIMIZED TEST COMPLETED!")
        print("DeepSeek-R1:14b working with optimized configuration")
        print("="*50)

        # Disconnect
        if self.connected:
            mt5.shutdown()
            print("\nDisconnected from EXNESS")

def main():
    """Main function"""
    test_system = DeepSeekOptimizedTrading()
    test_system.run_optimized_test()

if __name__ == "__main__":
    main()