"""
DIRECT LIVE TRADING EXECUTION
Execute trading bot with Exness account
"""
import os
import sys
import time
from datetime import datetime

# Add colors for visibility
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

print(f"\n{Colors.RED}{Colors.BOLD}")
print("="*70)
print("     LIVE TRADING BOT - EXNESS ACCOUNT 197678662")
print("="*70)
print(f"{Colors.RESET}")

# Load configuration
print(f"{Colors.YELLOW}Loading configuration...{Colors.RESET}")
from dotenv import load_dotenv
load_dotenv('configs/.env')

# Display configuration
print(f"\n{Colors.CYAN}📊 CONFIGURATION:{Colors.RESET}")
print(f"   Account:      {os.getenv('MT5_LOGIN')}")
print(f"   Server:       {os.getenv('MT5_SERVER')}")
print(f"   Symbol:       {os.getenv('SYMBOL')}")
print(f"   Live Trading: {os.getenv('LIVE_TRADING')}")
print(f"   Risk/Trade:   {float(os.getenv('RISK_PER_TRADE', 0.01))*100:.1f}%")
print(f"   Stop Loss:    ${os.getenv('DEF_SL_USD')}")
print(f"   Take Profit:  ${os.getenv('DEF_TP_USD')}")

# Test MT5 connection
print(f"\n{Colors.YELLOW}Testing MT5 connection...{Colors.RESET}")
try:
    import MetaTrader5 as mt5
    
    if mt5.initialize(
        path=os.getenv("MT5_PATH"),
        login=int(os.getenv("MT5_LOGIN")),
        password=os.getenv("MT5_PASSWORD"),
        server=os.getenv("MT5_SERVER"),
        timeout=60000
    ):
        account = mt5.account_info()
        if account:
            print(f"{Colors.GREEN}✅ MT5 Connected!{Colors.RESET}")
            print(f"   Balance:  ${account.balance:.2f}")
            print(f"   Equity:   ${account.equity:.2f}")
            print(f"   Company:  {account.company}")
            
            # Check if demo/trial
            server = os.getenv("MT5_SERVER").lower()
            if "trial" in server or "demo" in server:
                print(f"{Colors.GREEN}   Type: DEMO/TRIAL Account (Safe){Colors.RESET}")
            else:
                print(f"{Colors.RED}   Type: POSSIBLY REAL Account{Colors.RESET}")
        
        # Check symbol
        symbol = os.getenv("SYMBOL")
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info:
            print(f"\n{Colors.GREEN}✅ Symbol {symbol} available{Colors.RESET}")
            print(f"   Current Bid: {symbol_info.bid}")
            print(f"   Current Ask: {symbol_info.ask}")
        else:
            print(f"{Colors.RED}❌ Symbol {symbol} not found{Colors.RESET}")
            # Try to find crypto symbols
            symbols = mt5.symbols_get()
            crypto = [s.name for s in symbols if 'BTC' in s.name.upper() or 'CRYPTO' in s.name.upper()]
            if crypto:
                print(f"   Available: {', '.join(crypto[:5])}")
        
        mt5.shutdown()
    else:
        print(f"{Colors.RED}❌ MT5 connection failed: {mt5.last_error()}{Colors.RESET}")
except Exception as e:
    print(f"{Colors.RED}❌ MT5 Error: {e}{Colors.RESET}")

# Test TwelveData
print(f"\n{Colors.YELLOW}Testing TwelveData API...{Colors.RESET}")
try:
    import requests
    api_key = os.getenv("TWELVEDATA_API_KEY")
    response = requests.get(f"https://api.twelvedata.com/price?symbol=BTC/USD&apikey={api_key}")
    if response.status_code == 200:
        data = response.json()
        if "price" in data:
            print(f"{Colors.GREEN}✅ TwelveData connected{Colors.RESET}")
            print(f"   BTC/USD: ${float(data['price']):,.2f}")
    else:
        print(f"{Colors.RED}❌ TwelveData failed{Colors.RESET}")
except Exception as e:
    print(f"{Colors.RED}❌ TwelveData Error: {e}{Colors.RESET}")

# Test Telegram
print(f"\n{Colors.YELLOW}Testing Telegram...{Colors.RESET}")
try:
    import requests
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    test_message = f"""
🤖 *Trading Bot System Check*
📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
💼 Account: {os.getenv('MT5_LOGIN')}
📊 Status: Testing connection
"""
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": test_message, "parse_mode": "Markdown"}
    response = requests.post(url, data=data)
    
    if response.status_code == 200:
        print(f"{Colors.GREEN}✅ Telegram notification sent{Colors.RESET}")
    else:
        print(f"{Colors.RED}❌ Telegram failed{Colors.RESET}")
except Exception as e:
    print(f"{Colors.RED}❌ Telegram Error: {e}{Colors.RESET}")

# Menu
print(f"\n{Colors.CYAN}{'='*70}{Colors.RESET}")
print(f"{Colors.BOLD}SELECT ACTION:{Colors.RESET}")
print(f"{Colors.GREEN}1.{Colors.RESET} Start Trading Bot (Current mode: {os.getenv('LIVE_TRADING')})")
print(f"{Colors.YELLOW}2.{Colors.RESET} Switch to DEMO mode (Safe)")
print(f"{Colors.CYAN}3.{Colors.RESET} Run Quick Backtest")
print(f"{Colors.RED}4.{Colors.RESET} Exit")
print(f"{Colors.CYAN}{'='*70}{Colors.RESET}")

choice = input(f"\n{Colors.YELLOW}Enter choice (1-4): {Colors.RESET}")

if choice == "1":
    is_live = os.getenv('LIVE_TRADING', 'false').lower() == 'true'
    
    if is_live:
        print(f"\n{Colors.RED}{Colors.BOLD}⚠️  STARTING LIVE TRADING WITH REAL MONEY ⚠️{Colors.RESET}")
        print(f"{Colors.YELLOW}You can lose all your capital!{Colors.RESET}")
        confirm = input(f"{Colors.RED}Type 'YES' to confirm: {Colors.RESET}")
        
        if confirm != "YES":
            print(f"{Colors.GREEN}Cancelled for safety.{Colors.RESET}")
            sys.exit(0)
    else:
        print(f"\n{Colors.GREEN}Starting in DEMO mode (safe)...{Colors.RESET}")
    
    print(f"\n{Colors.CYAN}Launching Enhanced Trading Bot...{Colors.RESET}")
    print(f"{Colors.YELLOW}Press Ctrl+C to stop at any time{Colors.RESET}\n")
    
    # Import and run the enhanced bot
    try:
        from enhanced_trading_bot import EnhancedTradingBot
        bot = EnhancedTradingBot()
        bot.run()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Bot stopped by user{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.RED}Error: {e}{Colors.RESET}")

elif choice == "2":
    print(f"\n{Colors.GREEN}Switching to DEMO mode...{Colors.RESET}")
    
    # Read current config
    with open('configs/.env', 'r') as f:
        content = f.read()
    
    # Replace LIVE_TRADING
    content = content.replace('LIVE_TRADING=true', 'LIVE_TRADING=false')
    
    # Write back
    with open('configs/.env', 'w') as f:
        f.write(content)
    
    print(f"{Colors.GREEN}✅ Switched to DEMO mode{Colors.RESET}")
    print("Run the script again to start in DEMO mode")

elif choice == "3":
    print(f"\n{Colors.CYAN}Running quick backtest...{Colors.RESET}")
    try:
        from enhanced_trading_bot import EnhancedTradingBot
        bot = EnhancedTradingBot()
        bot.run_backtest()
    except Exception as e:
        print(f"{Colors.RED}Backtest error: {e}{Colors.RESET}")

else:
    print(f"\n{Colors.CYAN}Exiting...{Colors.RESET}")

print(f"\n{Colors.CYAN}Session ended at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
