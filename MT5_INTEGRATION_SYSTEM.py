"""
MetaTrader 5 Integration System
Integrates Enhanced Trading System with MT5
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
from typing import Dict, List, Optional, Tuple

# Add paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

print("MT5 INTEGRATION SYSTEM v3.0")
print("="*50)

class MT5TradingSystem:
    """Complete MT5 integration with enhanced components"""

    def __init__(self, initial_capital=50000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.connected = False
        self.account_info = None
        self.symbols = ['EURUSD', 'GBPUSD', 'BTCUSD', 'XAUUSD']

        # System components
        self.risk_manager = None
        self.portfolio_manager = None

        # Trading state
        self.positions = {}
        self.orders = {}
        self.total_pnl = 0
        self.cycle_count = 0

        print("Initializing MT5 Trading System...")
        self._load_components()

    def _load_components(self):
        """Load enhanced components"""
        print("Loading enhanced components...")

        # Load Risk Manager
        try:
            from src.risk.enhanced_risk_manager import EnhancedRiskManager
            self.risk_manager = EnhancedRiskManager(
                account_balance=self.initial_capital,
                max_risk_per_trade=0.02
            )
            self.risk_manager.set_risk_level('MODERATE')
            print("  [OK] Enhanced Risk Manager loaded")
        except Exception as e:
            print(f"  [ERROR] Risk Manager: {e}")

        # Load Portfolio Manager
        try:
            from src.portfolio.advanced_portfolio_manager import AdvancedPortfolioManager, AssetInfo
            self.portfolio_manager = AdvancedPortfolioManager(
                initial_capital=self.initial_capital
            )

            assets = [
                AssetInfo('EURUSD', 'Forex', 'Major', 'EU'),
                AssetInfo('GBPUSD', 'Forex', 'Major', 'GB'),
                AssetInfo('BTCUSD', 'Crypto', 'Digital Assets', 'US'),
                AssetInfo('XAUUSD', 'Commodity', 'Precious Metals', 'US')
            ]

            for asset in assets:
                self.portfolio_manager.add_asset(asset)

            print("  [OK] Portfolio Manager loaded")
        except Exception as e:
            print(f"  [ERROR] Portfolio Manager: {e}")

    def connect_mt5(self, path=None, login=None, password=None, server=None):
        """Connect to MetaTrader 5"""
        print("\nConnecting to MetaTrader 5...")

        # Try different MT5 paths
        mt5_paths = [
            r"C:\Program Files\MetaTrader 5\terminal64.exe",
            r"C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe",
            r"C:\Program Files (x86)\MetaTrader 5\terminal64.exe"
        ]

        if path:
            mt5_paths.insert(0, path)

        # Try to initialize MT5
        for mt5_path in mt5_paths:
            try:
                if os.path.exists(mt5_path):
                    print(f"  Trying: {mt5_path}")

                    if mt5.initialize(mt5_path):
                        print(f"  [OK] MT5 initialized from: {mt5_path}")

                        # Try to login if credentials provided
                        if login and password and server:
                            if mt5.login(login, password, server):
                                print(f"  [OK] Logged in to account: {login}")
                            else:
                                print(f"  [WARNING] Login failed, using demo account")

                        self.connected = True
                        self._get_account_info()
                        self._setup_symbols()
                        return True

            except Exception as e:
                print(f"  [ERROR] Failed to initialize {mt5_path}: {e}")
                continue

        # If all paths fail, try default initialization
        try:
            if mt5.initialize():
                print("  [OK] MT5 initialized with default path")
                self.connected = True
                self._get_account_info()
                self._setup_symbols()
                return True
        except Exception as e:
            print(f"  [ERROR] Default initialization failed: {e}")

        print("  [FAILED] Could not connect to MT5")
        return False

    def _get_account_info(self):
        """Get MT5 account information"""
        try:
            self.account_info = mt5.account_info()
            if self.account_info:
                print(f"\nAccount Information:")
                print(f"  Login: {self.account_info.login}")
                print(f"  Server: {self.account_info.server}")
                print(f"  Balance: ${self.account_info.balance:,.2f}")
                print(f"  Equity: ${self.account_info.equity:,.2f}")
                print(f"  Margin: ${self.account_info.margin:,.2f}")
                print(f"  Free Margin: ${self.account_info.margin_free:,.2f}")
                print(f"  Leverage: 1:{self.account_info.leverage}")

                # Update system capital with actual account balance
                self.current_capital = self.account_info.equity

                return True
        except Exception as e:
            print(f"  [ERROR] Getting account info: {e}")
        return False

    def _setup_symbols(self):
        """Setup and verify trading symbols"""
        print(f"\nSetting up trading symbols...")

        available_symbols = []

        for symbol in self.symbols:
            try:
                # Get symbol info
                symbol_info = mt5.symbol_info(symbol)

                if symbol_info is None:
                    print(f"  [SKIP] {symbol}: Not available")
                    continue

                # Select symbol for trading
                if not mt5.symbol_select(symbol, True):
                    print(f"  [ERROR] {symbol}: Failed to select")
                    continue

                # Get current tick
                tick = mt5.symbol_info_tick(symbol)
                if tick:
                    print(f"  [OK] {symbol}: Bid={tick.bid:.5f}, Ask={tick.ask:.5f}, Spread={tick.ask-tick.bid:.5f}")
                    available_symbols.append(symbol)
                else:
                    print(f"  [WARNING] {symbol}: No tick data")

            except Exception as e:
                print(f"  [ERROR] {symbol}: {e}")

        self.symbols = available_symbols
        print(f"  Available symbols: {len(self.symbols)}")

    def get_market_data(self, symbol, timeframe=mt5.TIMEFRAME_M1, count=100):
        """Get historical market data from MT5"""
        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            if rates is not None and len(rates) > 0:
                df = pd.DataFrame(rates)
                df['time'] = pd.to_datetime(df['time'], unit='s')
                df.set_index('time', inplace=True)
                df.rename(columns={'tick_volume': 'volume'}, inplace=True)
                return df
        except Exception as e:
            print(f"Error getting data for {symbol}: {e}")
        return pd.DataFrame()

    def get_current_prices(self):
        """Get current bid/ask prices for all symbols"""
        prices = {}
        try:
            for symbol in self.symbols:
                tick = mt5.symbol_info_tick(symbol)
                if tick:
                    prices[symbol] = {
                        'bid': tick.bid,
                        'ask': tick.ask,
                        'spread': tick.ask - tick.bid,
                        'mid': (tick.bid + tick.ask) / 2
                    }
        except Exception as e:
            print(f"Error getting prices: {e}")
        return prices

    def get_positions(self):
        """Get current open positions from MT5"""
        positions = {}
        try:
            mt5_positions = mt5.positions_get()
            if mt5_positions:
                for pos in mt5_positions:
                    positions[pos.ticket] = {
                        'symbol': pos.symbol,
                        'type': 'BUY' if pos.type == 0 else 'SELL',
                        'volume': pos.volume,
                        'price_open': pos.price_open,
                        'price_current': pos.price_current,
                        'profit': pos.profit,
                        'comment': pos.comment,
                        'time': datetime.fromtimestamp(pos.time)
                    }
        except Exception as e:
            print(f"Error getting positions: {e}")
        return positions

    def send_order(self, symbol, order_type, volume, price=None, sl=None, tp=None, comment=""):
        """Send order to MT5"""
        try:
            # Get symbol info
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                print(f"Symbol {symbol} not found")
                return False

            # Prepare request
            if order_type == "BUY":
                trade_type = mt5.ORDER_TYPE_BUY
                price = mt5.symbol_info_tick(symbol).ask if price is None else price
            else:
                trade_type = mt5.ORDER_TYPE_SELL
                price = mt5.symbol_info_tick(symbol).bid if price is None else price

            # Round volume to proper step
            volume = round(volume / symbol_info.volume_step) * symbol_info.volume_step
            volume = max(symbol_info.volume_min, min(symbol_info.volume_max, volume))

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": volume,
                "type": trade_type,
                "price": price,
                "deviation": 20,
                "magic": 123456,
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            # Add SL/TP if provided
            if sl:
                request["sl"] = sl
            if tp:
                request["tp"] = tp

            # Send order
            result = mt5.order_send(request)

            if result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"  [OK] Order executed: {symbol} {order_type} {volume} @ {price}")
                return True
            else:
                print(f"  [ERROR] Order failed: {result.retcode} - {result.comment}")
                return False

        except Exception as e:
            print(f"Error sending order: {e}")
            return False

    def close_position(self, ticket):
        """Close position by ticket"""
        try:
            positions = mt5.positions_get(ticket=ticket)
            if positions:
                position = positions[0]

                # Prepare close request
                if position.type == 0:  # BUY position
                    trade_type = mt5.ORDER_TYPE_SELL
                    price = mt5.symbol_info_tick(position.symbol).bid
                else:  # SELL position
                    trade_type = mt5.ORDER_TYPE_BUY
                    price = mt5.symbol_info_tick(position.symbol).ask

                request = {
                    "action": mt5.TRADE_ACTION_DEAL,
                    "symbol": position.symbol,
                    "volume": position.volume,
                    "type": trade_type,
                    "position": ticket,
                    "price": price,
                    "deviation": 20,
                    "magic": 123456,
                    "comment": "Close position",
                    "type_time": mt5.ORDER_TIME_GTC,
                    "type_filling": mt5.ORDER_FILLING_IOC,
                }

                result = mt5.order_send(request)

                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    print(f"  [OK] Position closed: {ticket}")
                    return True
                else:
                    print(f"  [ERROR] Close failed: {result.retcode}")
                    return False
        except Exception as e:
            print(f"Error closing position: {e}")
        return False

    def generate_signals(self):
        """Generate trading signals using enhanced components"""
        signals = []

        try:
            for symbol in self.symbols:
                # Get market data
                data = self.get_market_data(symbol, mt5.TIMEFRAME_M5, 100)

                if len(data) < 50:
                    continue

                # Simple signal generation (can be enhanced with signal scoring system)
                # Calculate simple moving averages
                data['sma_fast'] = data['close'].rolling(10).mean()
                data['sma_slow'] = data['close'].rolling(20).mean()

                # Generate signal based on MA crossover
                if len(data) >= 2:
                    current_fast = data['sma_fast'].iloc[-1]
                    current_slow = data['sma_slow'].iloc[-1]
                    prev_fast = data['sma_fast'].iloc[-2]
                    prev_slow = data['sma_slow'].iloc[-2]

                    # Bullish crossover
                    if prev_fast <= prev_slow and current_fast > current_slow:
                        signals.append({
                            'symbol': symbol,
                            'type': 'BUY',
                            'confidence': 75,
                            'reason': 'MA Bullish Crossover',
                            'current_price': data['close'].iloc[-1]
                        })

                    # Bearish crossover
                    elif prev_fast >= prev_slow and current_fast < current_slow:
                        signals.append({
                            'symbol': symbol,
                            'type': 'SELL',
                            'confidence': 75,
                            'reason': 'MA Bearish Crossover',
                            'current_price': data['close'].iloc[-1]
                        })

        except Exception as e:
            print(f"Error generating signals: {e}")

        return signals

    def calculate_position_size(self, signal, account_balance):
        """Calculate position size using enhanced risk manager"""
        if self.risk_manager:
            try:
                current_price = signal['current_price']

                # Calculate stop loss and take profit
                if signal['type'] == 'BUY':
                    stop_loss = current_price * 0.99  # 1% SL
                    take_profit = current_price * 1.02  # 2% TP
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

                # Convert to lots (for forex, 1 lot = 100,000 units)
                if signal['symbol'] in ['EURUSD', 'GBPUSD']:
                    lots = (result.position_size * current_price) / 100000
                else:
                    lots = result.position_size / current_price

                return round(lots, 2)

            except Exception as e:
                print(f"Error calculating position size: {e}")

        # Fallback calculation
        risk_amount = account_balance * 0.01  # 1% risk
        return round(risk_amount / signal['current_price'], 2)

    def run_trading_cycle(self):
        """Run one complete trading cycle"""
        self.cycle_count += 1

        print(f"\n[Cycle {self.cycle_count}] {datetime.now().strftime('%H:%M:%S')}")

        if not self.connected:
            print("  [ERROR] Not connected to MT5")
            return False

        try:
            # 1. Update account info
            self._get_account_info()

            # 2. Get current positions
            positions = self.get_positions()
            print(f"  Current positions: {len(positions)}")

            # 3. Get current prices
            prices = self.get_current_prices()
            print(f"  Market data updated for {len(prices)} symbols")

            # 4. Generate signals
            signals = self.generate_signals()
            print(f"  Generated {len(signals)} signals")

            # 5. Execute trades
            executed = 0
            for signal in signals:
                if len(positions) < 3:  # Max 3 positions
                    volume = self.calculate_position_size(signal, self.account_info.equity)

                    if volume > 0:
                        success = self.send_order(
                            symbol=signal['symbol'],
                            order_type=signal['type'],
                            volume=volume,
                            comment=signal['reason']
                        )

                        if success:
                            executed += 1

            print(f"  Executed {executed} trades")

            # 6. Display summary
            if positions:
                total_profit = sum(pos['profit'] for pos in positions.values())
                print(f"  Total unrealized P&L: ${total_profit:+.2f}")

            return True

        except Exception as e:
            print(f"  [ERROR] Trading cycle failed: {e}")
            return False

    def run_demo(self, cycles=10):
        """Run live trading demo with MT5"""
        print(f"\nStarting {cycles}-cycle MT5 trading demo...")
        print("Press Ctrl+C to stop")

        if not self.connected:
            print("ERROR: Not connected to MT5. Cannot start trading.")
            return

        try:
            for i in range(cycles):
                success = self.run_trading_cycle()
                if not success:
                    print("Cycle failed, stopping demo")
                    break

                time.sleep(10)  # 10 seconds between cycles

        except KeyboardInterrupt:
            print(f"\nDemo stopped by user")

        # Final summary
        final_positions = self.get_positions()
        print(f"\nFinal Summary:")
        print(f"  Cycles completed: {self.cycle_count}")
        print(f"  Open positions: {len(final_positions)}")

        if final_positions:
            total_profit = sum(pos['profit'] for pos in final_positions.values())
            print(f"  Total P&L: ${total_profit:+.2f}")

    def disconnect(self):
        """Disconnect from MT5"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            print("Disconnected from MT5")

def main():
    """Main function"""
    print("MT5 Integration System")
    print("This system connects your enhanced trading components to MetaTrader 5")

    # Initialize system
    trading_system = MT5TradingSystem(initial_capital=50000)

    try:
        # Connect to MT5
        if trading_system.connect_mt5():
            print("\n[SUCCESS] Connected to MT5!")

            # Ask user for demo or setup
            print("\nOptions:")
            print("1. Run live trading demo (10 cycles)")
            print("2. Just show account status")
            print("3. Test order placement")

            choice = input("\nEnter choice (1-3): ").strip()

            if choice == "1":
                trading_system.run_demo(cycles=10)

            elif choice == "2":
                positions = trading_system.get_positions()
                prices = trading_system.get_current_prices()

                print(f"\nAccount Status:")
                print(f"  Open positions: {len(positions)}")
                print(f"  Available symbols: {len(prices)}")

                if prices:
                    print(f"\nCurrent Prices:")
                    for symbol, price_data in prices.items():
                        print(f"  {symbol}: {price_data['mid']:.5f} (Spread: {price_data['spread']:.5f})")

            elif choice == "3":
                print("\nTesting order placement (DEMO)...")
                # This would place a small test order
                print("Test order functionality available but not executed in demo")

        else:
            print("\n[ERROR] Could not connect to MT5")
            print("Please ensure:")
            print("1. MetaTrader 5 is installed")
            print("2. MetaTrader 5 is running")
            print("3. Expert Advisors are enabled")
            print("4. Auto trading is enabled")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        trading_system.disconnect()

if __name__ == "__main__":
    main()