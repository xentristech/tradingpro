"""
DeepSeek-R1:14b WORKING Trading System
Usando configuracion exacta que funciona con curl
"""

import MetaTrader5 as mt5
import requests
import json
import time
from datetime import datetime

print("DEEPSEEK-R1:14B WORKING TRADING SYSTEM")
print("="*50)

class DeepSeekWorkingSystem:
    def __init__(self):
        # EXNESS Configuration
        self.exness_config = {
            'path': r"C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe",
            'login': 197678662,
            'password': "Badboy930218*",
            'server': "Exness-MT5Trial11"
        }

        self.ollama_url = "http://localhost:11434"
        self.model = "deepseek-r1:14b"

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

    def query_deepseek_working(self, prompt):
        """Query DeepSeek with exact working configuration"""
        try:
            # Exact payload that works with curl
            payload = {
                "model": "deepseek-r1:14b",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": 30,
                    "temperature": 0.1
                }
            }

            print(f"  Querying DeepSeek-R1...")

            # Exact request configuration
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )

            print(f"  Status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '').strip()

                print(f"  Response length: {len(response_text)}")

                if len(response_text) > 0:
                    print(f"  DeepSeek Says: {response_text}")
                    return response_text
                else:
                    print(f"  Full result: {result}")
                    return None
            else:
                print(f"  Query failed: {response.status_code}")
                print(f"  Error: {response.text}")
                return None

        except Exception as e:
            print(f"  Error querying DeepSeek: {e}")
            return None

    def get_market_data(self, symbol):
        """Get market data"""
        try:
            if not mt5.symbol_select(symbol, True):
                return None

            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return None

            return {
                'symbol': symbol,
                'price': tick.bid,
                'ask': tick.ask
            }

        except Exception as e:
            print(f"  Error getting {symbol} data: {e}")
            return None

    def test_deepseek_step_by_step(self):
        """Test DeepSeek step by step"""
        print("\n" + "="*50)
        print("DEEPSEEK WORKING SYSTEM TEST")
        print("="*50)

        # Test 1: Simple hello
        print("\n1. Testing simple hello...")
        response = self.query_deepseek_working("Hello")
        if response:
            print("  SUCCESS: DeepSeek responded to hello!")
        else:
            print("  FAIL: No response to hello")
            return

        time.sleep(2)

        # Test 2: Simple math
        print("\n2. Testing simple math...")
        response = self.query_deepseek_working("What is 2+2?")
        if response:
            print("  SUCCESS: DeepSeek did math!")
        else:
            print("  FAIL: No response to math")
            return

        time.sleep(2)

        # Test 3: Trading question
        print("\n3. Testing trading question...")
        response = self.query_deepseek_working("BUY or SELL EURUSD?")
        if response:
            print("  SUCCESS: DeepSeek answered trading question!")

            # Parse trading response
            response_upper = response.upper()
            if 'BUY' in response_upper:
                print("  Parsed action: BUY")
            elif 'SELL' in response_upper:
                print("  Parsed action: SELL")
            else:
                print("  Parsed action: HOLD/OTHER")
        else:
            print("  FAIL: No response to trading question")
            return

        time.sleep(2)

        # Test 4: Real market data
        print("\n4. Testing with real market data...")

        market_data = self.get_market_data('EURUSDm')
        if market_data:
            print(f"  EURUSD Price: {market_data['price']:.5f}")

            prompt = f"EURUSD is at {market_data['price']:.5f}. Should I BUY or SELL?"
            response = self.query_deepseek_working(prompt)

            if response:
                print("  SUCCESS: DeepSeek analyzed real market data!")

                # Look for trading signals
                response_upper = response.upper()
                if any(word in response_upper for word in ['BUY', 'SELL', 'HOLD']):
                    print("  SIGNAL DETECTED in response!")
                else:
                    print("  No clear signal in response")
            else:
                print("  FAIL: No response to market data")

    def run_working_test(self):
        """Run working test"""
        print("\nStarting DeepSeek-R1:14b Working System Test...")

        # Connect to MT5
        if not self.connect_mt5():
            print("\n[FAILED] MT5 connection failed")
            return

        # Test DeepSeek step by step
        self.test_deepseek_step_by_step()

        print(f"\n" + "="*50)
        print("DEEPSEEK WORKING SYSTEM TEST COMPLETED!")
        print("="*50)

        # Disconnect
        if self.connected:
            mt5.shutdown()
            print("\nDisconnected from EXNESS")

def main():
    """Main function"""
    system = DeepSeekWorkingSystem()
    system.run_working_test()

if __name__ == "__main__":
    main()