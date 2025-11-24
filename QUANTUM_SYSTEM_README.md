# 🌌 QUANTUM TRADING SYSTEM

**Sistema profesional de trading algorítmico basado en principios de física cuántica**

---

## 📋 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Conceptos Fundamentales](#conceptos-fundamentales)
3. [Arquitectura del Sistema](#arquitectura-del-sistema)
4. [Instalación y Configuración](#instalación-y-configuración)
5. [Uso del Sistema](#uso-del-sistema)
6. [Componentes Principales](#componentes-principales)
7. [Fórmulas y Cálculos](#fórmulas-y-cálculos)
8. [Modos de Trading](#modos-de-trading)
9. [Regímenes de Mercado](#regímenes-de-mercado)
10. [FAQ](#faq)

---

## 🎯 Introducción

El **Quantum Trading System** es un sistema avanzado de trading algorítmico que aplica conceptos de física cuántica y mecánica clásica al análisis de mercados financieros.

### Inspiración Teórica

El sistema está inspirado en:

- **Energía Cinética**: Movimiento del precio como energía en el mercado
- **Energía Potencial**: Volatilidad como energía almacenada
- **Acción Física**: Integral del momentum neto
- **Cuantización**: Niveles discretos de energía del mercado

---

## 🔬 Conceptos Fundamentales

### Acción Cuantizada A(t)

La **Acción** es la métrica fundamental del sistema:

```
A(t) = EMA(|ΔP| - ATR)
```

Donde:
- **T = |ΔP|**: "Energía cinética" (movimiento absoluto del precio)
- **V = ATR**: "Energía potencial" (volatilidad promedio)
- **Raw = T - V**: Momentum neto (movimiento real vs ruido)
- **A(t)**: Acción suavizada con EMA

### Cuantización en Niveles

```
level = round(A / h)
```

Donde:
- **h**: "Cuanto" = desviación estándar de la Acción
- **level**: Nivel discreto de energía del mercado

**Interpretación de niveles:**
- `level ≥ 3`: Momentum extremo
- `level = 2`: Momentum fuerte (zona de entrada)
- `level = 1`: Momentum moderado
- `level = 0`: Sin momentum (zona de salida)
- `level < 0`: Momentum contrario

### Bandas Cuánticas

```
Band_Upper = A(t) + k·h
Band_Lower = A(t) - k·h
```

Las bandas definen zonas de fuerza:

- **Ruptura banda superior**: Impulso extremo → Continuación
- **Dentro de bandas**: Movimiento normal
- **Ruptura banda inferior**: Agotamiento → Reversal

### Divergencias

**Divergencia Alcista** (señal de giro UP):
```
Precio hace mínimo más bajo
Acción hace mínimo más alto
```

**Divergencia Bajista** (señal de giro DOWN):
```
Precio hace máximo más alto
Acción hace máximo más bajo
```

---

## 🏗️ Arquitectura del Sistema

```
┌────────────────────────────────────────────────────────────┐
│                    QUANTUM TRADING SYSTEM                  │
└────────────────────────────────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼────┐      ┌─────▼─────┐      ┌────▼────┐
   │TwelveData│      │  Ollama   │      │   MT5   │
   │   API    │      │    AI     │      │  Broker │
   └────┬────┘      └─────┬─────┘      └────┬────┘
        │                  │                  │
        └─────────┬────────┴────────┬─────────┘
                  │                 │
           ┌──────▼──────┐   ┌─────▼──────┐
           │Quantum Core │   │Signal Gen  │
           └──────┬──────┘   └─────┬──────┘
                  │                 │
                  └────────┬────────┘
                           │
                    ┌──────▼──────┐
                    │MT5 Executor │
                    └─────────────┘
```

### Flujo de Datos

1. **TwelveData** → Proporciona datos OHLCV limpios
2. **Quantum Core** → Calcula A(t), niveles, bandas
3. **Ollama AI** → Valida señales con inteligencia artificial
4. **Signal Generator** → Genera señales BUY/EXIT/WAIT
5. **MT5 Executor** → Ejecuta trades con gestión de riesgo

---

## ⚙️ Instalación y Configuración

### Requisitos

- Python 3.9 o superior
- MetaTrader 5
- TwelveData API key (PRO recomendado)
- Ollama (opcional, para validación AI)

### Paso 1: Clonar o Descargar

```bash
cd C:\Users\user\OneDrive\Escritorio\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2
```

### Paso 2: Instalar Dependencias

```bash
pip install -r requirements.txt
```

O ejecutar:
```bash
CONFIGURACION_RAPIDA.bat
```

### Paso 3: Configurar Variables de Entorno

Editar `.env`:

```env
# TwelveData
TWELVEDATA_API_KEY=tu_api_key_aqui

# MetaTrader 5
MT5_LOGIN=tu_cuenta
MT5_PASSWORD=tu_password
MT5_SERVER=tu_servidor
MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe

# Telegram (opcional)
TELEGRAM_BOT_TOKEN=tu_token
TELEGRAM_CHAT_ID=tu_chat_id

# Trading
TRADE_ENABLED=false  # true para trading real
MAX_RISK_PER_TRADE=0.01  # 1%
DEFAULT_LOT=0.01
```

### Paso 4: Configurar Ollama (Opcional)

```bash
# Instalar Ollama
# Descargar desde: https://ollama.ai

# Descargar modelo DeepSeek
ollama pull deepseek-r1:14b

# Iniciar servidor
ollama serve
```

---

## 🚀 Uso del Sistema

### Método 1: Script BAT (Windows)

```bash
INICIAR_QUANTUM_SYSTEM.bat
```

Selecciona el modo:
1. **Analysis Only**: Solo análisis, sin trades
2. **Live Trading**: Trading automático (CUIDADO!)
3. **Single Cycle Test**: Un solo ciclo de prueba

### Método 2: Python Directo

```bash
python QUANTUM_TRADING_SYSTEM.py
```

### Método 3: Importar en tu Código

```python
from src.signals.quantum_core import QuantumCore
from src.signals.quantum_signal_generator import QuantumSignalGenerator

# Crear generador
generator = QuantumSignalGenerator(
    use_ai_validation=True,
    multi_timeframe=True,
    auto_scaling=True
)

# Analizar un símbolo
analysis = generator.analyze_symbol('BTC/USD', interval='1h')

# Ver señal
print(f"Señal: {analysis.signal.action}")
print(f"Confianza: {analysis.signal.confidence}%")
print(f"Nivel: {analysis.signal.metrics.level}")
```

---

## 🧩 Componentes Principales

### 1. quantum_core.py

**Núcleo del sistema** con todas las fórmulas matemáticas.

Clases principales:
- `QuantumCore`: Cálculos de Acción, niveles, bandas
- `QuantumMetrics`: Métricas calculadas
- `QuantumSignal`: Señal generada

Métodos clave:
```python
calculate_atr(df)                    # ATR
calculate_action(df)                 # A(t), h, level
calculate_quantum_bands(A, h)        # Bandas superior/inferior
detect_divergence(price, action)     # Divergencias
detect_market_regime(A, h, atr)      # Régimen de mercado
generate_signal(df)                  # Señal completa
```

### 2. quantum_signal_generator.py

**Generador de señales** integrado con TwelveData y Ollama.

Funcionalidades:
- Obtención de datos de TwelveData
- Análisis multi-timeframe
- Validación con AI
- Cálculo de velocidad/aceleración
- Intensity score (0-100)

### 3. quantum_mt5_executor.py

**Ejecutor de trading** en MetaTrader 5.

Funcionalidades:
- Apertura de posiciones con SL/TP dinámicos
- 4 modos de Trailing Stop
- Breakeven automático
- Risk management (% de balance)
- Gestión de múltiples posiciones

### 4. QUANTUM_TRADING_SYSTEM.py

**Script principal** que integra todo.

Modos de operación:
- Analysis Only (sin trading)
- Live Trading (automático)
- Single Cycle Test

---

## 📐 Fórmulas y Cálculos

### Acción A(t)

```
1. T = |close_t - close_{t-1}|
2. V = ATR(14)
3. Raw = T - V
4. A(t) = EMA(Raw, 20)
```

### Cuanto h

```
h = std(A) × h_factor
```

Donde `h_factor` se auto-ajusta por régimen:
- Trend: 1.0
- Range: 1.3
- Volatile: 1.8
- Low Energy: 0.8

### Bandas

```
Upper = A + k·h
Lower = A - k·h
```

Donde `k` se auto-ajusta:
- Trend: 2.0
- Range: 1.5
- Volatile: 3.0
- Low Energy: 1.0

### Stop Loss Dinámico

```
SL = price - (ATR × multiplier)
```

Default: `multiplier = 2.0`

### Take Profit Dinámico

```
TP = price + (k × h × multiplier)
```

Default: `multiplier = 1.0`

### Trailing Stop (4 Modos)

**Modo 1 - ATR:**
```
TSL = price - (ATR × multiplier)
```

**Modo 2 - H:**
```
TSL = price - (h × multiplier)
```

**Modo 3 - Quantum Band:**
```
TSL = A - (k × h)
```

**Modo 4 - Level Adaptive:**
```
if level ≥ 3:
    TSL = price - (ATR + h) × multiplier × 0.7  # Agresivo
elif level ≥ 1:
    TSL = price - (ATR + h) × multiplier        # Normal
else:
    TSL = price - (ATR + h) × 2.5               # Conservador
```

---

## 🎮 Modos de Trading

### 1. Analysis Only

- ✅ Analiza mercado en tiempo real
- ✅ Genera señales
- ✅ Muestra métricas
- ❌ NO ejecuta trades
- **Uso:** Backtesting, aprendizaje, validación

### 2. Live Trading

- ✅ Todo lo de Analysis Only
- ✅ Ejecuta trades automáticamente
- ✅ Gestiona posiciones
- ✅ Trailing stops
- ⚠️ **CUIDADO:** Dinero real en juego

### 3. Single Cycle Test

- ✅ Un solo ciclo de análisis
- ✅ Muestra estadísticas
- ✅ Perfecto para debugging
- ❌ NO continuo

---

## 🌍 Regímenes de Mercado

El sistema detecta automáticamente 4 regímenes y ajusta parámetros:

### 1. TREND (Tendencia)

**Detección:** `A(t) > 2·h`

**Auto-Scaling:**
```python
ATR_Period = 14
EMA_Period = 20
h_factor = 1.0
k = 2.0
trailing_mode = LEVEL  # Adaptativo
```

**Interpretación:** Momentum fuerte, tendencia clara

### 2. RANGE (Rango)

**Detección:** `|A(t)| < h`

**Auto-Scaling:**
```python
ATR_Period = 20
EMA_Period = 30
h_factor = 1.3
k = 1.5
trailing_mode = BAND  # Basado en bandas
```

**Interpretación:** Mercado lateral, sin tendencia

### 3. VOLATILE (Volátil)

**Detección:** `ATR > 3·h`

**Auto-Scaling:**
```python
ATR_Period = 10
EMA_Period = 15
h_factor = 1.8
k = 3.0
trailing_mode = ATR  # Más conservador
```

**Interpretación:** Alta volatilidad, riesgo elevado

### 4. LOW_ENERGY (Baja Energía)

**Detección:** `|A(t)| < 0.3·h`

**Auto-Scaling:**
```python
ATR_Period = 30
EMA_Period = 40
h_factor = 0.8
k = 1.0
trailing_mode = H  # Muy ajustado
```

**Interpretación:** Movimiento mínimo, consolidación

---

## ❓ FAQ

### ¿Cómo funciona la Acción A(t)?

Mide el **momentum neto** del precio:
- Si `A > 0`: Precio se mueve más que la volatilidad → Tendencia real
- Si `A ≈ 0`: Precio se mueve = volatilidad → Ruido, sin tendencia
- Si `A < 0`: Precio se mueve menos que volatilidad → Consolidación

### ¿Qué significan los niveles?

Los niveles indican **intensidad del momentum**:
- `level = 4+`: Extremo (posible sobreextensión)
- `level = 2-3`: Fuerte (zona de entrada)
- `level = 0-1`: Débil (esperar)
- `level < 0`: Contrario (posible reversal)

### ¿Cuándo entrar?

Señal BUY cuando:
1. **Divergencia alcista** + Acción > Banda Superior, O
2. **Level cruza de ≤0 a ≥2** con Acción creciente

### ¿Cuándo salir?

Señal EXIT cuando:
1. **Divergencia bajista**, O
2. **Acción < Banda Inferior**, O
3. **Level ≤ 0**, O
4. **Acción decreciente**

### ¿Por qué usar Ollama?

Ollama añade **inteligencia semántica**:
- Valida si la señal tiene sentido en el contexto actual
- Detecta patrones que las fórmulas matemáticas no ven
- Ajusta confianza basada en análisis textual

### ¿Es mejor que indicadores tradicionales?

**Ventajas:**
- ✅ Ajuste dinámico por régimen
- ✅ Separa momentum real de ruido
- ✅ Basado en física, no en heurísticas
- ✅ Multi-timeframe integrado
- ✅ Validación AI

**Desventajas:**
- ❌ Más complejo de entender
- ❌ Requiere TwelveData API (de pago)
- ❌ Necesita configuración inicial

### ¿Puedo usarlo sin Ollama?

**Sí.** El sistema funciona sin AI:
```python
generator = QuantumSignalGenerator(use_ai_validation=False)
```

Ollama es opcional pero recomendado.

### ¿Funciona en cualquier mercado?

**Sí.** El sistema es agnóstico al mercado:
- ✅ Forex
- ✅ Crypto
- ✅ Índices
- ✅ Commodities
- ✅ Acciones

Solo necesitas que TwelveData tenga datos del símbolo.

### ¿Cuánto capital necesito?

**Mínimo recomendado:**
- Demo: $0 (cuenta demo MT5)
- Live: $100-500 USD para lotes pequeños
- Profesional: $1,000+ para gestión de riesgo adecuada

### ¿Qué timeframe usar?

**Recomendado:**
- 1H para swing trading
- 15min para day trading
- 5min para scalping (más ruido)

El sistema ajusta automáticamente según timeframe.

---

## 📊 Ejemplos de Uso

### Ejemplo 1: Análisis Simple

```python
from src.signals.quantum_signal_generator import QuantumSignalGenerator

generator = QuantumSignalGenerator()
analysis = generator.analyze_symbol('EUR/USD', interval='1h')

print(f"Señal: {analysis.signal.action}")
print(f"Nivel: {analysis.signal.metrics.level}")
print(f"Régimen: {analysis.signal.metrics.regime.value}")
```

### Ejemplo 2: Multi-Timeframe

```python
mtf = generator.scan_multi_timeframe('BTC/USD')
consensus, conf = generator.get_multi_timeframe_consensus(mtf)

print(f"Consenso: {consensus} ({conf}%)")
```

### Ejemplo 3: Trading Automático

```python
from QUANTUM_TRADING_SYSTEM import QuantumTradingSystem

system = QuantumTradingSystem(
    symbols=['BTC/USD', 'EUR/USD'],
    trading_enabled=True,  # ⚠️ REAL TRADING
    auto_scaling=True
)

system.run_continuous()
```

---

## 🔧 Troubleshooting

### Error: "TwelveData API key not found"

```bash
# Editar .env
TWELVEDATA_API_KEY=tu_key_aqui
```

### Error: "MT5 not connected"

1. Verificar que MT5 esté abierto
2. Verificar credenciales en `.env`
3. Verificar que `AutoTrading` esté habilitado en MT5

### Error: "Ollama not available"

```bash
# Iniciar Ollama
ollama serve

# O deshabilitar AI
generator = QuantumSignalGenerator(use_ai_validation=False)
```

---

## 📈 Mejoras Futuras

- [ ] Dashboard web en tiempo real
- [ ] Backtesting histórico automático
- [ ] Optimización genética de parámetros
- [ ] Indicadores MQL5 para visualización
- [ ] Expert Advisor (EA) MQL5 completo
- [ ] Integración con más brokers
- [ ] Sistema de alertas Telegram
- [ ] Machine Learning para predicción

---

## 📝 Licencia

Propietario - Xentristech Trading AI

---

## 🤝 Soporte

Para soporte, contacta:
- Email: support@xentristech.com
- GitHub: Issues en el repositorio

---

**⚠️ DISCLAIMER**

Este sistema es para propósitos educativos e informativos.
El trading conlleva riesgos. Opera solo con capital que puedas permitirte perder.
No nos hacemos responsables de pérdidas financieras.

---

_Actualizado: 2025-01-16_
_Versión: 1.0.0_
