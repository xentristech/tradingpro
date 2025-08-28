# ✅ Checklist de Puesta en Marcha (v3)

Tiempo estimado: 10–20 minutos

1) Requisitos
- Windows 10/11 64-bit, conexión estable a Internet
- Python 3.10+ (64-bit) con “Add to PATH” marcado
- MetaTrader 5 instalado (cuenta demo activa)
- TwelveData API key (gratuita)
- Opcional: Telegram bot (token y chat_id)
- Opcional: Ollama instalado y modelo `deepseek-r1:14b`

2) Configuración
- Copia `configs/.env.example` a `configs/.env`
- Completa: `TWELVEDATA_API_KEY`, `MT5_LOGIN`, `MT5_PASSWORD`, `MT5_SERVER`
- Opcional: `TELEGRAM_TOKEN`, `TELEGRAM_CHAT_ID`, `OLLAMA_API_BASE`, `OLLAMA_MODEL`
- Copia `configs/settings.yaml.example` a `configs/settings.yaml` y ajusta parámetros

3) Instalación
```
python -m venv .venv
.\.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

4) Verificación
```
python test_mt5_connection.py     # Verifica conexión a MT5
python test_telegram.py           # Verifica Telegram (opcional)
python cli.py trade check --config configs/.env
```

5) Ejecución en DEMO
```
python cli.py trade run --mode demo --config configs/.env
```
- Abrir dashboard (opcional): `streamlit run streamlit_app.py`

6) Monitoreo
- Revisar `logs/` (errores y actividad)
- Confirmar notificaciones en Telegram si está configurado

7) Activar LIVE (cuando todo pase OK)
- Cambiar `LIVE_TRADING=true` en `configs/.env` únicamente si:
  - Todas las pruebas pasaron en demo y el comportamiento es estable (1–2 días)
  - Límites de riesgo revisados (`MAX_RISK_PER_TRADE`, `MAX_DAILY_LOSS`, `MAX_POSITIONS`)
  - Credenciales y servidor MT5 verificados

8) Recuperación ante errores
- Detener con Ctrl+C o script `.bat` correspondiente
- Consultar `diagnostic_and_fix.py` / `full_diagnosis.py`
- Ver `health_check.py` y `logs/` para causas raíz

9) Seguridad y backups
- Realizar backup de `configs/.env` y `configs/settings.yaml`
- Nunca subir `.env` al repositorio

10) Soporte
- Xentris Tech — contacto interno para escalado y soporte

