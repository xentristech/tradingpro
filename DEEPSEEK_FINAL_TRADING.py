"""
DeepSeek-R1:14b FINAL Trading System
Usando configuracion confirmada que funciona 100%
"""

import MetaTrader5 as mt5
import requests
import json
import time
from datetime import datetime

print("DEEPSEEK-R1:14B FINAL TRADING SYSTEM")
print("="*50)

class DeepSeekFinalTrading:
    def __init__(self):
        # EXNESS Configuration
        self.exness_config = {
            'path': r"C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe",
            'login': 197678662,
            'password': "Badboy930218*",
            'server': "Exness-MT5Trial11"
        }

        self.ollama_url = "http://localhost:11434/api/generate"
        self.model = "deepseek-r1:14b"

        # CONFIGURACION CONFIRMADA QUE FUNCIONA
        self.ollama_options = {
            "num_predict": 80,  # Mas tokens para analisis completo
            "temperature": 0.3   # Slightly higher for more variation
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

    def query_deepseek_final(self, prompt):
        """Query DeepSeek with final working configuration"""
        try:
            # EXACT payload that works
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": self.ollama_options
            }

            print(f"  Querying DeepSeek-R1...")

            # Simple request - no extra headers
            response = requests.post(
                self.ollama_url,
                json=payload,
                timeout=45
            )

            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '').strip()

                if len(response_text) > 0:
                    print(f"  [SUCCESS] DeepSeek responded ({len(response_text)} chars)")

                    # Clean response for display
                    clean_response = response_text.replace('\\n', ' ')[:150]
                    print(f"  Response: {clean_response}...")

                    self.successful_queries += 1
                    return response_text
                else:
                    print(f"  [EMPTY] No response content")
                    return None
            else:
                print(f"  [ERROR] HTTP {response.status_code}")
                return None

        except Exception as e:
            print(f"  [ERROR] Exception: {str(e)[:50]}...")
            return None

    def get_market_data_enhanced(self, symbol):
        """Get enhanced market data for analysis"""
        try:
            if not mt5.symbol_select(symbol, True):
                return None

            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return None

            # Get recent rates for technical analysis
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 50)
            if rates is None:
                return None

            import pandas as pd
            import numpy as np

            df = pd.DataFrame(rates)

            # Calculate technical indicators
            # RSI
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))

            # Moving averages
            sma_20 = df['close'].rolling(20).mean()
            sma_50 = df['close'].rolling(50).mean()

            # Price changes
            price_change_1h = ((df['close'].iloc[-1] - df['close'].iloc[-2]) / df['close'].iloc[-2]) * 100
            price_change_24h = ((df['close'].iloc[-1] - df['close'].iloc[-25]) / df['close'].iloc[-25]) * 100

            return {
                'symbol': symbol,
                'current_price': tick.bid,
                'ask_price': tick.ask,
                'spread': tick.ask - tick.bid,
                'rsi': rsi.iloc[-1] if not rsi.empty else 50,
                'sma_20': sma_20.iloc[-1] if not sma_20.empty else tick.bid,
                'sma_50': sma_50.iloc[-1] if not sma_50.empty else tick.bid,
                'price_change_1h': price_change_1h,
                'price_change_24h': price_change_24h,
                'volume': df['tick_volume'].iloc[-1],
                'high_24h': df['high'].tail(24).max(),
                'low_24h': df['low'].tail(24).min()
            }

        except Exception as e:
            print(f"  Error getting {symbol} data: {e}")
            return None

    def create_enhanced_prompt(self, symbol, data):
        """Create enhanced trading prompt for DeepSeek"""
        prompt = f"""Professional Forex Analysis Request:

Symbol: {symbol}
Current Price: {data['current_price']:.5f}
24H Change: {data['price_change_24h']:+.2f}%
1H Change: {data['price_change_1h']:+.2f}%

Technical Indicators:
- RSI(14): {data['rsi']:.1f}
- SMA(20): {data['sma_20']:.5f}
- SMA(50): {data['sma_50']:.5f}
- 24H High: {data['high_24h']:.5f}
- 24H Low: {data['low_24h']:.5f}
- Spread: {data['spread']:.5f}

Please provide a clear trading recommendation:
1. Decision: BUY, SELL, or HOLD
2. Confidence Level: 1-10
3. Entry Price: Suggest optimal entry
4. Stop Loss: Risk management level
5. Take Profit: Target profit level
6. Reasoning: Brief technical analysis

Be specific and actionable."""

        return prompt

    def parse_deepseek_analysis(self, response):
        """Parse DeepSeek trading analysis"""
        if not response:
            return None

        analysis = {}
        response_upper = response.upper()

        # Extract trading decision
        if 'BUY' in response_upper and 'SELL' not in response_upper:
            analysis['decision'] = 'BUY'
        elif 'SELL' in response_upper and 'BUY' not in response_upper:
            analysis['decision'] = 'SELL'
        else:
            analysis['decision'] = 'HOLD'

        # Try to extract confidence level
        import re
        confidence_match = re.search(r'confidence[:\s]*(\d+)', response_upper)
        if confidence_match:
            analysis['confidence'] = int(confidence_match.group(1))
        else:
            analysis['confidence'] = 5  # Default medium confidence

        # Extract reasoning (first sentence)
        sentences = response.split('.')
        if sentences:
            analysis['reasoning'] = sentences[0].strip()[:150]
        else:
            analysis['reasoning'] = response[:150]

        return analysis

    def analyze_with_deepseek(self, symbol):
        """Complete analysis with DeepSeek AI"""
        print(f"\\n[DEEPSEEK ANALYSIS] {symbol}")

        # Get market data
        market_data = self.get_market_data_enhanced(symbol)
        if not market_data:
            print(f"  [ERROR] Could not get market data")
            return None

        # Display market info
        print(f"  Price: {market_data['current_price']:.5f}")
        print(f"  RSI: {market_data['rsi']:.1f}")
        print(f"  24H Change: {market_data['price_change_24h']:+.2f}%")

        # Create enhanced prompt
        prompt = self.create_enhanced_prompt(symbol, market_data)

        # Query DeepSeek AI
        response = self.query_deepseek_final(prompt)

        if response:
            # Parse AI analysis
            analysis = self.parse_deepseek_analysis(response)

            if analysis:
                print(f"  AI Decision: {analysis['decision']}")
                print(f"  Confidence: {analysis['confidence']}/10")
                print(f"  Reasoning: {analysis['reasoning']}")

                # Count actionable signals
                if analysis['decision'] in ['BUY', 'SELL'] and analysis['confidence'] >= 7:
                    self.signals_generated += 1
                    print(f"  [HIGH CONFIDENCE SIGNAL] {analysis['decision']} {symbol}")

                    return {
                        'symbol': symbol,
                        'decision': analysis['decision'],
                        'confidence': analysis['confidence'],
                        'price': market_data['current_price'],
                        'reasoning': analysis['reasoning'],
                        'rsi': market_data['rsi'],
                        'timestamp': datetime.now().strftime("%H:%M:%S"),
                        'ai_response': response
                    }

        return None

    def run_deepseek_trading_session(self):
        """Run complete DeepSeek trading session"""
        print("\\n" + "="*70)
        print("DEEPSEEK-R1:14B LIVE TRADING SESSION")
        print("="*70)

        symbols = ['EURUSDm', 'GBPUSDm', 'XAUUSDm', 'USDJPYm', 'BTCUSDm']
        high_confidence_signals = []

        for symbol in symbols:
            signal_data = self.analyze_with_deepseek(symbol)
            if signal_data:
                high_confidence_signals.append(signal_data)

            print("  " + "-"*60)
            time.sleep(4)  # Pause to avoid overwhelming DeepSeek

        # Session Results
        print("\\n" + "="*70)
        print("DEEPSEEK TRADING SESSION RESULTS")
        print("="*70)
        print(f"AI Queries Successful: {self.successful_queries}")
        print(f"High Confidence Signals: {self.signals_generated}")

        if high_confidence_signals:
            print(f"\\n[HIGH CONFIDENCE TRADING SIGNALS]")
            for signal in high_confidence_signals:
                print(f"\\n{signal['timestamp']} - {signal['decision']} {signal['symbol']}")
                print(f"  Price: {signal['price']:.5f} | Confidence: {signal['confidence']}/10")
                print(f"  RSI: {signal['rsi']:.1f}")
                print(f"  AI Reasoning: {signal['reasoning']}")
        else:
            print(f"\\nNo high confidence signals detected in this session")

        return high_confidence_signals

    def run_final_session(self):
        """Run final DeepSeek trading session"""
        print("\\nStarting DeepSeek-R1:14b Final Trading Session...")

        # Connect to MT5
        if not self.connect_mt5():
            print("\\n[FAILED] MT5 connection failed")
            return []

        # Run DeepSeek analysis
        signals = self.run_deepseek_trading_session()

        print("\\n" + "="*70)
        print("DEEPSEEK-R1:14B FINAL SESSION COMPLETED!")

        if self.successful_queries > 0:
            print(f"✓ DeepSeek-R1:14b working perfectly!")
            print(f"✓ AI provided {self.successful_queries} trading analyses")
            print(f"✓ Generated {self.signals_generated} high confidence signals")
        else:
            print("✗ DeepSeek not responding")

        print("="*70)

        # Disconnect
        if self.connected:
            mt5.shutdown()
            print("\\nDisconnected from EXNESS")

        return signals

def main():
    """Main function"""
    system = DeepSeekFinalTrading()
    signals = system.run_final_session()

    # Summary
    if signals:
        print(f"\\n🎯 READY FOR LIVE TRADING WITH DEEPSEEK-R1:14B!")
        print(f"High confidence signals detected: {len(signals)}")
    else:
        print(f"\\n📊 System ready, waiting for optimal market conditions")

if __name__ == "__main__":
    main()