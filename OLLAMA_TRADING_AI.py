"""
OLLAMA AI Trading Integration System
Integrates Ollama LLM for intelligent trading decisions
Author: Trading Pro System
Version: 3.0
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import requests
import json
import time
import sys
import os
from datetime import datetime, timedelta

# Add paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

print("OLLAMA AI TRADING SYSTEM v3.0")
print("="*50)

class OllamaAITrader:
    """AI-powered trading system using Ollama LLM"""

    def __init__(self, ollama_url="http://localhost:11434", model="llama3.2"):
        # EXNESS Configuration
        self.exness_config = {
            'path': r"C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe",
            'login': 197678662,
            'password': "Badboy930218*",
            'server': "Exness-MT5Trial11"
        }

        # Ollama Configuration
        self.ollama_url = ollama_url
        self.model = model

        # Trading symbols
        self.symbols = ['XAUUSDm', 'EURUSDm', 'GBPUSDm', 'USDJPYm', 'BTCUSDm']

        self.connected = False
        self.account_info = None
        self.symbol_data = {}
        self.cycle_count = 0
        self.ai_decisions = []

        print("Initializing Ollama AI Trading System...")
        self._test_ollama_connection()

    def _test_ollama_connection(self):
        """Test connection to Ollama"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                print(f"  [OK] Ollama connected - Available models: {len(models)}")

                # Check if our model is available
                model_names = [m['name'] for m in models]
                if any(self.model in name for name in model_names):
                    print(f"  [OK] Model '{self.model}' available")
                else:
                    print(f"  [WARNING] Model '{self.model}' not found")
                    print(f"  Available models: {model_names}")
                return True
            else:
                print(f"  [ERROR] Ollama not responding")
                return False
        except Exception as e:
            print(f"  [ERROR] Ollama connection failed: {e}")
            print(f"  Make sure Ollama is running: 'ollama serve'")
            return False

    def query_ollama(self, prompt, max_tokens=500):
        """Query Ollama LLM for analysis"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": 0.3,
                    "top_p": 0.9
                }
            }

            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return result.get('response', '').strip()
            else:
                print(f"Ollama query failed: {response.status_code}")
                return None

        except Exception as e:
            print(f"Error querying Ollama: {e}")
            return None

    def connect_mt5(self):
        """Connect to EXNESS MT5"""
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

            print(f"\\nConnected to EXNESS:")
            print(f"  Balance: ${self.account_info.balance:,.2f}")
            print(f"  Equity: ${self.account_info.equity:,.2f}")

            self._setup_symbols()
            return True

        except Exception as e:
            print(f"MT5 connection error: {e}")
            return False

    def _setup_symbols(self):
        """Setup trading symbols"""
        for symbol in self.symbols:
            try:
                if mt5.symbol_select(symbol, True):
                    symbol_info = mt5.symbol_info(symbol)
                    if symbol_info:
                        self.symbol_data[symbol] = {
                            'min_volume': symbol_info.volume_min,
                            'max_volume': symbol_info.volume_max,
                            'volume_step': symbol_info.volume_step,
                        }
                        print(f"  [OK] {symbol}")
            except:
                pass

    def get_market_data(self, symbol, timeframe=mt5.TIMEFRAME_H1, count=50):
        """Get market data for AI analysis"""
        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            if rates is not None and len(rates) > 0:
                df = pd.DataFrame(rates)
                df['time'] = pd.to_datetime(df['time'], unit='s')
                return df
        except:
            pass
        return pd.DataFrame()

    def calculate_technical_indicators(self, data):
        """Calculate technical indicators for AI analysis"""
        try:
            # Price indicators
            data['sma_20'] = data['close'].rolling(20).mean()
            data['sma_50'] = data['close'].rolling(50).mean()
            data['ema_12'] = data['close'].ewm(span=12).mean()
            data['ema_26'] = data['close'].ewm(span=26).mean()

            # RSI
            delta = data['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            data['rsi'] = 100 - (100 / (1 + rs))

            # MACD
            data['macd'] = data['ema_12'] - data['ema_26']
            data['macd_signal'] = data['macd'].ewm(span=9).mean()
            data['macd_histogram'] = data['macd'] - data['macd_signal']

            # Bollinger Bands
            data['bb_middle'] = data['close'].rolling(20).mean()
            bb_std = data['close'].rolling(20).std()
            data['bb_upper'] = data['bb_middle'] + (bb_std * 2)
            data['bb_lower'] = data['bb_middle'] - (bb_std * 2)

            # Volume analysis
            data['volume_sma'] = data['tick_volume'].rolling(20).mean()
            data['volume_ratio'] = data['tick_volume'] / data['volume_sma']

            return data

        except Exception as e:
            print(f"Error calculating indicators: {e}")
            return data

    def prepare_ai_prompt(self, symbol, data):
        """Prepare comprehensive prompt for AI analysis"""
        try:
            latest = data.iloc[-1]
            prev = data.iloc[-2]

            # Calculate key metrics
            price_change = ((latest['close'] - prev['close']) / prev['close']) * 100
            volume_change = ((latest['tick_volume'] - prev['tick_volume']) / prev['tick_volume']) * 100

            # Trend analysis
            if latest['sma_20'] > latest['sma_50']:
                trend = "BULLISH"
            else:
                trend = "BEARISH"

            # Support/Resistance
            recent_high = data['high'].tail(10).max()
            recent_low = data['low'].tail(10).min()

            prompt = f"""
PROFESSIONAL TRADING ANALYSIS REQUEST

Symbol: {symbol}
Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Timeframe: 1-Hour Analysis

CURRENT MARKET DATA:
- Current Price: {latest['close']:.5f}
- Price Change: {price_change:+.2f}%
- Volume Change: {volume_change:+.2f}%
- Trend: {trend}

TECHNICAL INDICATORS:
- RSI: {latest['rsi']:.1f}
- MACD: {latest['macd']:.5f}
- MACD Signal: {latest['macd_signal']:.5f}
- MACD Histogram: {latest['macd_histogram']:.5f}
- Price vs SMA20: {((latest['close'] - latest['sma_20']) / latest['sma_20'] * 100):+.2f}%
- Price vs SMA50: {((latest['close'] - latest['sma_50']) / latest['sma_50'] * 100):+.2f}%

BOLLINGER BANDS:
- Upper Band: {latest['bb_upper']:.5f}
- Middle Band: {latest['bb_middle']:.5f}
- Lower Band: {latest['bb_lower']:.5f}
- BB Position: {((latest['close'] - latest['bb_lower']) / (latest['bb_upper'] - latest['bb_lower']) * 100):.1f}%

SUPPORT/RESISTANCE:
- Recent High: {recent_high:.5f}
- Recent Low: {recent_low:.5f}
- Distance to High: {((recent_high - latest['close']) / latest['close'] * 100):+.2f}%
- Distance to Low: {((latest['close'] - recent_low) / latest['close'] * 100):+.2f}%

VOLUME ANALYSIS:
- Current Volume: {latest['tick_volume']:,.0f}
- Volume vs Average: {latest['volume_ratio']:.2f}x

TASK: Analyze this market data and provide a trading recommendation.

REQUIRED RESPONSE FORMAT:
DECISION: [BUY/SELL/HOLD]
CONFIDENCE: [0-100]%
ENTRY_PRICE: [specific price]
STOP_LOSS: [specific price]
TAKE_PROFIT: [specific price]
REASONING: [brief explanation]
RISK_LEVEL: [LOW/MEDIUM/HIGH]

Consider:
1. Technical indicator convergence/divergence
2. Support/resistance levels
3. Volume confirmation
4. Risk/reward ratio (minimum 1:2)
5. Market volatility

Provide ONLY the trading analysis. Be specific with prices.
"""
            return prompt

        except Exception as e:
            print(f"Error preparing AI prompt: {e}")
            return None

    def parse_ai_response(self, response):
        """Parse AI response into structured trading decision"""
        try:
            if not response:
                return None

            lines = response.strip().split('\n')
            decision_data = {}

            for line in lines:
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().upper().replace(' ', '_')
                    value = value.strip()

                    if key == 'DECISION':
                        decision_data['action'] = value.upper()
                    elif key == 'CONFIDENCE':
                        decision_data['confidence'] = float(value.replace('%', ''))
                    elif key == 'ENTRY_PRICE':
                        decision_data['entry_price'] = float(value)
                    elif key == 'STOP_LOSS':
                        decision_data['stop_loss'] = float(value)
                    elif key == 'TAKE_PROFIT':
                        decision_data['take_profit'] = float(value)
                    elif key == 'REASONING':
                        decision_data['reasoning'] = value
                    elif key == 'RISK_LEVEL':
                        decision_data['risk_level'] = value.upper()

            # Validate required fields
            required_fields = ['action', 'confidence', 'entry_price']
            if all(field in decision_data for field in required_fields):
                return decision_data
            else:
                print(f"Missing required fields in AI response: {decision_data}")
                return None

        except Exception as e:
            print(f"Error parsing AI response: {e}")
            return None

    def get_ai_trading_decision(self, symbol):
        """Get AI-powered trading decision"""
        try:
            print(f"\\n[AI ANALYSIS] {symbol}")

            # Get market data
            data = self.get_market_data(symbol)
            if len(data) < 50:
                print(f"  Insufficient data for {symbol}")
                return None

            # Calculate indicators
            data = self.calculate_technical_indicators(data)

            # Prepare AI prompt
            prompt = self.prepare_ai_prompt(symbol, data)
            if not prompt:
                return None

            print(f"  Querying Ollama AI...")

            # Query AI
            ai_response = self.query_ollama(prompt)
            if not ai_response:
                print(f"  No AI response for {symbol}")
                return None

            print(f"  AI Response received")

            # Parse response
            decision = self.parse_ai_response(ai_response)
            if decision:
                decision['symbol'] = symbol
                decision['timestamp'] = datetime.now()
                decision['raw_response'] = ai_response

                print(f"  AI Decision: {decision['action']} - Confidence: {decision['confidence']:.1f}%")
                if 'reasoning' in decision:
                    print(f"  Reasoning: {decision['reasoning'][:100]}...")

                return decision

        except Exception as e:
            print(f"Error getting AI decision for {symbol}: {e}")

        return None

    def calculate_position_size(self, decision):
        """Calculate position size based on AI confidence and risk level"""
        try:
            if not self.account_info:
                return 0.01

            # Base risk percentage
            base_risk = 0.005  # 0.5%

            # Adjust risk based on AI confidence
            confidence_factor = decision['confidence'] / 100
            risk_multiplier = 0.5 + (confidence_factor * 0.5)  # 0.5x to 1.0x

            # Adjust based on AI risk level
            risk_level = decision.get('risk_level', 'MEDIUM')
            if risk_level == 'LOW':
                risk_multiplier *= 0.7
            elif risk_level == 'HIGH':
                risk_multiplier *= 1.3

            # Calculate position size
            account_risk = base_risk * risk_multiplier
            risk_amount = self.account_info.equity * account_risk

            entry_price = decision['entry_price']
            stop_loss = decision.get('stop_loss', entry_price * 0.99)

            if decision['action'] == 'BUY':
                risk_per_unit = abs(entry_price - stop_loss)
            else:
                risk_per_unit = abs(stop_loss - entry_price)

            if risk_per_unit > 0:
                position_size = risk_amount / risk_per_unit

                # Convert to lots for forex
                symbol = decision['symbol']
                if symbol in ['EURUSDm', 'GBPUSDm', 'USDJPYm']:
                    lots = position_size / 100000  # Standard lot size
                else:
                    lots = position_size / entry_price

                # Round to symbol's volume step
                if symbol in self.symbol_data:
                    volume_step = self.symbol_data[symbol]['volume_step']
                    lots = round(lots / volume_step) * volume_step
                    lots = max(self.symbol_data[symbol]['min_volume'],
                              min(self.symbol_data[symbol]['max_volume'], lots))

                return max(0.01, lots)

        except Exception as e:
            print(f"Error calculating position size: {e}")

        return 0.01

    def execute_ai_trade(self, decision, volume):
        """Execute trade based on AI decision"""
        try:
            symbol = decision['symbol']
            action = decision['action']

            if action not in ['BUY', 'SELL']:
                return False

            # Get current price
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return False

            price = tick.ask if action == 'BUY' else tick.bid

            print(f"\\n  [AI TRADE EXECUTION]")
            print(f"    Symbol: {symbol}")
            print(f"    Action: {action}")
            print(f"    Volume: {volume} lots")
            print(f"    Price: {price:.5f}")
            print(f"    AI Confidence: {decision['confidence']:.1f}%")

            if 'reasoning' in decision:
                print(f"    AI Reasoning: {decision['reasoning'][:80]}...")

            # Execute real trade
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": mt5.ORDER_TYPE_BUY if action == 'BUY' else mt5.ORDER_TYPE_SELL,
                "price": price,
                "sl": decision.get('stop_loss'),
                "tp": decision.get('take_profit'),
                "deviation": 20,
                "magic": 197678662,
                "comment": f"OllamaAI: {decision['confidence']:.0f}%",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"    [SUCCESS] AI Trade executed - Ticket: {result.order}")

                # Store AI decision for learning
                self.ai_decisions.append({
                    'decision': decision,
                    'volume': volume,
                    'executed_price': price,
                    'ticket': result.order,
                    'timestamp': datetime.now()
                })

                return True
            else:
                print(f"    [ERROR] Trade failed: {result.retcode} - {result.comment}")
                return False

        except Exception as e:
            print(f"Error executing AI trade: {e}")
            return False

    def run_ai_trading_cycle(self):
        """Run one AI trading cycle"""
        self.cycle_count += 1

        print(f"\\n{'='*60}")
        print(f"AI TRADING CYCLE {self.cycle_count} - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*60}")

        if not self.connected:
            return False

        try:
            # Update account info
            self.account_info = mt5.account_info()
            positions = mt5.positions_get()

            print(f"Account Equity: ${self.account_info.equity:,.2f}")
            print(f"Open Positions: {len(positions) if positions else 0}")

            # Get AI decisions for all symbols
            ai_decisions = []
            for symbol in self.symbols:
                decision = self.get_ai_trading_decision(symbol)
                if decision and decision['action'] in ['BUY', 'SELL']:
                    ai_decisions.append(decision)

            print(f"\\nAI Decisions Generated: {len(ai_decisions)}")

            # Execute top AI recommendations
            if ai_decisions:
                # Sort by confidence
                ai_decisions.sort(key=lambda x: x['confidence'], reverse=True)

                executed = 0
                max_positions = 2

                for decision in ai_decisions:
                    current_positions = len(mt5.positions_get() or [])

                    if current_positions + executed < max_positions:
                        if decision['confidence'] >= 70:  # High confidence threshold
                            volume = self.calculate_position_size(decision)

                            if volume >= 0.01:
                                if self.execute_ai_trade(decision, volume):
                                    executed += 1

                print(f"\\nAI Trades Executed: {executed}")

            # Show position P&L
            if positions:
                total_profit = sum(pos.profit for pos in positions)
                print(f"Total P&L: ${total_profit:+.2f}")

            return True

        except Exception as e:
            print(f"Error in AI trading cycle: {e}")
            return False

    def run_ai_trading(self, cycles=10, delay=120):
        """Run AI trading system"""
        print(f"\\n*** STARTING OLLAMA AI TRADING SYSTEM ***")
        print(f"Model: {self.model}")
        print(f"Cycles: {cycles}")
        print(f"Delay: {delay}s")

        if not self.connected:
            print("Not connected to MT5")
            return

        try:
            for i in range(cycles):
                success = self.run_ai_trading_cycle()
                if not success:
                    break

                if i < cycles - 1:
                    print(f"\\nNext AI cycle in {delay} seconds...")
                    time.sleep(delay)

        except KeyboardInterrupt:
            print(f"\\nAI Trading stopped by user")

        print(f"\\nAI TRADING SUMMARY:")
        print(f"Total Cycles: {self.cycle_count}")
        print(f"AI Decisions Made: {len(self.ai_decisions)}")
        print(f"Final Equity: ${self.account_info.equity:,.2f}")

    def disconnect(self):
        """Disconnect from MT5"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            print("Disconnected from EXNESS")

def main():
    """Main AI trading function"""
    # Initialize AI trader
    ai_trader = OllamaAITrader(
        ollama_url="http://localhost:11434",
        model="llama3.2"  # You can change this to any model you have
    )

    try:
        if ai_trader.connect_mt5():
            print(f"\\n[AI SYSTEM READY]")
            print(f"Symbols: {len(ai_trader.symbol_data)}")

            # Start AI trading
            ai_trader.run_ai_trading(cycles=5, delay=180)  # 3 minutes between cycles
        else:
            print("[ERROR] Failed to connect to MT5")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        ai_trader.disconnect()

if __name__ == "__main__":
    main()