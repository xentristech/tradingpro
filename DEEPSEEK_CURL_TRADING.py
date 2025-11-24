"""
DeepSeek-R1:14b Trading System usando curl (que funciona)
Solucion definitiva para integrar DeepSeek con trading
"""

import MetaTrader5 as mt5
import subprocess
import json
import time
import re
from datetime import datetime

print("DEEPSEEK-R1:14B CURL TRADING SYSTEM")
print("="*50)

class DeepSeekCurlTrading:
    def __init__(self):
        # EXNESS Configuration
        self.exness_config = {
            'path': r"C:\\Program Files\\MetaTrader 5 EXNESS\\terminal64.exe",
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

    def query_deepseek_curl(self, prompt):
        """Query DeepSeek using curl (method that works)"""
        try:
            # Escape prompt for JSON
            prompt_escaped = prompt.replace('"', '\\"')

            # Create curl command - exact format that works
            curl_data = f'{{"model":"{self.model}","prompt":"{prompt_escaped}","stream":false,"options":{{"num_predict":80,"temperature":0.2}}}}'

            curl_command = [
                'curl',
                '-X', 'POST',
                f'{self.ollama_url}/api/generate',
                '-d', curl_data
            ]

            print(f"  Querying DeepSeek-R1 via curl...")

            # Execute curl
            result = subprocess.run(
                curl_command,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                try:
                    # Parse JSON response
                    response_data = json.loads(result.stdout)
                    response_text = response_data.get('response', '').strip()

                    if len(response_text) > 0:
                        print(f"  [SUCCESS] DeepSeek responded ({len(response_text)} chars)")
                        # Clean up response for safe printing
                        clean_response = response_text.replace('\\n', ' ')[:150]
                        print(f"  Response: {clean_response}...")

                        self.successful_queries += 1
                        return response_text
                    else:
                        print(f"  [EMPTY] DeepSeek returned empty response")
                        return None

                except json.JSONDecodeError as e:
                    print(f"  [ERROR] Invalid JSON response: {e}")
                    return None

            else:
                print(f"  [ERROR] Curl failed: {result.stderr}")
                return None

        except subprocess.TimeoutExpired:
            print(f"  [TIMEOUT] DeepSeek query timed out")
            return None
        except Exception as e:
            print(f"  [ERROR] Exception: {e}")
            return None

    def get_market_data(self, symbol):
        """Get market data"""
        try:
            if not mt5.symbol_select(symbol, True):
                return None

            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return None

            # Get recent rates for basic analysis
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 20)
            if rates is None:
                return None

            import pandas as pd
            df = pd.DataFrame(rates)

            # Simple RSI calculation
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            return {
                'symbol': symbol,
                'price': tick.bid,
                'ask': tick.ask,
                'rsi': rsi.iloc[-1] if not rsi.empty else 50,
                'change': ((df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2]) * 100
            }

        except Exception as e:
            print(f"  Error getting {symbol} data: {e}")
            return None

    def create_trading_prompt(self, symbol, market_data):
        """Create specific trading prompt"""
        prompt = f"""Analyze {symbol}:
Price: {market_data['price']:.5f}
RSI: {market_data['rsi']:.1f}
Change: {market_data['change']:+.2f}%

Give clear trading decision: BUY, SELL, or HOLD with brief reason."""

        return prompt

    def parse_trading_signal(self, response):
        """Parse trading signal from response"""
        if not response:
            return None

        response_upper = response.upper()

        # Look for clear signals
        if 'BUY' in response_upper and 'SELL' not in response_upper:
            return 'BUY'
        elif 'SELL' in response_upper and 'BUY' not in response_upper:
            return 'SELL'
        elif 'HOLD' in response_upper:
            return 'HOLD'
        else:
            # Try to infer from sentiment
            if any(word in response_upper for word in ['BULLISH', 'STRONG', 'UP', 'RISE']):
                return 'BUY'
            elif any(word in response_upper for word in ['BEARISH', 'WEAK', 'DOWN', 'FALL']):
                return 'SELL'
            else:
                return 'HOLD'

    def analyze_symbol(self, symbol):
        """Analyze single symbol with DeepSeek"""
        print(f"\\n[ANALYZING] {symbol}")

        # Get market data
        market_data = self.get_market_data(symbol)
        if not market_data:
            print(f"  [ERROR] Could not get market data for {symbol}")
            return None

        print(f"  Price: {market_data['price']:.5f}")
        print(f"  RSI: {market_data['rsi']:.1f}")
        print(f"  Change: {market_data['change']:+.2f}%")

        # Create trading prompt
        prompt = self.create_trading_prompt(symbol, market_data)

        # Query DeepSeek
        response = self.query_deepseek_curl(prompt)

        if response:
            # Parse signal
            signal = self.parse_trading_signal(response)
            print(f"  Parsed Signal: {signal}")

            if signal in ['BUY', 'SELL']:
                self.signals_generated += 1
                print(f"  [SIGNAL GENERATED] {signal} {symbol}")

                # Extract reasoning
                reasoning = response.split('.')[0][:100] if '.' in response else response[:100]
                print(f"  Reasoning: {reasoning}...")

                return {
                    'symbol': symbol,
                    'signal': signal,
                    'price': market_data['price'],
                    'reasoning': reasoning
                }

        return None

    def run_deepseek_trading(self):
        """Run DeepSeek trading analysis"""
        print("\\n" + "="*60)
        print("DEEPSEEK-R1:14B LIVE TRADING ANALYSIS")
        print("="*60)

        symbols = ['EURUSDm', 'GBPUSDm', 'XAUUSDm', 'USDJPYm']
        detected_signals = []

        for symbol in symbols:
            signal_data = self.analyze_symbol(symbol)
            if signal_data:
                detected_signals.append(signal_data)

            print("  " + "-"*50)
            time.sleep(3)  # Pause between queries

        # Results summary
        print("\\n" + "="*60)
        print("DEEPSEEK TRADING RESULTS")
        print("="*60)
        print(f"Successful Queries: {self.successful_queries}")
        print(f"Trading Signals Generated: {self.signals_generated}")

        if detected_signals:
            print("\\n[DETECTED SIGNALS]")
            for signal in detected_signals:
                print(f"  {signal['signal']} {signal['symbol']} @ {signal['price']:.5f}")
                print(f"    Reason: {signal['reasoning']}")
        else:
            print("\\nNo trading signals detected")

        return detected_signals

    def run_curl_trading_test(self):
        """Run complete curl trading test"""
        print("\\nStarting DeepSeek-R1:14b Curl Trading System...")

        # Connect to MT5
        if not self.connect_mt5():
            print("\\n[FAILED] MT5 connection failed")
            return

        # Run trading analysis
        signals = self.run_deepseek_trading()

        print("\\n" + "="*60)
        print("DEEPSEEK CURL TRADING TEST COMPLETED!")

        if self.successful_queries > 0:
            print("✓ DeepSeek-R1:14b is working with curl method")
            print(f"✓ Generated {self.signals_generated} trading signals")
        else:
            print("✗ DeepSeek not responding")

        print("="*60)

        # Disconnect
        if self.connected:
            mt5.shutdown()
            print("\\nDisconnected from EXNESS")

        return signals

def main():
    """Main function"""
    system = DeepSeekCurlTrading()
    system.run_curl_trading_test()

if __name__ == "__main__":
    main()