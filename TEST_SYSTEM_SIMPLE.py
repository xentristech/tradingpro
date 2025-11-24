"""
Quick Test Script for Enhanced Trading System Components (Windows Compatible)
Author: Trading Pro System
Version: 3.0
"""

import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import time

print("TESTING ENHANCED TRADING SYSTEM COMPONENTS")
print("="*60)

# Add paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'backtesting', 'core'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'ml_evolution'))

def create_sample_data(symbol='BTCUSD', days=100):
    """Create sample OHLCV data for testing"""
    dates = pd.date_range(end=datetime.now(), periods=days*24, freq='H')

    base_price = 67000 if symbol == 'BTCUSD' else 1.1
    prices = []
    current_price = base_price

    for date in dates:
        change = np.random.normal(0, 0.02)  # 2% volatility
        current_price *= (1 + change)

        open_price = current_price * (1 + np.random.normal(0, 0.001))
        high_price = max(open_price, current_price) * (1 + abs(np.random.normal(0, 0.005)))
        low_price = min(open_price, current_price) * (1 - abs(np.random.normal(0, 0.005)))
        close_price = current_price
        volume = np.random.exponential(100000)

        prices.append({
            'timestamp': date,
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': volume
        })

    return pd.DataFrame(prices).set_index('timestamp')

def test_risk_manager():
    """Test Enhanced Risk Manager"""
    print("\n[1] Testing Enhanced Risk Manager...")

    try:
        from src.risk.enhanced_risk_manager import EnhancedRiskManager, RiskLevel

        # Initialize risk manager
        risk_manager = EnhancedRiskManager(account_balance=10000, max_risk_per_trade=0.02)
        risk_manager.set_risk_level('CONSERVATIVE')

        # Add sample trades
        sample_trades = [
            {'pnl': 150, 'returns': 0.015},
            {'pnl': -100, 'returns': -0.01},
            {'pnl': 200, 'returns': 0.02},
            {'pnl': -75, 'returns': -0.0075},
            {'pnl': 180, 'returns': 0.018},
        ]

        for trade in sample_trades:
            risk_manager.add_trade(trade)

        # Test position sizing
        signal = {
            'entry_price': 100,
            'stop_loss': 98,
            'take_profit': 105,
            'volatility': 0.02,
            'strength': 0.75,
            'ml_confidence': 0.82
        }

        result = risk_manager.calculate_position_size(signal, method='kelly')

        print(f"   [OK] Risk Manager initialized successfully")
        print(f"   Position Size: {result.position_size:.4f}")
        print(f"   Kelly Fraction: {result.kelly_fraction:.4%}")
        print(f"   Confidence: {result.confidence_level:.2%}")
        print(f"   Reasoning: {result.reasoning}")

        # Get risk metrics
        metrics = risk_manager.get_risk_metrics()
        print(f"   Win Rate: {metrics['win_rate']:.2%}")
        print(f"   Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")

        return True

    except Exception as e:
        print(f"   [ERROR] Risk Manager test failed: {e}")
        return False

def test_signal_scorer():
    """Test Signal Scoring System"""
    print("\n[2] Testing Signal Scoring System...")

    try:
        from src.signals.signal_scoring_system import SignalScoringSystem

        # Initialize scorer
        scorer = SignalScoringSystem()

        # Create sample data
        data = create_sample_data('BTCUSD', 30)

        # Calculate signal score
        signal_score = scorer.calculate_signal_score(data)

        print(f"   [OK] Signal Scorer initialized successfully")
        print(f"   Overall Score: {signal_score.overall_score:.1f}/100")
        print(f"   Signal Type: {signal_score.signal_type.value}")
        print(f"   Confidence: {signal_score.confidence:.1%}")
        print(f"   Strength: {signal_score.strength:.1%}")
        print(f"   Risk/Reward: {signal_score.risk_reward_ratio:.2f}")

        print(f"   Component Scores:")
        print(f"      Trend: {signal_score.trend_score:.1f}")
        print(f"      Momentum: {signal_score.momentum_score:.1f}")
        print(f"      Volume: {signal_score.volume_score:.1f}")
        print(f"      Volatility: {signal_score.volatility_score:.1f}")

        if signal_score.reasoning:
            print(f"   Top Reasoning: {signal_score.reasoning[0]}")

        return True

    except Exception as e:
        print(f"   [ERROR] Signal Scorer test failed: {e}")
        return False

def test_backtest_engine():
    """Test Backtesting Engine"""
    print("\n[3] Testing Professional Backtesting Engine...")

    try:
        from backtesting.core.backtest_engine import BacktestEngine, BacktestConfig

        # Create config
        config = BacktestConfig(
            initial_capital=10000,
            commission_rate=0.001,
            slippage_rate=0.0005,
            risk_per_trade=0.02
        )

        # Initialize engine
        engine = BacktestEngine(config)

        # Simple strategy
        def simple_strategy(bar_data, positions, capital, timestamp):
            signals = []

            if isinstance(bar_data, pd.DataFrame):
                close = bar_data['close'].iloc[0]
            else:
                close = bar_data['close']

            # Random entry with 5% probability
            if np.random.random() > 0.95 and not positions:
                signals.append({
                    'side': 'BUY',
                    'order_type': 'MARKET',
                    'stop_loss': close * 0.98,
                    'take_profit': close * 1.03
                })
            elif positions and np.random.random() > 0.98:
                signals.append({
                    'side': 'SELL',
                    'order_type': 'MARKET'
                })

            return signals

        # Create sample data and run backtest
        data = create_sample_data('BTCUSD', 60)
        result = engine.run(data, simple_strategy)

        print(f"   [OK] Backtest Engine initialized successfully")
        print(f"   Total Return: {result.total_return:.2%}")
        print(f"   Annual Return: {result.annual_return:.2%}")
        print(f"   Sharpe Ratio: {result.sharpe_ratio:.2f}")
        print(f"   Max Drawdown: {result.max_drawdown:.2%}")
        print(f"   Win Rate: {result.win_rate:.2%}")
        print(f"   Total Trades: {result.total_trades}")
        print(f"   Final Capital: ${result.final_capital:.2f}")

        return True

    except Exception as e:
        print(f"   [ERROR] Backtest Engine test failed: {e}")
        return False

def test_portfolio_manager():
    """Test Portfolio Manager"""
    print("\n[4] Testing Advanced Portfolio Manager...")

    try:
        from src.portfolio.advanced_portfolio_manager import AdvancedPortfolioManager, AssetInfo, AllocationMethod

        # Initialize portfolio
        portfolio = AdvancedPortfolioManager(initial_capital=100000)

        # Add assets
        assets = [
            AssetInfo('EURUSD', 'Forex', 'Major', 'EU', current_price=1.0850),
            AssetInfo('GBPUSD', 'Forex', 'Major', 'GB', current_price=1.2650),
            AssetInfo('BTCUSD', 'Crypto', 'Digital Assets', 'US', current_price=67000.0),
            AssetInfo('XAUUSD', 'Commodity', 'Precious Metals', 'US', current_price=2050.0)
        ]

        for asset in assets:
            portfolio.add_asset(asset)

        # Test allocation
        weights = portfolio.optimize_portfolio(AllocationMethod.EQUAL_WEIGHT)
        print(f"   [OK] Portfolio Manager initialized successfully")
        print(f"   Equal Weight allocation:")
        for symbol, weight in weights.items():
            print(f"      {symbol}: {weight:.2%}")

        # Get summary
        summary = portfolio.get_portfolio_summary()
        print(f"   Portfolio value: ${summary['portfolio_value']:,.0f}")
        print(f"   Active assets: {summary['num_assets']}")

        return True

    except Exception as e:
        print(f"   [ERROR] Portfolio Manager test failed: {e}")
        return False

def test_integration():
    """Test Integration System"""
    print("\n[5] Testing Integration System...")

    try:
        # Check if integration file exists
        integration_path = "INTEGRATION_SYSTEM.py"
        if os.path.exists(integration_path):
            print(f"   [OK] Integration system file exists")

            # Try importing
            from INTEGRATION_SYSTEM import IntegratedTradingSystem

            # Initialize system
            system = IntegratedTradingSystem(initial_capital=50000)
            status = system.get_system_status()

            print(f"   [OK] Integration System initialized")
            print(f"   Components available: {status['components_available']}")
            print(f"   Initial capital: ${status['current_capital']:,.0f}")

            return True
        else:
            print(f"   [ERROR] Integration file not found")
            return False

    except Exception as e:
        print(f"   [ERROR] Integration test failed: {e}")
        return False

def main():
    """Run all tests"""
    start_time = time.time()

    tests = [
        ("Risk Manager", test_risk_manager),
        ("Signal Scorer", test_signal_scorer),
        ("Backtest Engine", test_backtest_engine),
        ("Portfolio Manager", test_portfolio_manager),
        ("Integration", test_integration),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"   [ERROR] {test_name} test crashed: {e}")
            results[test_name] = False

    # Summary
    elapsed = time.time() - start_time

    print(f"\nTEST SUMMARY")
    print("="*40)

    passed = sum(results.values())
    total = len(results)

    for test_name, passed_test in results.items():
        status = "[PASS]" if passed_test else "[FAIL]"
        print(f"{test_name:20} {status}")

    print(f"\nRESULTS: {passed}/{total} tests passed")
    print(f"Duration: {elapsed:.1f} seconds")

    if passed == total:
        print(f"\nALL TESTS PASSED! System ready for use.")
        print(f"\nNEXT STEPS:")
        print(f"   1. Install requirements: pip install numpy pandas streamlit plotly")
        print(f"   2. Run integration: python INTEGRATION_SYSTEM.py")
        print(f"   3. Run dashboard: streamlit run dashboard/unified_trading_dashboard.py")
    else:
        print(f"\nSome tests failed. Installing missing dependencies...")
        print(f"   Run: pip install numpy pandas scipy scikit-learn")

if __name__ == "__main__":
    main()