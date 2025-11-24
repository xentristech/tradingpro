
import os
import requests
from datetime import datetime

class TwelveDataSimple:
    def __init__(self):
        self.api_key = os.getenv('TWELVEDATA_API_KEY', '23d17ce5b7044ad5aef9766770a6252b')
        self.base_url = 'https://api.twelvedata.com'
        self.symbol_map = {
            'EURUSD': 'EUR/USD',
            'XAUUSD': 'XAU/USD',
            'BTCUSD': 'BTC/USD'
        }
        
    def get_price(self, symbol):
        try:
            api_symbol = self.symbol_map.get(symbol, symbol)
            url = f"{self.base_url}/price"
            params = {'symbol': api_symbol, 'apikey': self.api_key}
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                return float(data.get('price', 0))
        except:
            pass
        return None
        
    def get_indicators(self, symbol):
        # Simulación de indicadores
        return {
            'rsi': 55.5,
            'macd': 0.0001,
            'sma_20': 1.0850,
            'sentiment': 'NEUTRAL'
        }
