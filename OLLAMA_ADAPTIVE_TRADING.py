"""
Adaptive Ollama Trading System
Tests available models and uses the best one for trading decisions
Author: Trading Pro System
Version: 3.0
"""

import MetaTrader5 as mt5
import requests
import json
import time
from datetime import datetime
import pandas as pd
import numpy as np

print("ADAPTIVE OLLAMA TRADING SYSTEM v3.0")
print("="*50)

class AdaptiveOllamaTrader:
    """Trading system that adapts to available Ollama models"""

    def __init__(self):
        # EXNESS Configuration
        self.exness_config = {
            'path': r"C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe",
            'login': 197678662,
            'password': "Badboy930218*",
            'server': "Exness-MT5Trial11"
        }

        # Ollama Configuration
        self.ollama_url = "http://localhost:11434"
        self.available_models = []
        self.best_model = None

        self.connected = False
        self.account_info = None
        self.symbol_data = {}
        self.trading_decisions = []

        print("Initializing Adaptive Ollama Trading System...")
        self._discover_models()

    def _discover_models(self):
        """Discover and test available models"""
        print("\\nDiscovering available models...")

        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]

                print(f"  Found {len(models)} models:")
                for name in model_names:
                    print(f"    - {name}")

                # Test models for trading capability
                self._test_models(model_names)

            else:
                print(f"  [ERROR] Ollama server not responding")

        except Exception as e:
            print(f"  [ERROR] Failed to discover models: {e}")

    def _test_models(self, model_names):
        """Test models for trading analysis capability"""
        print(f"\\nTesting models for trading analysis...")

        test_prompt = """
TRADING ANALYSIS TEST

Current Data:
- Symbol: EURUSD
- Price: 1.16259
- RSI: 60.5

Task: Provide trading recommendation.

Format:
ACTION: BUY/SELL/HOLD
CONFIDENCE: 0-100
REASON: brief explanation

Respond only with the analysis.
"""

        working_models = []

        for model in model_names:
            print(f"  Testing {model}...")

            try:
                payload = {
                    "model": model,
                    "prompt": test_prompt,
                    "stream": False,
                    "options": {
                        "num_predict": 150,
                        "temperature": 0.2
                    }
                }

                response = requests.post(
                    f"{self.ollama_url}/api/generate",
                    json=payload,
                    timeout=30
                )

                if response.status_code == 200:
                    result = response.json().get('response', '').strip()

                    if result and len(result) > 10:
                        print(f"    [OK] {model} - Response length: {len(result)}")
                        working_models.append({
                            'name': model,
                            'response_length': len(result),
                            'test_response': result[:100] + "..." if len(result) > 100 else result
                        })
                    else:
                        print(f"    [SKIP] {model} - Empty or minimal response")
                else:
                    print(f"    [SKIP] {model} - Request failed")

            except Exception as e:
                print(f"    [SKIP] {model} - Error: {e}")

        # Select best model
        if working_models:
            # Prefer models with longer, more detailed responses
            best = max(working_models, key=lambda x: x['response_length'])
            self.best_model = best['name']

            print(f"\\n  [SELECTED] Best model: {self.best_model}")
            print(f"  Sample response: {best['test_response']}")

            self.available_models = working_models
        else:
            print(f"\\n  [ERROR] No working models found")

    def connect_mt5(self):
        """Connect to EXNESS MT5"""
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

            self._setup_symbols()
            return True

        except Exception as e:
            print(f"  [ERROR] MT5 connection failed: {e}")
            return False

    def _setup_symbols(self):
        """Setup trading symbols"""
        symbols = ['EURUSDm', 'GBPUSDm', 'XAUUSDm', 'USDJPYm']

        for symbol in symbols:
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

    def get_market_analysis_data(self, symbol):
        """Get comprehensive market data for AI analysis"""
        try:
            # Get current tick
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return None

            # Get historical data
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 100)
            if rates is None or len(rates) < 50:
                return None

            df = pd.DataFrame(rates)

            # Calculate indicators
            df['sma_20'] = df['close'].rolling(20).mean()
            df['sma_50'] = df['close'].rolling(50).mean()

            # RSI
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))

            # MACD
            ema_12 = df['close'].ewm(span=12).mean()
            ema_26 = df['close'].ewm(span=26).mean()
            df['macd'] = ema_12 - ema_26
            df['macd_signal'] = df['macd'].ewm(span=9).mean()

            # Bollinger Bands
            df['bb_middle'] = df['close'].rolling(20).mean()
            bb_std = df['close'].rolling(20).std()
            df['bb_upper'] = df['bb_middle'] + (bb_std * 2)
            df['bb_lower'] = df['bb_middle'] - (bb_std * 2)

            latest = df.iloc[-1]

            return {
                'symbol': symbol,
                'current_price': tick.bid,
                'ask': tick.ask,
                'spread': tick.ask - tick.bid,
                'rsi': latest['rsi'],
                'macd': latest['macd'],
                'macd_signal': latest['macd_signal'],
                'sma_20': latest['sma_20'],
                'sma_50': latest['sma_50'],
                'bb_upper': latest['bb_upper'],
                'bb_lower': latest['bb_lower'],
                'bb_middle': latest['bb_middle'],
                'price_change_24h': ((latest['close'] - df['close'].iloc[-24]) / df['close'].iloc[-24]) * 100 if len(df) >= 24 else 0,
                'volatility': df['close'].tail(20).std(),
                'trend': 'BULLISH' if latest['sma_20'] > latest['sma_50'] else 'BEARISH'
            }

        except Exception as e:
            print(f"  Error getting market data for {symbol}: {e}")
            return None

    def create_trading_prompt(self, data):
        """Create detailed trading prompt for AI analysis"""
        return f"""
PROFESSIONAL FOREX TRADING ANALYSIS

Symbol: {data['symbol']}
Current Price: {data['current_price']:.5f}
Spread: {data['spread']:.5f}

TECHNICAL INDICATORS:
• RSI(14): {data['rsi']:.1f}
• MACD: {data['macd']:.6f}
• MACD Signal: {data['macd_signal']:.6f}
• SMA(20): {data['sma_20']:.5f}
• SMA(50): {data['sma_50']:.5f}
• Trend: {data['trend']}
• 24h Change: {data['price_change_24h']:+.2f}%

BOLLINGER BANDS:
• Upper: {data['bb_upper']:.5f}
• Middle: {data['bb_middle']:.5f}
• Lower: {data['bb_lower']:.5f}
• Position: {((data['current_price'] - data['bb_lower']) / (data['bb_upper'] - data['bb_lower']) * 100):.1f}%

MARKET STRUCTURE:
• Price vs SMA20: {((data['current_price'] - data['sma_20']) / data['sma_20'] * 100):+.2f}%
• Volatility: {data['volatility']:.5f}

TASK: Provide professional trading recommendation.

REQUIRED FORMAT:
ACTION: BUY/SELL/HOLD
CONFIDENCE: [0-100]
ENTRY: [price level]
STOP_LOSS: [price level]
TAKE_PROFIT: [price level]
REASONING: [technical analysis explanation]

Consider:
1. RSI overbought/oversold conditions
2. MACD momentum signals
3. Trend direction and strength
4. Bollinger band position
5. Risk/reward ratio (minimum 1.5:1)

Provide clear, actionable analysis.
"""

    def query_ai_analysis(self, prompt):
        """Query AI for trading analysis"""
        if not self.best_model:
            print("  No working AI model available")
            return None

        try:
            payload = {
                "model": self.best_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "num_predict": 400,
                    "temperature": 0.3,
                    "top_p": 0.9
                }
            }

            print(f"  Querying {self.best_model}...")
            response = requests.post(
                f"{self.ollama_url}/api/generate",
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                result = response.json().get('response', '').strip()
                return result if result else None
            else:
                print(f"  AI query failed: {response.status_code}")
                return None

        except Exception as e:
            print(f"  Error querying AI: {e}")
            return None

    def parse_ai_decision(self, response):
        """Parse AI response into trading decision"""
        try:
            if not response:
                return None

            lines = response.upper().split('\\n')
            decision = {}

            for line in lines:
                line = line.strip()
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()

                    if 'ACTION' in key:
                        for action in ['BUY', 'SELL', 'HOLD']:
                            if action in value:
                                decision['action'] = action
                                break
                    elif 'CONFIDENCE' in key:
                        conf_num = ''.join(c for c in value if c.isdigit())
                        if conf_num:
                            decision['confidence'] = min(100, int(conf_num))
                    elif 'ENTRY' in key:
                        try:
                            decision['entry'] = float(value.replace(',', ''))
                        except:
                            pass
                    elif 'STOP' in key:
                        try:
                            decision['stop_loss'] = float(value.replace(',', ''))
                        except:
                            pass
                    elif 'TAKE' in key or 'TARGET' in key:
                        try:
                            decision['take_profit'] = float(value.replace(',', ''))
                        except:
                            pass
                    elif 'REASONING' in key or 'REASON' in key:
                        decision['reasoning'] = value

            return decision if 'action' in decision else None

        except Exception as e:
            print(f"  Error parsing AI decision: {e}")
            return None

    def calculate_position_size(self, decision, symbol_data):
        """Calculate conservative position size"""
        try:
            base_risk = 0.002  # 0.2% of account
            confidence_factor = decision.get('confidence', 50) / 100
            risk_amount = self.account_info.equity * base_risk * confidence_factor

            # Simple position sizing
            symbol = decision.get('symbol', 'EURUSDm')
            if symbol in self.symbol_data:
                volume_step = self.symbol_data[symbol]['volume_step']
                min_volume = self.symbol_data[symbol]['min_volume']
                max_volume = min(0.1, self.symbol_data[symbol]['max_volume'])  # Cap at 0.1 lots

                lots = risk_amount / 1000  # Simple calculation
                lots = round(lots / volume_step) * volume_step
                lots = max(min_volume, min(max_volume, lots))

                return lots

        except Exception as e:
            print(f"  Error calculating position size: {e}")

        return 0.01

    def execute_ai_trade(self, decision, market_data, volume):
        """Execute trade based on AI decision"""
        try:
            symbol = decision.get('symbol', market_data['symbol'])
            action = decision['action']

            if action not in ['BUY', 'SELL']:
                return False

            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return False

            price = tick.ask if action == 'BUY' else tick.bid

            print(f"\\n  [AI TRADE EXECUTION]")
            print(f"    Model: {self.best_model}")
            print(f"    Symbol: {symbol}")
            print(f"    Action: {action}")
            print(f"    Volume: {volume} lots")
            print(f"    Price: {price:.5f}")
            print(f"    Confidence: {decision.get('confidence', 0):.1f}%")

            if 'reasoning' in decision:
                print(f"    AI Reasoning: {decision['reasoning'][:80]}...")

            # Execute trade
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": mt5.ORDER_TYPE_BUY if action == 'BUY' else mt5.ORDER_TYPE_SELL,
                "price": price,
                "deviation": 20,
                "magic": 197678662,
                "comment": f"AI:{self.best_model[:10]}-{decision.get('confidence', 0):.0f}%",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            # Add SL/TP if provided by AI
            if 'stop_loss' in decision:
                request["sl"] = decision['stop_loss']
            if 'take_profit' in decision:
                request["tp"] = decision['take_profit']

            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"    [SUCCESS] AI Trade executed - Ticket: {result.order}")

                # Store decision for analysis
                self.trading_decisions.append({
                    'model': self.best_model,
                    'decision': decision,
                    'market_data': market_data,
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
            print(f"  Error executing AI trade: {e}")
            return False

    def run_ai_trading_cycle(self):
        """Run one AI trading cycle"""
        print(f"\\n{'='*70}")
        print(f"AI TRADING CYCLE - {datetime.now().strftime('%H:%M:%S')}")
        print(f"Model: {self.best_model}")
        print(f"{'='*70}")

        if not self.connected or not self.best_model:
            return False

        try:
            # Update account
            self.account_info = mt5.account_info()
            positions = mt5.positions_get()

            print(f"Account Equity: ${self.account_info.equity:,.2f}")
            print(f"Open Positions: {len(positions) if positions else 0}")

            # Analyze symbols
            trading_opportunities = []

            for symbol in self.symbol_data.keys():
                print(f"\\n[ANALYZING] {symbol}")

                # Get market data
                market_data = self.get_market_analysis_data(symbol)
                if not market_data:
                    print(f"  No data available")
                    continue

                print(f"  Price: {market_data['current_price']:.5f}")
                print(f"  RSI: {market_data['rsi']:.1f}")
                print(f"  Trend: {market_data['trend']}")

                # Create AI prompt
                prompt = self.create_trading_prompt(market_data)

                # Get AI analysis
                ai_response = self.query_ai_analysis(prompt)
                if not ai_response:
                    print(f"  No AI response")
                    continue

                print(f"  AI Analysis received ({len(ai_response)} chars)")

                # Parse decision
                decision = self.parse_ai_decision(ai_response)
                if decision:
                    decision['symbol'] = symbol
                    decision['market_data'] = market_data

                    print(f"  AI Decision: {decision['action']} - Confidence: {decision.get('confidence', 0):.1f}%")

                    if decision['action'] in ['BUY', 'SELL'] and decision.get('confidence', 0) >= 70:
                        trading_opportunities.append(decision)

            # Execute best opportunities
            if trading_opportunities:
                print(f"\\nTrading Opportunities: {len(trading_opportunities)}")

                # Sort by confidence
                trading_opportunities.sort(key=lambda x: x.get('confidence', 0), reverse=True)

                executed = 0
                max_positions = 2

                for opportunity in trading_opportunities:
                    current_positions = len(mt5.positions_get() or [])

                    if current_positions + executed < max_positions:
                        volume = self.calculate_position_size(opportunity, opportunity['market_data'])

                        if volume >= 0.01:
                            if self.execute_ai_trade(opportunity, opportunity['market_data'], volume):
                                executed += 1

                print(f"\\nAI Trades Executed: {executed}")

            # Show P&L
            if positions:
                total_profit = sum(pos.profit for pos in positions)
                print(f"Total P&L: ${total_profit:+.2f}")

            return True

        except Exception as e:
            print(f"Error in AI trading cycle: {e}")
            return False

    def run_adaptive_trading(self, cycles=5, delay=120):
        """Run adaptive AI trading system"""
        print(f"\\n*** STARTING ADAPTIVE OLLAMA TRADING ***")

        if not self.best_model:
            print("No working AI model found")
            return

        print(f"Selected Model: {self.best_model}")
        print(f"Available Models: {len(self.available_models)}")
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
                    print(f"\\nNext cycle in {delay} seconds...")
                    time.sleep(delay)

        except KeyboardInterrupt:
            print(f"\\nAI Trading stopped by user")

        print(f"\\n*** AI TRADING SUMMARY ***")
        print(f"Model Used: {self.best_model}")
        print(f"Decisions Made: {len(self.trading_decisions)}")
        print(f"Final Equity: ${self.account_info.equity:,.2f}")

    def disconnect(self):
        """Disconnect from MT5"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            print("Disconnected from EXNESS")

def main():
    """Main adaptive trading function"""
    ai_trader = AdaptiveOllamaTrader()

    try:
        if ai_trader.best_model and ai_trader.connect_mt5():
            print(f"\\n[ADAPTIVE AI SYSTEM READY]")
            print(f"Symbols: {len(ai_trader.symbol_data)}")

            # Start adaptive AI trading
            ai_trader.run_adaptive_trading(cycles=4, delay=90)
        else:
            print("[ERROR] System not ready")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        ai_trader.disconnect()

if __name__ == "__main__":
    main()