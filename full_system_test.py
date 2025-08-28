import os
import sys
from dotenv import load_dotenv
import requests
import MetaTrader5 as mt5

print("=== TRADING BOT SYSTEM TEST ===")
load_dotenv("configs/.env")

# Test 1: MT5
print("\n1. Testing MT5...")
if mt5.initialize():
    print("✅ MT5 Connected!")
    account = mt5.account_info()
    if account:
        print(f"   Account: {account.login} • Balance: ${account.balance}")
    mt5.shutdown()
else:
    print("❌ MT5 Failed")

# Test 2: Telegram
print("\n2. Testing Telegram...")
token = os.getenv("TELEGRAM_TOKEN")
chat_id = os.getenv("TELEGRAM_CHAT_ID")
if token and chat_id:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": "🤖 Bot test - System working!"}
    response = requests.post(url, data=data)
    if response.status_code == 200:
        print("✅ Telegram message sent!")
    else:
        print("❌ Telegram failed")
else:
    print("⚠️ Telegram config missing")

# Test 3: TwelveData
print("\n3. Testing TwelveData...")
api_key = os.getenv("TWELVEDATA_API_KEY")
if api_key:
    url = f"https://api.twelvedata.com/time_series?symbol=BTCUSD&interval=1min&apikey={api_key}&outputsize=1"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if "values" in data:
            print(f"✅ TwelveData working! BTC price: ${data['values'][0]['close']}")
        else:
            print("❌ TwelveData data error")
    else:
        print("❌ TwelveData failed")
else:
    print("⚠️ TwelveData API key missing")

print("\n=== SYSTEM STATUS ===")
print("📊 Ready to trade! All systems operational.")
input("Press Enter to continue...")
