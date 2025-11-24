# 📡 DOCUMENTACIÓN API & ENDPOINTS

## 🌐 TWELVEDATA API ENDPOINTS

### Base URL
```
https://api.twelvedata.com
```

### Autenticación
Todos los endpoints requieren el parámetro `apikey` en la query string.

## 📊 ENDPOINTS DE DATOS DE MERCADO

### 1. Quote - Cotización Actual
```http
GET /quote
```

**Parámetros:**
- `symbol` (string, required): Símbolo del activo
- `apikey` (string, required): API key

**Ejemplo:**
```python
import requests

def get_quote(symbol):
    url = "https://api.twelvedata.com/quote"
    params = {
        "symbol": symbol,
        "apikey": "915b2ea02f7d49b986c1ae27d2711c73"
    }
    response = requests.get(url, params=params)
    return response.json()

# Uso
quote = get_quote("NAS100")
print(f"Precio NAS100: ${quote['price']}")
```

**Respuesta:**
```json
{
    "symbol": "NAS100",
    "name": "NASDAQ 100 Index",
    "exchange": "NASDAQ",
    "currency": "USD",
    "datetime": "2024-01-15 14:30:00",
    "timestamp": 1705333800,
    "open": "17234.50",
    "high": "17289.30",
    "low": "17201.20",
    "close": "17265.80",
    "volume": "1234567890",
    "previous_close": "17210.40",
    "change": "55.40",
    "percent_change": "0.32",
    "is_market_open": true
}
```

### 2. Time Series - Series Temporales
```http
GET /time_series
```

**Parámetros:**
- `symbol` (string, required): Símbolo
- `interval` (string, required): Intervalo temporal
  - Valores: `1min`, `5min`, `15min`, `30min`, `45min`, `1h`, `2h`, `4h`, `1day`, `1week`, `1month`
- `outputsize` (integer, optional): Número de puntos (default: 30, max: 5000)
- `apikey` (string, required): API key

**Ejemplo:**
```python
def get_time_series(symbol, interval='5min', outputsize=100):
    url = "https://api.twelvedata.com/time_series"
    params = {
        "symbol": symbol,
        "interval": interval,
        "outputsize": outputsize,
        "apikey": "915b2ea02f7d49b986c1ae27d2711c73"
    }
    response = requests.get(url, params=params)
    return response.json()

# Uso
data = get_time_series("BTC/USD", "1h", 200)
for candle in data['values'][:5]:
    print(f"{candle['datetime']}: O:{candle['open']} H:{candle['high']} L:{candle['low']} C:{candle['close']}")
```

### 3. Real-time Price - Precio en Tiempo Real
```http
GET /price
```

**Parámetros:**
- `symbol` (string, required): Símbolo
- `apikey` (string, required): API key

**Ejemplo:**
```python
def get_realtime_price(symbol):
    url = "https://api.twelvedata.com/price"
    params = {
        "symbol": symbol,
        "apikey": "915b2ea02f7d49b986c1ae27d2711c73"
    }
    response = requests.get(url, params=params)
    return response.json()

# Uso
price_data = get_realtime_price("EUR/USD")
print(f"EUR/USD: {price_data['price']}")
```

## 📈 ENDPOINTS DE INDICADORES TÉCNICOS

### 1. RSI - Relative Strength Index
```http
GET /rsi
```

**Parámetros:**
- `symbol` (string, required): Símbolo
- `interval` (string, required): Intervalo
- `time_period` (integer, optional): Período (default: 14)
- `outputsize` (integer, optional): Número de valores
- `apikey` (string, required): API key

**Ejemplo:**
```python
def get_rsi(symbol, interval='1h', period=14):
    url = "https://api.twelvedata.com/rsi"
    params = {
        "symbol": symbol,
        "interval": interval,
        "time_period": period,
        "apikey": "915b2ea02f7d49b986c1ae27d2711c73"
    }
    response = requests.get(url, params=params)
    return response.json()

# Uso
rsi_data = get_rsi("NAS100", "1h", 14)
current_rsi = float(rsi_data['values'][0]['rsi'])

if current_rsi < 30:
    print(f"RSI: {current_rsi:.2f} - SOBREVENTA (Posible compra)")
elif current_rsi > 70:
    print(f"RSI: {current_rsi:.2f} - SOBRECOMPRA (Posible venta)")
else:
    print(f"RSI: {current_rsi:.2f} - NEUTRAL")
```

### 2. MACD - Moving Average Convergence Divergence
```http
GET /macd
```

**Parámetros:**
- `symbol` (string, required): Símbolo
- `interval` (string, required): Intervalo
- `fast_period` (integer, optional): Período rápido (default: 12)
- `slow_period` (integer, optional): Período lento (default: 26)
- `signal_period` (integer, optional): Período señal (default: 9)
- `apikey` (string, required): API key

**Ejemplo:**
```python
def get_macd(symbol, interval='1h'):
    url = "https://api.twelvedata.com/macd"
    params = {
        "symbol": symbol,
        "interval": interval,
        "fast_period": 12,
        "slow_period": 26,
        "signal_period": 9,
        "apikey": "915b2ea02f7d49b986c1ae27d2711c73"
    }
    response = requests.get(url, params=params)
    return response.json()

# Uso
macd_data = get_macd("BTC/USD", "4h")
latest = macd_data['values'][0]

macd_line = float(latest['macd'])
signal_line = float(latest['macd_signal'])
histogram = float(latest['macd_histogram'])

if histogram > 0 and macd_line > signal_line:
    print("MACD: Señal ALCISTA")
elif histogram < 0 and macd_line < signal_line:
    print("MACD: Señal BAJISTA")
```

### 3. Bollinger Bands
```http
GET /bbands
```

**Parámetros:**
- `symbol` (string, required): Símbolo
- `interval` (string, required): Intervalo
- `time_period` (integer, optional): Período (default: 20)
- `sd` (float, optional): Desviaciones estándar (default: 2)
- `apikey` (string, required): API key

**Ejemplo:**
```python
def get_bollinger_bands(symbol, interval='1h'):
    url = "https://api.twelvedata.com/bbands"
    params = {
        "symbol": symbol,
        "interval": interval,
        "time_period": 20,
        "sd": 2,
        "apikey": "915b2ea02f7d49b986c1ae27d2711c73"
    }
    response = requests.get(url, params=params)
    return response.json()

# Uso
bb_data = get_bollinger_bands("EUR/USD", "30min")
latest = bb_data['values'][0]

upper_band = float(latest['upper_band'])
middle_band = float(latest['middle_band'])
lower_band = float(latest['lower_band'])

# Obtener precio actual
price = get_realtime_price("EUR/USD")['price']

if price < lower_band:
    print("Precio por debajo de Banda Inferior - Posible COMPRA")
elif price > upper_band:
    print("Precio por encima de Banda Superior - Posible VENTA")
```

### 4. ATR - Average True Range
```http
GET /atr
```

**Parámetros:**
- `symbol` (string, required): Símbolo
- `interval` (string, required): Intervalo
- `time_period` (integer, optional): Período (default: 14)
- `apikey` (string, required): API key

**Ejemplo:**
```python
def get_atr(symbol, interval='1h', period=14):
    url = "https://api.twelvedata.com/atr"
    params = {
        "symbol": symbol,
        "interval": interval,
        "time_period": period,
        "apikey": "915b2ea02f7d49b986c1ae27d2711c73"
    }
    response = requests.get(url, params=params)
    return response.json()

# Uso para calcular Stop Loss dinámico
atr_data = get_atr("NAS100", "1h")
current_atr = float(atr_data['values'][0]['atr'])

# Stop Loss = 2 x ATR
stop_loss_distance = current_atr * 2
print(f"ATR: {current_atr:.2f}")
print(f"Stop Loss recomendado: {stop_loss_distance:.2f} puntos desde entrada")
```

## 🔄 WEBSOCKET - DATOS EN TIEMPO REAL

### WebSocket Endpoint
```
wss://ws.twelvedata.com/v1/quotes/price
```

**Ejemplo de Conexión:**
```python
import websocket
import json

def on_message(ws, message):
    data = json.loads(message)
    if data['event'] == 'price':
        print(f"{data['symbol']}: ${data['price']} @ {data['timestamp']}")

def on_error(ws, error):
    print(f"Error: {error}")

def on_close(ws):
    print("WebSocket cerrado")

def on_open(ws):
    # Subscribir a símbolos
    subscribe_message = {
        "action": "subscribe",
        "params": {
            "symbols": "NAS100,BTC/USD,EUR/USD"
        }
    }
    ws.send(json.dumps(subscribe_message))

# Conectar
ws_url = "wss://ws.twelvedata.com/v1/quotes/price?apikey=915b2ea02f7d49b986c1ae27d2711c73"
ws = websocket.WebSocketApp(ws_url,
                            on_open=on_open,
                            on_message=on_message,
                            on_error=on_error,
                            on_close=on_close)
ws.run_forever()
```

## 🤖 MT5 API INTEGRATION

### Conexión con MetaTrader 5
```python
import MetaTrader5 as mt5

class MT5API:
    def __init__(self):
        self.connected = False
        
    def connect(self, login, password, server):
        """Conectar a MT5"""
        if not mt5.initialize(login=login, password=password, server=server):
            print(f"Error conectando: {mt5.last_error()}")
            return False
        
        self.connected = True
        return True
    
    def get_account_info(self):
        """Obtener información de cuenta"""
        if not self.connected:
            return None
            
        account = mt5.account_info()
        return {
            'balance': account.balance,
            'equity': account.equity,
            'margin': account.margin,
            'free_margin': account.margin_free,
            'profit': account.profit,
            'currency': account.currency
        }
    
    def get_symbol_info(self, symbol):
        """Obtener información del símbolo"""
        info = mt5.symbol_info(symbol)
        if info is None:
            return None
            
        return {
            'bid': info.bid,
            'ask': info.ask,
            'spread': info.spread,
            'volume_min': info.volume_min,
            'volume_max': info.volume_max,
            'volume_step': info.volume_step,
            'contract_size': info.trade_contract_size,
            'tick_size': info.trade_tick_size,
            'tick_value': info.trade_tick_value
        }
    
    def place_order(self, symbol, order_type, volume, price=None, 
                   sl=None, tp=None, comment=""):
        """Colocar orden"""
        # Preparar request
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": order_type,
            "deviation": 20,
            "magic": 234000,
            "comment": comment,
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Añadir precio si es necesario
        if order_type == mt5.ORDER_TYPE_BUY:
            request["price"] = mt5.symbol_info_tick(symbol).ask
        else:
            request["price"] = mt5.symbol_info_tick(symbol).bid
        
        # Añadir SL y TP si se proporcionan
        if sl is not None:
            request["sl"] = sl
        if tp is not None:
            request["tp"] = tp
        
        # Enviar orden
        result = mt5.order_send(request)
        
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            print(f"Error en orden: {result.comment}")
            return None
            
        return result.order
    
    def get_positions(self, symbol=None):
        """Obtener posiciones abiertas"""
        if symbol:
            positions = mt5.positions_get(symbol=symbol)
        else:
            positions = mt5.positions_get()
            
        if positions is None:
            return []
            
        return [{
            'ticket': pos.ticket,
            'symbol': pos.symbol,
            'type': 'buy' if pos.type == 0 else 'sell',
            'volume': pos.volume,
            'price_open': pos.price_open,
            'price_current': pos.price_current,
            'sl': pos.sl,
            'tp': pos.tp,
            'profit': pos.profit,
            'comment': pos.comment
        } for pos in positions]
    
    def close_position(self, ticket):
        """Cerrar posición por ticket"""
        position = mt5.positions_get(ticket=ticket)
        if not position:
            return False
            
        pos = position[0]
        
        # Preparar request de cierre
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "position": ticket,
            "symbol": pos.symbol,
            "volume": pos.volume,
            "type": mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY,
            "deviation": 20,
            "magic": 234000,
            "comment": "Close by Python",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        # Precio de cierre
        if pos.type == 0:  # Si es compra, cerrar con venta
            request["price"] = mt5.symbol_info_tick(pos.symbol).bid
        else:  # Si es venta, cerrar con compra
            request["price"] = mt5.symbol_info_tick(pos.symbol).ask
        
        result = mt5.order_send(request)
        return result.retcode == mt5.TRADE_RETCODE_DONE
    
    def modify_position(self, ticket, sl=None, tp=None):
        """Modificar SL/TP de posición"""
        position = mt5.positions_get(ticket=ticket)
        if not position:
            return False
            
        pos = position[0]
        
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": ticket,
            "symbol": pos.symbol,
            "sl": sl if sl is not None else pos.sl,
            "tp": tp if tp is not None else pos.tp,
            "deviation": 20,
            "magic": 234000,
            "comment": "Modify by Python",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        return result.retcode == mt5.TRADE_RETCODE_DONE
    
    def get_history(self, symbol=None, days=30):
        """Obtener historial de trades"""
        from datetime import datetime, timedelta
        
        # Rango de fechas
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days)
        
        # Obtener deals
        if symbol:
            deals = mt5.history_deals_get(from_date, to_date, symbol=symbol)
        else:
            deals = mt5.history_deals_get(from_date, to_date)
            
        if deals is None:
            return []
            
        return [{
            'ticket': deal.ticket,
            'order': deal.order,
            'time': datetime.fromtimestamp(deal.time),
            'symbol': deal.symbol,
            'type': 'buy' if deal.type == 0 else 'sell',
            'volume': deal.volume,
            'price': deal.price,
            'profit': deal.profit,
            'commission': deal.commission,
            'swap': deal.swap,
            'comment': deal.comment
        } for deal in deals]
```

## 🔐 AUTENTICACIÓN Y SEGURIDAD

### Headers Requeridos
```python
headers = {
    'Authorization': f'apikey {API_KEY}',
    'Content-Type': 'application/json',
    'User-Agent': 'AlgoTrader/3.0'
}
```

### Rate Limiting
```python
class RateLimiter:
    def __init__(self, max_requests_per_second=8):
        self.max_requests = max_requests_per_second
        self.requests = []
        
    async def wait_if_needed(self):
        """Esperar si se alcanzó el límite"""
        now = time.time()
        
        # Limpiar requests antiguos
        self.requests = [r for r in self.requests if now - r < 1]
        
        # Si alcanzamos el límite, esperar
        if len(self.requests) >= self.max_requests:
            wait_time = 1 - (now - self.requests[0])
            if wait_time > 0:
                await asyncio.sleep(wait_time)
        
        # Registrar nuevo request
        self.requests.append(now)
```

## 📊 RESPUESTAS DE ERROR

### Códigos de Error Comunes
```python
ERROR_CODES = {
    400: "Bad Request - Parámetros inválidos",
    401: "Unauthorized - API key inválida",
    404: "Not Found - Símbolo no encontrado",
    429: "Too Many Requests - Rate limit excedido",
    500: "Internal Server Error - Error del servidor",
    503: "Service Unavailable - Servicio no disponible"
}

def handle_api_error(response):
    """Manejar errores de API"""
    if response.status_code != 200:
        error_msg = ERROR_CODES.get(response.status_code, "Error desconocido")
        
        # Intentar obtener mensaje específico
        try:
            error_data = response.json()
            if 'message' in error_data:
                error_msg = error_data['message']
        except:
            pass
        
        print(f"Error API ({response.status_code}): {error_msg}")
        return None
    
    return response.json()
```

## 🎯 EJEMPLOS DE USO COMPLETO

### Sistema de Trading Completo
```python
import asyncio
import os
from datetime import datetime

class TradingSystem:
    def __init__(self):
        self.api_key = os.getenv('TWELVEDATA_API_KEY')
        self.mt5_api = MT5API()
        self.rate_limiter = RateLimiter(8)
        
    async def analyze_market(self, symbol):
        """Análisis completo del mercado"""
        # Rate limiting
        await self.rate_limiter.wait_if_needed()
        
        # Obtener datos
        price = await self.get_price(symbol)
        rsi = await self.get_rsi(symbol)
        macd = await self.get_macd(symbol)
        
        # Generar señal
        signal = self.generate_signal(price, rsi, macd)
        
        return {
            'symbol': symbol,
            'price': price,
            'rsi': rsi,
            'macd': macd,
            'signal': signal,
            'timestamp': datetime.now()
        }
    
    def generate_signal(self, price, rsi, macd):
        """Generar señal de trading"""
        score = 0
        
        # RSI
        if rsi < 30:
            score += 2  # Sobreventa fuerte
        elif rsi < 40:
            score += 1  # Sobreventa moderada
        elif rsi > 70:
            score -= 2  # Sobrecompra fuerte
        elif rsi > 60:
            score -= 1  # Sobrecompra moderada
        
        # MACD
        if macd['histogram'] > 0:
            score += 1  # Momentum alcista
        else:
            score -= 1  # Momentum bajista
        
        # Determinar señal
        if score >= 2:
            return 'BUY'
        elif score <= -2:
            return 'SELL'
        else:
            return 'NEUTRAL'
    
    async def execute_strategy(self):
        """Ejecutar estrategia de trading"""
        symbols = ['NAS100', 'BTC/USD', 'EUR/USD']
        
        while True:
            for symbol in symbols:
                try:
                    # Analizar mercado
                    analysis = await self.analyze_market(symbol)
                    
                    # Logging
                    print(f"\n{analysis['timestamp']}")
                    print(f"{symbol}: ${analysis['price']}")
                    print(f"RSI: {analysis['rsi']:.2f}")
                    print(f"Señal: {analysis['signal']}")
                    
                    # Ejecutar trade si hay señal fuerte
                    if analysis['signal'] in ['BUY', 'SELL']:
                        # Aquí iría la lógica de ejecución
                        pass
                        
                except Exception as e:
                    print(f"Error analizando {symbol}: {e}")
            
            # Esperar antes del próximo ciclo
            await asyncio.sleep(60)

# Ejecutar
if __name__ == "__main__":
    system = TradingSystem()
    asyncio.run(system.execute_strategy())
```

---

## 📝 NOTAS IMPORTANTES

### Límites de API
- **Free Tier**: 8 requests/segundo, 800/día
- **Basic**: 120 requests/minuto
- **Pro**: Sin límites

### Mejores Prácticas
1. Implementar rate limiting
2. Cachear datos cuando sea posible
3. Manejar errores gracefully
4. Usar WebSocket para datos en tiempo real
5. Validar todos los datos recibidos

### Seguridad
1. Nunca exponer API keys en código
2. Usar HTTPS siempre
3. Validar certificados SSL
4. Implementar timeouts
5. Loguear todas las transacciones

---

**Versión API**: 1.2.0  
**Última actualización**: 2024
