# 📊 DIARIO DE TRADING INTELIGENTE Y GESTIÓN DE RIESGO - GUÍA COMPLETA

## 🎯 **SISTEMA IMPLEMENTADO**

**✅ FASE 1 - DIARIO DE TRADING INTELIGENTE**
- ✅ Registro automático de operaciones
- ✅ Métricas avanzadas (Sharpe, Sortino, Drawdown, VaR)
- ✅ Análisis de patrones temporales
- ✅ Exportación a Google Sheets
- ✅ Reportes diarios automáticos

**✅ FASE 2 - GESTOR DE RIESGOS EN TIEMPO REAL**
- ✅ Dashboard local con Streamlit
- ✅ Alertas Telegram + sonido local
- ✅ Monitor de exposición y correlación
- ✅ Detección de posiciones sin SL/TP
- ✅ Análisis de margin level

---

## 🚀 **CÓMO USAR EL SISTEMA COMPLETO**

### **Opción 1: Sistema Completo (Recomendado)**
```batch
START_RISK_JOURNAL_SYSTEM.bat
```

**Esto incluye:**
- 🤖 Trading automático con IA
- 📊 Journal de trading inteligente
- ⚠️ Monitor de riesgo en tiempo real
- 📱 Alertas Telegram
- 🔊 Alertas sonoras locales
- 📈 Exportación automática a Google Sheets

### **Opción 2: Solo Dashboard de Riesgo**
```batch
START_RISK_DASHBOARD.bat
```
Abre dashboard interactivo en: `http://localhost:8501`

### **Opción 3: Solo Monitor de Riesgo**
```python
python src/risk/risk_monitor.py
```

---

## 📊 **CARACTERÍSTICAS DEL DIARIO INTELIGENTE**

### **Métricas Calculadas Automáticamente:**

#### 📈 **Rendimiento**
- **Win Rate**: Porcentaje de trades ganadores
- **Profit Factor**: Ganancia bruta / Pérdida bruta
- **Expectancy**: Ganancia esperada por trade
- **Risk/Reward Ratio**: Promedio ganancia/pérdida

#### 📊 **Métricas Financieras Profesionales**
- **Sharpe Ratio**: Retorno ajustado por riesgo
- **Sortino Ratio**: Sharpe considerando solo volatilidad negativa
- **Maximum Drawdown**: Máxima pérdida histórica
- **Calmar Ratio**: Retorno anual / Max Drawdown
- **VaR 95%**: Value at Risk al 95% de confianza
- **Recovery Factor**: Net Profit / Max Drawdown

#### 🎯 **Análisis de Patrones**
- **Mejores horas del día** para trading
- **Mejores días de la semana**
- **Rachas máximas** de ganancias/pérdidas
- **Performance por símbolo**
- **Performance por estrategia**

---

## ⚠️ **SISTEMA DE ALERTAS DE RIESGO**

### **Alertas Críticas (🚨 Sonido + Telegram):**
- Drawdown > 10%
- Posiciones sin Stop Loss
- Margin level < 200%
- Exposición total > 30%

### **Alertas de Advertencia (⚠️ Sonido + Telegram):**
- Drawdown > 5%
- 3+ pérdidas consecutivas
- Exposición > 20%
- Win rate < 40%
- Alta correlación entre posiciones

### **Configurar Límites de Riesgo:**
Editar en `src/risk/risk_monitor.py`:
```python
self.risk_limits = {
    'max_daily_drawdown': 5.0,  # %
    'max_total_drawdown': 10.0,  # %
    'max_exposure': 30.0,  # %
    'min_margin_level': 200.0,  # %
    'max_consecutive_losses': 3
}
```

---

## 📈 **DASHBOARD INTERACTIVO**

### **Métricas en Tiempo Real:**
- Balance y Equity actual
- Drawdown en tiempo real
- Win Rate y Profit Factor
- Risk Score (0-100)

### **Gráficos Disponibles:**
- 📊 **Equity Curve**: Evolución del capital
- 📉 **Drawdown Chart**: Pérdidas históricas
- 📈 **PnL Distribution**: Distribución de ganancias
- 🎯 **Symbol Performance**: Rendimiento por activo

### **Tabs del Dashboard:**
- **📊 Gráficos**: Visualizaciones interactivas
- **📋 Trades**: Historial de operaciones
- **💹 Posiciones**: Posiciones abiertas en vivo
- **📈 Métricas**: Estadísticas detalladas
- **🎯 Análisis**: Patrones y recomendaciones

---

## 📊 **GOOGLE SHEETS INTEGRATION**

### **Configuración Inicial:**

1. **Crear proyecto en Google Cloud Console**
2. **Habilitar Google Sheets API**
3. **Crear credenciales de Service Account**
4. **Descargar archivo JSON**
5. **Guardar como** `configs/google_credentials.json`

### **Datos Exportados Automáticamente:**
- **Trades Sheet**: Historial completo de operaciones
- **Metrics Sheet**: Métricas calculadas
- **Daily Summary**: Resumen diario de balance/equity
- **Dashboard Sheet**: Panel con fórmulas automáticas

### **Ejemplo de Dashboard Automático:**
```
ALGO TRADER V3 - DASHBOARD
=========================
Balance Actual:    $10,250.50
Equity Actual:     $10,180.75
PnL Total:         $250.50
Win Rate:          68.5%
Profit Factor:     1.85
Max Drawdown:      -2.5%
```

---

## 🔊 **ALERTAS SONORAS LOCALES**

### **Tipos de Sonido:**
- **Crítico**: 3 beeps seguidos (1000Hz)
- **Advertencia**: 1 beep (800Hz)
- **Información**: 1 beep suave (600Hz)

### **Sistema Multiplataforma:**
- ✅ **Windows**: `winsound.Beep()`
- ✅ **Linux/Mac**: Bell character `\a`

---

## 📱 **NOTIFICACIONES TELEGRAM**

### **Tipos de Mensaje:**

#### **🚨 Alerta Crítica:**
```
🚨🔴 ALERTA CRÍTICA 🚨🔴

Drawdown máximo alcanzado: 12.5%
Límite: 10%
⚠️ CONSIDERAR DETENER TRADING

Hora: 14:25:30
Sistema: AlgoTrader V3
```

#### **⚠️ Advertencia:**
```
⚠️🟡 ADVERTENCIA ⚠️🟡

Posición sin Stop Loss detectada
Ticket: 123456
Símbolo: XAUUSD
Tipo: BUY | Volumen: 0.1

Hora: 14:25:30
Sistema: AlgoTrader V3
```

---

## 📊 **ANÁLISIS DE PATRONES INTELIGENTE**

### **Detección Automática:**
- **Horarios más rentables**: ¿A qué hora trade mejor?
- **Días más exitosos**: ¿Qué días son mejores?
- **Símbolos más rentables**: ¿En qué activos eres mejor?
- **Estrategias más efectivas**: ¿Qué funciona mejor?

### **Ejemplo de Análisis:**
```python
patterns = journal.analyze_patterns()

# Mejores horas
print(patterns['best_hours'])
# [(14, {'trades': 15, 'profit': 450.50}), ...]

# Racha actual  
if patterns['current_streak'] > 0:
    print(f"Racha ganadora: {patterns['current_streak']} trades")
```

---

## 💡 **RECOMENDACIONES AUTOMÁTICAS**

### **Sistema de Sugerencias IA:**
El journal analiza tu historial y sugiere mejoras:

- ⚠️ **Win rate bajo** → "Revisar condiciones de entrada"
- ⚠️ **R:R bajo** → "Considerar targets más amplios"
- 🔴 **Drawdown alto** → "Reducir tamaño de posiciones"
- ⚠️ **Sharpe bajo** → "Mejorar consistencia"

---

## 📁 **ESTRUCTURA DE ARCHIVOS CREADOS**

```
algo-trader-mvp-v2/
├── src/
│   ├── journal/
│   │   ├── trading_journal.py      # Diario inteligente
│   │   └── google_sheets_exporter.py  # Exportador Sheets
│   └── risk/
│       └── risk_monitor.py         # Monitor de riesgo
├── data/
│   ├── trading_journal.json       # Historial de trades
│   └── bot_state.json             # Estado del sistema
├── logs/
│   └── risk_alerts.csv           # Log de alertas
├── configs/
│   └── google_credentials.json    # Credenciales Google (crear)
├── risk_dashboard.py              # Dashboard Streamlit
├── requirements_journal.txt       # Dependencias
├── START_RISK_JOURNAL_SYSTEM.bat  # Iniciar todo
└── START_RISK_DASHBOARD.bat      # Solo dashboard
```

---

## 🛠️ **INSTALACIÓN Y CONFIGURACIÓN**

### **1. Instalar Dependencias:**
```bash
pip install -r requirements_journal.txt
```

### **2. Configurar Google Sheets (Opcional):**
- Seguir guía en: https://docs.gspread.org/en/latest/oauth2.html
- Guardar credenciales en `configs/google_credentials.json`

### **3. Verificar Configuración:**
```python
python src/journal/trading_journal.py  # Test journal
python src/risk/risk_monitor.py        # Test monitor
```

### **4. Iniciar Sistema:**
```batch
START_RISK_JOURNAL_SYSTEM.bat
```

---

## 📊 **EJEMPLOS DE USO**

### **Registrar Trade Manualmente:**
```python
from src.journal.trading_journal import get_journal

journal = get_journal()

trade_data = {
    'ticket': 12345,
    'symbol': 'XAUUSD',
    'type': 'BUY',
    'volume': 0.01,
    'entry_price': 2650.50,
    'exit_price': 2655.00,
    'profit_usd': 45.0,
    'strategy': 'AI_Hybrid',
    'confidence': 0.85
}

journal.add_trade(trade_data)
```

### **Obtener Métricas:**
```python
metrics = journal.calculate_metrics(period_days=30)
print(f"Win Rate: {metrics['win_rate']*100:.1f}%")
print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
print(f"Max Drawdown: {metrics['max_drawdown_percent']:.2f}%")
```

### **Exportar a CSV:**
```python
journal.export_to_csv('mi_historial.csv')
```

---

## 🎯 **PRÓXIMAS MEJORAS (FASE 3)**

### **IA Aplicada al Diario:**
- 🤖 **Modelo ML** para predecir trades exitosos
- 📊 **Dataset automático** con features de indicadores
- ⚠️ **Alertas predictivas** antes de ejecutar trades
- 📈 **Análisis de régimen** de mercado (tendencia/reversal)

### **Extensiones Avanzadas:**
- 🎯 **ATR dinámico** para SL/TP
- 📊 **Backtesting automático** de estrategias
- 🔍 **Explicaciones LLM** de señales generadas

---

## 🆘 **SOLUCIÓN DE PROBLEMAS**

### **Error: "Google Sheets no disponible"**
```bash
pip install gspread google-auth
# Configurar credenciales en configs/google_credentials.json
```

### **Error: "Streamlit no encontrado"**
```bash
pip install streamlit plotly
```

### **No hay sonido en alertas**
```bash
pip install playsound  # Alternativa multiplataforma
```

### **Dashboard no carga**
- Verificar puerto 8501 disponible
- Ejecutar: `streamlit run risk_dashboard.py --server.port 8502`

---

## 📞 **SOPORTE Y LOGS**

### **Archivos de Log:**
- `logs/trading.log`: Actividad general
- `logs/risk_alerts.csv`: Historial de alertas
- `data/trading_journal.json`: Historial de trades

### **Verificar Estado:**
```python
# Estado del journal
journal = get_journal()
print(f"Trades: {len(journal.trades)}")

# Estado del monitor
monitor = RiskMonitor()
report = monitor.generate_risk_report()
print(f"Risk Score: {report['risk_score']:.1f}")
```

---

## 🎉 **SISTEMA COMPLETO ACTIVO**

**Ya tienes implementado:**
- ✅ **Diario inteligente** con 12+ métricas profesionales
- ✅ **Monitor de riesgo** con alertas críticas
- ✅ **Dashboard interactivo** en tiempo real
- ✅ **Google Sheets** automático
- ✅ **Análisis de patrones** IA
- ✅ **Alertas Telegram + sonido**

**Para usar:**
```batch
# Sistema completo
START_RISK_JOURNAL_SYSTEM.bat

# Solo dashboard
START_RISK_DASHBOARD.bat
```

**El sistema monitorea:**
- 📊 Todas las métricas de rendimiento
- ⚠️ Riesgos en tiempo real
- 🎯 Patrones de comportamiento
- 📈 Evolución del capital
- 🚨 Situaciones críticas

---

**🚀 ¡SISTEMA DE TRADING PROFESIONAL CON IA Y GESTIÓN DE RIESGO COMPLETAMENTE FUNCIONAL!**

*Desarrollado para Algo Trader V3 - Sistema avanzado de trading algorítmico*