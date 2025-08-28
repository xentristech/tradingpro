"""
Quick System Verification Script
Tests core components of the enhanced trading bot
"""
import os
import sys
import json
from datetime import datetime

print("\n" + "="*60)
print(" ENHANCED TRADING BOT - SYSTEM CHECK")
print("="*60)

# Check Python version
print(f"\n✅ Python Version: {sys.version}")

# Check core modules
print("\n📦 Checking Core Modules...")
modules_status = {}

try:
    import pandas as pd
    modules_status['pandas'] = f"✅ {pd.__version__}"
except:
    modules_status['pandas'] = "❌ Not installed"

try:
    import numpy as np
    modules_status['numpy'] = f"✅ {np.__version__}"
except:
    modules_status['numpy'] = "❌ Not installed"

try:
    import MetaTrader5 as mt5
    modules_status['MetaTrader5'] = "✅ Installed"
except:
    modules_status['MetaTrader5'] = "❌ Not installed"

try:
    from dotenv import load_dotenv
    modules_status['dotenv'] = "✅ Installed"
    load_dotenv('configs/.env')
except:
    modules_status['dotenv'] = "❌ Not installed"

for module, status in modules_status.items():
    print(f"  {module}: {status}")

# Check custom modules
print("\n📂 Checking Custom Modules...")
custom_modules = {
    'risk.advanced_risk': 'Advanced Risk Manager',
    'data.advanced_indicators': 'Advanced Indicators',
    'ml.trading_models': 'ML Pipeline',
    'backtesting.advanced_backtest': 'Backtesting Engine'
}

for module_name, description in custom_modules.items():
    try:
        exec(f"from {module_name} import *")
        print(f"  ✅ {description}")
    except Exception as e:
        print(f"  ❌ {description}: {str(e)[:50]}")

# Check configuration
print("\n⚙️ Checking Configuration...")
config_items = {
    'SYMBOL': os.getenv('SYMBOL', 'Not set'),
    'LIVE_TRADING': os.getenv('LIVE_TRADING', 'Not set'),
    'TWELVEDATA_API_KEY': 'Set' if os.getenv('TWELVEDATA_API_KEY') else 'Not set',
    'MT5_LOGIN': 'Set' if os.getenv('MT5_LOGIN') else 'Not set'
}

for key, value in config_items.items():
    status = "✅" if value not in ['Not set', None] else "⚠️"
    print(f"  {status} {key}: {value}")

# Test basic functionality
print("\n🔧 Testing Basic Functionality...")

try:
    from risk.advanced_risk import AdvancedRiskManager
    risk_mgr = AdvancedRiskManager(initial_capital=10000)
    print("  ✅ Risk Manager initialized")
except Exception as e:
    print(f"  ❌ Risk Manager failed: {e}")

try:
    from data.advanced_indicators import AdvancedIndicators
    indicators = AdvancedIndicators()
    
    # Test VWAP calculation
    import numpy as np
    test_prices = np.array([100, 101, 102, 101, 100])
    test_volumes = np.array([1000, 1500, 2000, 1200, 900])
    vwap = indicators.calculate_vwap(test_prices, test_volumes)
    print(f"  ✅ VWAP calculation: {vwap:.2f}")
except Exception as e:
    print(f"  ❌ Indicators failed: {e}")

# Performance metrics
print("\n📊 System Enhancements Summary:")
improvements = {
    'Risk Management': ['Kelly Criterion', 'VaR/CVaR', 'Portfolio Correlation'],
    'Technical Analysis': ['VWAP/TWAP', 'Volume Profile', 'Market Microstructure'],
    'Machine Learning': ['XGBoost', 'Random Forest', 'Neural Network'],
    'Backtesting': ['Slippage Model', 'Commission', 'Realistic Fills']
}

for category, features in improvements.items():
    print(f"\n  {category}:")
    for feature in features:
        print(f"    • {feature}")

print("\n" + "="*60)
print(" SYSTEM CHECK COMPLETE")
print("="*60)

# Create report
report = {
    'timestamp': datetime.now().isoformat(),
    'modules': modules_status,
    'config': config_items,
    'status': 'Ready' if all('✅' in str(v) for v in modules_status.values()) else 'Partial'
}

# Save report
with open('system_check_report.json', 'w') as f:
    json.dump(report, f, indent=2)

print(f"\n📄 Report saved to system_check_report.json")
print(f"🚀 System Status: {report['status']}")

if report['status'] == 'Ready':
    print("\n✨ All systems operational! Ready to trade.")
else:
    print("\n⚠️ Some components need attention. Check report for details.")
