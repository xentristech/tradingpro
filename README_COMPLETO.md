# 🤖 Algo Trader AI - Sistema de Trading Algorítmico con Inteligencia Artificial

## 📋 Tabla de Contenidos
- [Descripción General](#descripción-general)
- [Arquitectura del Sistema](#arquitectura-del-sistema)
- [Prerrequisitos](#prerrequisitos)
- [Instalación](#instalación)
- [Configuración](#configuración)
- [Uso](#uso)
- [Módulos del Sistema](#módulos-del-sistema)
- [Estrategia de Trading](#estrategia-de-trading)
- [Gestión de Riesgo](#gestión-de-riesgo)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)
- [Desarrollo](#desarrollo)
- [Seguridad](#seguridad)
- [Rendimiento](#rendimiento)
- [Roadmap](#roadmap)
- [Contribución](#contribución)
- [Licencia](#licencia)

## 📝 Descripción General

Algo Trader AI es un sistema de trading algorítmico avanzado que combina análisis técnico tradicional con inteligencia artificial local para operar en mercados de criptomonedas. El sistema está diseñado para operar de forma autónoma, tomando decisiones basadas en múltiples indicadores técnicos validados por un modelo de IA.

### Características Principales
- 🧠 **IA Local**: Utiliza Ollama con modelos como Deepseek-R1 para validación de señales
- 📊 **Análisis Multi-Timeframe**: Analiza 5m, 15m y 1h simultáneamente
- 🔒 **Seguridad First**: Modo demo por defecto, validaciones estrictas
- 📱 **Notificaciones en Tiempo Real**: Integración con Telegram
- 📈 **Dashboard Interactivo**: Interfaz web con Streamlit
- 🔄 **Gestión Automática**: Breakeven, cierres parciales, trailing stop
- 💾 **Persistencia de Datos**: SQLite para histórico de señales

## 🏗️ Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                         ENTRADA DE DATOS                      │
├────────────┬────────────────────────┬──────────────────────┤
│  MT5 API   │    TwelveData API      │   Market Data Cache  │
└────────────┴────────────────────────┴──────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    PROCESAMIENTO DE DATOS                    │
├──────────────────────────────────────────────────────────────┤
│  • Cálculo de Indicadores (RSI, MACD, RVOL)                │
│  • Normalización de Timeframes                              │
│  • Feature Engineering                                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    VALIDACIÓN CON IA                         │
├──────────────────────────────────────────────────────────────┤
│  • Ollama/OpenAI API Compatible                             │
│  • Prompts Especializados                                   │
│  • Guardrails de Precio (±0.3%)                            │
│  • Confluencia de Indicadores                               │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    EJECUCIÓN DE TRADES                       │
├──────────────────────────────────────────────────────────────┤
│  • MetaTrader 5 Integration                                 │
│  • Order Management                                         │
│  • Position Tracking                                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                 MONITOREO Y NOTIFICACIONES                   │
├──────────────────────────────────────────────────────────────┤
│  • Telegram Alerts                                          │
│  • Logging System                                           │
│  • Database Storage                                         │
│  • Web Dashboard                                            │
└─────────────────────────────────────────────────────────────┘
```

## 💻 Prerrequisitos

### Software Requerido

#### 1. Python 3.10+ (64-bit)
- **Windows**: Descargar de [python.org](https://www.python.org/downloads/)
- **Linux/Mac**: `brew install python@3.10` o usar pyenv
- ⚠️ **IMPORTANTE**: Marcar "Add Python to PATH" durante instalación

#### 2. MetaTrader 5
- Descargar desde tu broker (Exness, IC Markets, etc.)
- Crear cuenta demo para pruebas
- Habilitar algo trading en configuración

#### 3. Ollama (IA Local)
- **Windows**: Descargar de [ollama.ai](https://ollama.ai/download)
- **Linux**: `curl -fsSL https://ollama.ai/install.sh | sh`
- **Mac**: `brew install ollama`

#### 4. Modelos de IA
```bash
# Modelo recomendado (14B parámetros)
ollama pull deepseek-r1:14b

# Alternativas más ligeras
ollama pull llama3.1:7b
ollama pull mistral:7b
```

### Requisitos de Hardware
- **RAM**: Mínimo 8GB (16GB recomendado para modelos grandes)
- **CPU**: 4+ cores
- **Disco**: 20GB libres para modelos y datos
- **Red**: Conexión estable para APIs y trading

## 🚀 Instalación

### Instalación Automática (Windows)
```powershell
# Clonar repositorio
git clone https://github.com/tuusuario/algo-trader-mvp-v2.git
cd algo-trader-mvp-v2

# Setup automático
.\bot.ps1 setup
```

### Instalación Manual (Cross-platform)
```bash
# Clonar repositorio
git clone https://github.com/tuusuario/algo-trader-mvp-v2.git
cd algo-trader-mvp-v2

# Crear entorno virtual
python -m venv .venv

# Activar entorno
# Windows:
.\.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

## ⚙️ Configuración

### 1. Variables de Entorno
Crear `configs/.env` desde el template:

```bash
cp configs/.env.example configs/.env
```

Editar `configs/.env`:

```env
# === APIs Externas ===
TWELVEDATA_API_KEY=tu_api_key_aqui        # Obtener de twelvedata.com
TELEGRAM_TOKEN=tu_bot_token_aqui          # De @BotFather
TELEGRAM_CHAT_ID=tu_chat_id_aqui          # De @userinfobot

# === IA Local ===
OLLAMA_API_BASE=http://localhost:11434/v1
OLLAMA_MODEL=deepseek-r1:14b              # O tu modelo preferido

# === MetaTrader 5 ===
MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe
MT5_LOGIN=12345678                        # Tu número de cuenta
MT5_PASSWORD=tu_password                  # Contraseña MT5
MT5_SERVER=TuBroker-Demo                  # Servidor del broker
MT5_TIMEOUT=60000                          # Timeout en ms
MT5_DEVIATION=20                           # Desviación máxima en puntos
MT5_MAGIC=20250817                        # Magic number para identificar órdenes

# === Trading Config ===
LIVE_TRADING=false                        # NUNCA true hasta estar 100% seguro
SYMBOL=BTCUSDm                            # Símbolo a operar
DEF_SL_USD=50.0                           # Stop Loss por defecto en USD
DEF_TP_USD=100.0                          # Take Profit por defecto en USD
PIP_VALUE=1.0                             # Valor del pip

# === Sistema ===
TZ=America/Bogota                         # Tu zona horaria
DB_PATH=data/trading.db                   # Path base de datos
LOG_LEVEL=INFO                            # DEBUG, INFO, WARNING, ERROR
```

### 2. Configuración de Trading
Editar `configs/settings.yaml`:

```yaml
# Símbolos a monitorear
symbols:
  - BTCUSDm
  - ETHUSDm

# Timeframes para análisis
TIMEFRAMES:
  - "5min"
  - "15min"
  - "1h"

# Frecuencia de polling (segundos)
POLL_SECONDS: 20

# Trading
trade_enabled: true
min_confidence: 0.75      # Confianza mínima para operar (0-1)
max_positions: 3           # Máximo de posiciones simultáneas
max_daily_loss: 200.0      # Pérdida diaria máxima en USD

# Gestión de Riesgo
risk:
  risk_per_trade: 0.02     # 2% de riesgo por operación
  max_drawdown: 0.10       # 10% drawdown máximo
  breakeven_trigger: 1.5   # Mover a BE cuando profit = 1.5x riesgo
  partial_close: 0.5       # Cerrar 50% en primer TP

# Notificaciones
telegram:
  enabled: true
  parse_mode: MarkdownV2
  alert_on_signal: true
  alert_on_trade: true
  alert_on_error: true

# Indicadores
indicators:
  rsi:
    period: 14
    oversold: 30
    overbought: 70
  macd:
    fast: 12
    slow: 26
    signal: 9
  rvol:
    window: 20
    threshold: 1.3
```

### 3. Obtener API Keys

#### TwelveData (Datos de Mercado)
1. Registrarse en [twelvedata.com](https://twelvedata.com)
2. Plan gratuito: 800 calls/día
3. Copiar API key al `.env`

#### Telegram Bot
```bash
# En Telegram, hablar con @BotFather
/newbot
# Seguir instrucciones
# Copiar token al .env

# Obtener tu chat_id con @userinfobot
/start
# Copiar ID al .env
```

## 📊 Uso

### Comandos Básicos

#### Windows (PowerShell)
```powershell
# Iniciar bot
.\bot.ps1 start

# Ver estado
.\bot.ps1 status

# Ver logs en tiempo real
.\bot.ps1 logs

# Detener bot
.\bot.ps1 stop

# Reiniciar
.\bot.ps1 restart
```

#### Linux/Mac
```bash
# Iniciar bot
python orchestrator/run.py

# Con nohup para background
nohup python orchestrator/run.py > logs/run.log 2>&1 &

# Ver logs
tail -f logs/run.log
```

### Dashboard Web
```bash
# Iniciar dashboard (puerto 8501)
streamlit run streamlit_app.py

# Acceder en navegador
# http://localhost:8501
```

### Pruebas del Sistema

```bash
# Test conexión MT5
python test_mt5_connection.py

# Test Telegram
python test_telegram.py

# Test completo del sistema
python full_system_test.py

# Verificar sistema
python verify_system.py
```

## 📦 Módulos del Sistema

### 1. Broker Module (`broker/`)
Maneja la comunicación con MetaTrader 5.

```python
# broker/mt5.py
- init()                    # Inicializar conexión
- positions(symbol)         # Obtener posiciones abiertas
- close_position(ticket)    # Cerrar posición
- move_to_breakeven(ticket) # Mover SL a entrada
```

### 2. Signals Module (`signals/`)
Generación y validación de señales de trading.

```python
# signals/llm_validator.py
- validate_signal(snapshot) # Validar con IA
- reeval_position(data)     # Reevaluar posición abierta

# signals/schemas.py
- Setup                     # Modelo para entrada/SL/TP
- AIValidationResult        # Resultado de validación
```

### 3. Data Module (`data/`)
Obtención y procesamiento de datos de mercado.

```python
# data/twelvedata.py
- price(symbol)             # Precio actual
- indicator(symbol, name)   # Obtener indicador

# data/features.py
- rvol_from_series(volumes) # Calcular volumen relativo
```

### 4. Risk Module (`risk/`)
Gestión de riesgo y position sizing.

```python
# risk/position.py
- should_move_to_breakeven(rvol) # Lógica para breakeven
- calculate_position_size()       # Calcular tamaño de posición
```

### 5. Storage Module (`storage/`)
Persistencia en base de datos.

```python
# storage/db.py
- init()                    # Crear tablas
- insert_signal()           # Guardar señal
- last_signals(limit)       # Obtener últimas señales
```

### 6. Notifiers Module (`notifiers/`)
Sistema de notificaciones.

```python
# notifiers/telegram.py
- send_message(text)        # Enviar mensaje
- send_photo(photo_path)    # Enviar imagen
```

### 7. Orchestrator Module (`orchestrator/`)
Lógica principal y loops de ejecución.

```python
# orchestrator/run.py
- main()                    # Loop principal
- build_snapshot()          # Crear snapshot del mercado
```

## 📈 Estrategia de Trading

### Señales de Entrada

El sistema genera señales basándose en la confluencia de múltiples factores:

#### Condiciones para COMPRA:
1. **RSI**: > 55 en al menos 2 timeframes
2. **MACD Histogram**: Positivo y creciente
3. **RVOL**: >= 1.3 (volumen 30% superior al promedio)
4. **Confirmación IA**: Confianza > 75%

#### Condiciones para VENTA:
1. **RSI**: < 45 en al menos 2 timeframes
2. **MACD Histogram**: Negativo y decreciente
3. **RVOL**: >= 1.3
4. **Confirmación IA**: Confianza > 75%

### Gestión de Posiciones

```
ENTRADA
   │
   ├─> Precio alcanza 1.5x riesgo → Mover SL a Breakeven
   │
   ├─> RVOL < 0.9 → Considerar cierre parcial
   │
   ├─> Señal contraria → Cerrar posición
   │
   └─> TP/SL alcanzado → Cierre automático
```

## 🛡️ Gestión de Riesgo

### Position Sizing
```python
position_size = (account_balance * risk_per_trade) / (entry - stop_loss)
```

### Reglas de Riesgo
1. **Riesgo por operación**: Máximo 2% del capital
2. **Drawdown máximo**: 10% antes de detener trading
3. **Correlación**: No más de 3 posiciones correlacionadas
4. **Horario**: Evitar noticias de alto impacto

### Protecciones Automáticas
- Stop Loss obligatorio en todas las operaciones
- Breakeven automático cuando profit > 1.5x riesgo
- Cierre parcial del 50% en primer objetivo
- Kill switch si pérdida diaria > límite

## 🔌 API Reference

### REST Endpoints (Dashboard)

```http
GET /api/status
Response: {
  "running": true,
  "positions": 2,
  "daily_pnl": 150.50
}

GET /api/signals?limit=50
Response: [{
  "timestamp": "2024-01-15T10:30:00",
  "symbol": "BTCUSD",
  "signal": "BUY",
  "confidence": 0.85
}]

GET /api/performance
Response: {
  "total_trades": 100,
  "win_rate": 0.65,
  "profit_factor": 1.8
}
```

### WebSocket (Tiempo Real)
```javascript
ws://localhost:8501/ws

// Suscribirse a actualizaciones
{"action": "subscribe", "channel": "trades"}

// Recibir actualizaciones
{
  "type": "trade",
  "data": {
    "symbol": "BTCUSD",
    "action": "BUY",
    "price": 45000.50
  }
}
```

## 🔧 Troubleshooting

### Problemas Comunes

#### Error: "Python no encontrado"
```bash
# Windows: Reinstalar Python con "Add to PATH"
# Linux/Mac:
export PATH="$PATH:/usr/local/bin/python3"
```

#### Error: "MT5 connection failed"
```python
# Verificar en test_mt5_connection.py
1. MT5 está abierto
2. Credenciales correctas en .env
3. Servidor correcto
4. Firewall no bloquea MT5
```

#### Error: "Ollama not responding"
```bash
# Verificar Ollama está corriendo
ollama list  # Ver modelos instalados
ollama serve # Iniciar servidor

# Test manual
curl http://localhost:11434/api/generate -d '{
  "model": "deepseek-r1:14b",
  "prompt": "Hello"
}'
```

#### Error: "TwelveData rate limit"
```python
# Soluciones:
1. Reducir POLL_SECONDS en settings.yaml
2. Usar menos timeframes
3. Implementar cache local
4. Upgrade a plan pago
```

### Logs y Debugging

```bash
# Ver todos los logs
tail -f logs/*.log

# Logs específicos
tail -f logs/run_*.out.log      # Output principal
tail -f logs/run_*.err.log      # Errores
tail -f logs/positions_*.log    # Posiciones

# Modo debug
export LOG_LEVEL=DEBUG
python orchestrator/run.py
```

## 🚀 Desarrollo

### Estructura del Proyecto
```
algo-trader-mvp-v2/
├── broker/              # Integración con brokers
│   ├── __init__.py
│   └── mt5.py          # MetaTrader 5 wrapper
├── configs/            # Configuración
│   ├── .env.example    # Template variables
│   └── settings.yaml   # Config trading
├── data/               # Fuentes de datos
│   ├── candles.py      # Datos OHLCV
│   ├── features.py     # Feature engineering
│   └── twelvedata.py   # API wrapper
├── logs/               # Archivos de log
├── notifiers/          # Sistema de alertas
│   └── telegram.py     # Bot Telegram
├── orchestrator/       # Lógica principal
│   ├── positions.py    # Gestión posiciones
│   └── run.py         # Loop principal
├── risk/               # Gestión de riesgo
│   └── position.py     # Position sizing
├── signals/            # Generación señales
│   ├── llm_validator.py # Validación IA
│   ├── rules.py        # Reglas técnicas
│   └── schemas.py      # Modelos de datos
├── storage/            # Persistencia
│   └── db.py          # SQLAlchemy models
├── tests/              # Tests unitarios
├── utils/              # Utilidades
│   └── time.py        # Manejo de tiempo
├── backtester.py       # Sistema backtesting
├── bot.ps1            # Script control Windows
├── requirements.txt    # Dependencias Python
└── streamlit_app.py   # Dashboard web
```

### Agregar Nuevo Indicador

1. Editar `data/features.py`:
```python
def bollinger_bands(prices, period=20, std_dev=2):
    """Calcular Bandas de Bollinger"""
    sma = np.mean(prices[-period:])
    std = np.std(prices[-period:])
    upper = sma + (std * std_dev)
    lower = sma - (std * std_dev)
    return {"upper": upper, "middle": sma, "lower": lower}
```

2. Integrar en `orchestrator/run.py`:
```python
# En build_snapshot()
bb = bollinger_bands(prices)
tabla.append({
    "tf": tf,
    "bb_upper": bb["upper"],
    "bb_lower": bb["lower"],
    # ... otros indicadores
})
```

3. Actualizar prompt IA en `signals/llm_validator.py`

### Agregar Nuevo Exchange

1. Crear `broker/binance.py`:
```python
import ccxt

class BinanceConnector:
    def __init__(self):
        self.exchange = ccxt.binance({
            'apiKey': os.getenv('BINANCE_API_KEY'),
            'secret': os.getenv('BINANCE_SECRET'),
            'enableRateLimit': True,
        })
    
    def get_balance(self):
        return self.exchange.fetch_balance()
    
    def place_order(self, symbol, side, amount, price=None):
        # Implementar lógica de órdenes
        pass
```

### Testing

```bash
# Ejecutar todos los tests
pytest tests/

# Test específico
pytest tests/test_signals.py

# Con coverage
pytest --cov=. tests/

# Test de integración
python full_system_test.py
```

## 🔒 Seguridad

### Mejores Prácticas

1. **NUNCA** compartir archivos `.env`
2. **NUNCA** commitear credenciales
3. **SIEMPRE** usar cuenta demo primero
4. **SIEMPRE** validar inputs de usuario
5. **SIEMPRE** usar HTTPS para APIs

### Checklist de Seguridad

- [ ] `.env` en `.gitignore`
- [ ] Credenciales encriptadas
- [ ] Rate limiting implementado
- [ ] Validación de órdenes
- [ ] Logs sin información sensible
- [ ] Backup de configuración
- [ ] Kill switch configurado
- [ ] Límites de pérdida activos

### Auditoría

```bash
# Buscar credenciales en código
grep -r "password\|key\|token" --exclude-dir=.venv

# Verificar permisos de archivos
ls -la configs/

# Revisar logs por datos sensibles
grep -i "password\|token" logs/*.log
```

## 📊 Rendimiento

### Métricas del Sistema

| Métrica | Valor Esperado | Óptimo |
|---------|---------------|--------|
| Latencia orden | < 100ms | < 50ms |
| CPU uso | < 30% | < 15% |
| RAM uso | < 2GB | < 1GB |
| API calls/día | < 500 | < 200 |

### Optimización

```python
# Cache de datos
from functools import lru_cache

@lru_cache(maxsize=100)
def get_indicator_cached(symbol, timeframe):
    return calculate_indicator(symbol, timeframe)

# Procesamiento paralelo
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [
        executor.submit(process_timeframe, tf) 
        for tf in timeframes
    ]
```

### Backtesting

```bash
# Ejecutar backtest
python backtester.py \
  --symbol BTCUSD \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --initial-capital 10000

# Output esperado:
# Total Return: +45.3%
# Sharpe Ratio: 1.8
# Max Drawdown: -12.5%
# Win Rate: 65%
```

## 🗺️ Roadmap

### v2.1 (Q1 2025)
- [ ] Machine Learning para predicción
- [ ] Soporte multi-exchange
- [ ] API REST completa
- [ ] Mobile app

### v2.2 (Q2 2025)
- [ ] Arbitraje entre exchanges
- [ ] Options trading
- [ ] Social trading features
- [ ] Cloud deployment

### v3.0 (Q3 2025)
- [ ] DeFi integration
- [ ] Smart contracts
- [ ] Automated portfolio rebalancing
- [ ] Advanced risk metrics

## 🤝 Contribución

### Cómo Contribuir

1. Fork el proyecto
2. Crear feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add AmazingFeature'`)
4. Push al branch (`git push origin feature/AmazingFeature`)
5. Abrir Pull Request

### Guías de Estilo

- **Python**: PEP 8
- **Commits**: Conventional Commits
- **Documentación**: Google Style Docstrings

### Reporte de Bugs

Usar el template de issues en GitHub:
- Descripción clara del problema
- Pasos para reproducir
- Comportamiento esperado
- Screenshots si aplica
- Logs relevantes

## 📜 Licencia

Este proyecto está bajo licencia MIT. Ver archivo `LICENSE` para más detalles.

## ⚠️ Disclaimer

**IMPORTANTE**: Este software se proporciona "tal cual" sin garantías. El trading algorítmico conlleva riesgos significativos incluyendo la pérdida total del capital. 

- NO es asesoramiento financiero
- Úselo bajo su propio riesgo
- Pruebe exhaustivamente en demo antes de usar dinero real
- Los desarrolladores no son responsables de pérdidas

## 📞 Soporte

- **Documentation**: [docs.algo-trader.ai](https://docs.algo-trader.ai)
- **Discord**: [discord.gg/algotrader](https://discord.gg/algotrader)
- **Email**: support@algo-trader.ai
- **Issues**: [GitHub Issues](https://github.com/tuusuario/algo-trader-mvp-v2/issues)

## 🙏 Agradecimientos

- MetaTrader 5 por la plataforma de trading
- Ollama por IA local accesible
- TwelveData por datos de mercado
- Comunidad open source

---

**Desarrollado con ❤️ por el equipo de Algo Trader AI**

*Última actualización: Enero 2025*