"""
EXNESS LIVE TRADING SYSTEM - AUTO START
Automatically starts live trading without user input
Author: Trading Pro System
Version: 3.0
"""

import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import time
import sys
import os
from datetime import datetime, timedelta

# Add paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

print("EXNESS LIVE TRADING SYSTEM v3.0")
print("="*50)
print("*** AUTO-START LIVE TRADING ***")

class ExnessLiveSystem:
    """Auto-start live trading system"""

    def __init__(self):
        # EXNESS Configuration
        self.exness_config = {
            'path': r"C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe",
            'login': 197678662,
            'password': "Badboy930218*",
            'server': "Exness-MT5Trial11"
        }

        # Optimal symbols
        self.optimal_symbols = [
            'XAUUSDm',    # Gold - 0.004% spread
            'EURUSDm',    # EUR/USD - 0.007% spread
            'GBPUSDm',    # GBP/USD - 0.008% spread
            'USDJPYm',    # USD/JPY - 0.012% spread
            'AUDUSDm',    # AUD/USD - 0.014% spread
            'BTCUSDm',    # Bitcoin - 0.016% spread
        ]

        self.connected = False
        self.account_info = None
        self.symbol_data = {}
        self.cycle_count = 0
        self.total_trades = 0
        self.risk_manager = None

        print("Initializing Live Trading System...")
        self._load_components()

    def _load_components(self):
        """Load enhanced trading components"""
        try:
            from src.risk.enhanced_risk_manager import EnhancedRiskManager
            self.risk_manager = EnhancedRiskManager(
                account_balance=5289,
                max_risk_per_trade=0.003  # Very conservative 0.3% risk
            )
            self.risk_manager.set_risk_level('CONSERVATIVE')
            print("  [OK] Enhanced Risk Manager loaded (CONSERVATIVE)")
        except Exception as e:
            print(f"  [ERROR] Risk Manager: {e}")

    def connect(self):
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
            print("  [SUCCESS] Connected to EXNESS!")

            self.account_info = mt5.account_info()
            if self.account_info:
                print(f"\\nLIVE ACCOUNT STATUS:")
                print(f"  Login: {self.account_info.login}")
                print(f"  Balance: ${self.account_info.balance:,.2f}")
                print(f"  Equity: ${self.account_info.equity:,.2f}")
                print(f"  Free Margin: ${self.account_info.margin_free:,.2f}")

                if self.risk_manager:
                    self.risk_manager.account_balance = self.account_info.equity

            self._setup_symbols()
            return True

        except Exception as e:
            print(f"  [ERROR] Connection failed: {e}")
            return False

    def _setup_symbols(self):
        """Setup optimal trading symbols"""
        print(f"\\nSetting up symbols...")

        for symbol in self.optimal_symbols:
            try:
                if mt5.symbol_select(symbol, True):
                    symbol_info = mt5.symbol_info(symbol)
                    tick = mt5.symbol_info_tick(symbol)

                    if symbol_info and tick:
                        self.symbol_data[symbol] = {
                            'symbol_info': symbol_info,
                            'min_volume': symbol_info.volume_min,
                            'max_volume': symbol_info.volume_max,
                            'volume_step': symbol_info.volume_step,
                            'contract_size': symbol_info.trade_contract_size,
                        }
                        print(f"  [OK] {symbol}")

            except Exception as e:
                print(f"  [ERROR] {symbol}: {e}")

    def get_market_data(self, symbol, count=50):
        """Get market data"""
        try:
            rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, count)
            if rates is not None and len(rates) > 0:
                df = pd.DataFrame(rates)
                df['time'] = pd.to_datetime(df['time'], unit='s')
                df.set_index('time', inplace=True)
                return df
        except:
            pass
        return pd.DataFrame()

    def calculate_indicators(self, data):
        """Calculate technical indicators"""
        try:
            # Simple indicators
            data['sma_fast'] = data['close'].rolling(8).mean()
            data['sma_slow'] = data['close'].rolling(21).mean()

            # RSI
            delta = data['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            data['rsi'] = 100 - (100 / (1 + rs))

            # ATR
            high_low = data['high'] - data['low']
            high_close = np.abs(data['high'] - data['close'].shift())
            low_close = np.abs(data['low'] - data['close'].shift())
            true_range = pd.DataFrame({'hl': high_low, 'hc': high_close, 'lc': low_close}).max(axis=1)
            data['atr'] = true_range.rolling(14).mean()

            return data
        except:
            return data

    def generate_signal(self, symbol):
        """Generate enhanced trading signal"""
        try:
            data = self.get_market_data(symbol)
            if len(data) < 30:
                return None

            data = self.calculate_indicators(data)
            latest = data.iloc[-1]
            prev = data.iloc[-2]

            signal_score = 0
            reasons = []

            # MA Crossover
            if latest['sma_fast'] > latest['sma_slow'] and prev['sma_fast'] <= prev['sma_slow']:
                signal_score += 30
                reasons.append("MA Bullish Cross")
            elif latest['sma_fast'] < latest['sma_slow'] and prev['sma_fast'] >= prev['sma_slow']:
                signal_score -= 30
                reasons.append("MA Bearish Cross")

            # RSI
            if latest['rsi'] < 35:
                signal_score += 15
                reasons.append("RSI Oversold")
            elif latest['rsi'] > 65:
                signal_score -= 15
                reasons.append("RSI Overbought")

            # Generate signal if strong enough
            if abs(signal_score) >= 35:
                return {
                    'symbol': symbol,
                    'type': 'BUY' if signal_score > 0 else 'SELL',
                    'price': latest['close'],
                    'confidence': min(90, 50 + abs(signal_score)),
                    'score': signal_score,
                    'reasons': reasons,
                    'atr': latest['atr'],
                    'rsi': latest['rsi']
                }

        except Exception as e:
            print(f"Error generating signal for {symbol}: {e}")

        return None

    def calculate_position_size(self, signal):
        """Calculate conservative position size"""
        try:
            if not self.risk_manager or not self.account_info:
                return self.symbol_data[signal['symbol']]['min_volume']

            current_price = signal['price']
            atr = signal.get('atr', current_price * 0.01)
            symbol_data = self.symbol_data[signal['symbol']]

            # Conservative stop loss
            atr_multiplier = 2.0

            if signal['type'] == 'BUY':
                stop_loss = current_price - (atr * atr_multiplier)
                take_profit = current_price + (atr * atr_multiplier * 2.5)
            else:
                stop_loss = current_price + (atr * atr_multiplier)
                take_profit = current_price - (atr * atr_multiplier * 2.5)

            signal_dict = {
                'entry_price': current_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'strength': signal['confidence'] / 100,
                'ml_confidence': 0.7
            }

            result = self.risk_manager.calculate_position_size(signal_dict, method='kelly')

            # Convert to lots
            if signal['symbol'] in ['EURUSDm', 'GBPUSDm', 'USDJPYm', 'AUDUSDm']:
                lots = (result.position_size * current_price) / symbol_data['contract_size']
            else:
                lots = result.position_size / current_price

            # Conservative sizing
            volume_step = symbol_data['volume_step']
            lots = round(lots / volume_step) * volume_step
            lots = max(symbol_data['min_volume'], min(symbol_data['max_volume'], lots))

            # Additional safety cap
            lots = min(lots, 0.1)  # Max 0.1 lots per trade

            return lots

        except Exception as e:
            print(f"Error calculating position size: {e}")
            return self.symbol_data[signal['symbol']]['min_volume']

    def execute_trade(self, signal, volume):
        """Execute LIVE trade on EXNESS"""
        try:
            tick = mt5.symbol_info_tick(signal['symbol'])
            if not tick:
                return False

            price = tick.ask if signal['type'] == 'BUY' else tick.bid

            print(f"    [LIVE SIGNAL] {signal['symbol']} {signal['type']}")
            print(f"      Confidence: {signal['confidence']:.1f}%")
            print(f"      Reasons: {', '.join(signal['reasons'])}")
            print(f"      Volume: {volume} lots")
            print(f"      Price: {price:.5f}")

            # EXECUTE REAL TRADE
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": signal['symbol'],
                "volume": volume,
                "type": mt5.ORDER_TYPE_BUY if signal['type'] == 'BUY' else mt5.ORDER_TYPE_SELL,
                "price": price,
                "deviation": 20,
                "magic": 197678662,
                "comment": f"LiveSys: {signal['reasons'][0] if signal['reasons'] else 'Auto'}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"      [SUCCESS] LIVE TRADE EXECUTED - Ticket: {result.order}")
                self.total_trades += 1
                return True
            else:
                print(f"      [ERROR] Trade failed: {result.retcode} - {result.comment}")
                return False

        except Exception as e:
            print(f"Error executing trade: {e}")
            return False

    def get_positions(self):
        """Get current positions"""
        try:
            positions = mt5.positions_get()
            if positions:
                position_data = {}
                for pos in positions:
                    position_data[pos.ticket] = {
                        'symbol': pos.symbol,
                        'type': 'BUY' if pos.type == 0 else 'SELL',
                        'volume': pos.volume,
                        'price_open': pos.price_open,
                        'price_current': pos.price_current,
                        'profit': pos.profit,
                        'swap': pos.swap
                    }
                return position_data
            return {}
        except:
            return {}

    def run_cycle(self):
        """Run one trading cycle"""
        self.cycle_count += 1

        print(f"\\n[LIVE CYCLE {self.cycle_count}] {datetime.now().strftime('%H:%M:%S')}")

        if not self.connected:
            return False

        try:
            # Update account
            self.account_info = mt5.account_info()
            positions = self.get_positions()

            print(f"  Equity: ${self.account_info.equity:,.2f}")
            print(f"  Positions: {len(positions)}")

            # Generate signals
            signals = []
            for symbol in self.symbol_data.keys():
                signal = self.generate_signal(symbol)
                if signal:
                    signals.append(signal)

            print(f"  Signals: {len(signals)}")

            # Execute top signals
            signals.sort(key=lambda x: x['confidence'], reverse=True)

            executed = 0
            max_positions = 2  # Conservative limit

            for signal in signals:
                if len(positions) + executed < max_positions:
                    # Check no existing position
                    has_position = any(pos['symbol'] == signal['symbol'] for pos in positions.values())

                    if not has_position and signal['confidence'] >= 75:
                        volume = self.calculate_position_size(signal)

                        if volume >= self.symbol_data[signal['symbol']]['min_volume']:
                            if self.execute_trade(signal, volume):
                                executed += 1

            print(f"  Executed: {executed}")

            # Show P&L
            if positions:
                total_profit = sum(pos['profit'] for pos in positions.values())
                print(f"  Total P&L: ${total_profit:+.2f}")

                for ticket, pos in positions.items():
                    print(f"    {ticket}: {pos['symbol']} {pos['type']} - P&L: ${pos['profit']:+.2f}")

            return True

        except Exception as e:
            print(f"  [ERROR] Cycle failed: {e}")
            return False

    def run_live_trading(self, max_cycles=20, cycle_delay=60):
        """Run continuous live trading"""
        print(f"\\n*** STARTING LIVE TRADING ***")
        print(f"Max Cycles: {max_cycles}")
        print(f"Cycle Delay: {cycle_delay}s")
        print(f"Risk per trade: 0.3% (CONSERVATIVE)")
        print(f"Max positions: 2")

        if not self.connected:
            print("ERROR: Not connected")
            return

        try:
            for i in range(max_cycles):
                success = self.run_cycle()
                if not success:
                    print("Cycle failed, stopping")
                    break

                if i < max_cycles - 1:
                    print(f"  Next cycle in {cycle_delay}s...")
                    time.sleep(cycle_delay)

        except KeyboardInterrupt:
            print(f"\\nLive trading stopped by user")

        # Final summary
        positions = self.get_positions()
        print(f"\\nLIVE TRADING SUMMARY:")
        print(f"  Cycles: {self.cycle_count}")
        print(f"  Trades: {self.total_trades}")
        print(f"  Equity: ${self.account_info.equity:,.2f}")
        print(f"  Positions: {len(positions)}")

        if positions:
            total_profit = sum(pos['profit'] for pos in positions.values())
            print(f"  P&L: ${total_profit:+.2f}")

    def disconnect(self):
        """Disconnect"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            print("Disconnected from EXNESS")

def main():
    """Auto-start live trading"""
    system = ExnessLiveSystem()

    try:
        if system.connect():
            print(f"\\n*** READY FOR LIVE TRADING ***")
            print(f"Symbols: {len(system.symbol_data)}")

            # Auto-start live trading
            system.run_live_trading(max_cycles=15, cycle_delay=45)
        else:
            print("[ERROR] Connection failed")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        system.disconnect()

if __name__ == "__main__":
    main()