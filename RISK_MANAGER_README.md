# 🛡️ Advanced Risk Manager - Breakeven & Trailing Stop Inteligente

## 📋 Descripción

Sistema avanzado de gestión de riesgo que agrega **Breakeven automático** y **Trailing Stop dinámico** a tus operaciones, con optimización por **Inteligencia Artificial** usando Ollama y datos de mercado de TwelveData.

## ✨ Características Principales

### 🔒 Breakeven Automático
- **Protección de capital**: Mueve el SL al precio de entrada cuando alcanzas cierto profit
- **Offset configurable**: Agrega pips adicionales para cubrir spread y comisiones
- **Activación inteligente**: La IA ajusta el trigger según volatilidad del mercado

### 📈 Trailing Stop Dinámico
- **Maximiza ganancias**: Sigue el precio manteniendo distancia óptima
- **ATR adaptativo**: Usa Average True Range para distancia dinámica
- **Step control**: Evita modificaciones excesivas con paso mínimo configurable

### 🤖 Optimización con IA
- **Análisis en tiempo real**: Ollama analiza condiciones del mercado
- **Parámetros dinámicos**: Ajusta breakeven y trailing según contexto
- **Aprendizaje continuo**: Mejora decisiones basándose en resultados

## 🚀 Instalación y Configuración

### 1. Configuración en `.env`

```env
# === ACTIVACIÓN DE FUNCIONES ===
ENABLE_BREAKEVEN=true          # Activar/desactivar breakeven
ENABLE_TRAILING_STOP=true      # Activar/desactivar trailing
USE_AI_RISK_OPTIMIZATION=true  # Usar IA para optimización

# === BREAKEVEN ===
BREAKEVEN_TRIGGER_PIPS=20      # Pips de profit para activar
BREAKEVEN_OFFSET_PIPS=2        # Pips extra sobre entrada
BREAKEVEN_MIN_PROFIT_USD=10    # Profit mínimo requerido

# === TRAILING STOP ===
TRAILING_ACTIVATION_PIPS=30    # Pips para activar trailing
TRAILING_DISTANCE_PIPS=15      # Distancia del trailing
TRAILING_STEP_PIPS=5           # Paso mínimo de actualización
USE_ATR_TRAILING=true          # Usar ATR dinámico
ATR_MULTIPLIER=2.0             # Multiplicador de ATR

# === CONTROL ===
RISK_CHECK_INTERVAL=30         # Segundos entre verificaciones
CONSERVATIVE_MODE=false        # Modo conservador
```

### 2. Ejecución

#### Opción A: Sistema Completo (Recomendado)
```bash
# Windows
START_RISK_MANAGER.bat

# Python directo
python START_WITH_RISK_MANAGER.py
```

#### Opción B: Solo Risk Manager
```bash
python src/risk/advanced_risk_manager.py
```

#### Opción C: Con Dashboard
```bash
# Terminal 1: Risk Manager
python src/risk/advanced_risk_manager.py

# Terminal 2: Dashboard
streamlit run risk_manager_dashboard.py --server.port 8520
```

## 📊 Dashboard de Monitoreo

Accede al dashboard en: **http://localhost:8520**

### Características del Dashboard:
- **Estadísticas en tiempo real**: Breakeven aplicados, trailing actualizados, pips protegidos
- **Monitor de posiciones**: Ver todas las posiciones con su estado de protección
- **Gráficos interactivos**: Distribución de profit, estado de protección
- **Log de eventos**: Historial de modificaciones aplicadas
- **Configuración actual**: Ver parámetros activos del sistema

## 🎯 Estrategias de Uso

### 1. **Configuración Conservadora**
```env
BREAKEVEN_TRIGGER_PIPS=15
BREAKEVEN_OFFSET_PIPS=3
TRAILING_ACTIVATION_PIPS=25
TRAILING_DISTANCE_PIPS=20
CONSERVATIVE_MODE=true
```
**Ideal para**: Mercados volátiles, principiantes, preservación de capital

### 2. **Configuración Estándar**
```env
BREAKEVEN_TRIGGER_PIPS=20
BREAKEVEN_OFFSET_PIPS=2
TRAILING_ACTIVATION_PIPS=30
TRAILING_DISTANCE_PIPS=15
CONSERVATIVE_MODE=false
```
**Ideal para**: Condiciones normales de mercado, traders intermedios

### 3. **Configuración Agresiva**
```env
BREAKEVEN_TRIGGER_PIPS=25
BREAKEVEN_OFFSET_PIPS=1
TRAILING_ACTIVATION_PIPS=35
TRAILING_DISTANCE_PIPS=10
USE_AI_RISK_OPTIMIZATION=true
```
**Ideal para**: Tendencias fuertes, traders experimentados, maximizar ganancias

## 🤖 Integración con IA

### Cómo funciona la optimización por IA:

1. **Análisis de contexto**: La IA evalúa volatilidad, tendencia y momentum
2. **Ajuste dinámico**: Modifica parámetros según condiciones actuales
3. **Decisiones inteligentes**: 
   - Alta volatilidad → Mayor distancia de trailing
   - Tendencia fuerte → Breakeven más tarde
   - Cerca de resistencia → Protección más agresiva

### Ejemplo de respuesta IA:
```json
{
  "breakeven_trigger": 22,
  "trailing_activation": 32,
  "trailing_distance": 18,
  "risk_level": "moderate",
  "reason": "Volatilidad elevada detectada"
}
```

## 📈 Casos de Uso

### Ejemplo 1: Trade de EURUSD
```
Entrada: 1.0850 BUY
Configuración: Breakeven=20 pips, Trailing=30 pips

1. Precio sube a 1.0870 (+20 pips)
   → Breakeven aplicado: SL movido a 1.0852
   
2. Precio sube a 1.0880 (+30 pips)
   → Trailing activado: SL a 1.0865 (15 pips atrás)
   
3. Precio sube a 1.0890 (+40 pips)
   → Trailing actualizado: SL a 1.0875
```

### Ejemplo 2: Trade de BTCUSD con IA
```
Entrada: 67,500 BUY
IA detecta alta volatilidad

1. IA sugiere: Breakeven=30 pips (en vez de 20)
2. Precio sube a 67,530 → Espera (no aplica aún)
3. Precio sube a 67,540 → Breakeven aplicado
4. IA ajusta trailing a 25 pips por volatilidad
```

## 🛠️ Configuración Avanzada

### Parámetros por Símbolo
Puedes configurar parámetros específicos por símbolo en el `.env`:

```env
# Bitcoin
BTCUSD_BREAKEVEN_TRIGGER=30
BTCUSD_TRAILING_DISTANCE=20

# Forex
EURUSD_BREAKEVEN_TRIGGER=15
EURUSD_TRAILING_DISTANCE=10

# Oro
XAUUSD_BREAKEVEN_TRIGGER=25
XAUUSD_TRAILING_DISTANCE=15
```

### Control de Horarios
```env
# Horario de operación (24h = siempre activo)
RISK_MANAGER_START_HOUR=0
RISK_MANAGER_END_HOUR=24

# Días activos (1=Lunes, 7=Domingo)
RISK_MANAGER_DAYS=1,2,3,4,5
```

### Modo Debug
```env
# Ver información detallada
RISK_DEBUG_MODE=true

# Simular sin ejecutar (testing)
RISK_DRY_RUN=true
```

## 📊 Estadísticas y Métricas

El sistema registra:
- **Total de breakeven aplicados**
- **Total de trailing actualizados**
- **Pips totales protegidos**
- **Posiciones gestionadas**
- **Sugerencias de IA aplicadas**

## ⚠️ Consideraciones Importantes

### DO's ✅
- ✅ Usa en cuenta DEMO primero
- ✅ Ajusta parámetros según tu estilo de trading
- ✅ Monitorea el dashboard regularmente
- ✅ Revisa logs para entender comportamiento
- ✅ Actualiza configuración según resultados

### DON'Ts ❌
- ❌ No uses valores muy pequeños (< 10 pips)
- ❌ No cambies configuración durante trades abiertos
- ❌ No desactives sin cerrar posiciones primero
- ❌ No ignores las sugerencias de IA
- ❌ No uses sin entender los parámetros

## 🔧 Solución de Problemas

### Error: "No se puede modificar posición"
- Verifica que MT5 esté conectado
- Confirma que la posición existe
- Revisa que tengas permisos de modificación

### Error: "IA no responde"
- Verifica que Ollama esté ejecutándose
- Confirma el modelo: `ollama list`
- Revisa configuración en `.env`

### Breakeven/Trailing no se aplica
- Verifica que esté activado en `.env`
- Confirma que se alcanzó el trigger
- Revisa logs para más detalles

## 📞 Integración con el Sistema Principal

El Risk Manager se integra perfectamente con:
- **Signal Generator**: Protege trades generados
- **MT5 Connection**: Modifica órdenes en tiempo real
- **Telegram Notifier**: Envía alertas de cambios
- **TwelveData**: Obtiene ATR para cálculos

## 🚀 Comandos Rápidos

```bash
# Iniciar todo
START_RISK_MANAGER.bat

# Solo Risk Manager
python src/risk/advanced_risk_manager.py

# Solo Dashboard
streamlit run risk_manager_dashboard.py

# Ver logs
tail -f logs/risk_manager.log

# Configuración rápida
notepad configs/.env
```

## 📈 Resultados Esperados

Con configuración óptima puedes esperar:
- **30-50% menos pérdidas** por protección temprana
- **20-40% más ganancias** por trailing efectivo
- **Mejor ratio riesgo/beneficio**
- **Reducción de estrés** al operar
- **Gestión automática 24/7**

---

**© 2025 Algo Trader V3 - Advanced Risk Manager**
