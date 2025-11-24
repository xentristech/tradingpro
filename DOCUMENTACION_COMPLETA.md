# 📚 DOCUMENTACIÓN COMPLETA - ALGO TRADER AI v3.0

## 🏗️ ARQUITECTURA DEL SISTEMA

### Estructura del Proyecto
```
algo-trader-mvp-v2/
├── src/                    # Código fuente principal
│   ├── ai/                # Módulos de IA
│   ├── broker/            # Conexión con brokers
│   ├── core/              # Núcleo del sistema
│   ├── data/              # Gestión de datos
│   ├── director/          # Orquestador principal
│   ├── journal/           # Sistema de journaling
│   ├── ml/                # Machine Learning
│   ├── notifiers/         # Notificaciones
│   ├── risk/              # Gestión de riesgo
│   ├── signals/           # Generación de señales
│   ├── trading/           # Ejecución de trades
│   ├── ui/                # Interfaces de usuario
│   └── utils/             # Utilidades
├── configs/               # Configuraciones
├── storage/               # Almacenamiento persistente
├── logs/                  # Registros del sistema
├── tests/                 # Pruebas
└── tools/                 # Herramientas auxiliares
```

## 📦 COMPONENTES PRINCIPALES

### 1. MAIN.PY - Punto de Entrada Principal
```python
def main():
    """
    Función principal con CLI
    
    Comandos disponibles:
    - start: Inicia el bot de trading
    - stop: Detiene el bot
    - status: Muestra estado del sistema
    - test: Ejecuta pruebas
    - backtest: Ejecuta backtesting
    - optimize: Optimiza estrategias
    
    Argumentos:
    --mode: demo/live/paper
    --symbol: Símbolo a operar
    --config: Archivo de configuración
    --debug: Modo debug
    --no-telegram: Desactiva Telegram
    """
```

### 2. BOT MANAGER (src/core/bot_manager.py)
```python
class BotManager:
    """
    Gestor principal del bot de trading
    Coordina todos los componentes del sistema
    
    Métodos principales:
    - __init__(config_path): Inicializa el bot
    - start(): Inicia el bot de trading
    - stop(): Detiene el bot
    - get_status(): Obtiene estado actual
    - _initialize_components(): Inicializa componentes
    - _trading_loop(): Loop principal de trading
    """
```

### 3. SIGNAL GENERATOR (src/signals/signal_generator.py)
```python
class SignalGenerator:
    """
    Generador de señales usando múltiples estrategias
    
    Estrategias implementadas:
    - trend_following: Seguimiento de tendencia
    - mean_reversion: Reversión a la media
    - momentum: Momentum y velocidad
    - support_resistance: Soportes y resistencias
    - pattern_recognition: Reconocimiento de patrones
    
    Métodos:
    - generate(data): Genera señal consolidada
    - _trend_following_strategy(): Estrategia de tendencia
    - _momentum_strategy(): Estrategia de momentum
    - _calculate_signal_strength(): Calcula fuerza de señal
    """
```

### 4. RISK MANAGER (src/risk/risk_manager.py)
```python
class RiskManager:
    """
    Gestor profesional de riesgo
    
    Características:
    - Kelly Criterion para sizing
    - Value at Risk (VaR)
    - Control de drawdown
    - Límites de pérdida diaria
    - Gestión de correlaciones
    
    Métodos:
    - evaluate_trade(): Evalúa si permitir trade
    - calculate_position_size(): Calcula tamaño de posición
    - update_metrics(): Actualiza métricas
    - check_risk_limits(): Verifica límites
    - apply_kelly_criterion(): Aplica Kelly
    """
```

### 5. ML PREDICTOR (src/ml/ml_predictor.py)
```python
class MLPredictor:
    """
    Sistema de predicción con Machine Learning
    
    Modelos:
    - XGBoost (40% peso)
    - Random Forest (30% peso)
    - Gradient Boosting (30% peso)
    
    Métodos:
    - predict(data): Genera predicción
    - train_models(): Entrena modelos
    - evaluate_models(): Evalúa performance
    - ensemble_prediction(): Predicción ensemble
    """
```

## 🤖 MÓDULOS DE IA

### AI_TRADING_ASSISTANT.py
```python
class AITradingAssistant:
    """
    Asistente de trading con IA
    
    Funciones:
    - analyze_market(): Análisis de mercado con IA
    - generate_insights(): Genera insights
    - predict_movements(): Predice movimientos
    - recommend_actions(): Recomienda acciones
    """
```

### AI_SIGNAL_ALERT_SYSTEM.py
```python
class AISignalAlertSystem:
    """
    Sistema de alertas inteligente
    
    Funciones:
    - detect_opportunities(): Detecta oportunidades
    - filter_signals(): Filtra señales por calidad
    - prioritize_alerts(): Prioriza alertas
    - send_notifications(): Envía notificaciones
    """
```

### AI_OPPORTUNITY_HUNTER.py
```python
class AIOpportunityHunter:
    """
    Cazador de oportunidades con IA
    
    Funciones:
    - scan_markets(): Escanea mercados
    - identify_patterns(): Identifica patrones
    - calculate_probability(): Calcula probabilidad
    - rank_opportunities(): Clasifica oportunidades
    """
```

## 📊 SISTEMAS DE TRADING

### SISTEMA_COMPLETO_INTEGRADO.py
```python
class SistemaCompletoIntegrado:
    """
    Sistema completo de trading integrado
    
    Componentes:
    - Análisis técnico
    - Análisis con IA
    - Gestión de riesgo
    - Ejecución automática
    - Monitoreo en tiempo real
    """
```

### ADVANCED_SIGNAL_GENERATOR.py
```python
class AdvancedSignalGenerator:
    """
    Generador avanzado de señales
    
    Técnicas:
    - Multi-timeframe analysis
    - Volume profile analysis
    - Order flow analysis
    - Sentiment analysis
    - Machine learning predictions
    """
```

### AI_AUTO_BREAKEVEN_SYSTEM.py
```python
class AIAutoBreakevenSystem:
    """
    Sistema automático de breakeven
    
    Funciones:
    - monitor_positions(): Monitorea posiciones
    - calculate_breakeven_point(): Calcula punto BE
    - apply_breakeven(): Aplica breakeven
    - adjust_trailing_stop(): Ajusta trailing stop
    """
```

## 🛡️ GESTIÓN DE RIESGO

### EMERGENCY_RISK_MANAGER.py
```python
class EmergencyRiskManager:
    """
    Gestor de riesgo de emergencia
    
    Funciones:
    - detect_emergency(): Detecta emergencias
    - close_all_positions(): Cierra todas las posiciones
    - reduce_exposure(): Reduce exposición
    - notify_admin(): Notifica administrador
    """
```

### AI_ATR_INTELLIGENT_RISK_CALCULATOR.py
```python
class AIATRRiskCalculator:
    """
    Calculador inteligente de riesgo con ATR
    
    Funciones:
    - calculate_atr(): Calcula ATR
    - determine_stop_loss(): Determina SL dinámico
    - determine_take_profit(): Determina TP dinámico
    - adjust_for_volatility(): Ajusta por volatilidad
    """
```

## 📈 DASHBOARDS Y MONITOREO

### DASHBOARD_TIEMPO_REAL.py
```python
class DashboardTiempoReal:
    """
    Dashboard en tiempo real
    
    Características:
    - Gráficos en vivo
    - Métricas de performance
    - Estado de posiciones
    - Señales activas
    - Logs en tiempo real
    """
```

### MONITOR_SISTEMA.py
```python
class MonitorSistema:
    """
    Monitor del sistema completo
    
    Monitorea:
    - Conexión MT5
    - APIs de datos
    - Modelos ML
    - Sistema de notificaciones
    - Performance general
    """
```

## 🔧 UTILIDADES

### DIAGNOSTICO_COMPLETO.py
```python
def diagnostico_completo():
    """
    Diagnóstico completo del sistema
    
    Verifica:
    - Conexiones activas
    - Estado de componentes
    - Configuraciones
    - Errores y warnings
    - Performance
    """
```

### VERIFICAR_TODO.py
```python
def verificar_todo():
    """
    Verificación completa del sistema
    
    Checks:
    - MT5 connection
    - Data APIs
    - ML models
    - Risk limits
    - Positions status
    """
```

## 📡 CONECTORES Y APIs

### MT5 Connection (src/broker/mt5_connection.py)
```python
class MT5Connection:
    """
    Conexión con MetaTrader 5
    
    Métodos:
    - connect(): Conecta a MT5
    - disconnect(): Desconecta
    - place_order(): Coloca orden
    - close_position(): Cierra posición
    - get_positions(): Obtiene posiciones
    - get_account_info(): Info de cuenta
    """
```

### Data Manager (src/data/data_manager.py)
```python
class DataManager:
    """
    Gestor de datos de mercado
    
    Fuentes:
    - TwelveData API
    - MT5 Historical
    - Cached data
    
    Métodos:
    - get_data(): Obtiene datos OHLCV
    - get_indicators(): Calcula indicadores
    - get_realtime(): Datos en tiempo real
    """
```

## 🔐 CONFIGURACIÓN Y SEGURIDAD

### Variables de Entorno (.env)
```env
# MT5 Configuration
MT5_LOGIN=tu_login
MT5_PASSWORD=tu_password
MT5_SERVER=tu_servidor

# API Keys
TWELVEDATA_API_KEY=tu_api_key
OPENAI_API_KEY=tu_api_key (opcional)

# Trading Config
SYMBOL=BTCUSDm
RISK_PER_TRADE=0.01
MAX_CONCURRENT_TRADES=3

# Notifications
TELEGRAM_TOKEN=tu_token
TELEGRAM_CHAT_ID=tu_chat_id

# Mode
LIVE_TRADING=false
ML_ENABLED=true
```

## 🚀 EJECUCIÓN

### Modo Demo
```bash
python main.py start --mode demo
```

### Modo Live (Requiere confirmación)
```bash
python main.py start --mode live
```

### Sistema Completo con Monitoreo
```bash
python SISTEMA_COMPLETO_INTEGRADO.py
```

### Solo Señales
```bash
python ADVANCED_SIGNAL_GENERATOR.py
```

## 📊 BACKTESTING

### Ejecutar Backtest
```bash
python backtester.py --symbol BTCUSD --start 2024-01-01 --end 2024-12-31
```

## 🔍 TESTING Y DEBUGGING

### Test Completo
```bash
python main.py test
```

### Test Específicos
```bash
python test_mt5_quick.py        # Test MT5
python test_signal_generation.py # Test señales
python test_emergency_risk_manager.py # Test risk
```

## 📈 CARACTERÍSTICAS AVANZADAS

### 1. Multi-Timeframe Analysis
- Analiza M1, M5, M15, H1, H4 simultáneamente
- Confirma señales en múltiples timeframes

### 2. Machine Learning Ensemble
- Combina XGBoost, Random Forest, Gradient Boosting
- Predicciones con votación ponderada

### 3. Gestión Avanzada de Riesgo
- Kelly Criterion para position sizing
- Value at Risk (VaR) calculation
- Correlation-based risk management

### 4. Sistema de Alertas Inteligente
- Priorización por probabilidad de éxito
- Filtrado por condiciones de mercado
- Notificaciones multi-canal

### 5. Auto-Optimización
- Ajuste dinámico de parámetros
- Aprendizaje de patrones exitosos
- Adaptación a condiciones de mercado

## 🛠️ MANTENIMIENTO

### Logs
- Ubicación: `logs/`
- Rotación diaria
- Niveles: DEBUG, INFO, WARNING, ERROR

### Backups
- Ubicación: `backups/`
- Backup automático de configuraciones
- Backup de modelos ML

### Actualizaciones
```bash
# Actualizar dependencias
pip install -r requirements.txt --upgrade

# Actualizar modelos ML
python ml/train_models.py
```

## 📞 SOPORTE

Para problemas o consultas:
- Revisar logs en `logs/trading_bot.log`
- Ejecutar diagnóstico: `python DIAGNOSTICO_COMPLETO.py`
- Verificar configuración: `python check_mt5_status.py`

---
**Versión**: 3.0.0  
**Autor**: XentrisTech  
**Última actualización**: 2024
