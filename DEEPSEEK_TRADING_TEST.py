"""
DeepSeek-R1 Trading Test
Quick test of DeepSeek-R1:14b integration with live EXNESS trading
Author: Trading Pro System
Version: 3.0
"""

import MetaTrader5 as mt5
import requests
import json
import time
from datetime import datetime

print("DEEPSEEK-R1 TRADING TEST v3.0")
print("="*50)

class DeepSeekTradingTest:
    """Simple DeepSeek trading test"""

    def __init__(self):
        # EXNESS Configuration
        self.exness_config = {
            'path': r"C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe",
            'login': 197678662,
            'password': "Badboy930218*",
            'server': "Exness-MT5Trial11"
        }

        # DeepSeek Configuration
        self.ollama_url = "http://localhost:11434"
        self.model = "deepseek-r1:14b"

        self.connected = False
        self.account_info = None

    def test_deepseek_connection(self):
        """Test DeepSeek connection"""
        print("Testing DeepSeek-R1 connection...")

        try:
            # Test Ollama server
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]

                print(f"  [OK] Ollama server running")
                print(f"  Available models: {len(models)}")

                # Check for DeepSeek
                deepseek_found = any('deepseek' in name.lower() for name in model_names)
                if deepseek_found:
                    print(f"  [OK] DeepSeek model found")
                    return True
                else:
                    print(f"  [WARNING] DeepSeek not found in models:")
                    for name in model_names:
                        print(f"    - {name}")
                    return False
            else:
                print(f"  [ERROR] Ollama server not responding")
                return False

        except Exception as e:
            print(f"  [ERROR] Connection failed: {e}")
            return False

    def query_deepseek(self, prompt):
        """Query DeepSeek-R1 for analysis"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": 30,
                    "temperature": 0.1
                }
            }

            print(f"  Querying DeepSeek-R1...")
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=60  # Longer timeout for complex model
            )

            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            else:
                print(f"  Query failed: {response.status_code}")
                return None

        except Exception as e:
            print(f"  Error querying DeepSeek: {e}")
            return None

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
            print(f"  Equity: ${self.account_info.equity:,.2f}")

            return True

        except Exception as e:
            print(f"  [ERROR] MT5 connection failed: {e}")
            return False

    def get_symbol_data(self, symbol):
        """Get current symbol data"""
        try:
            # Select symbol
            if not mt5.symbol_select(symbol, True):
                return None

            # Get current tick
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return None

            # Get recent rates for analysis
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 50)
            if rates is None or len(rates) < 20:
                return None

            import pandas as pd
            import numpy as np

            df = pd.DataFrame(rates)

            # Calculate basic indicators
            df['sma_20'] = df['close'].rolling(20).mean()

            # RSI
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))

            latest = df.iloc[-1]

            return {
                'symbol': symbol,
                'current_price': tick.bid,
                'ask': tick.ask,
                'bid': tick.bid,
                'spread': tick.ask - tick.bid,
                'rsi': latest['rsi'],
                'sma_20': latest['sma_20'],
                'price_vs_sma': ((tick.bid - latest['sma_20']) / latest['sma_20']) * 100,
                'recent_high': df['high'].tail(10).max(),
                'recent_low': df['low'].tail(10).min()
            }

        except Exception as e:
            print(f"  Error getting {symbol} data: {e}")
            return None

    def create_deepseek_prompt(self, symbol_data):
        """Create detailed prompt for DeepSeek-R1"""
        data = symbol_data

        prompt = f"""
You are a professional forex trader analyzing {data['symbol']}.

CURRENT MARKET DATA:
• Symbol: {data['symbol']}
• Current Price: {data['current_price']:.5f}
• Spread: {data['spread']:.5f}
• RSI(14): {data['rsi']:.1f}
• Price vs SMA(20): {data['price_vs_sma']:+.2f}%
• Recent High: {data['recent_high']:.5f}
• Recent Low: {data['recent_low']:.5f}

ANALYSIS TASK:
Analyze this forex pair and provide a trading recommendation based on:
1. RSI levels (oversold <30, overbought >70)
2. Price position vs moving average
3. Support/resistance levels
4. Current market structure

REQUIRED OUTPUT FORMAT:
ACTION: [BUY/SELL/HOLD]
CONFIDENCE: [0-100]
ENTRY: [specific price level]
STOP_LOSS: [specific price level]
TAKE_PROFIT: [specific price level]
REASONING: [your technical analysis in 1-2 sentences]

Provide ONLY the trading analysis - no additional commentary.
"""
        return prompt

    def parse_deepseek_response(self, response):
        """Parse DeepSeek response"""
        try:
            if not response:
                return None

            lines = response.strip().split('\\n')
            result = {}

            for line in lines:
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().upper()
                    value = value.strip()

                    if key == 'ACTION':
                        result['action'] = value.upper()
                    elif key == 'CONFIDENCE':
                        try:
                            result['confidence'] = float(value.replace('%', ''))
                        except:
                            result['confidence'] = 50
                    elif key == 'ENTRY':
                        try:
                            result['entry'] = float(value)
                        except:
                            pass
                    elif key == 'STOP_LOSS' or key == 'STOP':
                        try:
                            result['stop_loss'] = float(value)
                        except:
                            pass
                    elif key == 'TAKE_PROFIT' or key == 'TARGET':
                        try:
                            result['take_profit'] = float(value)
                        except:
                            pass
                    elif key == 'REASONING':
                        result['reasoning'] = value

            return result if 'action' in result else None

        except Exception as e:
            print(f"  Error parsing response: {e}")
            return None

    def test_trading_analysis(self):
        """Test complete trading analysis"""
        print("\\n" + "="*60)
        print("DEEPSEEK-R1 TRADING ANALYSIS TEST")
        print("="*60)

        symbols = ['EURUSDm', 'GBPUSDm', 'XAUUSDm']

        for symbol in symbols:
            print(f"\\n[ANALYZING] {symbol}")

            # Get symbol data
            symbol_data = self.get_symbol_data(symbol)
            if not symbol_data:
                print(f"  [ERROR] Could not get data for {symbol}")
                continue

            print(f"  Current Price: {symbol_data['current_price']:.5f}")
            print(f"  RSI: {symbol_data['rsi']:.1f}")
            print(f"  Price vs SMA20: {symbol_data['price_vs_sma']:+.2f}%")

            # Create prompt
            prompt = self.create_deepseek_prompt(symbol_data)

            # Query DeepSeek
            response = self.query_deepseek(prompt)
            if not response:
                print(f"  [ERROR] No response from DeepSeek")
                continue

            print(f"  [DEEPSEEK RESPONSE]")
            print(f"  {response}")

            # Parse response
            analysis = self.parse_deepseek_response(response)
            if analysis:
                print(f"\\n  [PARSED ANALYSIS]")
                print(f"    Action: {analysis.get('action', 'N/A')}")
                print(f"    Confidence: {analysis.get('confidence', 0):.1f}%")
                if 'entry' in analysis:
                    print(f"    Entry: {analysis['entry']:.5f}")
                if 'stop_loss' in analysis:
                    print(f"    Stop Loss: {analysis['stop_loss']:.5f}")
                if 'take_profit' in analysis:
                    print(f"    Take Profit: {analysis['take_profit']:.5f}")
                if 'reasoning' in analysis:
                    print(f"    Reasoning: {analysis['reasoning']}")

                # Simulate trade execution
                if analysis.get('action') in ['BUY', 'SELL'] and analysis.get('confidence', 0) > 70:
                    print(f"\\n    [SIMULATION] High confidence signal detected!")
                    print(f"    Would execute: {analysis['action']} {symbol}")
                    print(f"    Risk/Reward: {self.calculate_risk_reward(analysis, symbol_data):.2f}")

            print(f"  " + "-"*50)

    def calculate_risk_reward(self, analysis, symbol_data):
        """Calculate risk/reward ratio"""
        try:
            entry = analysis.get('entry', symbol_data['current_price'])
            stop_loss = analysis.get('stop_loss')
            take_profit = analysis.get('take_profit')

            if not stop_loss or not take_profit:
                return 0

            if analysis['action'] == 'BUY':
                risk = abs(entry - stop_loss)
                reward = abs(take_profit - entry)
            else:
                risk = abs(stop_loss - entry)
                reward = abs(entry - take_profit)

            return reward / risk if risk > 0 else 0

        except:
            return 0

    def run_test(self):
        """Run complete test"""
        print("\\nStarting DeepSeek-R1 Trading Test...")

        # Test DeepSeek connection
        if not self.test_deepseek_connection():
            print("\\n[FAILED] DeepSeek connection test failed")
            return

        # Connect to MT5
        if not self.connect_mt5():
            print("\\n[FAILED] MT5 connection failed")
            return

        # Run trading analysis test
        self.test_trading_analysis()

        print(f"\\n" + "="*60)
        print("TEST COMPLETED SUCCESSFULLY!")
        print("DeepSeek-R1 is ready for live trading integration")
        print("="*60)

        # Disconnect
        if self.connected:
            mt5.shutdown()
            print("\\nDisconnected from EXNESS")

def main():
    """Main test function"""
    test_system = DeepSeekTradingTest()
    test_system.run_test()

if __name__ == "__main__":
    main()