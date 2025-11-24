"""
EXNESS MT5 Auto Symbol Detection System
Automatically detects available symbols and runs trading system
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

print("EXNESS AUTO SYMBOL DETECTION v3.0")
print("="*50)

class ExnessAutoSystem:
    """EXNESS MT5 system with automatic symbol detection"""

    def __init__(self):
        # EXNESS MT5 Configuration
        self.exness_config = {
            'path': r"C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe",
            'login': 197678662,
            'password': "Badboy930218*",
            'server': "Exness-MT5Trial11"
        }

        self.connected = False
        self.account_info = None
        self.available_symbols = []
        self.risk_manager = None

        print("Initializing EXNESS Auto System...")
        self._load_components()

    def _load_components(self):
        """Load enhanced components"""
        try:
            from src.risk.enhanced_risk_manager import EnhancedRiskManager
            self.risk_manager = EnhancedRiskManager(
                account_balance=10000,
                max_risk_per_trade=0.01
            )
            self.risk_manager.set_risk_level('CONSERVATIVE')
            print("  [OK] Enhanced Risk Manager loaded")
        except Exception as e:
            print(f"  [ERROR] Risk Manager: {e}")

    def connect_and_discover(self):
        """Connect to EXNESS and discover available symbols"""
        print("\nConnecting to EXNESS MT5...")

        try:
            # Initialize MT5
            if not mt5.initialize(self.exness_config['path']):
                print(f"  [ERROR] Failed to initialize EXNESS MT5")
                return False

            # Login
            if not mt5.login(
                login=self.exness_config['login'],
                password=self.exness_config['password'],
                server=self.exness_config['server']
            ):
                print(f"  [ERROR] Login failed")
                return False

            print(f"  [SUCCESS] Connected to EXNESS!")
            self.connected = True

            # Get account info
            self.account_info = mt5.account_info()
            if self.account_info:
                print(f"\nAccount: {self.account_info.login}")
                print(f"Balance: ${self.account_info.balance:,.2f}")
                print(f"Equity: ${self.account_info.equity:,.2f}")
                print(f"Leverage: 1:{self.account_info.leverage}")

            # Discover symbols
            self._discover_symbols()
            return True

        except Exception as e:
            print(f"Error connecting: {e}")
            return False

    def _discover_symbols(self):
        """Discover all available trading symbols"""
        print(f"\nDiscovering available symbols...")

        try:
            # Get all symbols
            all_symbols = mt5.symbols_get()

            if not all_symbols:
                print("  No symbols found")
                return

            print(f"  Found {len(all_symbols)} total symbols")

            # Filter for common trading pairs
            preferred_symbols = [
                'EURUSD', 'GBPUSD', 'USDCAD', 'AUDUSD', 'NZDUSD', 'USDCHF', 'USDJPY',
                'EURJPY', 'GBPJPY', 'AUDJPY',
                'XAUUSD', 'XAGUSD',  # Gold, Silver
                'US30', 'US500', 'NAS100',  # Indices
                'BTCUSD', 'ETHUSD'  # Crypto
            ]

            available = []

            for symbol_info in all_symbols:
                symbol = symbol_info.name

                # Check if it's a preferred symbol or major forex
                if (symbol in preferred_symbols or
                    (len(symbol) == 6 and 'USD' in symbol)):

                    try:
                        # Try to select the symbol
                        if mt5.symbol_select(symbol, True):
                            # Get tick data to verify it's tradeable
                            tick = mt5.symbol_info_tick(symbol)
                            if tick and tick.bid > 0 and tick.ask > 0:
                                spread = tick.ask - tick.bid
                                spread_pct = (spread / tick.bid) * 100

                                # Only include if spread is reasonable (< 1%)
                                if spread_pct < 1.0:
                                    available.append({
                                        'symbol': symbol,
                                        'bid': tick.bid,
                                        'ask': tick.ask,
                                        'spread': spread,
                                        'spread_pct': spread_pct,
                                        'contract_size': symbol_info.trade_contract_size,
                                        'min_volume': symbol_info.volume_min,
                                        'max_volume': symbol_info.volume_max,
                                        'volume_step': symbol_info.volume_step
                                    })

                    except Exception as e:
                        continue

            # Sort by spread quality
            available.sort(key=lambda x: x['spread_pct'])

            # Take top 10 best symbols
            self.available_symbols = available[:10]

            print(f"\nTop {len(self.available_symbols)} available symbols:")
            for i, sym in enumerate(self.available_symbols, 1):
                print(f"  {i:2d}. {sym['symbol']:8s} - Bid: {sym['bid']:8.5f}, Ask: {sym['ask']:8.5f}, Spread: {sym['spread_pct']:.3f}%")

        except Exception as e:
            print(f"Error discovering symbols: {e}")

    def get_market_data(self, symbol, timeframe=mt5.TIMEFRAME_M15, count=50):
        """Get market data for a symbol"""
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

    def generate_simple_signal(self, symbol_data):
        """Generate a simple trading signal"""
        try:
            symbol = symbol_data['symbol']
            data = self.get_market_data(symbol)

            if len(data) < 20:
                return None

            # Simple moving average strategy
            data['sma_fast'] = data['close'].rolling(5).mean()
            data['sma_slow'] = data['close'].rolling(15).mean()

            if len(data) >= 2:
                current_fast = data['sma_fast'].iloc[-1]
                current_slow = data['sma_slow'].iloc[-1]
                prev_fast = data['sma_fast'].iloc[-2]
                prev_slow = data['sma_slow'].iloc[-2]

                # Bullish crossover
                if prev_fast <= prev_slow and current_fast > current_slow:
                    return {
                        'symbol': symbol,
                        'type': 'BUY',
                        'price': data['close'].iloc[-1],
                        'confidence': 70,
                        'reason': 'MA Bullish Crossover'
                    }

                # Bearish crossover
                elif prev_fast >= prev_slow and current_fast < current_slow:
                    return {
                        'symbol': symbol,
                        'type': 'SELL',
                        'price': data['close'].iloc[-1],
                        'confidence': 70,
                        'reason': 'MA Bearish Crossover'
                    }

        except Exception as e:
            print(f"Error generating signal for {symbol}: {e}")

        return None

    def calculate_position_size(self, signal, symbol_data):
        """Calculate position size"""
        try:
            if self.risk_manager and self.account_info:
                current_price = signal['price']

                # Simple 1% stop loss
                if signal['type'] == 'BUY':
                    stop_loss = current_price * 0.99
                    take_profit = current_price * 1.02
                else:
                    stop_loss = current_price * 1.01
                    take_profit = current_price * 0.98

                signal_dict = {
                    'entry_price': current_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'strength': signal['confidence'] / 100,
                    'ml_confidence': 0.7
                }

                result = self.risk_manager.calculate_position_size(signal_dict, method='kelly')

                # Convert to lots based on symbol type
                if 'USD' in signal['symbol'] and len(signal['symbol']) == 6:
                    # Forex pair
                    lots = (result.position_size * current_price) / symbol_data['contract_size']
                else:
                    # Other instruments
                    lots = result.position_size / current_price

                # Round to symbol's volume step
                volume_step = symbol_data['volume_step']
                lots = round(lots / volume_step) * volume_step
                lots = max(symbol_data['min_volume'], min(symbol_data['max_volume'], lots))

                return lots

        except Exception as e:
            print(f"Error calculating position size: {e}")

        # Fallback: very small position
        return symbol_data['min_volume']

    def send_order(self, signal, symbol_data, volume):
        """Send order to EXNESS (demo mode for safety)"""
        try:
            symbol = signal['symbol']

            # Get current price
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return False

            if signal['type'] == 'BUY':
                price = tick.ask
                trade_type = mt5.ORDER_TYPE_BUY
            else:
                price = tick.bid
                trade_type = mt5.ORDER_TYPE_SELL

            print(f"    [DEMO] Would execute order:")
            print(f"      Symbol: {symbol}")
            print(f"      Type: {signal['type']}")
            print(f"      Volume: {volume}")
            print(f"      Price: {price}")
            print(f"      Reason: {signal['reason']}")

            # Uncomment below to execute real orders (USE WITH EXTREME CAUTION)
            # request = {
            #     "action": mt5.TRADE_ACTION_DEAL,
            #     "symbol": symbol,
            #     "volume": volume,
            #     "type": trade_type,
            #     "price": price,
            #     "deviation": 20,
            #     "magic": 197678662,
            #     "comment": signal['reason'],
            #     "type_time": mt5.ORDER_TIME_GTC,
            #     "type_filling": mt5.ORDER_FILLING_IOC,
            # }
            #
            # result = mt5.order_send(request)
            # return result.retcode == mt5.TRADE_RETCODE_DONE

            return True  # Demo success

        except Exception as e:
            print(f"Error sending order: {e}")
            return False

    def run_trading_cycle(self):
        """Run one trading cycle"""
        print(f"\n[Trading Cycle {datetime.now().strftime('%H:%M:%S')}]")

        if not self.connected or not self.available_symbols:
            print("  Not ready for trading")
            return False

        try:
            # Update account info
            self.account_info = mt5.account_info()
            print(f"  Account Equity: ${self.account_info.equity:,.2f}")

            # Get current positions
            positions = mt5.positions_get()
            num_positions = len(positions) if positions else 0
            print(f"  Open Positions: {num_positions}")

            # Generate signals for available symbols
            signals = []
            for symbol_data in self.available_symbols:
                signal = self.generate_simple_signal(symbol_data)
                if signal:
                    signals.append((signal, symbol_data))

            print(f"  Generated Signals: {len(signals)}")

            # Execute trades (limit to 3 open positions)
            executed = 0
            for signal, symbol_data in signals:
                if num_positions + executed < 3:
                    volume = self.calculate_position_size(signal, symbol_data)

                    if volume >= symbol_data['min_volume']:
                        if self.send_order(signal, symbol_data, volume):
                            executed += 1

            print(f"  Executed Trades: {executed}")

            # Show position P&L if any
            if positions:
                total_profit = sum(pos.profit for pos in positions)
                print(f"  Total P&L: ${total_profit:+.2f}")

            return True

        except Exception as e:
            print(f"  Error in trading cycle: {e}")
            return False

    def run_demo(self, cycles=5):
        """Run demo trading"""
        print(f"\nStarting {cycles}-cycle EXNESS demo...")
        print("DEMO MODE - No real trades will be executed")

        if not self.connected:
            print("ERROR: Not connected to EXNESS")
            return

        try:
            for i in range(cycles):
                success = self.run_trading_cycle()
                if not success:
                    break

                if i < cycles - 1:
                    print("  Waiting 20 seconds...")
                    time.sleep(20)

        except KeyboardInterrupt:
            print("\nDemo stopped by user")

        # Final summary
        positions = mt5.positions_get()
        print(f"\nFinal Summary:")
        print(f"  Account: {self.account_info.login}")
        print(f"  Equity: ${self.account_info.equity:,.2f}")
        print(f"  Open Positions: {len(positions) if positions else 0}")

        if positions:
            total_profit = sum(pos.profit for pos in positions)
            print(f"  Total P&L: ${total_profit:+.2f}")

    def disconnect(self):
        """Disconnect from MT5"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            print("Disconnected from EXNESS")

def main():
    """Main function"""
    system = ExnessAutoSystem()

    try:
        if system.connect_and_discover():
            print(f"\n[SUCCESS] Ready for trading!")

            if system.available_symbols:
                choice = input(f"\nRun demo with {len(system.available_symbols)} symbols? (y/n): ").strip().lower()

                if choice == 'y':
                    system.run_demo(cycles=5)
                else:
                    print("Demo cancelled")
            else:
                print("No suitable symbols found for trading")
        else:
            print("[ERROR] Failed to connect to EXNESS")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        system.disconnect()

if __name__ == "__main__":
    main()