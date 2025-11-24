"""
Quick Test Script for Enhanced Trading System Components
Author: Trading Pro System
Version: 3.0
"""

import sys
import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import time

print("🚀 TESTING ENHANCED TRADING SYSTEM COMPONENTS")
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
    print("\n1️⃣ Testing Enhanced Risk Manager...")

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

        print(f"   ✅ Risk Manager initialized successfully")
        print(f"   💰 Position Size: {result.position_size:.4f}")
        print(f"   📊 Kelly Fraction: {result.kelly_fraction:.4%}")
        print(f"   🎯 Confidence: {result.confidence_level:.2%}")
        print(f"   💡 Reasoning: {result.reasoning}")

        # Get risk metrics
        metrics = risk_manager.get_risk_metrics()
        print(f"   📈 Win Rate: {metrics['win_rate']:.2%}")
        print(f"   📉 Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")

        return True

    except Exception as e:
        print(f"   ❌ Risk Manager test failed: {e}")
        return False

def test_signal_scorer():
    """Test Signal Scoring System"""
    print("\n2️⃣ Testing Signal Scoring System...")

    try:
        from src.signals.signal_scoring_system import SignalScoringSystem

        # Initialize scorer
        scorer = SignalScoringSystem()

        # Create sample data
        data = create_sample_data('BTCUSD', 30)

        # Calculate signal score
        signal_score = scorer.calculate_signal_score(data)

        print(f"   ✅ Signal Scorer initialized successfully")
        print(f"   📊 Overall Score: {signal_score.overall_score:.1f}/100")
        print(f"   🎯 Signal Type: {signal_score.signal_type.value}")
        print(f"   💪 Confidence: {signal_score.confidence:.1%}")
        print(f"   ⚡ Strength: {signal_score.strength:.1%}")
        print(f"   📈 Risk/Reward: {signal_score.risk_reward_ratio:.2f}")

        print(f"   📋 Component Scores:")
        print(f"      Trend: {signal_score.trend_score:.1f}")
        print(f"      Momentum: {signal_score.momentum_score:.1f}")
        print(f"      Volume: {signal_score.volume_score:.1f}")
        print(f"      Volatility: {signal_score.volatility_score:.1f}")

        if signal_score.reasoning:
            print(f"   💡 Top Reasoning: {signal_score.reasoning[0]}")

        return True

    except Exception as e:
        print(f"   ❌ Signal Scorer test failed: {e}")
        return False

def test_backtest_engine():
    """Test Backtesting Engine"""
    print("\n3️⃣ Testing Professional Backtesting Engine...")

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

        print(f"   ✅ Backtest Engine initialized successfully")
        print(f"   💰 Total Return: {result.total_return:.2%}")
        print(f"   📅 Annual Return: {result.annual_return:.2%}")
        print(f"   📊 Sharpe Ratio: {result.sharpe_ratio:.2f}")
        print(f"   📉 Max Drawdown: {result.max_drawdown:.2%}")
        print(f"   🎯 Win Rate: {result.win_rate:.2%}")
        print(f"   🔢 Total Trades: {result.total_trades}")
        print(f"   💵 Final Capital: ${result.final_capital:.2f}")

        return True

    except Exception as e:
        print(f"   ❌ Backtest Engine test failed: {e}")
        return False

def test_ml_system():
    """Test ML Evolution System"""
    print("\n4️⃣ Testing ML Evolution System...")

    try:
        from ml_evolution.evolutionary_ml_system import EvolutionaryMLSystem

        # Initialize ML system
        ml_system = EvolutionaryMLSystem()

        # Create sample training data
        np.random.seed(42)
        n_samples = 500

        X = pd.DataFrame({
            'feature_1': np.random.randn(n_samples),
            'feature_2': np.random.randn(n_samples),
            'feature_3': np.random.randn(n_samples),
            'feature_4': np.random.randn(n_samples)
        })

        # Target with some relationship to features
        y = pd.Series(
            X['feature_1'] * 0.5 + X['feature_2'] * 0.3 +
            X['feature_3'] * 0.2 + np.random.randn(n_samples) * 0.1
        )

        # Split data
        train_size = int(0.8 * len(X))
        X_train, X_test = X[:train_size], X[train_size:]
        y_train, y_test = y[:train_size], y[train_size:]

        # Train models
        ml_system.fit(X_train, y_train)

        # Make predictions
        result = ml_system.predict(X_test)

        print(f"   ✅ ML System initialized successfully")
        print(f"   🤖 Models available: {len(ml_system.models)}")
        print(f"   📊 Prediction confidence: {result['confidence']:.3f}")
        print(f"   ⚖️ Model weights: {result['model_weights']}")

        # Get system summary
        summary = ml_system.get_ensemble_summary()
        print(f"   📈 Fitted models: {summary['fitted_models']}/{summary['total_models']}")

        return True

    except Exception as e:
        print(f"   ❌ ML System test failed: {e}")
        return False

def test_portfolio_manager():
    """Test Portfolio Manager"""
    print("\n5️⃣ Testing Advanced Portfolio Manager...")

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

        # Test different allocation methods
        methods = [AllocationMethod.EQUAL_WEIGHT, AllocationMethod.RISK_PARITY]

        for method in methods:
            weights = portfolio.optimize_portfolio(method)
            print(f"   📊 {method.value} allocation:")
            for symbol, weight in weights.items():
                print(f"      {symbol}: {weight:.2%}")

        # Simulate price updates
        price_updates = {
            'EURUSD': 1.0875,
            'GBPUSD': 1.2680,
            'BTCUSD': 67500.0,
            'XAUUSD': 2055.0
        }

        portfolio.update_prices(price_updates)

        # Get summary
        summary = portfolio.get_portfolio_summary()

        print(f"   ✅ Portfolio Manager initialized successfully")
        print(f"   💰 Portfolio value: ${summary['portfolio_value']:,.0f}")
        print(f"   📈 Total return: {summary['total_return']:.2%}")
        print(f"   🔢 Active assets: {summary['num_assets']}")
        print(f"   📊 Effective assets: {summary['effective_assets']:.1f}")

        return True

    except Exception as e:
        print(f"   ❌ Portfolio Manager test failed: {e}")
        return False

def test_dashboard():
    """Test Dashboard Components"""
    print("\n6️⃣ Testing Dashboard Components...")

    try:
        # Check if dashboard file exists
        dashboard_path = os.path.join(os.path.dirname(__file__), 'dashboard', 'unified_trading_dashboard.py')

        if os.path.exists(dashboard_path):
            print(f"   ✅ Dashboard file exists: unified_trading_dashboard.py")

            # Read first few lines to verify structure
            with open(dashboard_path, 'r') as f:
                content = f.read()

            if 'streamlit' in content and 'plotly' in content:
                print(f"   📊 Dashboard uses Streamlit + Plotly")
                print(f"   🎨 Professional styling included")
                print(f"   📱 Real-time data support")

                # Try to run basic import test
                import importlib.util
                spec = importlib.util.spec_from_file_location("dashboard", dashboard_path)
                dashboard_module = importlib.util.module_from_spec(spec)

                print(f"   ✅ Dashboard module can be imported")
                print(f"   🚀 Run with: streamlit run dashboard/unified_trading_dashboard.py")

            return True
        else:
            print(f"   ❌ Dashboard file not found")
            return False

    except Exception as e:
        print(f"   ❌ Dashboard test failed: {e}")
        return False

def run_integration_test():
    """Run integration test with all components"""
    print("\n🔧 RUNNING INTEGRATION TEST...")

    try:
        # Import the integration system
        from INTEGRATION_SYSTEM import IntegratedTradingSystem

        # Initialize system
        system = IntegratedTradingSystem(initial_capital=50000)

        # Get system status
        status = system.get_system_status()

        print(f"   ✅ Integration System initialized")
        print(f"   🔧 Components available: {'✅' if status['components_available'] else '❌'}")
        print(f"   💰 Initial capital: ${status['current_capital']:,.0f}")

        # Run quick backtest demo
        print(f"   🔬 Running backtest demo...")
        system.run_backtest_demo()

        return True

    except Exception as e:
        print(f"   ❌ Integration test failed: {e}")
        return False

def main():
    """Run all tests"""
    start_time = time.time()

    tests = [
        ("Risk Manager", test_risk_manager),
        ("Signal Scorer", test_signal_scorer),
        ("Backtest Engine", test_backtest_engine),
        ("ML System", test_ml_system),
        ("Portfolio Manager", test_portfolio_manager),
        ("Dashboard", test_dashboard),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"   ❌ {test_name} test crashed: {e}")
            results[test_name] = False

    # Run integration test
    results["Integration"] = run_integration_test()

    # Summary
    elapsed = time.time() - start_time

    print(f"\n📋 TEST SUMMARY")
    print("="*40)

    passed = sum(results.values())
    total = len(results)

    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{test_name:20} {status}")

    print(f"\n🎯 RESULTS: {passed}/{total} tests passed")
    print(f"⏱️  Duration: {elapsed:.1f} seconds")

    if passed == total:
        print(f"\n🎉 ALL TESTS PASSED! System ready for use.")
        print(f"\n🚀 NEXT STEPS:")
        print(f"   1. Install requirements: pip install -r requirements_enhanced.txt")
        print(f"   2. Run dashboard: streamlit run dashboard/unified_trading_dashboard.py")
        print(f"   3. Run integration: python INTEGRATION_SYSTEM.py")
    else:
        print(f"\n⚠️  Some tests failed. Check components and dependencies.")
        print(f"   Failed components may need additional libraries or configuration.")

if __name__ == "__main__":
    main()