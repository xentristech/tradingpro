"""
LIVE TRADING VERIFICATION AND SAFETY CHECK
Critical verification before enabling real money trading
"""
import os
import sys
import MetaTrader5 as mt5
import requests
from datetime import datetime
from dotenv import load_dotenv
import time

print("\n" + "="*70)
print(" ⚠️  LIVE TRADING VERIFICATION - REAL MONEY AT RISK ⚠️")
print("="*70)

# Load configuration
load_dotenv('configs/.env')

# Safety parameters
SAFETY_CHECKS = {
    'max_loss_per_day': 100.0,  # Maximum daily loss in USD
    'max_trades_per_day': 5,     # Maximum trades per day
    'min_balance_required': 100,  # Minimum balance to trade
    'emergency_stop_loss': 0.05, # 5% emergency stop
}

def verify_mt5_connection():
    """Verify MT5 connection and account"""
    print("\n📡 Verifying MetaTrader 5 Connection...")
    
    try:
        # Initialize MT5
        path = os.getenv("MT5_PATH")
        login = int(os.getenv("MT5_LOGIN"))
        password = os.getenv("MT5_PASSWORD")
        server = os.getenv("MT5_SERVER")
        
        if not mt5.initialize(
            path=path,
            login=login,
            password=password,
            server=server,
            timeout=60000
        ):
            print("❌ MT5 initialization failed")
            print(f"   Error: {mt5.last_error()}")
            return False
        
        # Get account info
        account_info = mt5.account_info()
        if account_info:
            print("✅ MT5 Connected Successfully!")
            print(f"\n📊 Account Information:")
            print(f"   Account:  {account_info.login}")
            print(f"   Server:   {account_info.server}")
            print(f"   Balance:  ${account_info.balance:.2f}")
            print(f"   Equity:   ${account_info.equity:.2f}")
            print(f"   Margin:   ${account_info.margin:.2f}")
            print(f"   Free:     ${account_info.margin_free:.2f}")
            print(f"   Leverage: 1:{account_info.leverage}")
            print(f"   Currency: {account_info.currency}")
            
            # Check if demo or real
            if "trial" in server.lower() or "demo" in server.lower():
                print(f"\n✅ ACCOUNT TYPE: DEMO (Safe for testing)")
            else:
                print(f"\n⚠️  ACCOUNT TYPE: REAL (Real money at risk!)")
            
            # Safety check - minimum balance
            if account_info.balance < SAFETY_CHECKS['min_balance_required']:
                print(f"\n❌ Balance too low: ${account_info.balance:.2f}")
                print(f"   Minimum required: ${SAFETY_CHECKS['min_balance_required']}")
                return False
            
            # Check symbol availability
            symbol = os.getenv("SYMBOL")
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info is None:
                print(f"\n❌ Symbol {symbol} not found")
                # Try to find similar symbols
                symbols = mt5.symbols_get()
                btc_symbols = [s.name for s in symbols if 'BTC' in s.name.upper()]
                if btc_symbols:
                    print(f"   Available BTC symbols: {', '.join(btc_symbols[:5])}")
                return False
            else:
                print(f"\n✅ Symbol {symbol} found and available for trading")
                print(f"   Bid: {symbol_info.bid}")
                print(f"   Ask: {symbol_info.ask}")
                print(f"   Spread: {symbol_info.spread}")
            
            mt5.shutdown()
            return True
        else:
            print("❌ Failed to get account info")
            mt5.shutdown()
            return False
            
    except Exception as e:
        print(f"❌ MT5 Error: {e}")
        return False

def verify_telegram():
    """Verify Telegram connection"""
    print("\n📱 Verifying Telegram Bot...")
    
    token = os.getenv("TELEGRAM_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not token or not chat_id:
        print("❌ Telegram credentials missing")
        return False
    
    try:
        # Test message
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        message = f"""
🤖 *TRADING BOT ACTIVATION*

⚠️ *LIVE TRADING ENABLED*
📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
💼 Account: {os.getenv('MT5_LOGIN')}
📊 Symbol: {os.getenv('SYMBOL')}
💰 Risk per trade: {float(os.getenv('RISK_PER_TRADE', 0.01))*100:.1f}%

*Safety Features:*
• Max daily loss: ${SAFETY_CHECKS['max_loss_per_day']}
• Max trades/day: {SAFETY_CHECKS['max_trades_per_day']}
• Emergency stop: {SAFETY_CHECKS['emergency_stop_loss']*100:.0f}%

⚠️ *Real money at risk! Monitor closely!*
"""
        
        data = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        response = requests.post(url, data=data)
        
        if response.status_code == 200:
            print("✅ Telegram notification sent successfully!")
            return True
        else:
            print(f"❌ Telegram failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Telegram error: {e}")
        return False

def verify_twelvedata():
    """Verify TwelveData API"""
    print("\n📈 Verifying TwelveData API...")
    
    api_key = os.getenv("TWELVEDATA_API_KEY")
    symbol = os.getenv("TWELVEDATA_SYMBOL", "BTC/USD")
    
    if not api_key:
        print("❌ TwelveData API key missing")
        return False
    
    try:
        url = f"https://api.twelvedata.com/price"
        params = {
            "symbol": symbol,
            "apikey": api_key
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if "price" in data:
                print(f"✅ TwelveData connected!")
                print(f"   Current {symbol} price: ${float(data['price']):,.2f}")
                return True
            else:
                print(f"❌ TwelveData error: {data}")
                return False
        else:
            print(f"❌ TwelveData failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ TwelveData error: {e}")
        return False

def create_safety_config():
    """Create safety configuration file"""
    print("\n🔒 Creating Safety Configuration...")
    
    safety_config = f"""# SAFETY CONFIGURATION - DO NOT MODIFY WITHOUT UNDERSTANDING RISKS

# === RISK LIMITS ===
MAX_DAILY_LOSS_USD={SAFETY_CHECKS['max_loss_per_day']}
MAX_TRADES_PER_DAY={SAFETY_CHECKS['max_trades_per_day']}
EMERGENCY_STOP_PERCENT={SAFETY_CHECKS['emergency_stop_loss']}
MIN_BALANCE_REQUIRED={SAFETY_CHECKS['min_balance_required']}

# === POSITION LIMITS ===
MAX_POSITION_SIZE=0.1  # Maximum 0.1 lots
MIN_POSITION_SIZE=0.01 # Minimum 0.01 lots
MAX_OPEN_POSITIONS=1   # Only 1 position at a time

# === TIME RESTRICTIONS ===
TRADE_HOURS_START=07:00
TRADE_HOURS_END=22:00
AVOID_WEEKENDS=true
AVOID_NEWS_EVENTS=true

# === KILL SWITCHES ===
STOP_ON_CONSECUTIVE_LOSSES=3
STOP_ON_DAILY_LOSS_REACHED=true
STOP_ON_TECHNICAL_ERROR=true
REQUIRE_CONFIRMATION_FOR_TRADES=false

# === NOTIFICATIONS ===
NOTIFY_ON_TRADE=true
NOTIFY_ON_ERROR=true
NOTIFY_ON_DAILY_SUMMARY=true

# === Created: {datetime.now().isoformat()} ===
"""
    
    with open('configs/safety.conf', 'w') as f:
        f.write(safety_config)
    
    print("✅ Safety configuration created")
    return True

def display_risk_warning():
    """Display final risk warning"""
    print("\n" + "="*70)
    print(" ⚠️  FINAL WARNING - REAL MONEY TRADING ⚠️")
    print("="*70)
    
    print("""
VOCÊ ESTÁ PRESTES A ATIVAR TRADING COM DINHEIRO REAL!

RISCOS:
1. Você pode perder TODO seu capital
2. Erros de software podem causar perdas
3. Condições de mercado podem mudar rapidamente
4. Conexão perdida pode deixar posições abertas
5. Slippage e spreads podem afetar resultados

RECOMENDAÇÕES:
• Monitore o bot constantemente
• Comece com posições mínimas (0.01 lots)
• Defina stop loss em TODAS as operações
• Tenha um plano de emergência
• Nunca arrisque dinheiro que não pode perder

CONFIGURAÇÃO ATUAL:
• Conta: {os.getenv('MT5_LOGIN')}
• Símbolo: {os.getenv('SYMBOL')}
• Risco por trade: {float(os.getenv('RISK_PER_TRADE', 0.01))*100:.1f}%
• Stop Loss padrão: ${os.getenv('DEF_SL_USD')}
• Take Profit padrão: ${os.getenv('DEF_TP_USD')}
""")

def main():
    """Main verification process"""
    
    checks = {
        'MT5 Connection': verify_mt5_connection(),
        'Telegram Bot': verify_telegram(),
        'TwelveData API': verify_twelvedata(),
        'Safety Config': create_safety_config()
    }
    
    print("\n" + "="*70)
    print(" 📊 VERIFICATION SUMMARY")
    print("="*70)
    
    all_passed = True
    for check, result in checks.items():
        status = "✅" if result else "❌"
        print(f"  {status} {check}")
        if not result:
            all_passed = False
    
    if not all_passed:
        print("\n❌ VERIFICATION FAILED - Cannot proceed with live trading")
        print("   Please fix the issues above and try again")
        return False
    
    print("\n✅ ALL CHECKS PASSED")
    
    # Final warning
    display_risk_warning()
    
    print("\n" + "="*70)
    confirmation = input("\nType 'YES I UNDERSTAND THE RISKS' to proceed with LIVE trading: ")
    
    if confirmation == "YES I UNDERSTAND THE RISKS":
        print("\n✅ LIVE TRADING AUTHORIZED")
        print("   Starting trading bot with real money...")
        print("   Press Ctrl+C at any time to stop")
        
        # Create activation timestamp
        with open('LIVE_TRADING_ACTIVATED.txt', 'w') as f:
            f.write(f"Live trading activated at: {datetime.now().isoformat()}\n")
            f.write(f"Account: {os.getenv('MT5_LOGIN')}\n")
            f.write(f"Risk per trade: {os.getenv('RISK_PER_TRADE')}\n")
        
        return True
    else:
        print("\n❌ Live trading cancelled")
        print("   Switching to DEMO mode for safety")
        
        # Switch to demo mode
        with open('configs/.env', 'r') as f:
            content = f.read()
        content = content.replace('LIVE_TRADING=true', 'LIVE_TRADING=false')
        with open('configs/.env', 'w') as f:
            f.write(content)
        
        return False

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("\n🚀 Launching Enhanced Trading Bot in LIVE mode...")
            time.sleep(3)
            # Import and run the bot
            from enhanced_trading_bot import EnhancedTradingBot
            bot = EnhancedTradingBot()
            bot.run()
    except KeyboardInterrupt:
        print("\n⚠️ Trading stopped by user")
    except Exception as e:
        print(f"\n❌ Critical error: {e}")
        print("   Live trading aborted for safety")
