"""
DeepSeek-R1:14b Working Trading System
Configuracion confirmada que funciona
"""

import MetaTrader5 as mt5
import requests
import json
import time
from datetime import datetime

print("DEEPSEEK-R1:14B WORKING TRADING SYSTEM")
print("="*50)

class DeepSeekWorkingTrading:
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

        # Configuracion que funciona con curl
        self.ollama_options = {
            "num_predict": 50,
            "temperature": 0.2
        }

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

    def query_deepseek_working(self, prompt):
        """Query DeepSeek with working configuration"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": self.ollama_options
            }

            print(f"  Querying DeepSeek-R1...")

            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=45
            )

            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '').strip()

                if len(response_text) > 0:
                    # Remove problematic characters for Windows console
                    safe_response = response_text.replace('\n', ' ').replace('\r', ' ')
                    # Limit length for display
                    display_response = safe_response[:120] + "..." if len(safe_response) > 120 else safe_response

                    print(f"  Response: {display_response}")
                    self.successful_queries += 1
                    return response_text
                else:
                    print(f"  Empty response from DeepSeek")
                    return None
            else:
                print(f"  Query failed: {response.status_code}")
                return None

        except Exception as e:
            print(f"  Error querying DeepSeek: {str(e)[:50]}...")
            return None

    def get_market_data(self, symbol):
        """Get market data with indicators"""
        try:
            if not mt5.symbol_select(symbol, True):
                return None

            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return None

            # Get recent rates for RSI calculation
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 20)
            if rates is None:
                return None

            import pandas as pd
            df = pd.DataFrame(rates)

            # Calculate RSI
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            return {
                'symbol': symbol,
                'price': tick.bid,
                'ask': tick.ask,
                'spread': tick.ask - tick.bid,
                'rsi': rsi.iloc[-1] if not rsi.empty else 50,
                'change': ((df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2]) * 100
            }

        except Exception as e:
            print(f"  Error getting {symbol} data: {e}")
            return None

    def create_trading_prompt(self, symbol, market_data):
        """Create clear trading prompt"""
        prompt = f"""Trading Analysis for {symbol}:

Current Price: {market_data['price']:.5f}
RSI: {market_data['rsi']:.1f}
Price Change: {market_data['change']:+.2f}%
Spread: {market_data['spread']:.5f}

Based on this data, provide a clear trading recommendation:
- Decision: BUY, SELL, or HOLD
- Reason: Brief explanation (1-2 sentences)

Format your response clearly."""

        return prompt

    def parse_trading_signal(self, response):
        """Parse trading signal from DeepSeek response"""
        if not response:
            return None, None

        response_upper = response.upper()

        # Look for clear trading signals
        if 'BUY' in response_upper and 'SELL' not in response_upper:
            signal = 'BUY'
        elif 'SELL' in response_upper and 'BUY' not in response_upper:
            signal = 'SELL'
        elif 'HOLD' in response_upper:
            signal = 'HOLD'
        else:
            # Try to infer from bullish/bearish sentiment
            if any(word in response_upper for word in ['BULLISH', 'STRONG', 'UP', 'RISE', 'HIGHER']):
                signal = 'BUY'
            elif any(word in response_upper for word in ['BEARISH', 'WEAK', 'DOWN', 'FALL', 'LOWER']):
                signal = 'SELL'
            else:
                signal = 'HOLD'

        # Extract reasoning (first sentence or first 100 chars)
        reasoning = response.split('.')[0] if '.' in response else response
        reasoning = reasoning[:100] + "..." if len(reasoning) > 100 else reasoning

        return signal, reasoning

    def analyze_symbol_with_deepseek(self, symbol):
        """Analyze symbol with DeepSeek AI"""
        print(f"\\n[ANALYZING] {symbol}")

        # Get market data
        market_data = self.get_market_data(symbol)
        if not market_data:
            print(f"  [ERROR] Could not get market data")
            return None

        print(f"  Price: {market_data['price']:.5f}")
        print(f"  RSI: {market_data['rsi']:.1f}")
        print(f"  Change: {market_data['change']:+.2f}%")

        # Create prompt
        prompt = self.create_trading_prompt(symbol, market_data)

        # Query DeepSeek
        response = self.query_deepseek_working(prompt)

        if response:
            # Parse signal and reasoning
            signal, reasoning = self.parse_trading_signal(response)

            print(f"  Signal: {signal}")
            if reasoning:
                print(f"  Reason: {reasoning}")

            # Count actionable signals
            if signal in ['BUY', 'SELL']:
                self.signals_generated += 1
                print(f"  [SIGNAL DETECTED] {signal} {symbol}")

                return {
                    'symbol': symbol,
                    'signal': signal,
                    'price': market_data['price'],
                    'rsi': market_data['rsi'],
                    'reasoning': reasoning,
                    'timestamp': datetime.now().strftime("%H:%M:%S")
                }

        return None

    def run_deepseek_trading_analysis(self):
        """Run complete DeepSeek trading analysis"""
        print("\\n" + "="*60)
        print("DEEPSEEK-R1:14B LIVE TRADING ANALYSIS")
        print("="*60)

        symbols = ['EURUSDm', 'GBPUSDm', 'XAUUSDm', 'USDJPYm']
        detected_signals = []

        for symbol in symbols:
            signal_data = self.analyze_symbol_with_deepseek(symbol)
            if signal_data:
                detected_signals.append(signal_data)

            print("  " + "-"*50)
            time.sleep(3)  # Pause between queries to avoid overloading

        # Summary
        print("\\n" + "="*60)
        print("DEEPSEEK TRADING ANALYSIS RESULTS")
        print("="*60)
        print(f"Successful AI Queries: {self.successful_queries}")
        print(f"Trading Signals Generated: {self.signals_generated}")

        if detected_signals:
            print(f"\\n[ACTIONABLE SIGNALS DETECTED]")
            for signal in detected_signals:
                print(f"  {signal['timestamp']} - {signal['signal']} {signal['symbol']}")
                print(f"    Price: {signal['price']:.5f} | RSI: {signal['rsi']:.1f}")
                print(f"    Reason: {signal['reasoning']}")
                print()
        else:
            print(f"\\nNo actionable trading signals detected")
            print("Current market conditions may not meet DeepSeek's criteria")

        return detected_signals

    def run_deepseek_test(self):
        """Run complete DeepSeek trading test"""
        print("\\nStarting DeepSeek-R1:14b Working Trading System...")

        # Connect to MT5
        if not self.connect_mt5():
            print("\\n[FAILED] MT5 connection failed")
            return []

        # Run analysis
        signals = self.run_deepseek_trading_analysis()

        print("\\n" + "="*60)
        print("DEEPSEEK WORKING TRADING SYSTEM COMPLETED!")

        if self.successful_queries > 0:
            print(f"SUCCESS: DeepSeek-R1:14b is working!")
            print(f"AI Responses: {self.successful_queries}")
            print(f"Signals Generated: {self.signals_generated}")
        else:
            print("FAILED: DeepSeek not responding")

        print("="*60)

        # Disconnect
        if self.connected:
            mt5.shutdown()
            print("\\nDisconnected from EXNESS")

        return signals

def main():
    """Main function"""
    system = DeepSeekWorkingTrading()
    system.run_deepseek_test()

if __name__ == "__main__":
    main()