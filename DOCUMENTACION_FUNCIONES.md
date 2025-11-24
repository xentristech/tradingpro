# 🔍 DOCUMENTACIÓN DETALLADA DE FUNCIONES

## 📋 ÍNDICE DE FUNCIONES POR CATEGORÍA

### 🎯 FUNCIONES PRINCIPALES

## 1. SISTEMA PRINCIPAL (main.py)

### `main()` - Función Principal
```python
def main():
    """
    Punto de entrada principal del sistema de trading algorítmico.
    
    Gestiona:
    - Parsing de argumentos CLI
    - Configuración de logging
    - Carga de configuración desde .env
    - Ejecución de comandos (start, stop, status, test, backtest, optimize)
    
    Returns:
        int: Código de salida (0 = éxito, 1 = error)
    
    Ejemplo:
        $ python main.py start --mode live --symbol BTCUSD
    """
```

### `start_trading(args)` - Iniciar Trading
```python
async def start_trading(args):
    """
    Inicia el bot de trading con la configuración especificada.
    
    Args:
        args: Argumentos de línea de comandos
            - mode: 'demo', 'live', o 'paper'
            - config: ruta al archivo de configuración
            - symbol: símbolo a operar (opcional)
    
    Returns:
        int: 0 si éxito, 1 si error
    
    Proceso:
    1. Crea instancia de BotManager
    2. Configura modo de trading
    3. Inicia el bot
    4. Maneja interrupciones
    """
```

### `signal_handler(signum, frame)` - Manejador de Señales
```python
def signal_handler(signum, frame):
    """
    Maneja señales del sistema (SIGINT, SIGTERM).
    
    Args:
        signum: Número de señal
        frame: Frame actual
    
    Funcionalidad:
    - Detiene el bot de forma segura
    - Guarda estado actual
    - Cierra conexiones
    - Sale del programa
    """
```

## 2. BOT MANAGER (src/core/bot_manager.py)

### `BotManager.__init__(config_path)`
```python
def __init__(self, config_path: str = 'configs/.env'):
    """
    Inicializa el gestor principal del bot.
    
    Args:
        config_path: Ruta al archivo de configuración
    
    Inicializa:
    - Logger del sistema
    - Configuración desde .env
    - Componentes del sistema (broker, data, signals, risk, ML)
    - Estadísticas iniciales
    
    Raises:
        ConfigurationError: Si falta configuración crítica
    """
```

### `BotManager._trading_loop()`
```python
async def _trading_loop(self):
    """
    Loop principal de trading.
    
    Ciclo continuo que:
    1. Obtiene datos de mercado
    2. Genera señales de trading
    3. Evalúa riesgo
    4. Ejecuta trades si procede
    5. Actualiza posiciones
    6. Registra métricas
    
    Frecuencia: Cada 60 segundos (configurable)
    
    Raises:
        TradingError: En errores críticos de trading
    """
```

### `BotManager.execute_trade(signal)`
```python
async def execute_trade(self, signal: Dict) -> bool:
    """
    Ejecuta una operación de trading.
    
    Args:
        signal: Diccionario con:
            - direction: 'buy' o 'sell'
            - entry_price: precio de entrada
            - stop_loss: stop loss
            - take_profit: take profit
            - lot_size: tamaño de posición
    
    Returns:
        bool: True si se ejecutó correctamente
    
    Proceso:
    1. Valida señal
    2. Calcula tamaño de posición
    3. Verifica límites de riesgo
    4. Coloca orden en MT5
    5. Registra operación
    6. Envía notificación
    """
```

## 3. GENERADOR DE SEÑALES (src/signals/signal_generator.py)

### `SignalGenerator.generate(data)`
```python
def generate(self, data: pd.DataFrame) -> Dict:
    """
    Genera señal de trading consolidada.
    
    Args:
        data: DataFrame con columnas OHLCV + indicadores
    
    Returns:
        Dict con:
            - direction: 'buy', 'sell', o 'neutral'
            - strength: 0.0 a 1.0
            - confidence: 0.0 a 1.0
            - strategy: estrategia dominante
            - reasons: lista de razones
    
    Estrategias aplicadas:
    - Trend Following (25% peso)
    - Mean Reversion (20% peso)
    - Momentum (25% peso)
    - Support/Resistance (15% peso)
    - Pattern Recognition (15% peso)
    """
```

### `SignalGenerator._trend_following_strategy(data)`
```python
def _trend_following_strategy(self, data: pd.DataFrame) -> TradingSignal:
    """
    Estrategia de seguimiento de tendencia.
    
    Args:
        data: DataFrame con datos de mercado
    
    Returns:
        TradingSignal con evaluación de tendencia
    
    Indicadores usados:
    - EMA 20/50/200
    - MACD
    - ADX
    - Supertrend
    
    Condiciones BUY:
    - EMA20 > EMA50 > EMA200
    - MACD histogram positivo
    - ADX > 25
    """
```

### `SignalGenerator._momentum_strategy(data)`
```python
def _momentum_strategy(self, data: pd.DataFrame) -> TradingSignal:
    """
    Estrategia basada en momentum.
    
    Args:
        data: DataFrame con datos de mercado
    
    Returns:
        TradingSignal basada en momentum
    
    Indicadores:
    - RSI (14)
    - Stochastic
    - Williams %R
    - CCI
    
    Señal fuerte cuando:
    - RSI entre 30-70 con tendencia
    - Stoch en zona de impulso
    - Volumen confirmatorio
    """
```

## 4. GESTOR DE RIESGO (src/risk/risk_manager.py)

### `RiskManager.evaluate_trade(symbol, direction, entry_price, lot_size)`
```python
def evaluate_trade(self, symbol: str, direction: str, 
                  entry_price: float, lot_size: float) -> Dict:
    """
    Evalúa si un trade cumple criterios de riesgo.
    
    Args:
        symbol: Símbolo del instrumento
        direction: 'buy' o 'sell'
        entry_price: Precio de entrada propuesto
        lot_size: Tamaño de posición propuesto
    
    Returns:
        Dict con:
            - trade_allowed: bool
            - adjusted_lot_size: tamaño ajustado
            - risk_score: 0-100
            - warnings: lista de advertencias
            - stop_loss: SL recomendado
            - take_profit: TP recomendado
    
    Validaciones:
    - Riesgo por trade < límite
    - Exposición total < máximo
    - Correlación con posiciones abiertas
    - Pérdida diaria < límite
    - Drawdown < máximo
    """
```

### `RiskManager.calculate_position_size(balance, risk_percent, stop_loss_pips)`
```python
def calculate_position_size(self, balance: float, 
                           risk_percent: float, 
                           stop_loss_pips: float) -> float:
    """
    Calcula tamaño óptimo de posición.
    
    Args:
        balance: Balance de cuenta
        risk_percent: % de riesgo (0.01 = 1%)
        stop_loss_pips: Distancia del SL en pips
    
    Returns:
        float: Tamaño de posición en lotes
    
    Métodos aplicados:
    - Fixed Fractional
    - Kelly Criterion (si hay histórico)
    - Volatility-based adjustment
    
    Ejemplo:
        size = rm.calculate_position_size(10000, 0.01, 50)
        # Returns: 0.02 lotes
    """
```

### `RiskManager.apply_kelly_criterion(win_rate, avg_win, avg_loss)`
```python
def apply_kelly_criterion(self, win_rate: float, 
                         avg_win: float, 
                         avg_loss: float) -> float:
    """
    Aplica criterio de Kelly para sizing óptimo.
    
    Args:
        win_rate: Tasa de acierto (0-1)
        avg_win: Ganancia promedio
        avg_loss: Pérdida promedio
    
    Returns:
        float: Fracción óptima de capital (0-0.25 cap)
    
    Fórmula:
        f* = (p * b - q) / b
        donde:
        - p = probabilidad de ganar
        - q = probabilidad de perder
        - b = ratio ganancia/pérdida
    """
```

## 5. PREDICTOR ML (src/ml/ml_predictor.py)

### `MLPredictor.predict(data)`
```python
def predict(self, data: pd.DataFrame) -> Dict:
    """
    Genera predicción usando ensemble de modelos.
    
    Args:
        data: DataFrame con features
    
    Returns:
        Dict con:
            - prediction: 'up', 'down', o 'neutral'
            - probability: 0.0 a 1.0
            - confidence: nivel de confianza
            - model_votes: votos por modelo
    
    Modelos utilizados:
    - XGBoost (40% peso)
    - Random Forest (30% peso)
    - Gradient Boosting (30% peso)
    
    Features:
    - Técnicos: RSI, MACD, BB, etc.
    - Precio: returns, volatilidad
    - Volumen: OBV, volume profile
    """
```

### `MLPredictor.train_models(historical_data)`
```python
def train_models(self, historical_data: pd.DataFrame):
    """
    Entrena modelos de ML con datos históricos.
    
    Args:
        historical_data: DataFrame con datos históricos
    
    Proceso:
    1. Prepara features
    2. Crea labels (dirección futura)
    3. Split train/test (80/20)
    4. Entrena cada modelo
    5. Evalúa performance
    6. Guarda modelos
    
    Métricas guardadas:
    - Accuracy
    - Precision/Recall
    - F1-Score
    - Confusion Matrix
    """
```

## 6. SISTEMAS DE IA

### `AITradingAssistant.analyze_market(data)`
```python
def analyze_market(self, data: pd.DataFrame) -> Dict:
    """
    Análisis completo de mercado con IA.
    
    Args:
        data: DataFrame con datos de mercado
    
    Returns:
        Dict con:
            - market_condition: 'trending', 'ranging', 'volatile'
            - trend_strength: 0-100
            - volatility_level: 'low', 'medium', 'high'
            - key_levels: soportes y resistencias
            - recommendations: lista de recomendaciones
    
    Técnicas aplicadas:
    - Análisis de régimen de mercado
    - Detección de cambios estructurales
    - Identificación de niveles clave
    - Análisis de sentimiento (si disponible)
    """
```

### `AIOpportunityHunter.scan_markets(symbols)`
```python
def scan_markets(self, symbols: List[str]) -> List[Dict]:
    """
    Escanea múltiples mercados buscando oportunidades.
    
    Args:
        symbols: Lista de símbolos a escanear
    
    Returns:
        Lista de oportunidades ordenadas por potencial
    
    Criterios de búsqueda:
    - Breakouts de rango
    - Reversiones en extremos
    - Momentum fuerte
    - Volumen anómalo
    - Patrones de alta probabilidad
    
    Cada oportunidad incluye:
    - symbol: símbolo
    - type: tipo de oportunidad
    - probability: probabilidad de éxito
    - risk_reward: ratio R:R
    - entry_point: punto de entrada
    """
```

## 7. GESTIÓN DE POSICIONES

### `PositionManager.update_trailing_stop(position)`
```python
def update_trailing_stop(self, position: Dict) -> bool:
    """
    Actualiza trailing stop dinámicamente.
    
    Args:
        position: Diccionario con datos de posición
    
    Returns:
        bool: True si se actualizó
    
    Lógica:
    - ATR-based trailing
    - Percentage-based trailing
    - Parabolic SAR trailing
    - Breakeven activation
    
    Se activa cuando:
    - Profit > X pips
    - Tiempo en posición > Y minutos
    - Condiciones de mercado favorables
    """
```

### `EmergencyRiskManager.emergency_close_all()`
```python
def emergency_close_all(self) -> Dict:
    """
    Cierre de emergencia de todas las posiciones.
    
    Returns:
        Dict con:
            - positions_closed: número de posiciones cerradas
            - total_loss: pérdida total
            - reason: razón del cierre
    
    Se activa cuando:
    - Drawdown > límite crítico
    - Pérdida diaria > máximo
    - Evento de mercado extremo
    - Fallo del sistema
    
    Proceso:
    1. Congela nuevas operaciones
    2. Cierra todas las posiciones
    3. Notifica administrador
    4. Genera reporte
    """
```

## 8. MONITOREO Y DASHBOARDS

### `DashboardTiempoReal.update_display()`
```python
def update_display(self):
    """
    Actualiza dashboard en tiempo real.
    
    Muestra:
    - Gráfico de precio con indicadores
    - Posiciones abiertas
    - P&L en tiempo real
    - Señales activas
    - Métricas de performance
    - Logs recientes
    
    Frecuencia: Cada 1 segundo
    
    Tecnología:
    - Streamlit para web
    - Rich para terminal
    - Plotly para gráficos
    """
```

### `MonitorSistema.health_check()`
```python
def health_check(self) -> Dict:
    """
    Verifica salud del sistema.
    
    Returns:
        Dict con estado de cada componente
    
    Verifica:
    - Conexión MT5: latencia, estado
    - APIs: disponibilidad, rate limits
    - ML Models: cargados, performance
    - Database: conexión, espacio
    - Sistema: CPU, memoria, disco
    
    Alertas cuando:
    - Componente crítico falla
    - Performance degradada
    - Recursos bajos
    """
```

## 9. UTILIDADES Y HERRAMIENTAS

### `calculate_indicators(data, indicators_list)`
```python
def calculate_indicators(data: pd.DataFrame, 
                        indicators_list: List[str]) -> pd.DataFrame:
    """
    Calcula indicadores técnicos.
    
    Args:
        data: DataFrame OHLCV
        indicators_list: Lista de indicadores
    
    Returns:
        DataFrame con indicadores añadidos
    
    Indicadores disponibles:
    - Moving Averages: SMA, EMA, WMA
    - Oscillators: RSI, MACD, Stochastic
    - Volatility: BB, ATR, Keltner
    - Volume: OBV, CMF, VWAP
    - Trend: ADX, Aroon, Ichimoku
    """
```

### `validate_signal(signal, min_confidence=0.6)`
```python
def validate_signal(signal: Dict, min_confidence: float = 0.6) -> bool:
    """
    Valida una señal de trading.
    
    Args:
        signal: Señal a validar
        min_confidence: Confianza mínima requerida
    
    Returns:
        bool: True si la señal es válida
    
    Validaciones:
    - Estructura correcta
    - Valores en rangos válidos
    - Confianza >= mínimo
    - Timeframe correcto
    - No duplicada
    """
```

## 10. NOTIFICACIONES

### `TelegramNotifier.send_trade_alert(trade_info)`
```python
async def send_trade_alert(self, trade_info: Dict):
    """
    Envía alerta de trade por Telegram.
    
    Args:
        trade_info: Información del trade
    
    Formato del mensaje:
    🚀 SEÑAL DE TRADING
    ━━━━━━━━━━━━━━━
    📊 Símbolo: {symbol}
    📈 Dirección: {direction}
    💰 Entrada: {entry}
    🛑 Stop Loss: {sl}
    🎯 Take Profit: {tp}
    📊 Confianza: {confidence}%
    
    Incluye:
    - Emoji según tipo
    - Formato markdown
    - Botones de acción (si configurado)
    """
```

---

## 📚 CONVENCIONES DE CÓDIGO

### Nomenclatura
- **Funciones**: snake_case
- **Clases**: PascalCase
- **Constantes**: UPPER_SNAKE_CASE
- **Variables privadas**: _prefijo_underscore

### Documentación
- Docstrings en formato Google
- Type hints para todos los parámetros
- Ejemplos de uso cuando sea relevante

### Manejo de Errores
- Try/except específicos
- Logging de errores
- Recuperación graceful
- Notificación de errores críticos

### Testing
- Unit tests para funciones críticas
- Integration tests para flujos
- Performance tests para optimización

---

**Última actualización**: 2024
**Versión**: 3.0.0
