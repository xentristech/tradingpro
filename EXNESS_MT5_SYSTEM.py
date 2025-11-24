"""
EXNESS MetaTrader 5 Integration System
Connects Enhanced Trading System with EXNESS MT5 Broker
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

print("EXNESS MT5 INTEGRATION SYSTEM v3.0")
print("="*50)

class ExnessTradingSystem:
    """Complete EXNESS MT5 integration with enhanced components"""

    def __init__(self, initial_capital=50000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.connected = False
        self.account_info = None
        self.symbols = ['EURUSD', 'GBPUSD', 'XAUUSD', 'USDCAD', 'AUDUSD']

        # EXNESS MT5 Configuration
        self.exness_config = {
            'path': r"C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe",
            'login': 197678662,
            'password': "Badboy930218*",
            'server': "Exness-MT5Trial11"
        }

        # System components
        self.risk_manager = None
        self.portfolio_manager = None

        # Trading state
        self.positions = {}
        self.orders = {}
        self.total_pnl = 0
        self.cycle_count = 0

        print("Initializing EXNESS MT5 Trading System...")
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
                AssetInfo('XAUUSD', 'Commodity', 'Precious Metals', 'US'),
                AssetInfo('USDCAD', 'Forex', 'Major', 'CA'),
                AssetInfo('AUDUSD', 'Forex', 'Major', 'AU')
            ]

            for asset in assets:
                self.portfolio_manager.add_asset(asset)

            print("  [OK] Portfolio Manager loaded")
        except Exception as e:
            print(f"  [ERROR] Portfolio Manager: {e}")

    def connect_exness_mt5(self):
        """Connect to EXNESS MetaTrader 5"""
        print("\nConnecting to EXNESS MetaTrader 5...")

        try:
            # Check if EXNESS MT5 path exists
            if not os.path.exists(self.exness_config['path']):
                print(f"  [ERROR] EXNESS MT5 not found at: {self.exness_config['path']}")
                print(f"  Please install EXNESS MT5 or check the path")
                return False

            print(f"  Initializing EXNESS MT5: {self.exness_config['path']}")

            # Initialize MT5 with EXNESS path
            if not mt5.initialize(self.exness_config['path']):
                print(f"  [ERROR] Failed to initialize EXNESS MT5")
                print(f"  Error: {mt5.last_error()}")
                return False

            print(f"  [OK] EXNESS MT5 initialized successfully")

            # Login to EXNESS account
            print(f"  Logging into EXNESS account: {self.exness_config['login']}")

            login_result = mt5.login(
                login=self.exness_config['login'],
                password=self.exness_config['password'],
                server=self.exness_config['server']
            )

            if not login_result:
                error = mt5.last_error()
                print(f"  [ERROR] Login to EXNESS failed!")
                print(f"  Error Code: {error}")
                print(f"  Please check your credentials:")
                print(f"    Login: {self.exness_config['login']}")
                print(f"    Server: {self.exness_config['server']}")
                print(f"    Password: {'*' * len(self.exness_config['password'])}")
                return False

            print(f"  [SUCCESS] Logged into EXNESS account successfully!")

            self.connected = True
            self._get_account_info()
            self._setup_symbols()
            return True

        except Exception as e:
            print(f"  [ERROR] Exception during EXNESS connection: {e}")
            return False

    def _get_account_info(self):
        """Get EXNESS account information"""
        try:
            self.account_info = mt5.account_info()
            if self.account_info:
                print(f"\nEXNESS ACCOUNT INFORMATION:")
                print(f"  Login: {self.account_info.login}")
                print(f"  Server: {self.account_info.server}")
                print(f"  Balance: ${self.account_info.balance:,.2f}")
                print(f"  Equity: ${self.account_info.equity:,.2f}")
                print(f"  Margin: ${self.account_info.margin:,.2f}")
                print(f"  Free Margin: ${self.account_info.margin_free:,.2f}")
                print(f"  Leverage: 1:{self.account_info.leverage}")
                print(f"  Company: {self.account_info.company}")
                print(f"  Currency: {self.account_info.currency}")

                # Update system capital with actual account balance
                self.current_capital = self.account_info.equity

                # Update risk manager with real balance
                if self.risk_manager:
                    self.risk_manager.account_balance = self.account_info.equity

                return True
        except Exception as e:
            print(f"  [ERROR] Getting EXNESS account info: {e}")
        return False

    def _setup_symbols(self):
        """Setup and verify EXNESS trading symbols"""
        print(f"\nSetting up EXNESS trading symbols...")

        available_symbols = []

        for symbol in self.symbols:
            try:
                # Get symbol info
                symbol_info = mt5.symbol_info(symbol)

                if symbol_info is None:
                    print(f"  [SKIP] {symbol}: Not available on EXNESS")
                    continue

                # Select symbol for trading
                if not mt5.symbol_select(symbol, True):
                    print(f"  [ERROR] {symbol}: Failed to select")
                    continue

                # Get current tick
                tick = mt5.symbol_info_tick(symbol)
                if tick:
                    spread = tick.ask - tick.bid
                    spread_points = spread / symbol_info.point

                    print(f"  [OK] {symbol}: Bid={tick.bid:.5f}, Ask={tick.ask:.5f}")
                    print(f"       Spread: {spread:.5f} ({spread_points:.1f} points)")
                    print(f"       Contract Size: {symbol_info.trade_contract_size}")
                    print(f"       Min Volume: {symbol_info.volume_min}")
                    print(f"       Max Volume: {symbol_info.volume_max}")
                    available_symbols.append(symbol)
                else:
                    print(f"  [WARNING] {symbol}: No tick data available")

            except Exception as e:
                print(f"  [ERROR] {symbol}: {e}")

        self.symbols = available_symbols
        print(f"  Available symbols: {len(self.symbols)}")

        if len(self.symbols) == 0:
            print(f"  WARNING: No symbols available for trading!")

    def get_market_data(self, symbol, timeframe=mt5.TIMEFRAME_M5, count=100):
        """Get historical market data from EXNESS MT5"""
        try:
            rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
            if rates is not None and len(rates) > 0:
                df = pd.DataFrame(rates)
                df['time'] = pd.to_datetime(df['time'], unit='s')
                df.set_index('time', inplace=True)
                df.rename(columns={'tick_volume': 'volume'}, inplace=True)
                return df
        except Exception as e:
            print(f"Error getting EXNESS data for {symbol}: {e}")
        return pd.DataFrame()

    def get_current_prices(self):
        """Get current bid/ask prices for all EXNESS symbols"""
        prices = {}
        try:
            for symbol in self.symbols:
                tick = mt5.symbol_info_tick(symbol)
                if tick:
                    prices[symbol] = {
                        'bid': tick.bid,
                        'ask': tick.ask,
                        'spread': tick.ask - tick.bid,
                        'mid': (tick.bid + tick.ask) / 2,
                        'time': datetime.fromtimestamp(tick.time)
                    }
        except Exception as e:
            print(f"Error getting EXNESS prices: {e}")
        return prices

    def get_positions(self):
        """Get current open positions from EXNESS MT5"""
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
                        'swap': pos.swap,
                        'comment': pos.comment,
                        'time': datetime.fromtimestamp(pos.time),
                        'magic': pos.magic
                    }
        except Exception as e:
            print(f"Error getting EXNESS positions: {e}")
        return positions

    def send_order(self, symbol, order_type, volume, price=None, sl=None, tp=None, comment="ExnessBot"):
        """Send order to EXNESS MT5"""
        try:
            # Get symbol info
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                print(f"Symbol {symbol} not found on EXNESS")
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
                "magic": 197678662,  # Using account number as magic
                "comment": comment,
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            # Add SL/TP if provided
            if sl:
                request["sl"] = sl
            if tp:
                request["tp"] = tp

            # Send order to EXNESS
            result = mt5.order_send(request)

            if result.retcode == mt5.TRADE_RETCODE_DONE:
                print(f"  [SUCCESS] EXNESS Order executed:")
                print(f"    Symbol: {symbol}")
                print(f"    Type: {order_type}")
                print(f"    Volume: {volume}")
                print(f"    Price: {price}")
                print(f"    Ticket: {result.order}")
                return True
            else:
                print(f"  [ERROR] EXNESS Order failed:")
                print(f"    Code: {result.retcode}")
                print(f"    Comment: {result.comment}")
                return False

        except Exception as e:
            print(f"Error sending EXNESS order: {e}")
            return False

    def generate_signals(self):
        """Generate trading signals using enhanced components"""
        signals = []

        try:
            for symbol in self.symbols:
                # Get market data
                data = self.get_market_data(symbol, mt5.TIMEFRAME_M15, 100)

                if len(data) < 50:
                    continue

                # Enhanced signal generation with multiple indicators
                # Calculate technical indicators
                data['sma_fast'] = data['close'].rolling(10).mean()
                data['sma_slow'] = data['close'].rolling(20).mean()
                data['rsi'] = self._calculate_rsi(data['close'], 14)
                data['atr'] = self._calculate_atr(data, 14)

                # Generate signal based on multiple conditions
                if len(data) >= 2:
                    current_fast = data['sma_fast'].iloc[-1]
                    current_slow = data['sma_slow'].iloc[-1]
                    prev_fast = data['sma_fast'].iloc[-2]
                    prev_slow = data['sma_slow'].iloc[-2]
                    current_rsi = data['rsi'].iloc[-1]
                    current_price = data['close'].iloc[-1]

                    # Enhanced Bullish signal
                    if (prev_fast <= prev_slow and current_fast > current_slow and
                        current_rsi < 70 and current_rsi > 30):

                        confidence = min(85, 60 + (70 - current_rsi) * 0.5)

                        signals.append({
                            'symbol': symbol,
                            'type': 'BUY',
                            'confidence': confidence,
                            'reason': f'Enhanced Bullish Signal (RSI: {current_rsi:.1f})',
                            'current_price': current_price,
                            'atr': data['atr'].iloc[-1]
                        })

                    # Enhanced Bearish signal
                    elif (prev_fast >= prev_slow and current_fast < current_slow and
                          current_rsi > 30 and current_rsi < 70):

                        confidence = min(85, 60 + (current_rsi - 30) * 0.5)

                        signals.append({
                            'symbol': symbol,
                            'type': 'SELL',
                            'confidence': confidence,
                            'reason': f'Enhanced Bearish Signal (RSI: {current_rsi:.1f})',
                            'current_price': current_price,
                            'atr': data['atr'].iloc[-1]
                        })

        except Exception as e:
            print(f"Error generating EXNESS signals: {e}")

        return signals

    def _calculate_rsi(self, prices, period=14):
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_atr(self, data, period=14):
        """Calculate Average True Range"""
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift())
        low_close = np.abs(data['low'] - data['close'].shift())

        true_range = pd.DataFrame({'hl': high_low, 'hc': high_close, 'lc': low_close}).max(axis=1)
        atr = true_range.rolling(window=period).mean()
        return atr

    def calculate_position_size(self, signal, account_balance):
        """Calculate position size using enhanced risk manager"""
        if self.risk_manager:
            try:
                current_price = signal['current_price']
                atr = signal.get('atr', current_price * 0.01)

                # Calculate dynamic stop loss based on ATR
                atr_multiplier = 2.0
                if signal['type'] == 'BUY':
                    stop_loss = current_price - (atr * atr_multiplier)
                    take_profit = current_price + (atr * atr_multiplier * 1.5)  # 1.5:1 R/R
                else:
                    stop_loss = current_price + (atr * atr_multiplier)
                    take_profit = current_price - (atr * atr_multiplier * 1.5)

                signal_dict = {
                    'entry_price': current_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'strength': signal['confidence'] / 100,
                    'ml_confidence': 0.75
                }

                result = self.risk_manager.calculate_position_size(signal_dict, method='kelly')

                # Convert to proper lot size for EXNESS
                if signal['symbol'] in ['EURUSD', 'GBPUSD', 'USDCAD', 'AUDUSD']:
                    # For forex pairs, 1 lot = 100,000 units
                    lots = (result.position_size * current_price) / 100000
                else:
                    # For XAUUSD and other instruments
                    lots = result.position_size / current_price

                # Ensure minimum lot size
                lots = max(0.01, round(lots, 2))

                return lots

            except Exception as e:
                print(f"Error calculating EXNESS position size: {e}")

        # Fallback calculation
        risk_amount = account_balance * 0.005  # 0.5% risk
        lots = max(0.01, round(risk_amount / signal['current_price'], 2))
        return lots

    def run_trading_cycle(self):
        """Run one complete EXNESS trading cycle"""
        self.cycle_count += 1

        print(f"\n[EXNESS Cycle {self.cycle_count}] {datetime.now().strftime('%H:%M:%S')}")

        if not self.connected:
            print("  [ERROR] Not connected to EXNESS MT5")
            return False

        try:
            # 1. Update account info
            self._get_account_info()

            # 2. Get current positions
            positions = self.get_positions()
            print(f"  Current EXNESS positions: {len(positions)}")

            # 3. Get current prices
            prices = self.get_current_prices()
            print(f"  Market data updated for {len(prices)} symbols")

            # 4. Generate signals
            signals = self.generate_signals()
            print(f"  Generated {len(signals)} signals")

            # 5. Display current prices
            if prices:
                print(f"  Current EXNESS Prices:")
                for symbol, price_data in prices.items():
                    print(f"     {symbol}: {price_data['mid']:.5f} (Spread: {price_data['spread']:.5f})")

            # 6. Execute trades
            executed = 0
            for signal in signals:
                if len(positions) < 3:  # Max 3 positions
                    volume = self.calculate_position_size(signal, self.account_info.equity)

                    if volume >= 0.01:  # Minimum lot size
                        print(f"  Signal: {signal['symbol']} {signal['type']} - Confidence: {signal['confidence']:.1f}%")
                        print(f"     Reason: {signal['reason']}")
                        print(f"     Calculated Volume: {volume} lots")

                        # Uncomment the line below to execute real trades
                        # success = self.send_order(
                        #     symbol=signal['symbol'],
                        #     order_type=signal['type'],
                        #     volume=volume,
                        #     comment=signal['reason']
                        # )

                        # For demo, just log the trade
                        print(f"     [DEMO] Would execute: {signal['symbol']} {signal['type']} {volume} lots")
                        executed += 1

            print(f"  Would execute {executed} trades (DEMO MODE)")

            # 7. Display summary
            if positions:
                total_profit = sum(pos['profit'] for pos in positions.values())
                total_swap = sum(pos['swap'] for pos in positions.values())
                print(f"  Total unrealized P&L: ${total_profit:+.2f}")
                print(f"  Total swap: ${total_swap:+.2f}")

                # Show individual positions
                for ticket, pos in positions.items():
                    print(f"     Position {ticket}: {pos['symbol']} {pos['type']} {pos['volume']} - P&L: ${pos['profit']:+.2f}")

            return True

        except Exception as e:
            print(f"  [ERROR] EXNESS trading cycle failed: {e}")
            return False

    def run_demo(self, cycles=10):
        """Run live trading demo with EXNESS MT5"""
        print(f"\nStarting {cycles}-cycle EXNESS MT5 trading demo...")
        print("Press Ctrl+C to stop")

        if not self.connected:
            print("ERROR: Not connected to EXNESS MT5. Cannot start trading.")
            return

        try:
            for i in range(cycles):
                success = self.run_trading_cycle()
                if not success:
                    print("❌ Cycle failed, stopping demo")
                    break

                print(f"  ⏳ Waiting 30 seconds before next cycle...")
                time.sleep(30)  # 30 seconds between cycles for real market data

        except KeyboardInterrupt:
            print(f"\nDemo stopped by user")

        # Final summary
        final_positions = self.get_positions()
        print(f"\nFINAL EXNESS SUMMARY:")
        print(f"  Cycles completed: {self.cycle_count}")
        print(f"  Open positions: {len(final_positions)}")

        if final_positions:
            total_profit = sum(pos['profit'] for pos in final_positions.values())
            print(f"  Total P&L: ${total_profit:+.2f}")

        if self.account_info:
            print(f"  Final Equity: ${self.account_info.equity:,.2f}")

    def disconnect(self):
        """Disconnect from EXNESS MT5"""
        if self.connected:
            mt5.shutdown()
            self.connected = False
            print("Disconnected from EXNESS MT5")

def main():
    """Main function"""
    print("EXNESS MT5 Integration System")
    print("This system connects your enhanced trading components to EXNESS MetaTrader 5")

    # Initialize system
    trading_system = ExnessTradingSystem(initial_capital=50000)

    try:
        # Connect to EXNESS MT5
        if trading_system.connect_exness_mt5():
            print("\n[SUCCESS] Connected to EXNESS MT5!")

            # Ask user for demo or setup
            print("\nOptions:")
            print("1. Run live trading demo (10 cycles)")
            print("2. Show account status only")
            print("3. Show current prices")
            print("4. Show open positions")

            choice = input("\nEnter choice (1-4): ").strip()

            if choice == "1":
                print("\nDEMO MODE - No real trades will be executed")
                trading_system.run_demo(cycles=10)

            elif choice == "2":
                positions = trading_system.get_positions()
                prices = trading_system.get_current_prices()

                print(f"\nEXNESS Account Status:")
                print(f"  Balance: ${trading_system.account_info.balance:,.2f}")
                print(f"  Equity: ${trading_system.account_info.equity:,.2f}")
                print(f"  Open positions: {len(positions)}")
                print(f"  Available symbols: {len(prices)}")

            elif choice == "3":
                prices = trading_system.get_current_prices()
                if prices:
                    print(f"\nCurrent EXNESS Prices:")
                    for symbol, price_data in prices.items():
                        print(f"  {symbol}: {price_data['mid']:.5f} (Spread: {price_data['spread']:.5f})")
                        print(f"    Last Update: {price_data['time']}")

            elif choice == "4":
                positions = trading_system.get_positions()
                if positions:
                    print(f"\nOpen EXNESS Positions:")
                    for ticket, pos in positions.items():
                        print(f"  Position {ticket}:")
                        print(f"    Symbol: {pos['symbol']}")
                        print(f"    Type: {pos['type']}")
                        print(f"    Volume: {pos['volume']}")
                        print(f"    Open Price: {pos['price_open']}")
                        print(f"    Current Price: {pos['price_current']}")
                        print(f"    P&L: ${pos['profit']:+.2f}")
                        print(f"    Time: {pos['time']}")
                        print()
                else:
                    print(f"\nNo open positions on EXNESS account")

        else:
            print("\n[ERROR] Could not connect to EXNESS MT5")
            print("Please ensure:")
            print("1. EXNESS MetaTrader 5 is installed")
            print("2. EXNESS MetaTrader 5 is running")
            print("3. Expert Advisors are enabled")
            print("4. Auto trading is enabled")
            print("5. Your login credentials are correct")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        trading_system.disconnect()

if __name__ == "__main__":
    main()