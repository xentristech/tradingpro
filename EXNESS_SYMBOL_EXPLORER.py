"""
EXNESS Symbol Explorer
Shows all available symbols in your EXNESS account
Author: Trading Pro System
Version: 3.0
"""

import MetaTrader5 as mt5
import sys
import os

print("EXNESS SYMBOL EXPLORER v3.0")
print("="*50)

def connect_exness():
    """Connect to EXNESS MT5"""
    exness_config = {
        'path': r"C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe",
        'login': 197678662,
        'password': "Badboy930218*",
        'server': "Exness-MT5Trial11"
    }

    print("Connecting to EXNESS MT5...")

    try:
        # Initialize MT5
        if not mt5.initialize(exness_config['path']):
            print(f"ERROR: Failed to initialize EXNESS MT5")
            return False

        # Login
        if not mt5.login(
            login=exness_config['login'],
            password=exness_config['password'],
            server=exness_config['server']
        ):
            print(f"ERROR: Login failed")
            return False

        print(f"SUCCESS: Connected to EXNESS!")
        return True

    except Exception as e:
        print(f"Error: {e}")
        return False

def explore_symbols():
    """Explore all available symbols"""
    print(f"\nExploring available symbols...")

    try:
        # Get all symbols
        all_symbols = mt5.symbols_get()

        if not all_symbols:
            print("No symbols found")
            return

        print(f"Found {len(all_symbols)} total symbols")

        # Categorize symbols
        forex_pairs = []
        commodities = []
        indices = []
        crypto = []
        stocks = []
        others = []

        tradeable_symbols = []

        for symbol_info in all_symbols:
            symbol = symbol_info.name

            try:
                # Try to select the symbol
                if mt5.symbol_select(symbol, True):
                    # Get tick data to verify it's tradeable
                    tick = mt5.symbol_info_tick(symbol)
                    if tick and tick.bid > 0 and tick.ask > 0:
                        spread = tick.ask - tick.bid
                        spread_pct = (spread / tick.bid) * 100 if tick.bid > 0 else 0

                        symbol_data = {
                            'symbol': symbol,
                            'bid': tick.bid,
                            'ask': tick.ask,
                            'spread': spread,
                            'spread_pct': spread_pct,
                            'contract_size': symbol_info.trade_contract_size,
                            'min_volume': symbol_info.volume_min,
                            'max_volume': symbol_info.volume_max,
                            'description': symbol_info.description
                        }

                        tradeable_symbols.append(symbol_data)

                        # Categorize
                        if len(symbol) == 6 and any(curr in symbol for curr in ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'NZD']):
                            forex_pairs.append(symbol_data)
                        elif 'XAU' in symbol or 'XAG' in symbol or 'OIL' in symbol:
                            commodities.append(symbol_data)
                        elif any(idx in symbol for idx in ['US30', 'US500', 'NAS100', 'DAX', 'UK100']):
                            indices.append(symbol_data)
                        elif 'BTC' in symbol or 'ETH' in symbol or 'crypto' in symbol.lower():
                            crypto.append(symbol_data)
                        elif len(symbol) <= 5 and symbol.isupper():
                            stocks.append(symbol_data)
                        else:
                            others.append(symbol_data)

            except Exception as e:
                continue

        print(f"\nTradeable symbols found: {len(tradeable_symbols)}")

        # Show categories
        categories = [
            ("FOREX PAIRS", forex_pairs),
            ("COMMODITIES", commodities),
            ("INDICES", indices),
            ("CRYPTO", crypto),
            ("STOCKS", stocks),
            ("OTHERS", others)
        ]

        for category_name, symbols in categories:
            if symbols:
                print(f"\n{category_name} ({len(symbols)} symbols):")
                # Sort by spread quality
                symbols.sort(key=lambda x: x['spread_pct'])

                for i, sym in enumerate(symbols[:10], 1):  # Show top 10
                    print(f"  {i:2d}. {sym['symbol']:12s} - {sym['description'][:30]:30s} - Spread: {sym['spread_pct']:.3f}%")
                    print(f"      Bid: {sym['bid']:10.5f}, Ask: {sym['ask']:10.5f}, Vol: {sym['min_volume']}-{sym['max_volume']}")

                if len(symbols) > 10:
                    print(f"      ... and {len(symbols) - 10} more")

        # Show best trading opportunities
        print(f"\nBEST TRADING OPPORTUNITIES (Low Spread):")
        all_tradeable = tradeable_symbols.copy()
        all_tradeable.sort(key=lambda x: x['spread_pct'])

        print(f"Top 15 symbols with lowest spreads:")
        for i, sym in enumerate(all_tradeable[:15], 1):
            print(f"  {i:2d}. {sym['symbol']:12s} - {sym['description'][:25]:25s} - Spread: {sym['spread_pct']:.3f}%")

        # Test a simple trade setup
        if tradeable_symbols:
            print(f"\nTEST TRADE SIMULATION:")
            best_symbol = all_tradeable[0]
            print(f"Testing with: {best_symbol['symbol']} ({best_symbol['description']})")

            # Get market data
            rates = mt5.copy_rates_from_pos(best_symbol['symbol'], mt5.TIMEFRAME_M15, 0, 20)
            if rates is not None and len(rates) > 0:
                print(f"Market data available: {len(rates)} bars")
                print(f"Latest price: {rates[-1]['close']:.5f}")
                print(f"Volume range: {best_symbol['min_volume']} - {best_symbol['max_volume']}")
                print(f"Ready for live trading!")
            else:
                print(f"No market data available for {best_symbol['symbol']}")

    except Exception as e:
        print(f"Error exploring symbols: {e}")

def main():
    """Main function"""
    if connect_exness():
        # Get account info
        account_info = mt5.account_info()
        if account_info:
            print(f"\nAccount Details:")
            print(f"  Login: {account_info.login}")
            print(f"  Balance: ${account_info.balance:,.2f}")
            print(f"  Equity: ${account_info.equity:,.2f}")
            print(f"  Server: {account_info.server}")
            print(f"  Company: {account_info.company}")

        explore_symbols()

        mt5.shutdown()
        print(f"\nDisconnected from EXNESS")
    else:
        print("Failed to connect to EXNESS")

if __name__ == "__main__":
    main()