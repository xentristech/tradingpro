# ALGO TRADER MVP V3 - SISTEMA DE TRADING PROFESIONAL

## 📋 ESTADO ACTUAL DEL PROYECTO

### 🔴 SERVICIOS ACTIVOS
- **Puerto 8512**: Revolutionary Dashboard (Web scraping + AI signals)
- **Puerto 8516**: Chart Simulation Reviewed (Canvas HTML5)
- **Puerto 8517**: TradingView Professional Chart (Lightweight Charts)
- **Background**: TICK_SYSTEM_FINAL.py (Análisis de ticks MT5)

### 📊 COMPONENTES PRINCIPALES

#### 1. DASHBOARDS
| Archivo | Puerto | Estado | Descripción |
|---------|--------|--------|-------------|
| revolutionary_dashboard_final.py | 8512 | ✅ Activo | Dashboard con scraping Investing.com |
| chart_simulation_reviewed.py | 8516 | ✅ Activo | Simulación de gráficos con Canvas |
| tradingview_professional_chart.py | 8517 | ✅ Activo | Chart profesional TradingView |
| modern_trading_dashboard.py | 8508 | ⚠️ Inactivo | Dashboard moderno base |
| innovative_signal_dashboard.py | 8510 | ⚠️ Inactivo | Dashboard con señales AI |

#### 2. SISTEMAS DE DATOS
| Archivo | Función | Estado |
|---------|---------|--------|
| TICK_SYSTEM_FINAL.py | Análisis ticks MT5 | ✅ Activo |
| FINAL_TICK_SYSTEM_WORKING.py | Sistema ticks completo | ✅ Funcional |
| mt5_advanced_scraper.py | Scraping docs MQL5 | ✅ Completo |

#### 3. CONFIGURACIÓN
- **API TwelveData**: 23d17ce5b7044ad5aef9766770a6252b
- **Cuenta MT5 Exness**: 197678662
- **Símbolos principales**: XAUUSD, EURUSD, GBPUSD, USDJPY

## 🎯 CONTEXTO PARA CLAUDE

### PROMPT DE CONTEXTO
```
Estoy trabajando en un sistema de trading profesional con múltiples dashboards.
Los archivos principales están en: C:\Users\user\Desktop\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2\

ESTADO ACTUAL:
- 3 dashboards funcionando en puertos 8512, 8516, 8517
- Sistema de ticks MT5 activo analizando 400+ símbolos
- TradingView Lightweight Charts implementado
- Web scraping de Investing.com activo

NECESITO:
[Describir aquí lo que necesitas hacer]

IMPORTANTE:
- Todo debe ser dinámico, no estático
- Usar diseño moderno tipo TradingView
- Integrar datos reales cuando sea posible
```

## 📁 ESTRUCTURA DEL PROYECTO

```
algo-trader-mvp-v2/
├── README.md                           # Este archivo - Fuente de verdad
├── requirements.txt                     # Dependencias Python
│
├── DASHBOARDS/
│   ├── revolutionary_dashboard_final.py
│   ├── chart_simulation_reviewed.py
│   ├── tradingview_professional_chart.py
│   └── [otros dashboards]
│
├── SISTEMAS/
│   ├── TICK_SYSTEM_FINAL.py
│   ├── FINAL_TICK_SYSTEM_WORKING.py
│   └── mt5_advanced_scraper.py
│
├── CHARTS/
│   ├── ultra_advanced_chart.py
│   └── test_chart_minimal.py
│
└── DOCS/
    ├── MT5_Function_Reference.md
    └── API_Documentation.md
```

## 🔧 COMANDOS ÚTILES

### Iniciar servicios principales
```bash
# Dashboard principal
python revolutionary_dashboard_final.py

# Chart profesional TradingView
python tradingview_professional_chart.py

# Sistema de ticks
python TICK_SYSTEM_FINAL.py
```

### Git workflow
```bash
# Inicializar repo (solo primera vez)
git init
git add .
git commit -m "Initial commit - Sistema de trading profesional"

# Antes de cada cambio mayor
git add .
git commit -m "Estado antes de [descripción del cambio]"
git push

# Para que Claude lea el estado
# "Lee el README.md desde GitHub en [url del repo]"
```

## 📝 HISTORIAL DE CAMBIOS

### 2024-08-29
- ✅ Implementado TradingView Professional Chart con Lightweight Charts
- ✅ Revisado chart simulation element
- ✅ Corregido problemas de encoding Unicode
- ✅ 3 dashboards funcionando simultáneamente
- ✅ Creado README.md como fuente de verdad

### 2024-08-28
- ✅ Creado revolutionary_dashboard_final.py
- ✅ Web scraping de Investing.com
- ✅ Integración MT5 con cuenta Exness
- ✅ Sistema de señales AI implementado

## 🎨 ESTILO Y DISEÑO

### Paleta de colores
- Background: #0a0a0a, #131722
- Cards: #1a1a2e, #1e222d
- Borders: #333, #2a2e39
- Text: #ffffff, #d1d4dc
- Success: #26a69a, #4CAF50
- Error: #ef5350, #f44336
- Primary: #2962ff, #667eea

### Principios de diseño
1. **Dinámico**: Todo actualizable en tiempo real
2. **Moderno**: Estilo TradingView/profesional
3. **Responsive**: Adaptable a diferentes pantallas
4. **Intuitivo**: Controles claros y accesibles
5. **Performante**: Optimizado para datos en tiempo real

## 🚀 PRÓXIMOS PASOS

1. [ ] Crear repositorio en GitHub
2. [ ] Configurar GitHub Actions para CI/CD
3. [ ] Unificar todos los dashboards en uno principal
4. [ ] Implementar WebSocket para datos reales
5. [ ] Agregar más indicadores técnicos
6. [ ] Sistema de alertas y notificaciones
7. [ ] Base de datos para históricos
8. [ ] Panel de backtesting

## 📞 CONTACTO Y SOPORTE

- **Proyecto**: Algo Trader MVP v3
- **Ubicación**: Xentristech/Developer
- **Stack**: Python, JavaScript, HTML5, MT5, TradingView

---

**NOTA PARA CLAUDE**: Este README es la fuente de verdad del proyecto. 
Antes de hacer cambios mayores, lee este archivo para entender el contexto completo.
Actualiza este README después de cada cambio significativo.