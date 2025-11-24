# 🚀 QUANTUM SYSTEM - GUÍA RÁPIDA DE INICIO

**Sistema de Trading Cuántico - Listo para usar en 5 minutos**

---

## ✅ CHECKLIST DE INSTALACIÓN

### Paso 1: Verificar Python
```bash
python --version
# Debe ser 3.9 o superior
```

### Paso 2: Instalar Dependencias
```bash
pip install -r requirements.txt
```

### Paso 3: Configurar Variables de Entorno

Editar el archivo `.env` (si no existe, copiar de `.env.example`):

```env
# === TWELVEDATA (REQUERIDO) ===
TWELVEDATA_API_KEY=tu_api_key_aqui

# === MT5 (REQUERIDO para trading real) ===
MT5_LOGIN=12345678
MT5_PASSWORD=tu_password
MT5_SERVER=Exness-MT5Real
MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe

# === TELEGRAM (OPCIONAL) ===
TELEGRAM_BOT_TOKEN=123456:ABC-DEF
TELEGRAM_CHAT_ID=123456789

# === TRADING CONFIG ===
TRADE_ENABLED=false  # true para trading real
MAX_RISK_PER_TRADE=0.01  # 1% del balance
DEFAULT_LOT=0.01
```

### Paso 4: Configurar Ollama (Opcional)
```bash
# Descargar Ollama desde: https://ollama.ai
# Descargar modelo DeepSeek
ollama pull deepseek-r1:14b

# Iniciar servidor
ollama serve
```

---

## 🎯 EJECUCIÓN RÁPIDA

### Opción 1: Script BAT (Recomendado para Windows)
```bash
INICIAR_QUANTUM_SYSTEM.bat
```

### Opción 2: Python Directo
```bash
python QUANTUM_TRADING_SYSTEM.py
```

### Opción 3: Modo Programático
```python
from QUANTUM_TRADING_SYSTEM import QuantumTradingSystem

system = QuantumTradingSystem(
    symbols=['BTC/USD', 'EUR/USD'],
    trading_enabled=False,  # Solo análisis
    use_ai_validation=True,
    multi_timeframe=True
)

# Un solo ciclo (test)
system.run_single_cycle()
system.display_statistics()

# O modo continuo
# system.run_continuous()
```

---

## 📊 MODOS DE OPERACIÓN

### Modo 1: Analysis Only (Seguro)
```
✅ Analiza mercado en tiempo real
✅ Genera señales
✅ Muestra métricas
❌ NO ejecuta trades
```

**Perfecto para:**
- Aprender cómo funciona
- Validar señales
- Backtesting manual

### Modo 2: Live Trading (Avanzado)
```
⚠️ CUIDADO: Trading automático con dinero real
✅ Ejecuta trades
✅ Gestiona posiciones
✅ Trailing stops automáticos
```

**Solo usar si:**
- Ya probaste en demo
- Entiendes cómo funciona
- Tienes risk management claro

### Modo 3: Single Cycle Test
```
✅ Un solo ciclo de análisis
✅ Perfecto para debugging
❌ No es continuo
```

---

## 🔬 CÓMO INTERPRETAR LAS SEÑALES

### Ejemplo de Output

```
═══════════════════════════════════════════════════════════════════
🟢 BTC/USD - 1H
═══════════════════════════════════════════════════════════════════
💰 Precio: $42,345.67
📊 Señal: BUY (85.0%)
💡 Razón: Nivel cuantizado 3 + Acción creciente

🔬 MÉTRICAS CUÁNTICAS:
   Acción A(t): 0.003456
   Cuanto h: 0.001234
   Nivel: 3
   Banda Superior: 0.005922
   Banda Inferior: 0.000990
   📈 Régimen: TREND

⚡ DINÁMICA:
   Velocidad: +1.234%
   Aceleración: +0.567%
   Intensidad: 75%

🔍 DIVERGENCIAS:
   Alcista: ✅
   Bajista: ❌

🤖 VALIDACIÓN AI:
   Validado: ✅
   Confianza AI: 88.0%
   Comentario: El momentum es fuerte y la divergencia confirma
═══════════════════════════════════════════════════════════════════
```

### ¿Qué Significa?

**Señal: BUY (85%)**
- Sistema recomienda comprar
- 85% de confianza

**Nivel: 3**
- Momentum fuerte (0=débil, 5=extremo)
- Nivel ≥2 es zona de entrada

**Régimen: TREND**
- Mercado en tendencia clara
- Parámetros optimizados para tendencia

**Validación AI: 88%**
- Ollama confirma la señal
- Alta confianza del modelo

---

## 🎓 CONCEPTOS CLAVE

### Acción A(t)
```
A(t) = EMA(|ΔP| - ATR)
```
Mide el **momentum neto** del precio:
- `A > 0`: Tendencia real
- `A ≈ 0`: Solo ruido
- `A < 0`: Consolidación

### Niveles Cuantizados
```
level = round(A / h)
```
Intensidad discreta del momentum:
- `4+`: Extremo
- `2-3`: Fuerte (entrar)
- `0-1`: Débil (esperar)
- `<0`: Contrario

### Bandas Cuánticas
```
Upper = A + k·h
Lower = A - k·h
```
Zonas de fuerza:
- Ruptura superior: Continuación
- Ruptura inferior: Reversal

---

## 🛠️ TROUBLESHOOTING

### Problema: "TwelveData API key not found"
**Solución:**
```env
# Editar .env
TWELVEDATA_API_KEY=tu_key_real
```

### Problema: "MT5 not connected"
**Solución:**
1. Abrir MetaTrader 5
2. Verificar que `AutoTrading` esté habilitado
3. Verificar credenciales en `.env`

### Problema: "Ollama not available"
**Solución 1 (Instalar Ollama):**
```bash
# Descargar de https://ollama.ai
ollama pull deepseek-r1:14b
ollama serve
```

**Solución 2 (Deshabilitar AI):**
```python
system = QuantumTradingSystem(use_ai_validation=False)
```

### Problema: "Module not found"
**Solución:**
```bash
pip install -r requirements.txt
```

---

## 📂 ESTRUCTURA DE ARCHIVOS

```
📁 algo-trader-mvp-v2/
│
├── 📄 QUANTUM_TRADING_SYSTEM.py     ← Script principal
├── 📄 INICIAR_QUANTUM_SYSTEM.bat   ← Lanzador rápido
├── 📄 QUANTUM_SYSTEM_README.md     ← Documentación completa
├── 📄 QUANTUM_SYSTEM_QUICKSTART.md ← Esta guía
├── 📄 .env                          ← Configuración (CREAR)
│
└── 📁 src/
    ├── 📁 signals/
    │   ├── quantum_core.py              ← Fórmulas matemáticas
    │   └── quantum_signal_generator.py  ← Generador de señales
    │
    └── 📁 trading/
        └── quantum_mt5_executor.py      ← Ejecutor MT5
```

---

## 🧪 TEST RÁPIDO

### Test 1: Verificar Instalación

```python
python -c "from src.signals.quantum_core import QuantumCore; print('✅ OK')"
```

### Test 2: Generar Señal de Prueba

```python
from src.signals.quantum_signal_generator import QuantumSignalGenerator

gen = QuantumSignalGenerator(use_ai_validation=False)
analysis = gen.analyze_symbol('BTC/USD', interval='1h')

print(f"Señal: {analysis.signal.action}")
print(f"Nivel: {analysis.signal.metrics.level}")
```

### Test 3: Sistema Completo (1 Ciclo)

```bash
python QUANTUM_TRADING_SYSTEM.py
# Seleccionar opción: 3 (Single Cycle Test)
```

---

## 📈 PRÓXIMOS PASOS

### 1. Familiarízate con el Sistema
- Ejecuta en modo "Analysis Only"
- Observa las señales generadas
- Compara con tu análisis manual

### 2. Prueba en Demo
- Configura cuenta demo MT5
- Activa `TRADE_ENABLED=true` en .env
- Ejecuta con lote mínimo

### 3. Optimiza Parámetros
- Ajusta `ATR_Period`, `EMA_Period`
- Prueba diferentes símbolos
- Experimenta con timeframes

### 4. Trading Real (Solo si estás listo)
- Cuenta real MT5
- Capital que puedas perder
- Risk management estricto

---

## ⚠️ RECORDATORIOS IMPORTANTES

### Antes de Trading Real

- [ ] He probado en modo "Analysis Only"
- [ ] He probado en cuenta DEMO
- [ ] Entiendo cómo funcionan las señales
- [ ] Tengo risk management definido
- [ ] Solo arriesgo capital que puedo perder
- [ ] He leído la documentación completa

### Durante Trading

- ✅ Monitorea logs: `logs/quantum_trading_system.log`
- ✅ Revisa posiciones en MT5 regularmente
- ✅ Ten un plan de salida de emergencia
- ✅ No cambies parámetros en caliente

### Después de Trading

- ✅ Revisa performance
- ✅ Analiza señales ganadoras y perdedoras
- ✅ Ajusta si es necesario
- ✅ Haz backups de configuración

---

## 🆘 CONTACTO Y SOPORTE

### Logs
```
logs/quantum_trading_system.log
```

### GitHub Issues
Reporta bugs o solicita features

### Email
support@xentristech.com

---

## 📚 RECURSOS ADICIONALES

### Documentación Completa
`QUANTUM_SYSTEM_README.md`

### Código Fuente
```python
src/signals/quantum_core.py              # Núcleo matemático
src/signals/quantum_signal_generator.py  # Generador de señales
src/trading/quantum_mt5_executor.py      # Ejecutor MT5
```

### Conversación Original ChatGPT
La idea original del Quantum Action vino de una investigación sobre aplicar principios de física al trading. Ver archivo compartido.

---

## 🎉 ¡LISTO!

**Ya tienes todo para empezar a usar el Quantum Trading System.**

Ejecuta:
```bash
INICIAR_QUANTUM_SYSTEM.bat
```

Y selecciona el modo de operación.

**¡Happy Trading! 🚀**

---

_Actualizado: 2025-01-16_
_Versión: 1.0.0_
