# 🚀 ALGO TRADER v3.0 - Sistema Profesional de Trading Algorítmico con IA

## 🆕 Mejoras Implementadas en v3.0

### ✅ **Problemas Críticos Resueltos**

1. **Punto de Entrada Único** (`main_trader.py`)
   - Consolidación de múltiples archivos duplicados
   - CLI con argumentos para diferentes modos
   - Gestión centralizada del ciclo de vida

2. **State Manager Unificado** (`utils/state_manager.py`)
   - Gestión centralizada del estado del sistema
   - Persistencia automática cada 60 segundos
   - Thread-safe con locks
   - Tracking de posiciones, señales y errores

3. **Rate Limiter Inteligente** (`utils/rate_limiter.py`)
   - Token bucket algorithm
   - Límites configurables por API
   - Decorador @rate_limited para fácil uso
   - Estadísticas de uso y throttling

4. **MT5 Connection Manager** (`utils/mt5_connection.py`)
   - Reconexión automática en caso de desconexión
   - Health checks cada 30 segundos
   - Reintentos con backoff exponencial
   - Ejecución robusta de operaciones

## 📁 **Estructura del Proyecto v3.0**

```
algo-trader-mvp-v2/
│
├── 📄 main_trader.py          # ⭐ PUNTO DE ENTRADA ÚNICO
├── 📄 TRADER.bat             # Launcher Windows con menú
│
├── 📁 utils/                 # 🆕 Componentes mejorados
│   ├── state_manager.py     # Gestión de estado
│   ├── rate_limiter.py      # Control de APIs
│   ├── mt5_connection.py    # Conexión robusta MT5
│   └── logger_config.py     # Logging centralizado
│
├── 📁 orchestrator/          # Loop principal mejorado
│   └── run.py               # Integra todos los componentes
│
├── 📁 signals/               # Validación con IA
│   └── llm_validator.py     # Ollama/OpenAI integration
│
├── 📁 risk/                  # Gestión de riesgo
│   ├── advanced_risk.py     # Kelly Criterion, VaR
│   └── position.py          # Gestión de posiciones
│
├── 📁 data/                  # Indicadores y features
│   ├── advanced_indicators.py
│   ├── features.py
│   └── twelvedata.py
│
├── 📁 ml/                    # Machine Learning
│   └── trading_models.py    # XGBoost, LSTM
│
├── 📁 broker/                # Integración broker
│   └── mt5.py              
│
├── 📁 notifiers/             # Notificaciones
│   └── telegram.py          # Telegram mejorado
│
├── 📁 backtesting/           # Motor de backtesting
│   └── advanced_backtest.py
│
├── 📁 configs/               # Configuración
│   ├── .env                 # Variables de entorno
│   └── settings.yaml        # Parámetros trading
│
└── 📁 logs/                  # Logs con rotación
```

## 🚀 **Inicio Rápido**

### **Opción 1: Usar el Launcher Windows**
```batch
TRADER.bat
```
Menú interactivo con todas las opciones.

### **Opción 2: Línea de Comandos**
```bash
# Modo DEMO (por defecto)
python main_trader.py

# Modo Paper Trading
python main_trader.py --mode paper

# Modo LIVE (requiere confirmación)
python main_trader.py --mode live

# Solo verificar sistema
python main_trader.py --check

# Usar configuración personalizada
python main_trader.py --config configs/custom.env
```

## ⚙️ **Configuración**

### **1. Variables de Entorno (.env)**
```env
# APIs
TWELVEDATA_API_KEY=tu_api_key
TELEGRAM_TOKEN=tu_bot_token
TELEGRAM_CHAT_ID=tu_chat_id

# MT5
MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe
MT5_LOGIN=tu_cuenta
MT5_PASSWORD=tu_password
MT5_SERVER=tu_servidor

# Trading
SYMBOL=BTCUSDm
LIVE_TRADING=false  # IMPORTANTE: false para demo
MIN_CONFIDENCE=0.75
MAX_RISK_PER_TRADE=0.02
MAX_PORTFOLIO_RISK=0.06
MAX_POSITIONS=3
MAX_DAILY_LOSS=200.0

# IA
OLLAMA_API_BASE=http://localhost:11434/v1
OLLAMA_MODEL=deepseek-r1:14b

# Sistema
LOG_LEVEL=INFO
POLL_SECONDS=20
```

### **2. Configuración de Trading (settings.yaml)**
```yaml
symbols:
  - BTCUSDm
  
telegram:
  enabled: true
  parse_mode: HTML
  
trade_enabled: true
min_confidence: 0.75

risk_management:
  use_breakeven: true
  use_trailing: true
  trailing_distance: 30
  breakeven_trigger: 20
```

## 📊 **Características Principales**

### **🧠 Inteligencia Artificial**
- Validación de señales con Ollama/OpenAI
- Multi-timeframe analysis (5m, 15m, 1h)
- JSON schema validation
- Guardrails y fallbacks

### **💰 Risk Management Profesional**
- Kelly Criterion para sizing óptimo
- Value at Risk (VaR) al 95%
- Control de drawdown máximo
- Gestión de correlación
- Stop loss dinámico con ATR

### **📈 Indicadores Técnicos Avanzados**
- VWAP/TWAP
- Volume Profile con POC
- Order Flow Imbalance
- Market Regime Detection
- Support/Resistance dinámicos

### **🤖 Machine Learning**
- XGBoost para predicción
- Feature engineering automático (50+ features)
- Walk-forward optimization
- Ensemble methods

### **🔄 Sistema Robusto**
- Reconexión automática MT5
- Rate limiting inteligente
- Estado persistente
- Health checks continuos
- Logging con rotación

## 📈 **Monitoreo**

### **Dashboard Web (Streamlit)**
```bash
streamlit run streamlit_app.py
```
Acceder en: http://localhost:8501

### **Logs en Tiempo Real**
```bash
# Windows
type logs\algo_trader_*.log | more

# PowerShell
Get-Content logs\algo_trader_*.log -Tail 50 -Wait
```

### **Notificaciones Telegram**
- Apertura/cierre de operaciones
- Señales detectadas
- Errores del sistema
- Resumen diario

## 🧪 **Testing**

### **Test de Conexión MT5**
```python
python -c "from utils.mt5_connection import MT5ConnectionManager; m = MT5ConnectionManager(); print(m.connect())"
```

### **Test de Rate Limiter**
```python
python -c "from utils.rate_limiter import RateLimiter; r = RateLimiter(); print(r.get_remaining_calls('twelvedata'))"
```

### **Test de State Manager**
```python
python -c "from utils.state_manager import StateManager; s = StateManager(); print(s.get_health_status())"
```

## 🛡️ **Seguridad**

1. **Nunca activar LIVE_TRADING sin:**
   - Mínimo 1 mes en demo
   - Backtest con resultados positivos
   - Paper trading exitoso
   - Capital que puedas perder

2. **Límites de Seguridad:**
   - Max daily loss: $200
   - Max positions: 3
   - Max risk per trade: 2%
   - Min confidence: 75%

3. **Monitoreo Obligatorio:**
   - Telegram activo
   - Logs revisados diariamente
   - Health checks cada 30s
   - Auto-shutdown en errores críticos

## 🐛 **Troubleshooting**

### **"MT5 no se conecta"**
```python
# Verificar credenciales
python test_mt5_connection.py

# Verificar que MT5 esté abierto
# Verificar servidor correcto en .env
```

### **"Rate limit excedido"**
```python
# Ver límites actuales
from utils.rate_limiter import RateLimiter
r = RateLimiter()
print(r.get_stats())

# Resetear límites (solo testing)
r.reset_limits('twelvedata')
```

### **"Estado corrupto"**
```bash
# Backup estado actual
copy data\system_state.json data\system_state.backup.json

# Borrar estado
del data\system_state.json

# Reiniciar sistema
python main_trader.py
```

## 📚 **Documentación API**

### **State Manager**
```python
from utils.state_manager import StateManager, TradingState

sm = StateManager()
sm.set_trading_state(TradingState.ANALYZING)
sm.add_signal({'symbol': 'BTCUSD', 'signal': 'BUY'})
stats = sm.get_session_stats()
```

### **Rate Limiter**
```python
from utils.rate_limiter import rate_limited

@rate_limited('twelvedata', cost=1.0)
def get_data():
    # Tu código aquí
    pass
```

### **MT5 Connection**
```python
from utils.mt5_connection import MT5ConnectionManager

mt5 = MT5ConnectionManager()
mt5.connect()
positions = mt5.get_open_positions()
mt5.place_order(request_dict)
```

## 🎯 **Roadmap v3.1**

- [ ] WebSocket para datos en tiempo real
- [ ] Dashboard React profesional
- [ ] Backtesting distribuido
- [ ] Optimización con Ray/Optuna
- [ ] Integración con más exchanges
- [ ] Mobile app para monitoreo
- [ ] Cloud deployment (AWS/GCP)

## 📝 **Licencia**

Uso privado. No distribuir sin autorización.

## 🤝 **Soporte**

Para soporte, revisar logs en `logs/` o contactar al desarrollador.

---

**⚠️ DISCLAIMER**: Trading algorítmico conlleva riesgos significativos. Este software se proporciona "como está" sin garantías. Úsalo bajo tu propio riesgo. Siempre prueba exhaustivamente en demo antes de usar dinero real.

---

**Versión**: 3.0.0  
**Última actualización**: Enero 2025  
**Desarrollado por**: Xentristech
