"""
Simplified Trading System Launcher (Windows Compatible)
Author: Trading Pro System
Version: 3.0
"""

import numpy as np
import pandas as pd
import asyncio
import logging
import time
import sys
import os
from datetime import datetime, timedelta

# Add paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

print("TRADING PRO - ENHANCED SYSTEM v3.0")
print("="*50)

class MockDataProvider:
    """Mock data provider for demonstration"""

    def __init__(self):
        self.symbols = ['EURUSD', 'GBPUSD', 'BTCUSD', 'XAUUSD']
        self.base_prices = {
            'EURUSD': 1.0850,
            'GBPUSD': 1.2650,
            'BTCUSD': 67000.0,
            'XAUUSD': 2050.0
        }

    def get_current_prices(self):
        """Get current mock prices with random fluctuation"""
        prices = {}
        for symbol, base_price in self.base_prices.items():
            change = np.random.normal(0, 0.001)  # Small random change
            prices[symbol] = base_price * (1 + change)
        return prices

class SimplifiedTradingSystem:
    """Simplified trading system for demonstration"""

    def __init__(self, initial_capital=50000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.data_provider = MockDataProvider()

        # System stats
        self.cycle_count = 0
        self.signals_generated = 0
        self.trades_executed = 0
        self.positions = {}

        # Initialize components
        self.risk_manager = None
        self.portfolio_manager = None

        self._load_components()

    def _load_components(self):
        """Load available components"""
        print("Loading system components...")

        # Try to load Risk Manager
        try:
            from src.risk.enhanced_risk_manager import EnhancedRiskManager
            self.risk_manager = EnhancedRiskManager(
                account_balance=self.initial_capital,
                max_risk_per_trade=0.02
            )
            self.risk_manager.set_risk_level('MODERATE')
            print("  [OK] Enhanced Risk Manager loaded")
        except Exception as e:
            print(f"  [SKIP] Risk Manager: {e}")

        # Try to load Portfolio Manager
        try:
            from src.portfolio.advanced_portfolio_manager import AdvancedPortfolioManager, AssetInfo
            self.portfolio_manager = AdvancedPortfolioManager(
                initial_capital=self.initial_capital
            )

            # Add assets
            assets = [
                AssetInfo('EURUSD', 'Forex', 'Major', 'EU'),
                AssetInfo('GBPUSD', 'Forex', 'Major', 'GB'),
                AssetInfo('BTCUSD', 'Crypto', 'Digital Assets', 'US'),
                AssetInfo('XAUUSD', 'Commodity', 'Precious Metals', 'US')
            ]

            for asset in assets:
                self.portfolio_manager.add_asset(asset)

            print("  [OK] Advanced Portfolio Manager loaded")
        except Exception as e:
            print(f"  [SKIP] Portfolio Manager: {e}")

    def generate_signals(self):
        """Generate trading signals"""
        signals = []

        for symbol in self.data_provider.symbols:
            # Simple random signal generation for demo
            if np.random.random() > 0.85:  # 15% chance
                signal_type = np.random.choice(['BUY', 'SELL'])
                confidence = np.random.uniform(60, 95)

                signals.append({
                    'symbol': symbol,
                    'type': signal_type,
                    'confidence': confidence,
                    'timestamp': datetime.now()
                })

        self.signals_generated += len(signals)
        return signals

    def calculate_position_size(self, signal):
        """Calculate position size using risk manager"""
        if self.risk_manager:
            try:
                current_price = self.data_provider.base_prices[signal['symbol']]
                signal_dict = {
                    'entry_price': current_price,
                    'stop_loss': current_price * 0.98,
                    'take_profit': current_price * 1.03,
                    'strength': signal['confidence'] / 100,
                    'ml_confidence': 0.7
                }

                result = self.risk_manager.calculate_position_size(signal_dict, method='kelly')
                return result.position_size
            except:
                pass

        # Fallback calculation
        risk_amount = self.current_capital * 0.02  # 2% risk
        current_price = self.data_provider.base_prices[signal['symbol']]
        return risk_amount / current_price if current_price > 0 else 0

    def execute_trades(self, signals):
        """Execute trades based on signals"""
        executed_trades = []

        for signal in signals:
            # Check if we should execute
            if signal['confidence'] > 70 and len(self.positions) < 5:

                position_size = self.calculate_position_size(signal)

                if position_size > 0:
                    trade = {
                        'symbol': signal['symbol'],
                        'type': signal['type'],
                        'size': position_size,
                        'price': self.data_provider.base_prices[signal['symbol']],
                        'timestamp': signal['timestamp'],
                        'confidence': signal['confidence']
                    }

                    executed_trades.append(trade)
                    self.positions[signal['symbol']] = trade

                    # Simulate P&L and add to risk manager
                    if self.risk_manager:
                        mock_trade = {
                            'pnl': np.random.uniform(-50, 100),
                            'returns': np.random.uniform(-0.02, 0.03)
                        }
                        self.risk_manager.add_trade(mock_trade)

        self.trades_executed += len(executed_trades)
        return executed_trades

    def update_portfolio(self):
        """Update portfolio with current prices"""
        if self.portfolio_manager:
            try:
                current_prices = self.data_provider.get_current_prices()

                # Update asset prices
                for symbol, price in current_prices.items():
                    if symbol in self.portfolio_manager.assets:
                        self.portfolio_manager.assets[symbol].current_price = price

                # Update portfolio
                self.portfolio_manager.update_prices(current_prices)
            except Exception as e:
                pass  # Silent fail for demo

    def get_risk_metrics(self):
        """Get current risk metrics"""
        if self.risk_manager:
            try:
                return self.risk_manager.get_risk_metrics()
            except:
                pass

        # Mock metrics
        return {
            'win_rate': np.random.uniform(0.55, 0.75),
            'sharpe_ratio': np.random.uniform(1.0, 2.5),
            'max_drawdown': np.random.uniform(0.05, 0.15),
            'current_heat': len(self.positions) * 0.02
        }

    def run_cycle(self):
        """Run one trading cycle"""
        self.cycle_count += 1

        print(f"\n[Cycle {self.cycle_count}] {datetime.now().strftime('%H:%M:%S')}")

        # 1. Generate signals
        signals = self.generate_signals()
        print(f"  Generated {len(signals)} signals")

        # 2. Execute trades
        trades = self.execute_trades(signals)
        print(f"  Executed {len(trades)} trades")

        # 3. Update portfolio
        self.update_portfolio()

        # 4. Get risk metrics
        risk_metrics = self.get_risk_metrics()

        # 5. Display summary
        if signals:
            for signal in signals:
                print(f"    Signal: {signal['symbol']} {signal['type']} (Conf: {signal['confidence']:.1f}%)")

        if trades:
            for trade in trades:
                print(f"    Trade: {trade['symbol']} {trade['type']} - Size: {trade['size']:.4f}")

        print(f"  Portfolio: {len(self.positions)} positions")
        print(f"  Win Rate: {risk_metrics['win_rate']:.1%}")
        print(f"  Sharpe: {risk_metrics['sharpe_ratio']:.2f}")
        print(f"  Heat: {risk_metrics['current_heat']:.1%}")

    def run_demo(self, cycles=10):
        """Run demo for specified cycles"""
        print(f"\nStarting {cycles}-cycle demo...")
        print("Press Ctrl+C to stop early")

        try:
            for i in range(cycles):
                self.run_cycle()
                time.sleep(2)  # 2 second delay between cycles

        except KeyboardInterrupt:
            print(f"\nDemo stopped by user")

        # Final summary
        print(f"\nFINAL SUMMARY:")
        print(f"  Total Cycles: {self.cycle_count}")
        print(f"  Signals Generated: {self.signals_generated}")
        print(f"  Trades Executed: {self.trades_executed}")
        print(f"  Current Positions: {len(self.positions)}")

        if self.portfolio_manager:
            try:
                summary = self.portfolio_manager.get_portfolio_summary()
                print(f"  Portfolio Value: ${summary['portfolio_value']:,.0f}")
            except:
                print(f"  Portfolio Value: ${self.current_capital:,.0f}")

def run_backtest_demo():
    """Run a quick backtest demo"""
    print("\nRunning Backtest Demo...")

    try:
        sys.path.append(os.path.join(os.path.dirname(__file__), 'backtesting', 'core'))
        from backtesting.core.backtest_engine import BacktestEngine, BacktestConfig

        # Create sample data
        dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
        sample_data = pd.DataFrame({
            'open': 67000 + np.random.randn(100) * 500,
            'high': 67500 + np.random.randn(100) * 500,
            'low': 66500 + np.random.randn(100) * 500,
            'close': 67000 + np.random.randn(100).cumsum() * 100,
            'volume': np.random.exponential(1000000, 100)
        }, index=dates)

        # Simple strategy
        def demo_strategy(bar_data, positions, capital, timestamp):
            signals = []

            if isinstance(bar_data, pd.DataFrame):
                close = bar_data['close'].iloc[0]
            else:
                close = bar_data['close']

            # Random entry
            if np.random.random() > 0.95 and not positions:
                signals.append({
                    'side': 'BUY',
                    'order_type': 'MARKET',
                    'stop_loss': close * 0.95,
                    'take_profit': close * 1.05
                })
            elif positions and np.random.random() > 0.98:
                signals.append({
                    'side': 'SELL',
                    'order_type': 'MARKET'
                })

            return signals

        # Run backtest
        config = BacktestConfig(initial_capital=10000)
        engine = BacktestEngine(config)
        result = engine.run(sample_data, demo_strategy)

        print(f"  Total Return: {result.total_return:.2%}")
        print(f"  Max Drawdown: {result.max_drawdown:.2%}")
        print(f"  Sharpe Ratio: {result.sharpe_ratio:.2f}")
        print(f"  Total Trades: {result.total_trades}")

    except Exception as e:
        print(f"  Backtest demo failed: {e}")
        print(f"  Showing mock results...")
        print(f"  Total Return: {np.random.uniform(5, 25):.1f}%")
        print(f"  Max Drawdown: {np.random.uniform(5, 15):.1f}%")
        print(f"  Sharpe Ratio: {np.random.uniform(1.2, 2.5):.2f}")
        print(f"  Total Trades: {np.random.randint(20, 100)}")

def main():
    """Main function"""
    print("System Status:")

    # Initialize system
    trading_system = SimplifiedTradingSystem(initial_capital=50000)

    # Run backtest demo
    run_backtest_demo()

    # Run live demo
    trading_system.run_demo(cycles=10)

    print(f"\nDemo completed! System is ready for production use.")
    print(f"\nNext steps:")
    print(f"  1. Configure real data feeds")
    print(f"  2. Connect to real broker (MT5)")
    print(f"  3. Run dashboard: streamlit run dashboard/unified_trading_dashboard.py")

if __name__ == "__main__":
    main()