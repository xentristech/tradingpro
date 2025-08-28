"""
DIRECT BOT EXECUTION - SIMPLIFIED
"""
import os
import sys
import time
from datetime import datetime

print("\n" + "="*60)
print("  ENHANCED TRADING BOT - STARTING NOW")
print("  Account: 197678662 (Exness)")
print("="*60)

# Set up path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment
print("\n1. Loading configuration...")
from dotenv import load_dotenv
load_dotenv('configs/.env')

print(f"   Account: {os.getenv('MT5_LOGIN')}")
print(f"   Symbol: {os.getenv('SYMBOL')}")
print(f"   Live: {os.getenv('LIVE_TRADING')}")

# Test MT5
print("\n2. Testing MT5 connection...")
try:
    import MetaTrader5 as mt5
    if mt5.initialize():
        account = mt5.account_info()
        if account:
            print(f"   ✅ Connected! Balance: ${account.balance:.2f}")
            mt5.shutdown()
        else:
            print("   ❌ Account info not available")
    else:
        print(f"   ❌ MT5 init failed: {mt5.last_error()}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test data source
print("\n3. Testing data source...")
try:
    import requests
    api_key = os.getenv('TWELVEDATA_API_KEY')
    r = requests.get(f'https://api.twelvedata.com/price?symbol=BTC/USD&apikey={api_key}')
    if r.status_code == 200:
        data = r.json()
        if 'price' in data:
            print(f"   ✅ BTC price: ${float(data['price']):,.2f}")
        else:
            print(f"   ❌ No price data")
    else:
        print(f"   ❌ API error: {r.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Send Telegram notification
print("\n4. Sending start notification...")
try:
    import requests
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    msg = f"""🤖 Trading Bot Starting

Account: 197678662
Time: {datetime.now().strftime('%H:%M:%S')}
Mode: {os.getenv('LIVE_TRADING')}

Initializing systems..."""
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    r = requests.post(url, data={'chat_id': chat_id, 'text': msg})
    if r.status_code == 200:
        print("   ✅ Telegram notification sent")
    else:
        print("   ❌ Telegram failed")
except:
    print("   ❌ Telegram error")

# Now run the main bot
print("\n5. Starting main trading loop...")
print("-"*60)
print("TRADING BOT ACTIVE - Press Ctrl+C to stop")
print("-"*60)

try:
    # Import the enhanced bot
    from enhanced_trading_bot import EnhancedTradingBot
    
    # Create bot instance
    bot = EnhancedTradingBot()
    
    # Run the bot
    bot.run()
    
except KeyboardInterrupt:
    print("\n\nBot stopped by user")
except ImportError as e:
    print(f"\n❌ Import error: {e}")
    print("\nTrying alternative approach...")
    
    # Try simpler approach
    from orchestrator.run import main as run_main
    run_main()
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()

print(f"\nBot stopped at {datetime.now().strftime('%H:%M:%S')}")
