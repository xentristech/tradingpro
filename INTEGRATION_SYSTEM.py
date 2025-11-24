"""
Integrated Trading System with All Enhanced Components
Author: Trading Pro System
Version: 3.0
"""

import numpy as np
import pandas as pd
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import time
import json
import sys
import os

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'backtesting', 'core'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'ml_evolution'))

# Import our enhanced components
try:
    from src.risk.enhanced_risk_manager import EnhancedRiskManager, RiskLevel
    from src.signals.signal_scoring_system import SignalScoringSystem, SignalType
    from src.portfolio.advanced_portfolio_manager import AdvancedPortfolioManager, AssetInfo, AllocationMethod
    from backtesting.core.backtest_engine import BacktestEngine, BacktestConfig
    from ml_evolution.evolutionary_ml_system import EvolutionaryMLSystem, ModelConfig, ModelType

    COMPONENTS_AVAILABLE = True
    print("✅ All enhanced components loaded successfully")
except ImportError as e:
    COMPONENTS_AVAILABLE = False
    print(f"❌ Component import failed: {e}")
    print("Running in demo mode with mock components...")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('integrated_system.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


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

    def get_market_data(self, symbol: str, timeframe: str = '1h', bars: int = 100) -> pd.DataFrame:
        """Generate mock OHLCV data"""
        end_time = datetime.now()
        if timeframe == '1h':
            freq = 'H'
        elif timeframe == '1d':
            freq = 'D'
        else:
            freq = 'H'

        dates = pd.date_range(end=end_time, periods=bars, freq=freq)
        base_price = self.base_prices.get(symbol, 100.0)

        data = []
        current_price = base_price

        for date in dates:
            # Random walk with some volatility
            change = np.random.normal(0, 0.01)  # 1% volatility
            current_price *= (1 + change)

            high = current_price * (1 + abs(np.random.normal(0, 0.005)))
            low = current_price * (1 - abs(np.random.normal(0, 0.005)))
            open_price = current_price * (1 + np.random.normal(0, 0.002))
            close = current_price
            volume = np.random.exponential(1000000)

            data.append({
                'timestamp': date,
                'open': open_price,
                'high': high,
                'low': low,
                'close': close,
                'volume': volume
            })

        df = pd.DataFrame(data)
        df.set_index('timestamp', inplace=True)
        return df


class IntegratedTradingSystem:
    """
    Integrated trading system combining all enhanced components
    """

    def __init__(self, initial_capital: float = 50000):
        """Initialize the integrated trading system"""
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.data_provider = MockDataProvider()

        # System status
        self.is_running = False
        self.last_update = None
        self.system_stats = {
            'signals_generated': 0,
            'trades_executed': 0,
            'positions_managed': 0,
            'risk_checks': 0,
            'ml_predictions': 0
        }

        # Initialize components if available
        if COMPONENTS_AVAILABLE:
            self._initialize_components()
        else:
            self._initialize_mock_components()

        logger.info("Integrated Trading System initialized successfully")

    def _initialize_components(self):
        """Initialize all enhanced components"""

        # 1. Risk Manager with Kelly Criterion
        self.risk_manager = EnhancedRiskManager(
            account_balance=self.initial_capital,
            max_risk_per_trade=0.02
        )
        self.risk_manager.set_risk_level('MODERATE')

        # 2. Signal Scoring System
        self.signal_scorer = SignalScoringSystem()

        # 3. Portfolio Manager
        self.portfolio_manager = AdvancedPortfolioManager(
            initial_capital=self.initial_capital
        )

        # Add assets to portfolio
        assets = [
            AssetInfo('EURUSD', 'Forex', 'Major', 'EU', current_price=1.0850),
            AssetInfo('GBPUSD', 'Forex', 'Major', 'GB', current_price=1.2650),
            AssetInfo('BTCUSD', 'Crypto', 'Digital Assets', 'US', current_price=67000.0),
            AssetInfo('XAUUSD', 'Commodity', 'Precious Metals', 'US', current_price=2050.0)
        ]

        for asset in assets:
            self.portfolio_manager.add_asset(asset)

        # 4. Machine Learning System
        self.ml_system = EvolutionaryMLSystem()

        # 5. Backtesting Engine
        self.backtest_config = BacktestConfig(
            initial_capital=self.initial_capital,
            commission_rate=0.001,
            slippage_rate=0.0005,
            risk_per_trade=0.02
        )
        self.backtest_engine = BacktestEngine(self.backtest_config)

        logger.info("All enhanced components initialized")

    def _initialize_mock_components(self):
        """Initialize mock components for demo"""
        self.risk_manager = None
        self.signal_scorer = None
        self.portfolio_manager = None
        self.ml_system = None
        self.backtest_engine = None

        logger.info("Mock components initialized for demo mode")

    def start_system(self):
        """Start the integrated trading system"""
        self.is_running = True
        logger.info("🚀 Starting Integrated Trading System")

        # Perform initial setup
        self._initial_system_check()

        # Start main loop
        asyncio.run(self._main_loop())

    def stop_system(self):
        """Stop the trading system"""
        self.is_running = False
        logger.info("🛑 Stopping Integrated Trading System")

    def _initial_system_check(self):
        """Perform initial system health check"""
        logger.info("🔧 Performing initial system check...")

        checks = {
            'Risk Manager': self.risk_manager is not None,
            'Signal Scorer': self.signal_scorer is not None,
            'Portfolio Manager': self.portfolio_manager is not None,
            'ML System': self.ml_system is not None,
            'Backtest Engine': self.backtest_engine is not None,
            'Data Provider': self.data_provider is not None
        }

        for component, status in checks.items():
            status_emoji = "✅" if status else "❌"
            logger.info(f"{status_emoji} {component}: {'OK' if status else 'MISSING'}")

        if all(checks.values()):
            logger.info("✅ All system components ready")
        else:
            logger.warning("⚠️ Some components missing - running in limited mode")

    async def _main_loop(self):
        """Main system loop"""
        logger.info("🔄 Starting main system loop")

        cycle_count = 0

        while self.is_running:
            try:
                cycle_start = time.time()
                cycle_count += 1

                logger.info(f"📊 Cycle {cycle_count} - Analyzing markets...")

                # 1. Update market data
                await self._update_market_data()

                # 2. Generate and score signals
                signals = await self._generate_signals()

                # 3. ML predictions
                ml_predictions = await self._get_ml_predictions()

                # 4. Risk assessment
                risk_metrics = await self._assess_risk()

                # 5. Portfolio optimization
                await self._optimize_portfolio()

                # 6. Execute trades (simulated)
                executed_trades = await self._execute_trades(signals, ml_predictions, risk_metrics)

                # 7. Update system stats
                self._update_stats(signals, executed_trades, risk_metrics)

                # 8. Log cycle summary
                cycle_time = time.time() - cycle_start
                self._log_cycle_summary(cycle_count, cycle_time, signals, executed_trades)

                # Wait before next cycle (60 seconds)
                await asyncio.sleep(60)

            except Exception as e:
                logger.error(f"❌ Error in main loop: {e}")
                await asyncio.sleep(5)  # Short wait before retry

    async def _update_market_data(self):
        """Update market data for all symbols"""
        try:
            for symbol in self.data_provider.symbols:
                data = self.data_provider.get_market_data(symbol, '1h', 100)

                # Update current prices
                current_price = data['close'].iloc[-1]

                if COMPONENTS_AVAILABLE and self.portfolio_manager:
                    if symbol in self.portfolio_manager.assets:
                        self.portfolio_manager.assets[symbol].current_price = current_price

            self.last_update = datetime.now()

        except Exception as e:
            logger.error(f"Error updating market data: {e}")

    async def _generate_signals(self) -> List[Dict]:
        """Generate and score trading signals"""
        signals = []

        try:
            for symbol in self.data_provider.symbols:
                data = self.data_provider.get_market_data(symbol, '1h', 100)

                if COMPONENTS_AVAILABLE and self.signal_scorer:
                    # Use real signal scoring system
                    signal_result = self.signal_scorer.calculate_signal_score(data)

                    if signal_result.overall_score > 60 or signal_result.overall_score < 40:
                        signals.append({
                            'symbol': symbol,
                            'signal_type': signal_result.signal_type.value,
                            'score': signal_result.overall_score,
                            'confidence': signal_result.confidence,
                            'strength': signal_result.strength,
                            'risk_reward': signal_result.risk_reward_ratio,
                            'timestamp': datetime.now(),
                            'reasoning': signal_result.reasoning
                        })
                else:
                    # Mock signal generation
                    if np.random.random() > 0.8:  # 20% chance
                        signal_type = np.random.choice(['BUY', 'SELL'])
                        score = np.random.uniform(30, 90)

                        signals.append({
                            'symbol': symbol,
                            'signal_type': signal_type,
                            'score': score,
                            'confidence': np.random.uniform(0.6, 0.9),
                            'strength': np.random.uniform(0.5, 0.8),
                            'risk_reward': np.random.uniform(1.5, 3.0),
                            'timestamp': datetime.now(),
                            'reasoning': ['Mock signal for demo']
                        })

            self.system_stats['signals_generated'] += len(signals)

        except Exception as e:
            logger.error(f"Error generating signals: {e}")

        return signals

    async def _get_ml_predictions(self) -> Dict:
        """Get ML predictions for market direction"""
        predictions = {}

        try:
            if COMPONENTS_AVAILABLE and self.ml_system:
                # Create sample features for ML prediction
                for symbol in self.data_provider.symbols:
                    data = self.data_provider.get_market_data(symbol, '1h', 50)

                    # Simple feature engineering
                    features = pd.DataFrame({
                        'rsi': self._calculate_rsi(data['close']),
                        'returns': data['close'].pct_change(),
                        'volume_ratio': data['volume'] / data['volume'].rolling(20).mean(),
                        'volatility': data['close'].pct_change().rolling(20).std()
                    }).fillna(0)

                    if len(features) > 10:
                        # Use only last row for prediction
                        X = features.tail(1)

                        try:
                            result = self.ml_system.predict(X, use_ensemble=True)
                            predictions[symbol] = {
                                'direction': 'BUY' if result['ensemble_prediction'][0] > 0 else 'SELL',
                                'confidence': result['confidence'],
                                'prediction_value': result['ensemble_prediction'][0]
                            }
                        except:
                            # ML system not trained or failed
                            predictions[symbol] = {
                                'direction': 'NEUTRAL',
                                'confidence': 0.5,
                                'prediction_value': 0.0
                            }
            else:
                # Mock ML predictions
                for symbol in self.data_provider.symbols:
                    predictions[symbol] = {
                        'direction': np.random.choice(['BUY', 'SELL', 'NEUTRAL']),
                        'confidence': np.random.uniform(0.5, 0.9),
                        'prediction_value': np.random.uniform(-0.02, 0.02)
                    }

            self.system_stats['ml_predictions'] += len(predictions)

        except Exception as e:
            logger.error(f"Error getting ML predictions: {e}")

        return predictions

    async def _assess_risk(self) -> Dict:
        """Assess current risk levels"""
        risk_metrics = {}

        try:
            if COMPONENTS_AVAILABLE and self.risk_manager:
                risk_metrics = self.risk_manager.get_risk_metrics()
            else:
                # Mock risk metrics
                risk_metrics = {
                    'kelly_fraction': np.random.uniform(0.01, 0.05),
                    'current_heat': np.random.uniform(0.02, 0.08),
                    'max_heat': 0.06,
                    'sharpe_ratio': np.random.uniform(1.0, 2.5),
                    'win_rate': np.random.uniform(0.55, 0.75),
                    'max_drawdown': np.random.uniform(0.05, 0.15),
                    'var_95': np.random.uniform(-0.03, -0.01),
                    'positions_count': np.random.randint(0, 5)
                }

            self.system_stats['risk_checks'] += 1

        except Exception as e:
            logger.error(f"Error assessing risk: {e}")

        return risk_metrics

    async def _optimize_portfolio(self):
        """Optimize portfolio allocation"""
        try:
            if COMPONENTS_AVAILABLE and self.portfolio_manager:
                # Update prices
                prices = {}
                for symbol in self.data_provider.symbols:
                    data = self.data_provider.get_market_data(symbol, '1h', 10)
                    prices[symbol] = data['close'].iloc[-1]

                self.portfolio_manager.update_prices(prices)

                # Rebalance if needed (this will check internally)
                # The portfolio manager handles its own rebalancing logic

        except Exception as e:
            logger.error(f"Error optimizing portfolio: {e}")

    async def _execute_trades(self, signals: List[Dict], ml_predictions: Dict, risk_metrics: Dict) -> List[Dict]:
        """Execute trades based on signals, ML predictions, and risk assessment"""
        executed_trades = []

        try:
            for signal in signals:
                symbol = signal['symbol']

                # Check if we should execute this trade
                should_execute = self._should_execute_trade(signal, ml_predictions.get(symbol), risk_metrics)

                if should_execute:
                    # Calculate position size
                    position_size = self._calculate_position_size(signal, risk_metrics)

                    if position_size > 0:
                        # Simulate trade execution
                        trade = {
                            'symbol': symbol,
                            'side': signal['signal_type'],
                            'size': position_size,
                            'price': self.data_provider.base_prices[symbol],
                            'timestamp': datetime.now(),
                            'signal_score': signal['score'],
                            'ml_confidence': ml_predictions.get(symbol, {}).get('confidence', 0.5),
                            'risk_score': risk_metrics.get('kelly_fraction', 0.02)
                        }

                        executed_trades.append(trade)

                        # Update system state
                        if COMPONENTS_AVAILABLE and self.risk_manager:
                            # Add trade to risk manager history
                            trade_record = {
                                'pnl': np.random.uniform(-100, 200),  # Simulated P&L
                                'returns': np.random.uniform(-0.02, 0.03),
                                'timestamp': datetime.now()
                            }
                            self.risk_manager.add_trade(trade_record)

            self.system_stats['trades_executed'] += len(executed_trades)

        except Exception as e:
            logger.error(f"Error executing trades: {e}")

        return executed_trades

    def _should_execute_trade(self, signal: Dict, ml_prediction: Optional[Dict], risk_metrics: Dict) -> bool:
        """Determine if a trade should be executed"""

        # Check signal strength
        if signal['confidence'] < 0.6:
            return False

        # Check ML agreement (if available)
        if ml_prediction:
            ml_agrees = (
                (signal['signal_type'] == 'BUY' and ml_prediction['direction'] == 'BUY') or
                (signal['signal_type'] == 'SELL' and ml_prediction['direction'] == 'SELL')
            )

            if not ml_agrees and ml_prediction['confidence'] > 0.7:
                return False  # ML strongly disagrees

        # Check risk limits
        current_heat = risk_metrics.get('current_heat', 0)
        max_heat = risk_metrics.get('max_heat', 0.06)

        if current_heat >= max_heat * 0.8:  # 80% of max heat
            return False

        # Check portfolio heat
        positions_count = risk_metrics.get('positions_count', 0)
        if positions_count >= 5:  # Max 5 positions
            return False

        return True

    def _calculate_position_size(self, signal: Dict, risk_metrics: Dict) -> float:
        """Calculate position size for a trade"""

        if COMPONENTS_AVAILABLE and self.risk_manager:
            # Use enhanced risk manager
            signal_dict = {
                'entry_price': self.data_provider.base_prices[signal['symbol']],
                'stop_loss': self.data_provider.base_prices[signal['symbol']] * 0.98,
                'take_profit': self.data_provider.base_prices[signal['symbol']] * 1.03,
                'strength': signal['strength'],
                'ml_confidence': signal.get('ml_confidence', 0.7)
            }

            try:
                result = self.risk_manager.calculate_position_size(signal_dict, method='kelly')
                return result.position_size
            except:
                pass

        # Fallback calculation
        kelly_fraction = risk_metrics.get('kelly_fraction', 0.02)
        risk_amount = self.current_capital * kelly_fraction
        entry_price = self.data_provider.base_prices[signal['symbol']]

        if entry_price > 0:
            return risk_amount / entry_price

        return 0

    def _update_stats(self, signals: List[Dict], executed_trades: List[Dict], risk_metrics: Dict):
        """Update system statistics"""
        # Update portfolio positions count
        if executed_trades:
            self.system_stats['positions_managed'] += len(executed_trades)

    def _log_cycle_summary(self, cycle: int, cycle_time: float, signals: List[Dict], executed_trades: List[Dict]):
        """Log summary of the current cycle"""

        logger.info(f"📈 Cycle {cycle} Summary:")
        logger.info(f"   ⏱️  Execution time: {cycle_time:.2f}s")
        logger.info(f"   🎯 Signals generated: {len(signals)}")
        logger.info(f"   💼 Trades executed: {len(executed_trades)}")

        if signals:
            avg_score = np.mean([s['score'] for s in signals])
            logger.info(f"   📊 Average signal score: {avg_score:.1f}")

        if executed_trades:
            logger.info(f"   🔄 Active trades: {len(executed_trades)}")
            for trade in executed_trades:
                logger.info(f"      {trade['symbol']} {trade['side']} - Size: {trade['size']:.4f}")

        # System stats summary
        logger.info(f"📋 System Stats:")
        logger.info(f"   Total signals: {self.system_stats['signals_generated']}")
        logger.info(f"   Total trades: {self.system_stats['trades_executed']}")
        logger.info(f"   Risk checks: {self.system_stats['risk_checks']}")
        logger.info(f"   ML predictions: {self.system_stats['ml_predictions']}")

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50)

    def run_backtest_demo(self):
        """Run a demonstration backtest"""
        logger.info("🔬 Running Backtesting Demo...")

        if not COMPONENTS_AVAILABLE or not self.backtest_engine:
            logger.warning("Backtest engine not available - showing mock results")
            self._show_mock_backtest_results()
            return

        # Generate sample data for backtesting
        sample_data = self.data_provider.get_market_data('BTCUSD', '1d', 252)  # 1 year

        def sample_strategy(bar_data, positions, capital, timestamp):
            """Simple moving average strategy for demo"""
            signals = []

            if isinstance(bar_data, pd.DataFrame):
                close = bar_data['close'].iloc[0]
            else:
                close = bar_data['close']

            # Simple logic: random entry with 5% probability
            if np.random.random() > 0.95 and not positions:
                signals.append({
                    'side': 'BUY',
                    'order_type': 'MARKET',
                    'stop_loss': close * 0.95,
                    'take_profit': close * 1.05,
                    'metadata': {'strategy': 'Demo_Strategy'}
                })
            elif positions and np.random.random() > 0.98:
                signals.append({
                    'side': 'SELL',
                    'order_type': 'MARKET',
                    'metadata': {'strategy': 'Demo_Strategy', 'reason': 'Exit'}
                })

            return signals

        try:
            # Run backtest
            result = self.backtest_engine.run(sample_data, sample_strategy)

            # Display results
            logger.info("📊 Backtest Results:")
            logger.info(f"   Total Return: {result.total_return:.2%}")
            logger.info(f"   Annual Return: {result.annual_return:.2%}")
            logger.info(f"   Sharpe Ratio: {result.sharpe_ratio:.2f}")
            logger.info(f"   Max Drawdown: {result.max_drawdown:.2%}")
            logger.info(f"   Win Rate: {result.win_rate:.2%}")
            logger.info(f"   Total Trades: {result.total_trades}")
            logger.info(f"   Profit Factor: {result.profit_factor:.2f}")

        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            self._show_mock_backtest_results()

    def _show_mock_backtest_results(self):
        """Show mock backtest results for demo"""
        logger.info("📊 Mock Backtest Results:")
        logger.info(f"   Total Return: {np.random.uniform(0.05, 0.25):.2%}")
        logger.info(f"   Annual Return: {np.random.uniform(0.08, 0.30):.2%}")
        logger.info(f"   Sharpe Ratio: {np.random.uniform(1.2, 2.5):.2f}")
        logger.info(f"   Max Drawdown: {np.random.uniform(0.05, 0.15):.2%}")
        logger.info(f"   Win Rate: {np.random.uniform(0.55, 0.75):.2%}")
        logger.info(f"   Total Trades: {np.random.randint(50, 200)}")
        logger.info(f"   Profit Factor: {np.random.uniform(1.2, 2.0):.2f}")

    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        return {
            'is_running': self.is_running,
            'last_update': self.last_update,
            'current_capital': self.current_capital,
            'components_available': COMPONENTS_AVAILABLE,
            'system_stats': self.system_stats.copy(),
            'risk_metrics': asyncio.run(self._assess_risk()) if self.is_running else {},
            'timestamp': datetime.now()
        }


def main():
    """Main function to run the integrated system"""

    print("🚀 TRADING PRO - INTEGRATED SYSTEM v3.0")
    print("="*60)

    # Initialize system
    trading_system = IntegratedTradingSystem(initial_capital=50000)

    # Show system status
    status = trading_system.get_system_status()
    print(f"\n📋 System Status:")
    print(f"   Components Available: {'✅' if status['components_available'] else '❌'}")
    print(f"   Initial Capital: ${status['current_capital']:,.0f}")

    try:
        # Run backtest demo first
        print(f"\n🔬 Running Backtest Demo...")
        trading_system.run_backtest_demo()

        print(f"\n🎯 Starting Live Trading Simulation...")
        print(f"   Press Ctrl+C to stop")

        # Start the main system (will run for demonstration)
        trading_system.start_system()

    except KeyboardInterrupt:
        print(f"\n🛑 System stopped by user")
        trading_system.stop_system()

    except Exception as e:
        print(f"\n❌ System error: {e}")

    finally:
        # Final status
        final_status = trading_system.get_system_status()
        print(f"\n📊 Final System Statistics:")
        for key, value in final_status['system_stats'].items():
            print(f"   {key.replace('_', ' ').title()}: {value}")


if __name__ == "__main__":
    main()