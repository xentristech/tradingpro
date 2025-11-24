"""
Multi-AI Trading System
Integrates multiple AI sources: Ollama, OpenAI, Claude, etc.
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

print("MULTI-AI TRADING SYSTEM v3.0")
print("="*50)

class MultiAITradingSystem:
    """Advanced trading system with multiple AI engines"""

    def __init__(self):
        # EXNESS Configuration
        self.exness_config = {
            'path': r"C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe",
            'login': 197678662,
            'password': "Badboy930218*",
            'server': "Exness-MT5Trial11"
        }

        # AI Configuration
        self.ai_configs = {
            'ollama': {
                'url': 'http://localhost:11434',
                'model': 'deepseek-r1:14b',
                'enabled': True,
                'weight': 0.4  # Increased weight for DeepSeek
            },
            'openai': {
                'enabled': False,  # Set to True if you have API key
                'weight': 0.25
            },
            'internal_ml': {
                'enabled': True,
                'weight': 0.35  # Reduced to give more weight to DeepSeek
            }
        }

        self.symbols = ['XAUUSDm', 'EURUSDm', 'GBPUSDm', 'USDJPYm', 'BTCUSDm']
        self.connected = False
        self.account_info = None
        self.symbol_data = {}
        self.risk_manager = None
        self.cycle_count = 0
        self.ai_decisions_history = []

        print("Initializing Multi-AI Trading System...")
        self._load_components()
        self._test_ai_connections()

    def _load_components(self):
        """Load enhanced components"""
        try:
            from src.risk.enhanced_risk_manager import EnhancedRiskManager
            self.risk_manager = EnhancedRiskManager(
                account_balance=5289,
                max_risk_per_trade=0.003
            )
            self.risk_manager.set_risk_level('CONSERVATIVE')
            print("  [OK] Enhanced Risk Manager loaded")
        except Exception as e:
            print(f"  [ERROR] Risk Manager: {e}")

    def _test_ai_connections(self):
        """Test all AI connections"""
        print("\\nTesting AI Connections:")

        # Test Ollama
        if self.ai_configs['ollama']['enabled']:
            try:
                url = self.ai_configs['ollama']['url']
                response = requests.get(f"{url}/api/tags", timeout=5)
                if response.status_code == 200:
                    print("  [OK] Ollama connected")
                else:
                    print("  [ERROR] Ollama not responding")
                    self.ai_configs['ollama']['enabled'] = False
            except:
                print("  [ERROR] Ollama not available")
                self.ai_configs['ollama']['enabled'] = False

        # Test Internal ML
        if self.ai_configs['internal_ml']['enabled']:
            try:
                # Simple test of ML components
                test_data = pd.DataFrame({
                    'close': np.random.randn(50).cumsum() + 100,
                    'volume': np.random.exponential(1000, 50)
                })
                self._calculate_ml_features(test_data)
                print("  [OK] Internal ML ready")
            except Exception as e:
                print(f"  [ERROR] Internal ML failed: {e}")
                self.ai_configs['internal_ml']['enabled'] = False

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

    def get_market_data(self, symbol, timeframe=mt5.TIMEFRAME_H1, count=100):
        """Get comprehensive market data"""
        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            if rates is not None and len(rates) > 0:
                df = pd.DataFrame(rates)
                df['time'] = pd.to_datetime(df['time'], unit='s')
                df = self._calculate_technical_indicators(df)
                df = self._calculate_ml_features(df)
                return df
        except Exception as e:
            print(f"Error getting data for {symbol}: {e}")
        return pd.DataFrame()

    def _calculate_technical_indicators(self, data):
        """Calculate comprehensive technical indicators"""
        try:
            # Moving averages
            data['sma_10'] = data['close'].rolling(10).mean()
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

            # ATR
            high_low = data['high'] - data['low']
            high_close = np.abs(data['high'] - data['close'].shift())
            low_close = np.abs(data['low'] - data['close'].shift())
            true_range = pd.DataFrame({'hl': high_low, 'hc': high_close, 'lc': low_close}).max(axis=1)
            data['atr'] = true_range.rolling(14).mean()

            # Stochastic
            low_14 = data['low'].rolling(14).min()
            high_14 = data['high'].rolling(14).max()
            data['stoch_k'] = ((data['close'] - low_14) / (high_14 - low_14)) * 100
            data['stoch_d'] = data['stoch_k'].rolling(3).mean()

            return data

        except Exception as e:
            print(f"Error calculating technical indicators: {e}")
            return data

    def _calculate_ml_features(self, data):
        """Calculate ML features for AI analysis"""
        try:
            # Price momentum features
            data['price_momentum_1'] = data['close'].pct_change(1)
            data['price_momentum_5'] = data['close'].pct_change(5)
            data['price_momentum_10'] = data['close'].pct_change(10)

            # Volatility features
            data['volatility_5'] = data['close'].rolling(5).std()
            data['volatility_20'] = data['close'].rolling(20).std()

            # Volume features
            if 'tick_volume' in data.columns:
                data['volume_sma'] = data['tick_volume'].rolling(20).mean()
                data['volume_ratio'] = data['tick_volume'] / data['volume_sma']

            # Price position features
            data['price_position_bb'] = (data['close'] - data['bb_lower']) / (data['bb_upper'] - data['bb_lower'])
            data['price_position_sma'] = (data['close'] - data['sma_20']) / data['sma_20']

            return data

        except Exception as e:
            print(f"Error calculating ML features: {e}")
            return data

    def query_ollama_ai(self, symbol, data):
        """Query Ollama for trading decision"""
        try:
            if not self.ai_configs['ollama']['enabled']:
                return None

            latest = data.iloc[-1]

            prompt = f"""
PROFESSIONAL FOREX TRADING ANALYSIS - {symbol}

TECHNICAL INDICATORS:
• Price: {latest['close']:.5f}
• RSI(14): {latest['rsi']:.1f}
• MACD: {latest['macd']:.6f}
• MACD Signal: {latest['macd_signal']:.6f}
• Trend: {"BULLISH" if latest['sma_20'] > latest['sma_50'] else "BEARISH"} (SMA20 vs SMA50)
• Bollinger Position: {latest['price_position_bb']:.2f} (0=lower band, 1=upper band)
• ATR: {latest['atr']:.5f}
• Stochastic: {latest['stoch_k']:.1f}

MARKET CONTEXT:
• Price vs SMA20: {((latest['close'] - latest['sma_20']) / latest['sma_20'] * 100):+.2f}%
• MACD Histogram: {latest['macd_histogram']:.6f}
• Volume Ratio: {latest.get('volume_ratio', 1.0):.2f}

TASK: As a professional trader, analyze this data and provide a precise trading decision.

REQUIRED FORMAT:
ACTION: [BUY/SELL/HOLD]
CONFIDENCE: [0-100]
REASONING: [detailed technical analysis in 1-2 sentences]

Consider:
1. RSI overbought/oversold levels
2. MACD momentum and crossovers
3. Bollinger band position
4. Trend alignment
5. Risk/reward potential

Provide only the analysis - no preamble.
"""

            payload = {
                "model": self.ai_configs['ollama']['model'],
                "prompt": prompt,
                "stream": False,
                "options": {"num_predict": 200, "temperature": 0.3}
            }

            response = requests.post(
                f"{self.ai_configs['ollama']['url']}/api/generate",
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json().get('response', '').strip()
                return self._parse_ai_response(result, 'ollama')

        except Exception as e:
            print(f"Ollama query error: {e}")

        return None

    def get_internal_ml_decision(self, symbol, data):
        """Get decision from internal ML system"""
        try:
            if not self.ai_configs['internal_ml']['enabled']:
                return None

            latest = data.iloc[-1]

            # ML-based scoring
            score = 0

            # Technical indicator signals
            if latest['rsi'] < 30:
                score += 20  # Oversold
            elif latest['rsi'] > 70:
                score -= 20  # Overbought

            # MACD signals
            if latest['macd'] > latest['macd_signal']:
                score += 15
            else:
                score -= 15

            # Trend signals
            if latest['sma_20'] > latest['sma_50']:
                score += 10
            else:
                score -= 10

            # Bollinger Band signals
            if latest['price_position_bb'] < 0.2:
                score += 15  # Near lower band
            elif latest['price_position_bb'] > 0.8:
                score -= 15  # Near upper band

            # Volume confirmation
            if 'volume_ratio' in latest and latest['volume_ratio'] > 1.2:
                score *= 1.1  # Volume confirmation

            # Generate decision
            confidence = min(95, abs(score))

            if score > 25:
                action = 'BUY'
            elif score < -25:
                action = 'SELL'
            else:
                action = 'HOLD'

            return {
                'action': action,
                'confidence': confidence,
                'score': score,
                'source': 'internal_ml',
                'reasoning': f"ML Score: {score:.1f}, RSI: {latest['rsi']:.1f}"
            }

        except Exception as e:
            print(f"Internal ML error: {e}")

        return None

    def _parse_ai_response(self, response, source):
        """Parse AI response into structured format"""
        try:
            lines = response.upper().split('\\n')
            decision = {'source': source}

            for line in lines:
                line = line.strip()
                if 'ACTION:' in line:
                    action = line.split('ACTION:')[1].strip()
                    if any(a in action for a in ['BUY', 'SELL', 'HOLD']):
                        for a in ['BUY', 'SELL', 'HOLD']:
                            if a in action:
                                decision['action'] = a
                                break
                elif 'CONFIDENCE:' in line:
                    conf_str = line.split('CONFIDENCE:')[1].strip()
                    conf_num = ''.join(c for c in conf_str if c.isdigit())
                    if conf_num:
                        decision['confidence'] = min(100, int(conf_num))
                elif 'REASONING:' in line:
                    decision['reasoning'] = line.split('REASONING:')[1].strip()

            return decision if 'action' in decision and 'confidence' in decision else None

        except Exception as e:
            print(f"Error parsing AI response: {e}")
            return None

    def get_multi_ai_consensus(self, symbol):
        """Get consensus from multiple AI sources"""
        try:
            print(f"\\n[MULTI-AI ANALYSIS] {symbol}")

            # Get market data
            data = self.get_market_data(symbol)
            if len(data) < 50:
                print(f"  Insufficient data")
                return None

            ai_decisions = []

            # Query Ollama
            if self.ai_configs['ollama']['enabled']:
                print(f"  Querying Ollama...")
                ollama_decision = self.query_ollama_ai(symbol, data)
                if ollama_decision:
                    ai_decisions.append(ollama_decision)
                    print(f"    Ollama: {ollama_decision['action']} ({ollama_decision['confidence']}%)")

            # Get Internal ML decision
            if self.ai_configs['internal_ml']['enabled']:
                print(f"  Analyzing with Internal ML...")
                ml_decision = self.get_internal_ml_decision(symbol, data)
                if ml_decision:
                    ai_decisions.append(ml_decision)
                    print(f"    Internal ML: {ml_decision['action']} ({ml_decision['confidence']}%)")

            # Calculate weighted consensus
            if ai_decisions:
                consensus = self._calculate_consensus(ai_decisions)
                print(f"  Consensus: {consensus['action']} - Confidence: {consensus['confidence']:.1f}%")
                return consensus

        except Exception as e:
            print(f"Error in multi-AI analysis: {e}")

        return None

    def _calculate_consensus(self, decisions):
        """Calculate weighted consensus from multiple AI decisions"""
        try:
            buy_weight = 0
            sell_weight = 0
            total_confidence = 0

            for decision in decisions:
                source = decision['source']
                weight = self.ai_configs.get(source, {}).get('weight', 0.33)
                confidence = decision['confidence'] / 100
                adjusted_weight = weight * confidence

                if decision['action'] == 'BUY':
                    buy_weight += adjusted_weight
                elif decision['action'] == 'SELL':
                    sell_weight += adjusted_weight

                total_confidence += adjusted_weight

            # Determine consensus action
            if buy_weight > sell_weight and buy_weight > 0.3:
                action = 'BUY'
                confidence = (buy_weight / (buy_weight + sell_weight)) * 100
            elif sell_weight > buy_weight and sell_weight > 0.3:
                action = 'SELL'
                confidence = (sell_weight / (buy_weight + sell_weight)) * 100
            else:
                action = 'HOLD'
                confidence = 50

            return {
                'action': action,
                'confidence': min(95, confidence),
                'buy_weight': buy_weight,
                'sell_weight': sell_weight,
                'total_confidence': total_confidence,
                'decisions': decisions,
                'symbol': decision['symbol'] if decisions else None
            }

        except Exception as e:
            print(f"Error calculating consensus: {e}")
            return None

    def calculate_ai_position_size(self, consensus):
        """Calculate position size based on AI consensus"""
        try:
            if not self.account_info:
                return 0.01

            # Base risk calculation
            base_risk = 0.003  # 0.3%
            confidence_factor = consensus['confidence'] / 100
            consensus_strength = abs(consensus['buy_weight'] - consensus['sell_weight'])

            # Adjust risk based on AI confidence and consensus strength
            risk_multiplier = 0.5 + (confidence_factor * consensus_strength)
            account_risk = base_risk * risk_multiplier

            risk_amount = self.account_info.equity * account_risk

            # Use ATR for stop loss calculation
            symbol = consensus['symbol']
            if symbol in self.symbol_data:
                volume_step = self.symbol_data[symbol]['volume_step']
                min_volume = self.symbol_data[symbol]['min_volume']
                max_volume = self.symbol_data[symbol]['max_volume']

                # Simple position sizing
                lots = risk_amount / 1000  # Conservative sizing

                # Round to volume step
                lots = round(lots / volume_step) * volume_step
                lots = max(min_volume, min(max_volume, lots))

                return lots

        except Exception as e:
            print(f"Error calculating AI position size: {e}")

        return 0.01

    def execute_ai_consensus_trade(self, consensus, volume):
        """Execute trade based on AI consensus"""
        try:
            symbol = consensus['symbol']
            action = consensus['action']

            if action not in ['BUY', 'SELL']:
                return False

            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return False

            price = tick.ask if action == 'BUY' else tick.bid

            print(f"\\n  [MULTI-AI TRADE EXECUTION]")
            print(f"    Symbol: {symbol}")
            print(f"    Action: {action}")
            print(f"    Volume: {volume} lots")
            print(f"    Price: {price:.5f}")
            print(f"    Consensus Confidence: {consensus['confidence']:.1f}%")
            print(f"    Buy Weight: {consensus['buy_weight']:.3f}")
            print(f"    Sell Weight: {consensus['sell_weight']:.3f}")

            # Execute trade
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": mt5.ORDER_TYPE_BUY if action == 'BUY' else mt5.ORDER_TYPE_SELL,
                "price": price,
                "deviation": 20,
                "magic": 197678662,
                "comment": f"MultiAI: {consensus['confidence']:.0f}%",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"    [SUCCESS] Multi-AI Trade executed - Ticket: {result.order}")

                # Store decision for analysis
                self.ai_decisions_history.append({
                    'consensus': consensus,
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
            print(f"Error executing AI consensus trade: {e}")
            return False

    def run_multi_ai_cycle(self):
        """Run one multi-AI trading cycle"""
        self.cycle_count += 1

        print(f"\\n{'='*70}")
        print(f"MULTI-AI TRADING CYCLE {self.cycle_count} - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*70}")

        if not self.connected:
            return False

        try:
            # Update account
            self.account_info = mt5.account_info()
            positions = mt5.positions_get()

            print(f"Account Equity: ${self.account_info.equity:,.2f}")
            print(f"Open Positions: {len(positions) if positions else 0}")

            # Get AI consensus for all symbols
            consensus_decisions = []
            for symbol in self.symbols:
                consensus = self.get_multi_ai_consensus(symbol)
                if consensus and consensus['action'] in ['BUY', 'SELL']:
                    consensus['symbol'] = symbol
                    consensus_decisions.append(consensus)

            print(f"\\nMulti-AI Consensus Decisions: {len(consensus_decisions)}")

            # Execute top consensus decisions
            if consensus_decisions:
                # Sort by confidence
                consensus_decisions.sort(key=lambda x: x['confidence'], reverse=True)

                executed = 0
                max_positions = 2

                for consensus in consensus_decisions:
                    current_positions = len(mt5.positions_get() or [])

                    if current_positions + executed < max_positions:
                        if consensus['confidence'] >= 75:  # High confidence
                            volume = self.calculate_ai_position_size(consensus)

                            if volume >= 0.01:
                                if self.execute_ai_consensus_trade(consensus, volume):
                                    executed += 1

                print(f"\\nMulti-AI Trades Executed: {executed}")

            # Show P&L
            if positions:
                total_profit = sum(pos.profit for pos in positions)
                print(f"Total P&L: ${total_profit:+.2f}")

            return True

        except Exception as e:
            print(f"Error in multi-AI cycle: {e}")
            return False

    def run_multi_ai_trading(self, cycles=8, delay=180):
        """Run multi-AI trading system"""
        print(f"\\n*** STARTING MULTI-AI TRADING SYSTEM ***")

        # Show enabled AI engines
        enabled_ais = [name for name, config in self.ai_configs.items() if config.get('enabled', False)]
        print(f"Enabled AI Engines: {', '.join(enabled_ais)}")

        for name, config in self.ai_configs.items():
            if config.get('enabled', False):
                print(f"  {name}: Weight {config.get('weight', 0):.2f}")

        print(f"Cycles: {cycles}")
        print(f"Delay: {delay}s")

        if not self.connected:
            print("Not connected to MT5")
            return

        try:
            for i in range(cycles):
                success = self.run_multi_ai_cycle()
                if not success:
                    break

                if i < cycles - 1:
                    print(f"\\nNext cycle in {delay} seconds...")
                    time.sleep(delay)

        except KeyboardInterrupt:
            print(f"\\nMulti-AI Trading stopped by user")

        print(f"\\n*** MULTI-AI TRADING SUMMARY ***")
        print(f"Total Cycles: {self.cycle_count}")
        print(f"AI Decisions Made: {len(self.ai_decisions_history)}")
        print(f"Final Equity: ${self.account_info.equity:,.2f}")

        # Show AI performance summary
        if self.ai_decisions_history:
            print(f"\\nAI Decision Sources:")
            sources = {}
            for decision in self.ai_decisions_history:
                for ai_decision in decision['consensus']['decisions']:
                    source = ai_decision['source']
                    if source not in sources:
                        sources[source] = {'count': 0, 'avg_confidence': 0}
                    sources[source]['count'] += 1
                    sources[source]['avg_confidence'] += ai_decision['confidence']

            for source, stats in sources.items():
                avg_conf = stats['avg_confidence'] / stats['count']
                print(f"  {source}: {stats['count']} decisions, avg confidence: {avg_conf:.1f}%")

    def disconnect(self):
        """Disconnect from MT5"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            print("Disconnected from EXNESS")

def main():
    """Main multi-AI trading function"""
    ai_system = MultiAITradingSystem()

    try:
        if ai_system.connect_mt5():
            print(f"\\n[MULTI-AI SYSTEM READY]")
            print(f"Symbols: {len(ai_system.symbol_data)}")

            # Start multi-AI trading
            ai_system.run_multi_ai_trading(cycles=6, delay=120)  # 2 minutes between cycles
        else:
            print("[ERROR] Failed to connect to MT5")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        ai_system.disconnect()

if __name__ == "__main__":
    main()