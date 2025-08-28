"""
TRADING BOT MONITOR
Real-time monitoring of trading bot status
"""
import os
import time
import MetaTrader5 as mt5
from datetime import datetime
from dotenv import load_dotenv

load_dotenv('configs/.env')

def monitor_bot():
    """Monitor bot status and positions"""
    print("\n" + "="*60)
    print("  TRADING BOT MONITOR - LIVE STATUS")
    print("="*60)
    
    # Connect to MT5
    if mt5.initialize(
        path=os.getenv("MT5_PATH"),
        login=int(os.getenv("MT5_LOGIN")),
        password=os.getenv("MT5_PASSWORD"),
        server=os.getenv("MT5_SERVER")
    ):
        while True:
            try:
                # Clear screen (Windows)
                os.system('cls' if os.name == 'nt' else 'clear')
                
                print("\n" + "="*60)
                print(f"  LIVE MONITOR - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("="*60)
                
                # Account info
                account = mt5.account_info()
                print(f"\n💼 ACCOUNT INFO:")
                print(f"   Number:    {account.login}")
                print(f"   Balance:   ${account.balance:.2f}")
                print(f"   Equity:    ${account.equity:.2f}")
                print(f"   Profit:    ${account.profit:+.2f}")
                print(f"   Margin:    ${account.margin:.2f}")
                print(f"   Free:      ${account.margin_free:.2f}")
                
                # Open positions
                positions = mt5.positions_get()
                print(f"\n📈 OPEN POSITIONS: {len(positions) if positions else 0}")
                
                if positions:
                    for pos in positions:
                        print(f"\n   Position #{pos.ticket}:")
                        print(f"   Symbol:    {pos.symbol}")
                        print(f"   Type:      {'BUY' if pos.type == 0 else 'SELL'}")
                        print(f"   Volume:    {pos.volume}")
                        print(f"   Open:      {pos.price_open:.5f}")
                        print(f"   Current:   {pos.price_current:.5f}")
                        print(f"   Profit:    ${pos.profit:+.2f}")
                        print(f"   SL:        {pos.sl if pos.sl > 0 else 'None'}")
                        print(f"   TP:        {pos.tp if pos.tp > 0 else 'None'}")
                
                # Symbol info
                symbol = os.getenv("SYMBOL", "BTCUSDm")
                tick = mt5.symbol_info_tick(symbol)
                if tick:
                    print(f"\n💹 {symbol} MARKET:")
                    print(f"   Bid:       {tick.bid:.5f}")
                    print(f"   Ask:       {tick.ask:.5f}")
                    print(f"   Spread:    {(tick.ask - tick.bid):.5f}")
                
                # Recent orders
                orders = mt5.orders_get()
                if orders:
                    print(f"\n⏳ PENDING ORDERS: {len(orders)}")
                    for order in orders[:3]:  # Show max 3
                        print(f"   #{order.ticket}: {order.symbol} {order.type_description}")
                
                print("\n" + "-"*60)
                print("Press Ctrl+C to stop monitoring")
                print("Refreshing in 5 seconds...")
                
                time.sleep(5)
                
            except KeyboardInterrupt:
                print("\n\nMonitoring stopped")
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(5)
        
        mt5.shutdown()
    else:
        print("❌ Failed to connect to MT5")

if __name__ == "__main__":
    monitor_bot()
