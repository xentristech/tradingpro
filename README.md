# 🤖 Algo Trader v3 — Sistema de Trading Algorítmico con IA

<p align="right">
  <a href="https://wa.me/573125827128" target="_blank">
    <img alt="Contactar por WhatsApp" src="https://img.shields.io/badge/Contactar%20por%20WhatsApp-25D366?logo=whatsapp&logoColor=white&labelColor=1f1f1f" />
  </a>
  &nbsp;
  <a href="mailto:info@xentris.tech">
    <img alt="Enviar Email" src="https://img.shields.io/badge/Enviar%20Email-0078D4?logo=microsoftoutlook&logoColor=white&labelColor=1f1f1f" />
  </a>
  &nbsp;
  <a href="https://xentris.tech/" target="_blank">
    <img alt="Xentris Tech" src="https://img.shields.io/badge/Xentris%20Tech-0EA5A4?labelColor=1f1f1f" />
  </a>
  &nbsp;
  <a href="https://github.com/xentristech/tradingpro/actions/workflows/lint.yml" target="_blank">
    <img alt="CI Status" src="https://github.com/xentristech/tradingpro/actions/workflows/lint.yml/badge.svg" />
  </a>
  &nbsp;
  <a href="https://github.com/xentristech/tradingpro/actions/workflows/quality.yml" target="_blank">
    <img alt="Quality Status" src="https://github.com/xentristech/tradingpro/actions/workflows/quality.yml/badge.svg" />
  </a>
</p>

<strong>Repositorio:</strong> <code>tradingpro</code>

Este repositorio contiene la versión v3 del sistema de trading algorítmico con integración MT5, análisis técnico, gestión de riesgo avanzada, módulos de ML y soporte para IA local (Ollama). Incluye CLI unificada, dashboards en Streamlit y múltiples scripts de operación y diagnóstico.

Tecnología hecha con IA y científicos de datos por Xentris Tech.

## Novedades v3 (resumen)
- CLI unificada (`cli.py`) para configuración y ejecución.
- `main_trader.py` como punto de entrada con health checks y shutdown seguro.
- `configs/settings.yaml` validado con Pydantic (`settings_loader.py`).
- Generador de señales multi‑estrategia y consenso (`signals/signal_generator.py`).
- Gestor de riesgo avanzado con límites, drawdown y Kelly parcial (`risk/risk_manager.py`).
- Integración ML opcional (`ml/ml_predictor.py`).
- Notificaciones Telegram con formatos ricos (`notifiers/telegram_notifier.py`).
- Dashboards: `streamlit_app.py`, `advanced_dashboard.py`, `trading_dashboard.py`, `ai_dashboard.py`.

## Quickstart en 5 pasos
1) Crear entorno e instalar dependencias
```
python -m venv .venv
.\.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```
2) Copiar plantillas de configuración
```
copy configs\.env.example configs\.env
copy configs\settings.yaml.example configs\settings.yaml
```
3) Completar `.env` (MT5, TwelveData, Telegram) y ajustar `settings.yaml`.
4) Verificar el sistema
```
python test_mt5_connection.py
python test_telegram.py
python VERIFICAR_TODO.py
```
5) Ejecutar en demo y abrir dashboard (opcional)
```
python cli.py trade run --mode demo --config configs/.env
streamlit run streamlit_app.py
```

Referencia: Checklist de Puesta en Marcha → `docs/SETUP_CHECKLIST.md`

## Prerrequisitos

1) Python 3.10+ (64-bit)
- Descargar: https://www.python.org/downloads/
- Importante: en Windows marca “Add Python to PATH” al instalar.

2) MetaTrader 5
- Descarga desde tu broker (ej. Exness) y crea primero una cuenta demo.

3) IA (opcional)
- Ollama (local): https://ollama.ai/download
- Modelo recomendado: `ollama pull deepseek-r1:14b`

## Configuración

1) Variables de entorno (.env)
- Copia `configs/.env.example` a `configs/.env` y completa tus datos.
- Claves principales del .env:
```
TWELVEDATA_API_KEY=...
TELEGRAM_TOKEN=...
TELEGRAM_CHAT_ID=...
OLLAMA_API_BASE=http://localhost:11434/v1
OLLAMA_MODEL=deepseek-r1:14b
LIVE_TRADING=false
SYMBOL=BTCUSDm
MT5_PATH=C:\\Program Files\\MetaTrader 5 EXNESS\\terminal64.exe
MT5_LOGIN=...
MT5_PASSWORD=...
MT5_SERVER=...
MT5_TIMEOUT=60000
```

2) Settings de trading (YAML)
- Copia `configs/settings.yaml.example` a `configs/settings.yaml`.
- Se valida con Pydantic (ver `configs/settings_loader.py`).

3) Obtener API Keys
- TwelveData: https://twelvedata.com/ (plan gratuito disponible). Añade `TWELVEDATA_API_KEY`.
- Telegram: crea un bot con @BotFather (token) y obtén tu `chat_id` (p.ej. con @userinfobot).

## Instalación

Windows PowerShell (proyecto en la carpeta actual):
```
python -m venv .venv
.\.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

Alternativa rápida (scripts):
- `QUICK_INSTALL.bat` o `INSTALL_COMPLETE.bat` configuran dependencias y atajos en Windows.

## Verificaciones rápidas

- Probar MT5: `python test_mt5_connection.py` o `python CONECTAR_MT5.py`
- Probar Telegram: `python test_telegram.py`
- Chequeo general: `python VERIFICAR_TODO.py` o `python health_check.py`

## Formas de ejecución

Opción A — CLI unificada (recomendada)
```
python cli.py trade run --mode demo --config configs/.env
python cli.py trade check --config configs/.env
python cli.py trade snapshot --symbol BTC/USD --interval 15min --lookback 200
```

Opción B — Punto de entrada principal
```
python main_trader.py --mode demo --config configs/.env
python main_trader.py --check --config configs/.env
```

Opción C — Scripts/Batch (Windows)
- Arranque rápido: `START.bat`, `START_SYSTEM.bat`, `RUN.bat`, `TRADER.bat`
- Dashboards: `DASHBOARD.bat`, `DASHBOARD_SIMPLE.bat`
- Utilidades: `CHECK.bat`, `VERIFICAR_IA.bat`, `VERIFICAR_OLLAMA.bat`

## Dashboards (Streamlit)

Interfaz visual en navegador:
```
streamlit run streamlit_app.py
```
Otros paneles disponibles: `advanced_dashboard.py`, `trading_dashboard.py`, `ai_dashboard.py`.

## Arquitectura (módulos principales)

- `core/`: Orquestación del bot y estado del sistema (`bot_manager.py`, `system_manager.py`).
- `broker/`: Conexión y operaciones MT5 (`mt5_connection.py`).
- `data/`: Ingesta TwelveData + caché + indicadores (`data_manager.py`).
- `signals/`: Generación de señales multi-estrategia (`signal_generator.py`).
- `risk/`: Gestión de riesgo avanzada (tamaño posición, límites, drawdown) (`risk_manager.py`).
- `ml/`: Predicción con ML (XGBoost/Sklearn), features y modelos (`ml_predictor.py`).
- `ai/` y raíz: utilidades de IA (Ollama), generadores y monitores (`ai_signal_generator.py`, `ai_trade_monitor.py`).
- `notifiers/`: Notificaciones por Telegram (`telegram_notifier.py`).
- `configs/`: `.env`, `settings.yaml` y loader con validaciones.
- `utils/`, `tools/`, `logs/`, `storage/`, `signals/`, `orchestrator/`: soporte, utilidades y estado.

Flujo (simplificado):
1) DataManager obtiene OHLCV de TwelveData y agrega indicadores.
2) SignalGenerator produce señales multi-timeframe y consenso.
3) RiskManager evalúa si operar (límites, drawdown, rachas, correlación).
4) Broker MT5 ejecuta/cierra y gestiona SL/TP (+ trailing), con logs/notifs.
5) ML/IA pueden reforzar señales o monitorear condiciones.

## Variables clave (.env)

- Trading: `LIVE_TRADING`, `SYMBOL`, `MIN_CONFIDENCE`, `MAX_RISK_PER_TRADE`, `MAX_PORTFOLIO_RISK`, `MAX_POSITIONS`, `MAX_DAILY_LOSS`.
- MT5: `MT5_LOGIN`, `MT5_PASSWORD`, `MT5_SERVER`, `MT5_TIMEOUT`, `MT5_DEVIATION`, `MT5_MAGIC`.
- IA: `OLLAMA_API_BASE`, `OLLAMA_MODEL` (opcional `OPENAI_API_KEY`).
- Sistema: `TZ`, `LOG_LEVEL`, `POLL_SECONDS`.

## Buenas prácticas (Live Trading)

Nunca actives `LIVE_TRADING=true` hasta que:
1) Pasen todas las pruebas en demo (MT5, señales, riesgo, Telegram).
2) Revises logs y comportamiento por al menos 1–2 días.
3) Ajustes `settings.yaml` y límites de riesgo a tu perfil.
4) Tengas respaldos de `.env` y `settings.yaml`.

## Solución de problemas

- Python no encontrado: reinstala Python 3.10+ y marca “Add to PATH”.
- MT5 no conecta: verifica credenciales y servidor; abre MT5 con la cuenta conectada.
- TwelveData sin datos: confirma API key y límite de rate; revisa símbolo/intervalo.
- Telegram falla: confirma `TELEGRAM_TOKEN` y `TELEGRAM_CHAT_ID`.
- Ollama: verifica servicio activo (`ollama list`) y modelo descargado.

## Scripts útiles (selección)

- Diagnóstico: `full_diagnosis.py`, `health_check.py`, `VERIFICAR_TODO.py`.
- Pruebas: `test_mt5_connection.py`, `test_trade.py`, `live_test_trade.py`.
- Ejecución: `main_trader.py`, `multi_trader.py`, `execute_trading.py`, `exness_automated_trader.py`.
- Dashboards: `streamlit_app.py`, `advanced_dashboard.py`, `trading_dashboard.py`, `ai_dashboard.py`.

## Tecnologías usadas y ecosistema
- IA/LLM: DeepSeek (vía Ollama), OpenAI API, Claude (Anthropic).
- Datos: TwelveData (OHLCV e indicadores); soporte opcional yfinance/Alpha Vantage.
- Broker: MetaTrader 5 (ej. Exness) para ejecución y datos de cuenta.
- Cloud/Infra: AWS (despliegues e integración opcionales).
- Herramientas: Microsoft (Windows/PowerShell/VS Code), Google (Colab/Cloud opcional).
- Stack Python: pandas, numpy, aiohttp, pydantic, scikit‑learn, xgboost, streamlit, colorlog.

## Badges (tecnologías)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![MetaTrader 5](https://img.shields.io/badge/Broker-MetaTrader%205-green)
![Exness](https://img.shields.io/badge/Broker-Exness-black)
![TwelveData](https://img.shields.io/badge/Data-TwelveData-orange)
![Ollama](https://img.shields.io/badge/AI-Ollama-black)
![DeepSeek R1](https://img.shields.io/badge/Model-DeepSeek--R1-8A2BE2)
![OpenAI](https://img.shields.io/badge/LLM-OpenAI-412991?logo=openai)
![Claude](https://img.shields.io/badge/LLM-Claude-9f79ee)
![AWS](https://img.shields.io/badge/Cloud-AWS-232f3e?logo=amazon-aws&logoColor=ff9900)
![Google Cloud](https://img.shields.io/badge/Cloud-Google%20Cloud-4285F4?logo=googlecloud&logoColor=white)
![Microsoft](https://img.shields.io/badge/Platform-Microsoft-0078D4?logo=microsoft)
![Streamlit](https://img.shields.io/badge/Web-Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![pandas](https://img.shields.io/badge/Lib-pandas-150458?logo=pandas)
![numpy](https://img.shields.io/badge/Lib-numpy-013243?logo=numpy)
![scikit-learn](https://img.shields.io/badge/ML-scikit--learn-F7931E?logo=scikitlearn)
![XGBoost](https://img.shields.io/badge/ML-XGBoost-EB5F07)

## Links y logos
- Xentris Tech: https://xentris.tech/
- DeepSeek (Ollama): https://ollama.com/library/deepseek-r1
- OpenAI: https://platform.openai.com/
- Claude (Anthropic): https://www.anthropic.com/claude
- Microsoft (Windows/VS Code): https://code.visualstudio.com/
- Google Cloud: https://cloud.google.com/
- AWS: https://aws.amazon.com/
- TwelveData: https://twelvedata.com/
- MetaTrader 5: https://www.metatrader5.com/
- Exness (MT5 broker): https://www.exness.com/

Se incluyen logos locales (SVG con nombre) para fácil distinción en `assets/logos/`.

## Logos (SVG locales)

Empresa

<table>
  <tr>
    <td align="center"><a href="https://xentris.tech/"><img alt="Xentris Tech" src="assets/logos/xentris-tech.svg" height="40" /></a><br><sub>Xentris Tech</sub></td>
  </tr>
</table>

Broker

<table>
  <tr>
    <td align="center"><img alt="MetaTrader 5" src="assets/logos/metatrader5.svg" height="40" /><br><sub>MetaTrader 5</sub></td>
    <td align="center"><img alt="Exness" src="assets/logos/exness.svg" height="40" /><br><sub>Exness</sub></td>
  </tr>
</table>

IA / LLM

<table>
  <tr>
    <td align="center"><img alt="Ollama" src="assets/logos/ollama.svg" height="40" /><br><sub>Ollama</sub></td>
    <td align="center"><img alt="DeepSeek R1" src="assets/logos/deepseek.svg" height="40" /><br><sub>DeepSeek R1</sub></td>
    <td align="center"><img alt="OpenAI" src="assets/logos/openai.svg" height="40" /><br><sub>OpenAI</sub></td>
    <td align="center"><img alt="Claude (Anthropic)" src="assets/logos/claude.svg" height="40" /><br><sub>Claude</sub></td>
  </tr>
</table>

Datos

<table>
  <tr>
    <td align="center"><img alt="TwelveData" src="assets/logos/twelvedata.svg" height="40" /><br><sub>TwelveData</sub></td>
  </tr>
</table>

Cloud / Infra

<table>
  <tr>
    <td align="center"><img alt="AWS" src="assets/logos/aws.svg" height="40" /><br><sub>AWS</sub></td>
    <td align="center"><img alt="Google Cloud" src="assets/logos/google-cloud.svg" height="40" /><br><sub>Google Cloud</sub></td>
    <td align="center"><img alt="Microsoft" src="assets/logos/microsoft.svg" height="40" /><br><sub>Microsoft</sub></td>
  </tr>
</table>

Python Stack

<table>
  <tr>
    <td align="center"><img alt="Python" src="assets/logos/python.svg" height="40" /><br><sub>Python</sub></td>
    <td align="center"><img alt="pandas" src="assets/logos/pandas.svg" height="40" /><br><sub>pandas</sub></td>
    <td align="center"><img alt="NumPy" src="assets/logos/numpy.svg" height="40" /><br><sub>NumPy</sub></td>
    <td align="center"><img alt="scikit-learn" src="assets/logos/scikit-learn.svg" height="40" /><br><sub>scikit‑learn</sub></td>
    <td align="center"><img alt="XGBoost" src="assets/logos/xgboost.svg" height="40" /><br><sub>XGBoost</sub></td>
    <td align="center"><img alt="Streamlit" src="assets/logos/streamlit.svg" height="40" /><br><sub>Streamlit</sub></td>
  </tr>
</table>

<p align="center"><sub>Más logos bajo demanda en <code>assets/logos/</code></sub></p>

## Sobre Xentris Tech
- Misión: impulsar resultados medibles con innovación en IA, ciencia de datos y automatización aplicada, elevando velocidad, calidad y seguridad de los procesos.
- Visión: liderar en LATAM soluciones inteligentes y confiables para trading algorítmico y automatización financiera end‑to‑end.
- Servicios:
  - Trading algorítmico y ejecución MT5 (brokers como Exness).
  - Automatización y orquestación con monitoreo 24/7 (bots, alertas, dashboards).
  - IA/LLM: copilotos locales (Ollama/DeepSeek) y nube (OpenAI/Claude).
  - Ciencia de datos y ML: modelos predictivos, backtesting y optimización (XGBoost/Sklearn).
  - Integraciones y APIs: TwelveData, Telegram, brokers y servicios cloud.
  - Dashboards y observabilidad: Streamlit, logging estructurado y métricas.
  - Cloud e infraestructura: AWS/GCP, despliegues y pipelines CI/CD.
- Compromiso: innovando y automatizando para maximizar resultados con seguridad y gobernanza.

## Contacto
- Web: https://xentris.tech/
 - Email: [info@xentris.tech](mailto:info@xentris.tech)
- WhatsApp/Telegram: +57 312 5827128
- WhatsApp Directo: https://wa.me/573125827128
Escríbenos para consultoría, implementación o soporte de trading algorítmico y automatización.

## Créditos
- Xentris Tech — Ingeniería y data science. https://xentris.tech/
- Comunidad OSS y proveedores: TwelveData, MetaTrader 5, Ollama/DeepSeek, OpenAI, Anthropic, Microsoft, Google, AWS.

## Notas

- El proyecto incluye múltiples .bat/.ps1 para facilitar uso en Windows; equivalentes Python están disponibles para ejecución cross‑platform.
- Existen varios README alternativos (README_V3.md, INFORME_FINAL.md, SISTEMA_COMPLETO.md). Este README es la guía principal y actualizada para v3.

---

🚀 Listo: configura `.env` y `settings.yaml`, verifica conexión y ejecuta con `python cli.py trade run --mode demo`.

## Changelog v3
- 2025-08-28: Documentación consolidada (Quickstart, Tecnologías, Créditos, Links) y README actualizado a arquitectura v3.
- 2025-08-28: Revisión de módulos principales (core/broker/data/signals/risk/ml/notifiers) y alineación con `configs/settings.yaml`.

Formato sugerido futuro:
```
YYYY-MM-DD: Breve descripción del cambio (archivo/s)
Commit: <hash> (opcional)
Autor: <nombre> (opcional)
```
