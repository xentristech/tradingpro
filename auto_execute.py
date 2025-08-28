"""
AUTO-EXECUTE TRADING BOT
Starts the enhanced trading bot automatically
"""
import os
import sys
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/auto_execute.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

print("\n" + "="*70)
print("  ENHANCED TRADING BOT - AUTO EXECUTION")
print("  Account: 197678662 (Exness)")
print("="*70)

# Load environment
from dotenv import load_dotenv
load_dotenv('configs/.env')

# Log configuration
logger.info("Configuration loaded:")
logger.info(f"  Account: {os.getenv('MT5_LOGIN')}")
logger.info(f"  Server: {os.getenv('MT5_SERVER')}")
logger.info(f"  Symbol: {os.getenv('SYMBOL')}")
logger.info(f"  Live Trading: {os.getenv('LIVE_TRADING')}")

# Check if live trading
is_live = os.getenv('LIVE_TRADING', 'false').lower() == 'true'

if is_live:
    print("\n⚠️  WARNING: LIVE TRADING MODE ENABLED")
    print("   Real money at risk!")
    print("   Starting in 5 seconds... Press Ctrl+C to cancel")
    
    import time
    for i in range(5, 0, -1):
        print(f"   {i}...")
        time.sleep(1)
else:
    print("\n✅ DEMO MODE - No real money at risk")

print("\n🚀 Starting Enhanced Trading Bot...")
print("   Press Ctrl+C to stop at any time\n")

# Send Telegram notification
try:
    import requests
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    mode = "LIVE 🔴" if is_live else "DEMO 🟢"
    message = f"""
🤖 *Trading Bot Started*

Mode: {mode}
Account: {os.getenv('MT5_LOGIN')}
Server: {os.getenv('MT5_SERVER')}
Symbol: {os.getenv('SYMBOL')}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Risk per trade: {float(os.getenv('RISK_PER_TRADE', 0.01))*100:.1f}%
Stop Loss: ${os.getenv('DEF_SL_USD')}
Take Profit: ${os.getenv('DEF_TP_USD')}

{"⚠️ Real money at risk!" if is_live else "✅ Safe demo mode"}
"""
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    response = requests.post(url, data=data, timeout=5)
    
    if response.status_code == 200:
        print("✅ Telegram notification sent")
except Exception as e:
    print(f"⚠️  Telegram notification failed: {e}")

# Import and run the bot
try:
    logger.info("Importing Enhanced Trading Bot...")
    from enhanced_trading_bot import EnhancedTradingBot
    
    logger.info("Initializing bot...")
    bot = EnhancedTradingBot()
    
    logger.info("Starting main loop...")
    bot.run()
    
except KeyboardInterrupt:
    logger.info("Bot stopped by user (Ctrl+C)")
    print("\n\n✋ Trading bot stopped by user")
    
    # Send stop notification
    try:
        message = f"🛑 *Trading Bot Stopped*\n\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
        requests.post(url, data=data, timeout=5)
    except:
        pass
        
except Exception as e:
    logger.error(f"Critical error: {e}")
    print(f"\n❌ ERROR: {e}")
    
    # Send error notification
    try:
        message = f"❌ *Bot Error*\n\n{str(e)[:200]}"
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
        requests.post(url, data=data, timeout=5)
    except:
        pass
    
    import traceback
    traceback.print_exc()

finally:
    logger.info("Session ended")
    print(f"\n📊 Session ended at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Try to close MT5 connection
    try:
        import MetaTrader5 as mt5
        mt5.shutdown()
        logger.info("MT5 connection closed")
    except:
        pass
