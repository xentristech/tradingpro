"""
DeepSeek-R1:14b FINAL Working Trading System
Con manejo correcto de Unicode para Windows
"""

import MetaTrader5 as mt5
import requests
import json
import time
import sys
import codecs
from datetime import datetime

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())

print("DEEPSEEK-R1:14B FINAL TRADING SYSTEM")
print("="*50)

class DeepSeekFinalSystem:
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
        self.signals_generated = 0
        self.successful_queries = 0

    def connect_mt5(self):
        """Connect to EXNESS"""
        print("\\nConnecting to EXNESS...")

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

    def query_deepseek_safe(self, prompt):
        """Query DeepSeek with safe Unicode handling"""
        try:
            payload = {
                "model": "deepseek-r1:14b",
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": 50,  # Increased for better responses
                    "temperature": 0.1
                }
            }

            print(f"  Querying DeepSeek-R1...")

            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '').strip()

                if len(response_text) > 0:
                    # Safe Unicode handling
                    try:
                        # Remove problematic characters
                        safe_response = response_text.encode('ascii', 'ignore').decode('ascii')
                        if len(safe_response) < 3:  # If too much was removed, use original
                            safe_response = response_text.replace('😊', ':)').replace('🤔', '?')

                        print(f"  DeepSeek Response: {safe_response}")
                        self.successful_queries += 1
                        return safe_response

                    except Exception as encoding_error:
                        print(f"  Response received but encoding error: {len(response_text)} chars")
                        self.successful_queries += 1
                        return response_text  # Return original even if can't print

                else:
                    print(f"  Empty response")
                    return None
            else:
                print(f"  Query failed: {response.status_code}")
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

    def analyze_trading_signal(self, symbol, price):
        """Analyze trading signal with DeepSeek"""
        print(f"\\n[ANALYZING] {symbol}")
        print(f"  Price: {price:.5f}")

        # Simple, clear prompt for trading
        prompt = f"Analyze {symbol} at price {price:.5f}. Give trading decision: BUY, SELL, or HOLD. Explain briefly."

        response = self.query_deepseek_safe(prompt)

        if response:
            # Parse response for signals
            response_upper = response.upper()

            if 'BUY' in response_upper and 'SELL' not in response_upper:
                signal = 'BUY'
            elif 'SELL' in response_upper and 'BUY' not in response_upper:
                signal = 'SELL'
            else:
                signal = 'HOLD'

            print(f"  Parsed Signal: {signal}")

            if signal in ['BUY', 'SELL']:
                self.signals_generated += 1
                print(f"  [SIGNAL GENERATED] {signal} {symbol}")
                print(f"  Reasoning: {response[:100]}...")

            return signal

        else:
            print(f"  [NO RESPONSE] from DeepSeek")
            return None

    def run_deepseek_trading_test(self):
        """Run DeepSeek trading test"""
        print("\\n" + "="*60)
        print("DEEPSEEK-R1:14B TRADING ANALYSIS")
        print("="*60)

        symbols = ['EURUSDm', 'GBPUSDm', 'XAUUSDm', 'USDJPYm']

        for symbol in symbols:
            market_data = self.get_market_data(symbol)
            if market_data:
                signal = self.analyze_trading_signal(symbol, market_data['price'])
                time.sleep(3)  # Pause between queries

        print("\\n" + "="*60)
        print("DEEPSEEK TRADING TEST RESULTS")
        print("="*60)
        print(f"Successful Queries: {self.successful_queries}")
        print(f"Trading Signals Generated: {self.signals_generated}")

        if self.successful_queries > 0:
            print("\\n[SUCCESS] DeepSeek-R1:14b is working for trading!")
            print("Model is generating responses and trading analysis.")
        else:
            print("\\n[FAIL] DeepSeek-R1:14b not responding")

    def run_final_test(self):
        """Run final test"""
        print("\\nStarting DeepSeek-R1:14b Final Trading Test...")

        # Connect to MT5
        if not self.connect_mt5():
            print("\\n[FAILED] MT5 connection failed")
            return

        # Run trading test
        self.run_deepseek_trading_test()

        print("\\n" + "="*60)
        print("DEEPSEEK-R1:14B FINAL TEST COMPLETED!")
        print("="*60)

        # Disconnect
        if self.connected:
            mt5.shutdown()
            print("\\nDisconnected from EXNESS")

def main():
    """Main function"""
    system = DeepSeekFinalSystem()
    system.run_final_test()

if __name__ == "__main__":
    main()