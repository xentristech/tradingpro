# 🚀 Trading Pro - AI-Powered Algorithmic Trading System

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![MetaTrader5](https://img.shields.io/badge/MetaTrader-5-orange.svg)](https://www.metatrader5.com/)
[![TwelveData](https://img.shields.io/badge/TwelveData-API-green.svg)](https://twelvedata.com/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)](LICENSE)

## 📋 Overview

Trading Pro is an advanced algorithmic trading system that combines artificial intelligence with technical analysis to generate trading signals for Forex, Commodities, and Cryptocurrencies. The system features real-time market analysis, automated trade execution, and intelligent risk management.

### 🎯 Key Features

- **AI-Powered Analysis**: Integration with Ollama (DeepSeek-R1 14B model) for intelligent market analysis
- **Multi-Asset Support**: Trade XAU/USD (Gold), BTC/USD (Bitcoin), EUR/USD, GBP/USD
- **Dual Strategy System**: 
  - AI Hybrid Strategy (Technical + AI Analysis)
  - Multi-Timeframe Strategy (5min, 15min, 30min, 1h convergence)
- **Automated Trading**: Direct integration with MetaTrader 5 for automatic order execution
- **Risk Management**: Dynamic SL/TP calculation based on ATR, position monitoring every 30 seconds
- **Real-Time Data**: TwelveData API integration for live market data and indicators
- **Telegram Notifications**: Real-time alerts for trades and system status

## 🏗️ Architecture

```
algo-trader-mvp-v2/
├── src/
│   ├── signals/              # Trading strategies
│   │   ├── ai_hybrid_strategy.py
│   │   ├── multi_timeframe_strategy.py
│   │   └── advanced_signal_generator.py
│   ├── broker/               # MT5 integration
│   │   └── mt5_connection.py
│   ├── data/                 # Data providers
│   │   └── twelvedata_client.py
│   ├── ai/                   # AI integration
│   │   └── ollama_client.py
│   └── notifiers/            # Notifications
│       └── telegram_notifier.py
├── configs/
│   └── .env                  # Configuration
├── tests/                    # Test files
└── START_TRADING_SYSTEM_MONITOR_PRIORITY_CLEAN.py  # Main entry point
```

## 🔧 Installation

### Prerequisites

- Python 3.9 or higher
- MetaTrader 5 Terminal
- Ollama with DeepSeek-R1 model
- TwelveData API key (PRO plan recommended)

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/xentristech/tradingpro.git
cd tradingpro
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**
```bash
cp configs/.env.example configs/.env
# Edit configs/.env with your credentials
```

4. **Install and configure Ollama**
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull the DeepSeek model
ollama pull deepseek-r1:14b
```

5. **Configure MetaTrader 5**
- Install MT5 from your broker
- Enable automated trading in MT5
- Update MT5_PATH in .env file

## ⚙️ Configuration

### Environment Variables (.env)

```env
# API Keys
TWELVEDATA_API_KEY=your_api_key_here
TELEGRAM_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# MetaTrader 5
MT5_PATH=C:\\Program Files\\MetaTrader 5\\terminal64.exe
MT5_LOGIN=your_account_number
MT5_PASSWORD=your_password
MT5_SERVER=your_broker_server

# Trading Configuration
RISK_PER_TRADE=0.01  # 1% risk per trade
MAX_CONCURRENT_TRADES=3

# AI Configuration
OLLAMA_API_BASE=http://localhost:11434/v1
OLLAMA_MODEL=deepseek-r1:14b
```

## 🚀 Usage

### Starting the System

```bash
# Run the main trading system with priority monitoring
python START_TRADING_SYSTEM_MONITOR_PRIORITY_CLEAN.py
```

### System Components

1. **Signal Generator**: Analyzes markets every 60 seconds
2. **SL/TP Monitor**: Checks and corrects positions every 30 seconds
3. **AI Analysis**: Processes market data through Ollama for decisions
4. **Auto Execution**: Places trades automatically when signals meet criteria

### Trading Schedule

| Asset | Trading Hours (UTC) |
|-------|-------------------|
| **BTC/USD** | 24/7 |
| **XAU/USD** | Sunday 22:00 - Friday 22:00 |
| **EUR/USD** | Sunday 22:00 - Friday 22:00 |
| **GBP/USD** | Sunday 22:00 - Friday 22:00 |

## 📊 Arquitectura del Sistema

### Componentes Principales

```
📁 src/
├── 🤖 ai/
│   └── ollama_client.py          # Cliente Ollama IA
├── 🔌 broker/
│   └── mt5_connection.py         # Conexión MT5 mejorada
├── 📈 data/
│   └── twelvedata_client.py      # Cliente TwelveData API
├── 📡 notifications/
│   └── telegram_notifier.py      # Notificaciones Telegram
└── 📊 signals/
    ├── advanced_signal_generator.py  # Generador principal
    └── ai_hybrid_strategy.py         # Estrategia IA Híbrida
```

### Flujo de Funcionamiento

```mermaid
graph TD
    A[Inicio del Sistema] --> B[Conectar Ollama + TwelveData]
    B --> C[Verificar MT5 cada 60s]
    C --> D[Obtener Datos Reales]
    D --> E{Datos Válidos?}
    E -->|No| F[No Generar Señales]
    E -->|Sí| G[Análisis IA Multi-TF]
    G --> H[Generar Señal]
    H --> I[Monitorear Posiciones]
    I --> J{Trade sin SL/TP?}
    J -->|Sí| K[Notificar + Corregir]
    J -->|No| L[Continuar Monitoreo]
    K --> L
    L --> C
```

## 🛡️ Sistema de Detección y Corrección

### Detección Automática
- **Frecuencia**: Cada 60 segundos
- **Método**: Triple verificación MT5 (terminal_info, account_info, last_error)
- **Cobertura**: Todas las posiciones abiertas sin excepción

### Corrección Inteligente
```python
# Ejemplo de cálculo automático
if position_type == 'BUY':
    stop_loss = entry_price - (atr * 2.0)    # Riesgo: 2x ATR
    take_profit = entry_price + (atr * 3.0)   # Beneficio: 3x ATR
else:  # SELL
    stop_loss = entry_price + (atr * 2.0)
    take_profit = entry_price - (atr * 3.0)
```

### Notificaciones de Detección
```
🚨 **TRADE SIN PROTECCION DETECTADO** 🚨

Simbolo: BTCUSD
Ticket: #12345
Tipo: BUY
Volumen: 0.1 lotes
Precio Entrada: 67245.50
Estado: Sin SL, Sin TP
P&L Actual: -15.25 USD

⚠️ Corrigiendo automáticamente...
```

### Confirmación de Corrección
```
✅ **POSICION CORREGIDA EXITOSAMENTE** ✅

📊 **Detalles:**
Simbolo: BTCUSD
Tipo: BUY
Ticket: #12345
Volumen: 0.1 lotes
Precio Entrada: 67245.50

🛡️ **Protección Agregada:**
Stop Loss: 67100.25 (NUEVO)
Take Profit: 67390.75 (NUEVO)
ATR usado: 145.25
Riesgo: 2x ATR | Beneficio: 3x ATR

📈 **Estadísticas:**
Total Correcciones Hoy: 1
```

## 📈 Características Avanzadas

### Reconexión Automática MT5
- **Detección Multi-Nivel**: 
  - `mt5.terminal_info()` - Verifica si MT5 está corriendo
  - `mt5.account_info()` - Verifica información de cuenta  
  - `mt5.last_error()` - Verifica errores de MT5
- **Frecuencia**: Cada ciclo (60 segundos)
- **Notificaciones**: Telegram inmediato al reconectar

### Gestión de Mercados
- **Forex**: Solo durante horarios de mercado (Dom 22:00 - Vie 22:00 UTC)
- **Crypto**: 24/7 (BTCUSD siempre activo)
- **Detección Automática**: Sistema identifica símbolos activos

### Estrategia IA Híbrida
- **Análisis Multi-Timeframe**: Combina 5min, 15min, 1h
- **Indicadores Reales**: RSI, MACD, ATR, Bollinger Bands desde TwelveData
- **Procesamiento IA**: Ollama deepseek-r1:14b para decisiones inteligentes
- **Umbral de Confianza**: Solo ejecuta señales >70% confianza

## 🔍 Logs y Monitoreo

### Logs del Sistema
```
[Ciclo 0001] 23:16:31 - Analizando mercados...
  -> MT5: Conexion verificada
🎯 AI Hybrid Analysis #1 para BTCUSD
✅ Datos reales obtenidos para BTCUSD: 100 barras
🤖 Analizando BTCUSD con IA...
✅ Señal IA generada: BTCUSD BUY (Fuerza: 85.2%)
  -> 1 senales generadas
  -> Trades ejecutados: 1
  -> Posiciones corregidas: 0
```

### Estados del Sistema
- **Señales generadas**: Contador total de señales
- **Trades ejecutados**: Operaciones ejecutadas en MT5
- **Posiciones corregidas**: Trades corregidos automáticamente
- **Estado MT5**: Conexión en tiempo real

## ⚠️ Políticas de Seguridad

### Datos Reales Únicamente
- **🚫 CERO Datos Simulados**: Sistema rechaza cualquier dato sintético
- **✅ Solo TwelveData**: Fuente única de datos de mercado
- **✅ Solo Ollama IA**: Análisis únicamente con IA real
- **❌ Fallback Desactivado**: No hay análisis de respaldo tradicional

### Gestión de Errores
- **API Falla** → **No genera señales** (sistema se detiene hasta tener datos reales)
- **IA Falla** → **No opera** (requiere análisis IA válido)
- **MT5 Desconectado** → **Reconexión automática** + notificación

## 📋 Comandos Útiles

### Testing y Verificación
```bash
# Test completo del sistema
python TEST_MT5_RECONNECTION_ENHANCED.py

# Verificar conexiones
python -c "from src.data.twelvedata_client import TwelveDataClient; TwelveDataClient()"
python -c "from src.ai.ollama_client import OllamaClient; OllamaClient().test_connection()"

# Estado MT5
python -c "from src.broker.mt5_connection import MT5Connection; MT5Connection().connect()"
```

### Monitoreo en Vivo
```bash
# Seguir logs del sistema
tail -f logs/trading.log

# Monitor de posiciones
watch -n 60 "python -c 'from src.broker.mt5_connection import MT5Connection; conn=MT5Connection(); conn.connect(); print(conn.get_positions())'"
```

## 📊 Estadísticas y Performance

### Métricas del Sistema
- **Tiempo de Detección**: <60 segundos (trades sin SL/TP)
- **Tiempo de Corrección**: <5 segundos (modificación automática)
- **Precisión IA**: >70% confianza mínima
- **Uptime**: 24/7 con reconexión automática

### Configuraciones Optimizadas
- **Ciclo de Análisis**: 60 segundos (balance velocidad/recursos)
- **Verificación MT5**: Cada ciclo (detección rápida)
- **Timeout API**: 15 segundos (evita bloqueos)
- **Rate Limiting**: 0.5s entre llamadas API

## 🔄 Actualizaciones Implementadas

### Versión 3.0 (Actual)
- ✅ **Detección automática trades sin SL/TP**
- ✅ **Corrección automática con ATR dinámico** 
- ✅ **Eliminación completa de datos simulados**
- ✅ **Reconexión MT5 mejorada (5x más rápida)**
- ✅ **Solo estrategia IA Híbrida con datos reales**
- ✅ **Notificaciones Telegram detalladas**

### Cambios Críticos
```python
# ANTES: Generaba señales simuladas cuando fallaba la API
if not market_data:
    return self.fallback_analysis()  # ❌ DATOS SIMULADOS

# DESPUÉS: NO genera señales sin datos reales  
if not market_data:
    return []  # ✅ SOLO DATOS REALES
```

## 🆘 Solución de Problemas

### Error: "apikey parameter is incorrect"
```bash
# Verificar API key en .env
echo $TWELVEDATA_API_KEY

# Obtener nueva API key
# https://twelvedata.com/pricing
```

### Error: "MT5 initialize failed"
```bash
# Verificar MT5 corriendo
tasklist | findstr terminal64

# Verificar credenciales en .env
cat configs/.env | grep MT5
```

### Error: "Ollama connection failed"
```bash
# Verificar Ollama corriendo
curl http://localhost:11434/api/tags

# Iniciar Ollama
ollama serve
```

## 📞 Soporte

### Estructura del Proyecto
- **Configuración**: `configs/.env`
- **Logs**: `logs/`
- **Tests**: `TEST_*.py`
- **Principal**: `START_TRADING_SYSTEM.py`

### Contacto
Para soporte técnico, revisa los logs del sistema y verifica:
1. ✅ APIs conectadas (TwelveData + Telegram)
2. ✅ Ollama corriendo con deepseek-r1:14b
3. ✅ MT5 abierto con credenciales correctas
4. ✅ Permisos de trading habilitados

---

## 🎯 **IMPORTANTE: SOLO DATOS REALES**

Este sistema está configurado para usar **ÚNICAMENTE datos reales** de TwelveData API con análisis de Inteligencia Artificial de Ollama. **NO se generan señales con datos simulados o sintéticos bajo ninguna circunstancia.**

**🚫 Sin datos reales = Sin señales = Sin trading**

---

**© 2025 Algo Trader V3 - Sistema de Trading Automático con IA Real**