# 🔌 DOCUMENTACIÓN DE INTEGRACIÓN - TWELVEDATA & MCP

## 📊 TWELVEDATA INTEGRATION

### Configuración Básica
```python
# .env configuration
TWELVEDATA_API_KEY=915b2ea02f7d49b986c1ae27d2711c73
TWELVEDATA_SYMBOL=BTC/USD
TWELVEDATA_INTERVAL=1min
```

### DataManager - Integración con TwelveData

```python
class DataManager:
    """
    Gestor de datos que integra TwelveData API
    """
    
    def __init__(self, config: Dict):
        self.api_key = os.getenv('TWELVEDATA_API_KEY')
        self.base_url = 'https://api.twelvedata.com'
        self.session = requests.Session()
        
    async def get_realtime_data(self, symbol: str) -> Dict:
        """
        Obtiene datos en tiempo real de TwelveData
        
        Endpoint: /price
        Params:
            - symbol: BTC/USD, EUR/USD, etc.
            - apikey: API key
            
        Returns:
            Dict con precio actual
        """
        
    async def get_historical_data(self, 
                                 symbol: str, 
                                 interval: str,
                                 outputsize: int = 100) -> pd.DataFrame:
        """
        Obtiene datos históricos OHLCV
        
        Endpoint: /time_series
        Params:
            - symbol: Símbolo del activo
            - interval: 1min, 5min, 15min, 30min, 1h, 1day
            - outputsize: Número de velas (max 5000)
            - apikey: API key
            
        Returns:
            DataFrame con columnas: datetime, open, high, low, close, volume
        """
        
    async def get_technical_indicators(self, 
                                      symbol: str,
                                      indicator: str,
                                      **params) -> pd.DataFrame:
        """
        Obtiene indicadores técnicos calculados
        
        Indicadores disponibles:
        - rsi: RSI con time_period
        - macd: MACD con fast_period, slow_period, signal_period
        - bbands: Bollinger Bands con time_period, sd
        - ema: EMA con time_period
        - sma: SMA con time_period
        - atr: ATR con time_period
        - adx: ADX con time_period
        - stoch: Stochastic con k_period, d_period, smooth_k
        
        Endpoint: /{indicator}
        
        Returns:
            DataFrame con valores del indicador
        """
```

### Implementación de TwelveData en el Sistema

```python
# src/data/twelvedata_client.py

import asyncio
import aiohttp
import pandas as pd
from typing import Dict, Optional
import os

class TwelveDataClient:
    """
    Cliente asíncrono para TwelveData API
    """
    
    def __init__(self):
        self.api_key = os.getenv('TWELVEDATA_API_KEY')
        self.base_url = 'https://api.twelvedata.com'
        self.rate_limit = 8  # requests per second for free tier
        self.last_request_time = 0
        
    async def _make_request(self, endpoint: str, params: Dict) -> Dict:
        """
        Realiza petición a la API con rate limiting
        """
        # Add API key
        params['apikey'] = self.api_key
        
        # Rate limiting
        await self._rate_limit()
        
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/{endpoint}"
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"API Error: {response.status}")
    
    async def get_quote(self, symbol: str) -> Dict:
        """
        Obtiene cotización actual
        
        Ejemplo:
            quote = await client.get_quote('BTC/USD')
            # Returns: {'symbol': 'BTC/USD', 'price': 65432.10, ...}
        """
        return await self._make_request('quote', {'symbol': symbol})
    
    async def get_time_series(self, 
                            symbol: str,
                            interval: str = '1min',
                            outputsize: int = 100) -> pd.DataFrame:
        """
        Obtiene series temporales OHLCV
        
        Ejemplo:
            df = await client.get_time_series('BTC/USD', '5min', 500)
            # Returns DataFrame with OHLCV data
        """
        data = await self._make_request('time_series', {
            'symbol': symbol,
            'interval': interval,
            'outputsize': outputsize
        })
        
        # Convert to DataFrame
        df = pd.DataFrame(data['values'])
        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True)
        
        # Convert to numeric
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col])
            
        return df
    
    async def get_indicator(self,
                          symbol: str,
                          indicator: str,
                          interval: str = '1min',
                          **kwargs) -> pd.DataFrame:
        """
        Obtiene indicador técnico
        
        Ejemplo:
            rsi = await client.get_indicator('BTC/USD', 'rsi', 
                                            time_period=14)
        """
        params = {
            'symbol': symbol,
            'interval': interval,
            **kwargs
        }
        
        data = await self._make_request(indicator, params)
        
        df = pd.DataFrame(data['values'])
        df['datetime'] = pd.to_datetime(df['datetime'])
        df.set_index('datetime', inplace=True)
        
        return df
```

### Símbolos Disponibles

#### Forex (Divisas)
```python
FOREX_SYMBOLS = [
    'EUR/USD',  # Euro/Dólar
    'GBP/USD',  # Libra/Dólar
    'USD/JPY',  # Dólar/Yen
    'USD/CHF',  # Dólar/Franco Suizo
    'AUD/USD',  # Dólar Australiano/USD
    'USD/CAD',  # USD/Dólar Canadiense
    'NZD/USD',  # Dólar Neozelandés/USD
]
```

#### Índices
```python
INDEX_SYMBOLS = [
    'SPX',      # S&P 500
    'NDX',      # NASDAQ-100
    'DJI',      # Dow Jones
    'RUT',      # Russell 2000
    'VIX',      # Volatility Index
]

# CFDs de Índices
CFD_SYMBOLS = [
    'NAS100',   # NASDAQ 100 CFD
    'US500',    # S&P 500 CFD
    'US30',     # Dow Jones CFD
]
```

#### Criptomonedas
```python
CRYPTO_SYMBOLS = [
    'BTC/USD',  # Bitcoin
    'ETH/USD',  # Ethereum
    'BNB/USD',  # Binance Coin
    'XRP/USD',  # Ripple
    'SOL/USD',  # Solana
    'ADA/USD',  # Cardano
]
```

## 🔧 MCP (Model Context Protocol) INTEGRATION

### ¿Qué es MCP?
MCP es un protocolo que permite a los modelos de IA interactuar con herramientas externas y APIs de forma estandarizada.

### Configuración de MCP para Trading

#### 1. Instalación del Servidor MCP
```bash
# Instalar MCP SDK
npm install @modelcontextprotocol/sdk

# Instalar dependencias
npm install express axios ws
```

#### 2. Configuración del Servidor MCP

```javascript
// mcp-trading-server.js

const { Server } = require('@modelcontextprotocol/sdk');
const TwelveDataAPI = require('./twelvedata-api');

class TradingMCPServer {
    constructor() {
        this.server = new Server({
            name: 'trading-mcp',
            version: '1.0.0',
            description: 'MCP server for algorithmic trading'
        });
        
        this.twelvedata = new TwelveDataAPI();
        this.setupTools();
    }
    
    setupTools() {
        // Registrar herramientas disponibles
        this.server.setRequestHandler('tools/list', async () => ({
            tools: [
                {
                    name: 'get_market_data',
                    description: 'Get real-time market data',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            symbol: { type: 'string' },
                            interval: { type: 'string' }
                        },
                        required: ['symbol']
                    }
                },
                {
                    name: 'analyze_market',
                    description: 'Analyze market with indicators',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            symbol: { type: 'string' },
                            indicators: { 
                                type: 'array',
                                items: { type: 'string' }
                            }
                        },
                        required: ['symbol']
                    }
                },
                {
                    name: 'execute_trade',
                    description: 'Execute a trading order',
                    inputSchema: {
                        type: 'object',
                        properties: {
                            symbol: { type: 'string' },
                            action: { 
                                type: 'string',
                                enum: ['buy', 'sell']
                            },
                            quantity: { type: 'number' },
                            stop_loss: { type: 'number' },
                            take_profit: { type: 'number' }
                        },
                        required: ['symbol', 'action', 'quantity']
                    }
                }
            ]
        }));
        
        // Implementar llamadas a herramientas
        this.server.setRequestHandler('tools/call', async (request) => {
            const { name, arguments: args } = request.params;
            
            switch(name) {
                case 'get_market_data':
                    return await this.getMarketData(args);
                    
                case 'analyze_market':
                    return await this.analyzeMarket(args);
                    
                case 'execute_trade':
                    return await this.executeTrade(args);
                    
                default:
                    throw new Error(`Unknown tool: ${name}`);
            }
        });
    }
    
    async getMarketData(args) {
        const { symbol, interval = '1min' } = args;
        
        // Obtener datos de TwelveData
        const data = await this.twelvedata.getTimeSeries(
            symbol, 
            interval,
            100
        );
        
        // Calcular métricas básicas
        const latest = data[0];
        const change = ((latest.close - latest.open) / latest.open) * 100;
        
        return {
            success: true,
            data: {
                symbol,
                price: latest.close,
                change: change.toFixed(2),
                volume: latest.volume,
                high: latest.high,
                low: latest.low,
                timestamp: latest.datetime
            }
        };
    }
    
    async analyzeMarket(args) {
        const { symbol, indicators = ['rsi', 'macd', 'bbands'] } = args;
        
        // Obtener datos históricos
        const ohlcv = await this.twelvedata.getTimeSeries(symbol, '5min', 500);
        
        // Obtener indicadores
        const analysis = {};
        
        for (const indicator of indicators) {
            const data = await this.twelvedata.getIndicator(
                symbol,
                indicator,
                '5min'
            );
            analysis[indicator] = data;
        }
        
        // Generar señal
        const signal = this.generateSignal(ohlcv, analysis);
        
        return {
            success: true,
            data: {
                symbol,
                signal: signal.direction,
                strength: signal.strength,
                indicators: analysis,
                recommendation: signal.recommendation
            }
        };
    }
    
    async executeTrade(args) {
        const { symbol, action, quantity, stop_loss, take_profit } = args;
        
        // Aquí se conectaría con MT5 o el broker
        // Por ahora, simulamos la ejecución
        
        const trade = {
            id: Date.now(),
            symbol,
            action,
            quantity,
            entry_price: await this.getCurrentPrice(symbol),
            stop_loss,
            take_profit,
            status: 'executed',
            timestamp: new Date().toISOString()
        };
        
        // Registrar trade
        await this.logTrade(trade);
        
        return {
            success: true,
            data: trade
        };
    }
    
    generateSignal(ohlcv, indicators) {
        // Lógica de generación de señales
        let bullishSignals = 0;
        let bearishSignals = 0;
        
        // RSI
        if (indicators.rsi) {
            const lastRSI = indicators.rsi[0].value;
            if (lastRSI < 30) bullishSignals++;
            if (lastRSI > 70) bearishSignals++;
        }
        
        // MACD
        if (indicators.macd) {
            const macd = indicators.macd[0];
            if (macd.histogram > 0) bullishSignals++;
            else bearishSignals++;
        }
        
        // Bollinger Bands
        if (indicators.bbands) {
            const bb = indicators.bbands[0];
            const price = ohlcv[0].close;
            if (price < bb.lower) bullishSignals++;
            if (price > bb.upper) bearishSignals++;
        }
        
        // Determinar dirección
        let direction = 'neutral';
        let strength = 0;
        
        if (bullishSignals > bearishSignals) {
            direction = 'buy';
            strength = bullishSignals / (bullishSignals + bearishSignals);
        } else if (bearishSignals > bullishSignals) {
            direction = 'sell';
            strength = bearishSignals / (bullishSignals + bearishSignals);
        }
        
        return {
            direction,
            strength,
            recommendation: this.getRecommendation(direction, strength)
        };
    }
    
    getRecommendation(direction, strength) {
        if (direction === 'neutral') {
            return 'Wait for better setup';
        }
        
        if (strength > 0.7) {
            return `Strong ${direction} signal - Consider entering position`;
        } else if (strength > 0.5) {
            return `Moderate ${direction} signal - Wait for confirmation`;
        } else {
            return `Weak ${direction} signal - Not recommended`;
        }
    }
    
    start() {
        this.server.connect();
        console.log('MCP Trading Server started');
    }
}

// Iniciar servidor
const server = new TradingMCPServer();
server.start();
```

#### 3. Configuración en Claude Desktop

```json
// claude_desktop_config.json
{
  "mcpServers": {
    "trading": {
      "command": "node",
      "args": ["path/to/mcp-trading-server.js"],
      "env": {
        "TWELVEDATA_API_KEY": "915b2ea02f7d49b986c1ae27d2711c73",
        "MT5_LOGIN": "your_mt5_login",
        "MT5_PASSWORD": "your_mt5_password",
        "MT5_SERVER": "your_mt5_server"
      }
    }
  }
}
```

### Uso del MCP en Claude

Una vez configurado, puedes usar comandos como:

```
"Analiza el mercado de NAS100"
"Obtén datos en tiempo real de EUR/USD"
"Genera señales de trading para BTC/USD"
"Ejecuta una operación de compra en GOLD"
```

## 📈 ANÁLISIS DE NAS100 CON TWELVEDATA

### Configuración Específica para NAS100

```python
class NAS100Analyzer:
    """
    Analizador especializado para NASDAQ 100
    """
    
    def __init__(self):
        self.symbol = 'NAS100'  # or 'NDX' for index
        self.client = TwelveDataClient()
        
    async def get_market_analysis(self) -> Dict:
        """
        Análisis completo del NAS100
        """
        # Obtener datos en múltiples timeframes
        data_1h = await self.client.get_time_series(self.symbol, '1h', 100)
        data_15m = await self.client.get_time_series(self.symbol, '15min', 200)
        
        # Obtener indicadores
        rsi = await self.client.get_indicator(self.symbol, 'rsi', '1h', time_period=14)
        macd = await self.client.get_indicator(self.symbol, 'macd', '1h')
        bb = await self.client.get_indicator(self.symbol, 'bbands', '1h')
        
        # Análisis de tendencia
        trend = self.analyze_trend(data_1h)
        
        # Niveles clave
        levels = self.calculate_key_levels(data_1h)
        
        # Señal consolidada
        signal = self.generate_signal({
            'trend': trend,
            'rsi': rsi.iloc[0]['rsi'],
            'macd': macd.iloc[0],
            'bb': bb.iloc[0],
            'price': data_15m.iloc[0]['close']
        })
        
        return {
            'symbol': self.symbol,
            'current_price': data_15m.iloc[0]['close'],
            'trend': trend,
            'signal': signal,
            'key_levels': levels,
            'indicators': {
                'rsi': rsi.iloc[0]['rsi'],
                'macd': macd.iloc[0]['macd'],
                'bb_upper': bb.iloc[0]['upper_band'],
                'bb_lower': bb.iloc[0]['lower_band']
            }
        }
    
    def analyze_trend(self, data: pd.DataFrame) -> str:
        """
        Analiza la tendencia actual
        """
        # Calcular EMAs
        data['ema20'] = data['close'].ewm(span=20).mean()
        data['ema50'] = data['close'].ewm(span=50).mean()
        
        current_price = data.iloc[0]['close']
        ema20 = data.iloc[0]['ema20']
        ema50 = data.iloc[0]['ema50']
        
        if current_price > ema20 > ema50:
            return 'bullish'
        elif current_price < ema20 < ema50:
            return 'bearish'
        else:
            return 'neutral'
    
    def calculate_key_levels(self, data: pd.DataFrame) -> Dict:
        """
        Calcula niveles de soporte y resistencia
        """
        highs = data['high'].values
        lows = data['low'].values
        
        # Pivot points
        pivot = (highs[0] + lows[0] + data.iloc[0]['close']) / 3
        r1 = 2 * pivot - lows[0]
        s1 = 2 * pivot - highs[0]
        
        return {
            'resistance_1': r1,
            'pivot': pivot,
            'support_1': s1,
            'daily_high': highs[0],
            'daily_low': lows[0]
        }
```

## 🔄 FLUJO DE TRABAJO COMPLETO

### 1. Inicialización
```python
# Iniciar sistema
system = AlgoTraderSystem()
system.configure_twelvedata(api_key='915b2ea02f7d49b986c1ae27d2711c73')
system.configure_mcp(server_path='./mcp-trading-server.js')
```

### 2. Análisis de Mercado
```python
# Analizar NAS100
analyzer = NAS100Analyzer()
analysis = await analyzer.get_market_analysis()
```

### 3. Generación de Señales
```python
# Generar señal de trading
signal_generator = SignalGenerator()
signal = signal_generator.generate(analysis)
```

### 4. Evaluación de Riesgo
```python
# Evaluar riesgo
risk_manager = RiskManager()
risk_assessment = risk_manager.evaluate_trade(signal)
```

### 5. Ejecución
```python
# Ejecutar trade si pasa validaciones
if risk_assessment['trade_allowed']:
    trade = await broker.execute_trade(signal)
```

## 📝 EJEMPLOS DE USO

### Ejemplo 1: Obtener Datos de NAS100
```python
async def get_nas100_data():
    client = TwelveDataClient()
    
    # Datos en tiempo real
    quote = await client.get_quote('NAS100')
    print(f"NAS100 Price: ${quote['price']}")
    
    # Datos históricos
    data = await client.get_time_series('NAS100', '5min', 100)
    print(f"Last 100 candles: {data}")
    
    # RSI
    rsi = await client.get_indicator('NAS100', 'rsi', time_period=14)
    print(f"Current RSI: {rsi.iloc[0]['rsi']}")
```

### Ejemplo 2: Análisis Multi-Timeframe
```python
async def multi_timeframe_analysis():
    analyzer = NAS100Analyzer()
    
    timeframes = ['1min', '5min', '15min', '1h', '4h']
    signals = {}
    
    for tf in timeframes:
        data = await analyzer.client.get_time_series('NAS100', tf, 100)
        signal = analyzer.analyze_timeframe(data)
        signals[tf] = signal
    
    # Consolidar señales
    final_signal = analyzer.consolidate_signals(signals)
    return final_signal
```

### Ejemplo 3: Trading Automatizado
```python
async def automated_trading():
    # Configurar sistema
    bot = TradingBot(
        symbol='NAS100',
        api_key='915b2ea02f7d49b986c1ae27d2711c73',
        risk_per_trade=0.01
    )
    
    # Loop de trading
    while True:
        # Obtener análisis
        analysis = await bot.analyze_market()
        
        # Generar señal
        signal = bot.generate_signal(analysis)
        
        # Ejecutar si hay señal fuerte
        if signal['strength'] > 0.7:
            await bot.execute_trade(signal)
        
        # Esperar próximo ciclo
        await asyncio.sleep(60)  # 1 minuto
```

## 🚨 CONSIDERACIONES IMPORTANTES

### Rate Limits de TwelveData
- **Plan Gratuito**: 8 requests/segundo, 800 requests/día
- **Plan Basic**: 120 requests/minuto
- **Plan Pro**: Sin límites

### Mejores Prácticas
1. **Cache de datos**: Almacenar datos históricos localmente
2. **Rate limiting**: Implementar control de peticiones
3. **Error handling**: Manejar errores de API gracefully
4. **Backup data source**: Tener fuente de datos alternativa

### Seguridad
1. **API Keys**: Nunca hardcodear, usar variables de entorno
2. **Conexiones seguras**: Siempre usar HTTPS
3. **Validación de datos**: Validar todos los datos recibidos
4. **Logs**: No loguear información sensible

---

**Última actualización**: 2024
**Versión**: 1.0.0
