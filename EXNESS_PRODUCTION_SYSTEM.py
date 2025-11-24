"""
EXNESS Production Trading System
Professional trading system with optimal symbols and enhanced risk management
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

print("EXNESS PRODUCTION TRADING SYSTEM v3.0")
print("="*50)

class ExnessProductionSystem:
    """Production-ready EXNESS trading system"""

    def __init__(self):
        # EXNESS Configuration
        self.exness_config = {
            'path': r"C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe",
            'login': 197678662,
            'password': "Badboy930218*",
            'server': "Exness-MT5Trial11"
        }

        # Optimal symbols based on spread analysis
        self.optimal_symbols = [
            'XAUUSDm',    # Gold - 0.004% spread
            'EURUSDm',    # EUR/USD - 0.007% spread
            'GBPUSDm',    # GBP/USD - 0.008% spread
            'USDJPYm',    # USD/JPY - 0.012% spread
            'AUDUSDm',    # AUD/USD - 0.014% spread
            'BTCUSDm',    # Bitcoin - 0.016% spread
            'USDCHFm',    # USD/CHF - 0.016% spread
            'USDCADm',    # USD/CAD - 0.026% spread
        ]

        self.connected = False
        self.account_info = None
        self.symbol_data = {}
        self.positions = {}
        self.cycle_count = 0
        self.total_trades = 0

        # Enhanced components
        self.risk_manager = None
        self.portfolio_manager = None

        print("Initializing EXNESS Production System...")
        self._load_components()

    def _load_components(self):
        """Load enhanced trading components"""
        try:
            from src.risk.enhanced_risk_manager import EnhancedRiskManager
            self.risk_manager = EnhancedRiskManager(
                account_balance=5289,  # Your current balance
                max_risk_per_trade=0.005  # Conservative 0.5% risk per trade
            )
            self.risk_manager.set_risk_level('MODERATE')
            print("  [OK] Enhanced Risk Manager loaded")
        except Exception as e:
            print(f"  [ERROR] Risk Manager: {e}")

        try:
            from src.portfolio.advanced_portfolio_manager import AdvancedPortfolioManager, AssetInfo
            self.portfolio_manager = AdvancedPortfolioManager(
                initial_capital=5289
            )

            # Add optimal assets
            assets = [
                AssetInfo('XAUUSDm', 'Commodity', 'Precious Metals', 'US'),
                AssetInfo('EURUSDm', 'Forex', 'Major', 'EU'),
                AssetInfo('GBPUSDm', 'Forex', 'Major', 'GB'),
                AssetInfo('USDJPYm', 'Forex', 'Major', 'JP'),
                AssetInfo('AUDUSDm', 'Forex', 'Major', 'AU'),
                AssetInfo('BTCUSDm', 'Crypto', 'Digital Assets', 'US'),
                AssetInfo('USDCHFm', 'Forex', 'Major', 'CH'),
                AssetInfo('USDCADm', 'Forex', 'Major', 'CA'),
            ]

            for asset in assets:
                self.portfolio_manager.add_asset(asset)

            print("  [OK] Portfolio Manager loaded")
        except Exception as e:
            print(f"  [ERROR] Portfolio Manager: {e}")

    def connect(self):
        """Connect to EXNESS MT5"""
        print("\\nConnecting to EXNESS...")

        try:
            # Initialize and login
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

            # Get account info
            self.account_info = mt5.account_info()
            if self.account_info:
                print(f"\\nACCOUNT STATUS:")
                print(f"  Login: {self.account_info.login}")
                print(f"  Balance: ${self.account_info.balance:,.2f}")
                print(f"  Equity: ${self.account_info.equity:,.2f}")
                print(f"  Free Margin: ${self.account_info.margin_free:,.2f}")
                print(f"  Leverage: 1:{self.account_info.leverage}")

                # Update risk manager with actual balance
                if self.risk_manager:
                    self.risk_manager.account_balance = self.account_info.equity

            # Setup optimal symbols
            self._setup_symbols()
            return True

        except Exception as e:
            print(f"  [ERROR] Connection failed: {e}")
            return False

    def _setup_symbols(self):
        """Setup optimal trading symbols"""
        print(f"\\nSetting up optimal symbols...")

        for symbol in self.optimal_symbols:
            try:
                # Select symbol
                if mt5.symbol_select(symbol, True):
                    # Get symbol info
                    symbol_info = mt5.symbol_info(symbol)
                    tick = mt5.symbol_info_tick(symbol)

                    if symbol_info and tick:
                        spread = tick.ask - tick.bid
                        spread_pct = (spread / tick.bid) * 100

                        self.symbol_data[symbol] = {
                            'symbol_info': symbol_info,
                            'min_volume': symbol_info.volume_min,
                            'max_volume': symbol_info.volume_max,
                            'volume_step': symbol_info.volume_step,
                            'contract_size': symbol_info.trade_contract_size,
                            'spread_pct': spread_pct,
                            'description': symbol_info.description
                        }

                        print(f"  [OK] {symbol:12s} - {symbol_info.description[:25]:25s} - Spread: {spread_pct:.3f}%")

            except Exception as e:
                print(f"  [ERROR] {symbol}: {e}")

        print(f"  Ready symbols: {len(self.symbol_data)}")

    def get_market_data(self, symbol, timeframe=mt5.TIMEFRAME_M15, count=100):
        """Get market data for technical analysis"""
        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            if rates is not None and len(rates) > 0:
                df = pd.DataFrame(rates)
                df['time'] = pd.to_datetime(df['time'], unit='s')
                df.set_index('time', inplace=True)
                return df
        except Exception as e:
            print(f"Error getting data for {symbol}: {e}")
        return pd.DataFrame()

    def calculate_technical_indicators(self, data):
        """Calculate technical indicators"""
        try:
            # Moving averages
            data['sma_fast'] = data['close'].rolling(8).mean()
            data['sma_slow'] = data['close'].rolling(21).mean()
            data['ema_fast'] = data['close'].ewm(span=12).mean()
            data['ema_slow'] = data['close'].ewm(span=26).mean()

            # RSI
            delta = data['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            data['rsi'] = 100 - (100 / (1 + rs))

            # MACD
            data['macd'] = data['ema_fast'] - data['ema_slow']
            data['macd_signal'] = data['macd'].ewm(span=9).mean()

            # Bollinger Bands
            data['bb_middle'] = data['close'].rolling(20).mean()
            bb_std = data['close'].rolling(20).std()
            data['bb_upper'] = data['bb_middle'] + (bb_std * 2)
            data['bb_lower'] = data['bb_middle'] - (bb_std * 2)

            # ATR for volatility
            high_low = data['high'] - data['low']
            high_close = np.abs(data['high'] - data['close'].shift())
            low_close = np.abs(data['low'] - data['close'].shift())
            true_range = pd.DataFrame({'hl': high_low, 'hc': high_close, 'lc': low_close}).max(axis=1)
            data['atr'] = true_range.rolling(14).mean()

            return data

        except Exception as e:
            print(f"Error calculating indicators: {e}")
            return data

    def generate_enhanced_signal(self, symbol):
        """Generate enhanced trading signal"""
        try:
            data = self.get_market_data(symbol)
            if len(data) < 50:
                return None

            data = self.calculate_technical_indicators(data)

            # Get latest values
            latest = data.iloc[-1]
            prev = data.iloc[-2]

            signal_score = 0
            signal_reasons = []

            # Moving Average signals
            if latest['sma_fast'] > latest['sma_slow'] and prev['sma_fast'] <= prev['sma_slow']:
                signal_score += 25
                signal_reasons.append("MA Bullish Crossover")
            elif latest['sma_fast'] < latest['sma_slow'] and prev['sma_fast'] >= prev['sma_slow']:
                signal_score -= 25
                signal_reasons.append("MA Bearish Crossover")

            # RSI signals
            if latest['rsi'] < 30:
                signal_score += 15
                signal_reasons.append("RSI Oversold")
            elif latest['rsi'] > 70:
                signal_score -= 15
                signal_reasons.append("RSI Overbought")

            # MACD signals
            if latest['macd'] > latest['macd_signal'] and prev['macd'] <= prev['macd_signal']:
                signal_score += 20
                signal_reasons.append("MACD Bullish")
            elif latest['macd'] < latest['macd_signal'] and prev['macd'] >= prev['macd_signal']:
                signal_score -= 20
                signal_reasons.append("MACD Bearish")

            # Bollinger Bands
            if latest['close'] < latest['bb_lower']:
                signal_score += 10
                signal_reasons.append("BB Oversold")
            elif latest['close'] > latest['bb_upper']:
                signal_score -= 10
                signal_reasons.append("BB Overbought")

            # Generate signal if score is significant
            if abs(signal_score) >= 30:
                signal_type = 'BUY' if signal_score > 0 else 'SELL'
                confidence = min(95, 50 + abs(signal_score))

                return {
                    'symbol': symbol,
                    'type': signal_type,
                    'price': latest['close'],
                    'confidence': confidence,
                    'score': signal_score,
                    'reasons': signal_reasons,
                    'atr': latest['atr'],
                    'rsi': latest['rsi']
                }

        except Exception as e:
            print(f"Error generating signal for {symbol}: {e}")

        return None

    def calculate_dynamic_position_size(self, signal):
        """Calculate position size with enhanced risk management"""
        try:
            if not self.risk_manager or not self.account_info:
                return self.symbol_data[signal['symbol']]['min_volume']

            current_price = signal['price']
            atr = signal.get('atr', current_price * 0.01)
            symbol_data = self.symbol_data[signal['symbol']]

            # Dynamic stop loss based on ATR and volatility
            atr_multiplier = 1.5 if signal['confidence'] > 80 else 2.0

            if signal['type'] == 'BUY':
                stop_loss = current_price - (atr * atr_multiplier)
                take_profit = current_price + (atr * atr_multiplier * 2)  # 2:1 R/R
            else:
                stop_loss = current_price + (atr * atr_multiplier)
                take_profit = current_price - (atr * atr_multiplier * 2)

            # Prepare signal for risk manager
            signal_dict = {
                'entry_price': current_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'strength': signal['confidence'] / 100,
                'ml_confidence': signal['confidence'] / 100,
                'volatility': atr / current_price
            }

            # Calculate position size using Kelly Criterion
            result = self.risk_manager.calculate_position_size(signal_dict, method='kelly')

            # Convert to proper lot size
            if signal['symbol'] in ['EURUSDm', 'GBPUSDm', 'USDJPYm', 'AUDUSDm', 'USDCHFm', 'USDCADm']:
                # Forex pairs
                lots = (result.position_size * current_price) / symbol_data['contract_size']
            else:
                # Commodities/Crypto
                lots = result.position_size / current_price

            # Round to symbol's volume step
            volume_step = symbol_data['volume_step']
            lots = round(lots / volume_step) * volume_step
            lots = max(symbol_data['min_volume'], min(symbol_data['max_volume'], lots))

            return lots

        except Exception as e:
            print(f"Error calculating position size: {e}")
            return self.symbol_data[signal['symbol']]['min_volume']

    def execute_trade(self, signal, volume):
        """Execute trade on EXNESS (DEMO MODE for safety)"""
        try:
            tick = mt5.symbol_info_tick(signal['symbol'])
            if not tick:
                return False

            price = tick.ask if signal['type'] == 'BUY' else tick.bid

            print(f"    [SIGNAL] {signal['symbol']} {signal['type']}")
            print(f"      Confidence: {signal['confidence']:.1f}%")
            print(f"      Score: {signal['score']}")
            print(f"      Reasons: {', '.join(signal['reasons'])}")
            print(f"      Volume: {volume} lots")
            print(f"      Price: {price:.5f}")

            # REAL TRADING MODE - ACTIVATED
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": signal['symbol'],
                "volume": volume,
                "type": mt5.ORDER_TYPE_BUY if signal['type'] == 'BUY' else mt5.ORDER_TYPE_SELL,
                "price": price,
                "deviation": 20,
                "magic": 197678662,
                "comment": f"ProdSys: {signal['reasons'][0] if signal['reasons'] else 'Auto'}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"      [SUCCESS] REAL Trade executed - Ticket: {result.order}")
                self.total_trades += 1
                return True
            else:
                print(f"      [ERROR] Trade failed: {result.retcode} - {result.comment}")
                return False

        except Exception as e:
            print(f"Error executing trade: {e}")
            return False

    def get_current_positions(self):
        """Get current open positions"""
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
                        'swap': pos.swap,
                        'time': datetime.fromtimestamp(pos.time)
                    }
                return position_data
            return {}
        except Exception as e:
            print(f"Error getting positions: {e}")
            return {}

    def run_trading_cycle(self):
        """Run one complete trading cycle"""
        self.cycle_count += 1

        print(f"\\n[PRODUCTION CYCLE {self.cycle_count}] {datetime.now().strftime('%H:%M:%S')}")

        if not self.connected:
            return False

        try:
            # Update account info
            self.account_info = mt5.account_info()
            positions = self.get_current_positions()

            print(f"  Account Equity: ${self.account_info.equity:,.2f}")
            print(f"  Open Positions: {len(positions)}")

            # Generate signals for all optimal symbols
            signals = []
            for symbol in self.symbol_data.keys():
                signal = self.generate_enhanced_signal(symbol)
                if signal:
                    signals.append(signal)

            print(f"  Generated Signals: {len(signals)}")

            # Sort signals by confidence and execute best ones
            signals.sort(key=lambda x: x['confidence'], reverse=True)

            executed = 0
            max_positions = 3  # Conservative position limit

            for signal in signals:
                if len(positions) + executed < max_positions:
                    # Check if we already have a position in this symbol
                    has_position = any(pos['symbol'] == signal['symbol'] for pos in positions.values())

                    if not has_position and signal['confidence'] >= 70:
                        volume = self.calculate_dynamic_position_size(signal)

                        if volume >= self.symbol_data[signal['symbol']]['min_volume']:
                            if self.execute_trade(signal, volume):
                                executed += 1

            print(f"  Executed Trades: {executed}")

            # Show position status
            if positions:
                total_profit = sum(pos['profit'] for pos in positions.values())
                total_swap = sum(pos['swap'] for pos in positions.values())
                print(f"  Total P&L: ${total_profit:+.2f}")
                print(f"  Swap: ${total_swap:+.2f}")

                for ticket, pos in positions.items():
                    print(f"    Position {ticket}: {pos['symbol']} {pos['type']} {pos['volume']} - P&L: ${pos['profit']:+.2f}")

            # Update portfolio manager
            if self.portfolio_manager:
                try:
                    current_prices = {}
                    for symbol in self.symbol_data.keys():
                        tick = mt5.symbol_info_tick(symbol)
                        if tick:
                            current_prices[symbol] = (tick.bid + tick.ask) / 2

                    self.portfolio_manager.update_prices(current_prices)
                except:
                    pass

            return True

        except Exception as e:
            print(f"  [ERROR] Cycle failed: {e}")
            return False

    def run_production(self, cycles=10, cycle_delay=60):
        """Run production trading system"""
        print(f"\\nStarting PRODUCTION TRADING SYSTEM")
        print(f"Cycles: {cycles}, Delay: {cycle_delay}s")
        print(f"*** REAL TRADING MODE ACTIVATED ***")
        print(f"*** LIVE ORDERS WILL BE EXECUTED ***")

        if not self.connected:
            print("ERROR: Not connected to EXNESS")
            return

        try:
            for i in range(cycles):
                success = self.run_trading_cycle()
                if not success:
                    print("Cycle failed, stopping system")
                    break

                if i < cycles - 1:
                    print(f"  Next cycle in {cycle_delay} seconds...")
                    time.sleep(cycle_delay)

        except KeyboardInterrupt:
            print(f"\\nProduction system stopped by user")

        # Final summary
        positions = self.get_current_positions()
        print(f"\\nPRODUCTION SUMMARY:")
        print(f"  Total Cycles: {self.cycle_count}")
        print(f"  Total Trades: {self.total_trades}")
        print(f"  Final Equity: ${self.account_info.equity:,.2f}")
        print(f"  Open Positions: {len(positions)}")

        if positions:
            total_profit = sum(pos['profit'] for pos in positions.values())
            print(f"  Total P&L: ${total_profit:+.2f}")

    def disconnect(self):
        """Disconnect from EXNESS"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            print("Disconnected from EXNESS")

def main():
    """Main production system"""
    system = ExnessProductionSystem()

    try:
        if system.connect():
            print(f"\\n[PRODUCTION READY]")
            print(f"Optimal symbols configured: {len(system.symbol_data)}")

            choice = input(f"\\nStart production trading? (y/n): ").strip().lower()

            if choice == 'y':
                cycles = int(input("Number of cycles (default 10): ") or "10")
                delay = int(input("Delay between cycles in seconds (default 60): ") or "60")

                system.run_production(cycles=cycles, cycle_delay=delay)
            else:
                print("Production cancelled")
        else:
            print("[ERROR] Failed to connect to EXNESS")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        system.disconnect()

if __name__ == "__main__":
    main()