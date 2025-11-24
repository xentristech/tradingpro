"""
TwelveData Professional Trading System
Sistema profesional con datos de mercado de alta calidad
API Key: 23d17ce5b7044ad5aef9766770a6252b
"""

import MetaTrader5 as mt5
import requests
import json
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

print("TWELVEDATA PROFESSIONAL TRADING SYSTEM")
print("="*50)

class TwelveDataProSystem:
    def __init__(self):
        # EXNESS Configuration
        self.exness_config = {
            'path': r"C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe",
            'login': 197678662,
            'password': "Badboy930218*",
            'server': "Exness-MT5Trial11"
        }

        # TwelveData Professional API
        self.twelvedata_api_key = "23d17ce5b7044ad5aef9766770a6252b"
        self.twelvedata_base_url = "https://api.twelvedata.com"

        # DeepSeek Integration
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model = "deepseek-r1:14b"

        self.connected = False
        self.account_info = None
        self.market_data_cache = {}

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

    def test_twelvedata_connection(self):
        """Test TwelveData API connection"""
        print("\\nTesting TwelveData API...")

        try:
            # Test API with quote endpoint
            url = f"{self.twelvedata_base_url}/quote"
            params = {
                'symbol': 'EUR/USD',
                'apikey': self.twelvedata_api_key
            }

            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if 'close' in data:
                    print(f"  [OK] TwelveData API working")
                    print(f"  Sample: EURUSD = {data['close']}")
                    return True
                else:
                    print(f"  [ERROR] Invalid response: {data}")
                    return False
            else:
                print(f"  [ERROR] HTTP {response.status_code}: {response.text}")
                return False

        except Exception as e:
            print(f"  [ERROR] Connection failed: {e}")
            return False

    def get_professional_market_data(self, symbol):
        """Get professional market data from TwelveData"""
        try:
            # Convert MT5 symbols to TwelveData format
            symbol_map = {
                'EURUSDm': 'EUR/USD',
                'GBPUSDm': 'GBP/USD',
                'USDJPYm': 'USD/JPY',
                'AUDUSDm': 'AUD/USD',
                'USDCHFm': 'USD/CHF',
                'USDCADm': 'USD/CAD',
                'XAUUSDm': 'XAU/USD',
                'BTCUSDm': 'BTC/USD'
            }

            td_symbol = symbol_map.get(symbol, symbol.replace('m', ''))

            print(f"  Fetching professional data for {td_symbol}...")

            # 1. Real-time quote
            quote_url = f"{self.twelvedata_base_url}/quote"
            quote_params = {
                'symbol': td_symbol,
                'apikey': self.twelvedata_api_key
            }

            quote_response = requests.get(quote_url, params=quote_params, timeout=10)

            if quote_response.status_code != 200:
                print(f"    [ERROR] Quote failed: {quote_response.status_code}")
                return None

            quote_data = quote_response.json()

            # 2. Technical indicators
            indicators = {}

            # RSI
            rsi_url = f"{self.twelvedata_base_url}/rsi"
            rsi_params = {
                'symbol': td_symbol,
                'interval': '1h',
                'time_period': 14,
                'apikey': self.twelvedata_api_key
            }

            rsi_response = requests.get(rsi_url, params=rsi_params, timeout=10)
            if rsi_response.status_code == 200:
                rsi_data = rsi_response.json()
                if 'values' in rsi_data and rsi_data['values']:
                    indicators['rsi'] = float(rsi_data['values'][0]['rsi'])

            time.sleep(1)  # Rate limiting

            # Moving Averages
            sma_url = f"{self.twelvedata_base_url}/sma"
            sma_params = {
                'symbol': td_symbol,
                'interval': '1h',
                'time_period': 20,
                'apikey': self.twelvedata_api_key
            }

            sma_response = requests.get(sma_url, params=sma_params, timeout=10)
            if sma_response.status_code == 200:
                sma_data = sma_response.json()
                if 'values' in sma_data and sma_data['values']:
                    indicators['sma_20'] = float(sma_data['values'][0]['sma'])

            time.sleep(1)  # Rate limiting

            # 3. Time series for additional analysis
            ts_url = f"{self.twelvedata_base_url}/time_series"
            ts_params = {
                'symbol': td_symbol,
                'interval': '1h',
                'outputsize': 50,
                'apikey': self.twelvedata_api_key
            }

            ts_response = requests.get(ts_url, params=ts_params, timeout=10)
            price_history = []
            if ts_response.status_code == 200:
                ts_data = ts_response.json()
                if 'values' in ts_data:
                    price_history = ts_data['values'][:10]  # Last 10 periods

            # Compile professional data
            current_price = float(quote_data.get('close', 0))

            professional_data = {
                'symbol': symbol,
                'td_symbol': td_symbol,
                'current_price': current_price,
                'open': float(quote_data.get('open', current_price)),
                'high': float(quote_data.get('high', current_price)),
                'low': float(quote_data.get('low', current_price)),
                'volume': int(quote_data.get('volume', 0)),
                'change': float(quote_data.get('change', 0)),
                'percent_change': float(quote_data.get('percent_change', 0)),
                'rsi': indicators.get('rsi', 50),
                'sma_20': indicators.get('sma_20', current_price),
                'price_history': price_history,
                'timestamp': quote_data.get('datetime', datetime.now().isoformat()),
                'data_source': 'TwelveData Professional'
            }

            print(f"    [SUCCESS] Professional data loaded")
            return professional_data

        except Exception as e:
            print(f"    [ERROR] TwelveData fetch failed: {e}")
            return None

    def query_deepseek_with_professional_data(self, symbol, professional_data):
        """Query DeepSeek with professional market data"""
        try:
            # Create enhanced prompt with TwelveData
            prompt = f"""Professional Trading Analysis using TwelveData API:

Symbol: {professional_data['td_symbol']}
Current Price: {professional_data['current_price']:.5f}
Daily Change: {professional_data['percent_change']:+.2f}%
Volume: {professional_data['volume']:,}

Professional Technical Indicators:
- RSI(14): {professional_data['rsi']:.1f}
- SMA(20): {professional_data['sma_20']:.5f}
- Day High: {professional_data['high']:.5f}
- Day Low: {professional_data['low']:.5f}

Price vs SMA20: {((professional_data['current_price'] - professional_data['sma_20']) / professional_data['sma_20'] * 100):+.2f}%

Data Source: {professional_data['data_source']}
Timestamp: {professional_data['timestamp']}

Based on this professional-grade market data, provide:
1. Trading Decision: BUY/SELL/HOLD
2. Confidence: 1-10 scale
3. Key reasoning (2-3 sentences)

Focus on technical analysis using the professional indicators."""

            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": 100,
                    "temperature": 0.3
                }
            }

            print(f"  Querying DeepSeek with professional data...")

            response = requests.post(
                self.ollama_url,
                json=payload,
                timeout=45
            )

            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '').strip()

                if len(response_text) > 0:
                    print(f"  [SUCCESS] DeepSeek analysis received")
                    return response_text
                else:
                    print(f"  [EMPTY] No AI response")
                    return None
            else:
                print(f"  [ERROR] AI query failed: {response.status_code}")
                return None

        except Exception as e:
            print(f"  [ERROR] AI analysis failed: {e}")
            return None

    def parse_professional_analysis(self, ai_response):
        """Parse AI analysis of professional data"""
        if not ai_response:
            return None

        analysis = {}
        response_upper = ai_response.upper()

        # Extract decision
        if 'BUY' in response_upper and 'SELL' not in response_upper:
            analysis['decision'] = 'BUY'
        elif 'SELL' in response_upper and 'BUY' not in response_upper:
            analysis['decision'] = 'SELL'
        else:
            analysis['decision'] = 'HOLD'

        # Extract confidence
        import re
        confidence_patterns = [
            r'confidence[:\s]*(\d+)',
            r'(\d+)[/]10',
            r'(\d+)\s*out\s*of\s*10'
        ]

        confidence = 5  # Default
        for pattern in confidence_patterns:
            match = re.search(pattern, response_upper)
            if match:
                confidence = min(int(match.group(1)), 10)
                break

        analysis['confidence'] = confidence

        # Extract reasoning
        sentences = ai_response.split('.')
        if sentences:
            analysis['reasoning'] = sentences[0].strip()[:200]
        else:
            analysis['reasoning'] = ai_response[:200]

        return analysis

    def analyze_symbol_professionally(self, symbol):
        """Complete professional analysis of symbol"""
        print(f"\\n[PROFESSIONAL ANALYSIS] {symbol}")

        # Get professional market data
        professional_data = self.get_professional_market_data(symbol)
        if not professional_data:
            print(f"  [FAILED] Could not get professional data")
            return None

        print(f"  Price: {professional_data['current_price']:.5f}")
        print(f"  Change: {professional_data['percent_change']:+.2f}%")
        print(f"  RSI: {professional_data['rsi']:.1f}")
        print(f"  Volume: {professional_data['volume']:,}")

        # AI analysis with professional data
        ai_response = self.query_deepseek_with_professional_data(symbol, professional_data)

        if ai_response:
            analysis = self.parse_professional_analysis(ai_response)

            if analysis:
                print(f"  AI Decision: {analysis['decision']}")
                print(f"  Confidence: {analysis['confidence']}/10")
                print(f"  Reasoning: {analysis['reasoning']}")

                # Professional signal
                if analysis['decision'] in ['BUY', 'SELL'] and analysis['confidence'] >= 7:
                    print(f"  [PROFESSIONAL SIGNAL] {analysis['decision']} {symbol}")

                    return {
                        'symbol': symbol,
                        'decision': analysis['decision'],
                        'confidence': analysis['confidence'],
                        'market_data': professional_data,
                        'ai_reasoning': analysis['reasoning'],
                        'signal_quality': 'PROFESSIONAL',
                        'timestamp': datetime.now().strftime("%H:%M:%S")
                    }

        return None

    def run_professional_trading_session(self):
        """Run professional trading session with TwelveData"""
        print("\\n" + "="*70)
        print("TWELVEDATA PROFESSIONAL TRADING SESSION")
        print("="*70)

        # Test TwelveData first
        if not self.test_twelvedata_connection():
            print("\\n[FAILED] TwelveData API not working")
            return []

        symbols = ['EURUSDm', 'GBPUSDm', 'XAUUSDm', 'USDJPYm', 'BTCUSDm']
        professional_signals = []

        for symbol in symbols:
            signal_data = self.analyze_symbol_professionally(symbol)
            if signal_data:
                professional_signals.append(signal_data)

            print("  " + "-"*60)
            time.sleep(3)  # Rate limiting for API

        # Professional Results
        print("\\n" + "="*70)
        print("PROFESSIONAL TRADING SESSION RESULTS")
        print("="*70)
        print(f"Symbols Analyzed: {len(symbols)}")
        print(f"Professional Signals: {len(professional_signals)}")

        if professional_signals:
            print(f"\\n[PROFESSIONAL TRADING SIGNALS]")
            for signal in professional_signals:
                print(f"\\n{signal['timestamp']} - {signal['decision']} {signal['symbol']}")
                print(f"  Price: {signal['market_data']['current_price']:.5f}")
                print(f"  Confidence: {signal['confidence']}/10")
                print(f"  Quality: {signal['signal_quality']}")
                print(f"  AI Analysis: {signal['ai_reasoning']}")
        else:
            print(f"\\nNo professional signals detected")
            print("Market conditions may not meet professional criteria")

        return professional_signals

    def run_professional_system(self):
        """Run complete professional system"""
        print("\\nStarting TwelveData Professional Trading System...")

        # Connect to MT5
        if not self.connect_mt5():
            print("\\n[FAILED] MT5 connection failed")
            return []

        # Run professional analysis
        signals = self.run_professional_trading_session()

        print("\\n" + "="*70)
        print("TWELVEDATA PROFESSIONAL SYSTEM COMPLETED!")

        if signals:
            print(f"✓ Professional trading system operational")
            print(f"✓ TwelveData API integration successful")
            print(f"✓ Generated {len(signals)} professional signals")
        else:
            print("System operational, awaiting optimal conditions")

        print("="*70)

        # Disconnect
        if self.connected:
            mt5.shutdown()
            print("\\nDisconnected from EXNESS")

        return signals

def main():
    """Main function"""
    system = TwelveDataProSystem()
    signals = system.run_professional_system()

    if signals:
        print(f"\\nPROFESSIONAL TRADING SYSTEM READY!")
        print(f"High-quality signals detected: {len(signals)}")

if __name__ == "__main__":
    main()