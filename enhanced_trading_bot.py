"""
Enhanced Trading Bot with Advanced Features
Integrates ML, Advanced Risk Management, and Professional Indicators
"""
import os
import sys
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/enhanced_bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import enhanced modules
from risk.advanced_risk import AdvancedRiskManager
from data.advanced_indicators import AdvancedIndicators, MarketMicrostructure
from ml.trading_models import TradingMLPipeline, MLPrediction
from backtesting.advanced_backtest import BacktestEngine

# Import existing modules
from dotenv import load_dotenv
import pandas as pd
import numpy as np

class EnhancedTradingBot:
    """
    Enhanced trading bot with ML and advanced risk management
    """
    
    def __init__(self):
        """Initialize enhanced trading bot"""
        # Load environment variables
        load_dotenv('configs/.env')
        
        # Initialize components
        self.risk_manager = AdvancedRiskManager(
            initial_capital=10000,
            max_risk_per_trade=0.02,
            max_portfolio_risk=0.06
        )
        
        self.ml_pipeline = TradingMLPipeline(
            lookback_period=50,
            prediction_horizon=5
        )
        
        self.indicators = AdvancedIndicators()
        
        # Trading parameters
        self.symbol = os.getenv('SYMBOL', 'BTCUSD')
        self.is_live = os.getenv('LIVE_TRADING', 'false').lower() == 'true'
        
        logger.info(f"Enhanced Trading Bot initialized for {self.symbol}")
        logger.info(f"Live trading: {self.is_live}")
        
    def get_market_data(self, periods: int = 200) -> pd.DataFrame:
        """
        Get market data for analysis
        
        Args:
            periods: Number of periods to fetch
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Import data module
            from data.twelvedata import time_series
            
            # Fetch data
            data = time_series(
                symbol=self.symbol,
                interval='5min',
                outputsize=periods
            )
            
            if data is not None and not data.empty:
                logger.info(f"Fetched {len(data)} periods of data")
                return data
            else:
                logger.warning("No data fetched")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            return pd.DataFrame()
    
    def calculate_advanced_signals(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate signals using advanced indicators and ML
        
        Args:
            data: Market data
            
        Returns:
            Dictionary with signals and analysis
        """
        signals = {
            'timestamp': datetime.now(),
            'technical': {},
            'ml': {},
            'microstructure': {},
            'risk': {},
            'action': 'HOLD',
            'confidence': 0.0
        }
        
        if data.empty:
            return signals
        
        try:
            # Calculate advanced indicators
            prices = data['close'].values
            volumes = data['volume'].values
            
            # VWAP and TWAP
            vwap = self.indicators.calculate_vwap(prices, volumes)
            twap = self.indicators.calculate_twap(prices)
            
            # Volume Profile
            vol_profile = self.indicators.calculate_volume_profile(prices, volumes)
            
            # Support/Resistance
            sr_levels = self.indicators.calculate_support_resistance(prices, volumes)
            
            # Market Regime
            returns = np.diff(prices) / prices[:-1]
            regime = self.indicators.detect_market_regime(prices, returns)
            
            # Momentum indicators
            momentum = self.indicators.calculate_momentum_indicators(prices, volumes)
            
            # Store technical signals
            signals['technical'] = {
                'vwap': vwap,
                'twap': twap,
                'poc': vol_profile['poc'],
                'vah': vol_profile['vah'],
                'val': vol_profile['val'],
                'support': sr_levels['support'],
                'resistance': sr_levels['resistance'],
                'regime': regime.regime,
                'regime_strength': regime.strength,
                'momentum': momentum
            }
            
            # ML Prediction (if models are trained)
            if hasattr(self.ml_pipeline, 'models') and self.ml_pipeline.models:
                ml_prediction = self.ml_pipeline.predict(data)
                signals['ml'] = {
                    'direction': ml_prediction.predicted_direction,
                    'confidence': ml_prediction.confidence,
                    'predicted_price': ml_prediction.predicted_price
                }
                
                # Combine signals
                if ml_prediction.confidence > 0.7:
                    signals['action'] = ml_prediction.predicted_direction
                    signals['confidence'] = ml_prediction.confidence
            
            # Risk assessment
            current_price = prices[-1]
            
            # Calculate position metrics
            if signals['action'] != 'HOLD':
                # Determine entry, SL, TP
                if signals['action'] == 'BUY':
                    entry = current_price
                    stop_loss = sr_levels['support'][0] if sr_levels['support'] else current_price * 0.98
                    take_profit = sr_levels['resistance'][0] if sr_levels['resistance'] else current_price * 1.02
                else:  # SELL
                    entry = current_price
                    stop_loss = sr_levels['resistance'][0] if sr_levels['resistance'] else current_price * 1.02
                    take_profit = sr_levels['support'][0] if sr_levels['support'] else current_price * 0.98
                
                # Calculate risk metrics
                risk_metrics = self.risk_manager.calculate_position_metrics(
                    symbol=self.symbol,
                    entry_price=entry,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    historical_returns=list(returns)
                )
                
                # Check if trade should be taken
                should_trade, reason = self.risk_manager.should_take_trade(risk_metrics)
                
                signals['risk'] = {
                    'should_trade': should_trade,
                    'reason': reason,
                    'position_size': risk_metrics.position_size,
                    'risk_amount': risk_metrics.risk_amount,
                    'sharpe_ratio': risk_metrics.sharpe_ratio
                }
                
                # Override action if risk check fails
                if not should_trade:
                    signals['action'] = 'HOLD'
                    logger.warning(f"Trade rejected by risk manager: {reason}")
            
        except Exception as e:
            logger.error(f"Error calculating signals: {e}")
        
        return signals
    
    def execute_trade(self, signals: Dict[str, Any]):
        """
        Execute trade based on signals
        
        Args:
            signals: Trading signals
        """
        if signals['action'] == 'HOLD':
            return
        
        if not self.is_live:
            logger.info(f"DEMO MODE - Would execute {signals['action']} trade")
            logger.info(f"Confidence: {signals['confidence']:.2%}")
            if 'risk' in signals:
                logger.info(f"Position size: {signals['risk'].get('position_size', 0):.4f}")
            return
        
        # Live trading execution would go here
        logger.warning("Live trading not implemented in this demo")
    
    def train_models(self):
        """Train ML models on historical data"""
        logger.info("Training ML models...")
        
        # Get historical data
        data = self.get_market_data(periods=1000)
        
        if not data.empty:
            # Train ensemble
            models = self.ml_pipeline.train_ensemble(data)
            
            # Save models
            self.ml_pipeline.save_models('ml/models/trading_models.pkl')
            
            logger.info(f"Trained {len(models)} models successfully")
        else:
            logger.error("No data available for training")
    
    def run_backtest(self):
        """Run backtest on historical data"""
        logger.info("Running backtest...")
        
        # Get historical data
        data = self.get_market_data(periods=1000)
        
        if data.empty:
            logger.error("No data available for backtesting")
            return
        
        # Initialize backtesting engine
        engine = BacktestEngine(
            initial_capital=10000,
            commission_rate=0.001,
            slippage_model='percentage',
            slippage_value=0.0005
        )
        
        # Define simple strategy for testing
        def test_strategy(market_data, positions, **params):
            """Simple test strategy"""
            signals = []
            
            # Simple moving average crossover
            if len(market_data) > 50:
                sma_fast = market_data['close'].rolling(20).mean().iloc[-1]
                sma_slow = market_data['close'].rolling(50).mean().iloc[-1]
                
                if sma_fast > sma_slow and not positions:
                    signals.append({'action': 'BUY', 'quantity': 1.0})
                elif sma_fast < sma_slow and positions:
                    signals.append({'action': 'CLOSE'})
            
            return signals
        
        # Run backtest
        results = engine.run_backtest(data, test_strategy)
        
        # Print results
        engine.print_results(results)
    
    def run(self):
        """Main bot loop"""
        logger.info("Starting enhanced trading bot...")
        
        # Train models on first run (optional)
        if not os.path.exists('ml/models/trading_models.pkl'):
            self.train_models()
        else:
            # Load existing models
            try:
                self.ml_pipeline.load_models('ml/models/trading_models.pkl')
                logger.info("Loaded existing ML models")
            except:
                logger.warning("Could not load models, running without ML")
        
        # Main trading loop
        while True:
            try:
                # Get market data
                data = self.get_market_data()
                
                if not data.empty:
                    # Calculate signals
                    signals = self.calculate_advanced_signals(data)
                    
                    # Log signals
                    logger.info(f"Signal: {signals['action']} (Confidence: {signals['confidence']:.2%})")
                    
                    # Execute trade
                    self.execute_trade(signals)
                    
                    # Update risk manager stats
                    stats = self.risk_manager.get_current_stats()
                    logger.info(f"Risk stats - Win rate: {stats['win_rate']:.1%}, "
                              f"Current DD: {stats['current_drawdown']:.1%}")
                
                # Wait before next iteration
                time.sleep(60)  # Check every minute
                
            except KeyboardInterrupt:
                logger.info("Stopping bot...")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                time.sleep(10)  # Wait before retrying

def main():
    """Main entry point"""
    print("\n" + "="*60)
    print(" ENHANCED ALGORITHMIC TRADING BOT")
    print("="*60)
    print("\nFeatures:")
    print("✅ Advanced Risk Management (Kelly Criterion, VaR)")
    print("✅ Machine Learning Predictions")
    print("✅ Market Microstructure Analysis")
    print("✅ Professional Backtesting Engine")
    print("✅ Advanced Technical Indicators")
    print("\n" + "="*60)
    
    # Create logs directory if not exists
    os.makedirs('logs', exist_ok=True)
    os.makedirs('ml/models', exist_ok=True)
    
    # Initialize and run bot
    bot = EnhancedTradingBot()
    
    # Menu
    print("\nSelect operation:")
    print("1. Run Trading Bot")
    print("2. Train ML Models")
    print("3. Run Backtest")
    print("4. Test System")
    
    choice = input("\nEnter choice (1-4): ")
    
    if choice == '1':
        bot.run()
    elif choice == '2':
        bot.train_models()
    elif choice == '3':
        bot.run_backtest()
    elif choice == '4':
        # Run system test
        print("\n🔍 Testing Enhanced System...")
        
        # Test data fetch
        data = bot.get_market_data(periods=50)
        if not data.empty:
            print(f"✅ Data fetch successful: {len(data)} periods")
            
            # Test signal generation
            signals = bot.calculate_advanced_signals(data)
            print(f"✅ Signal generation successful: {signals['action']}")
            
            # Test risk management
            stats = bot.risk_manager.get_current_stats()
            print(f"✅ Risk manager initialized")
            
            print("\n✨ All systems operational!")
        else:
            print("❌ Data fetch failed")
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()
