@echo off
REM ===========================================
REM ALGO TRADER v3 - Instalador completo (Windows)
REM ===========================================
setlocal enabledelayedexpansion
chcp 65001 >nul 2>&1

echo.
echo ============================================
echo   INSTALANDO ALGO TRADER v3 - COMPLETO
echo ============================================
echo.

REM Ir al directorio del proyecto (donde está este .bat)
cd /d "%~dp0"

REM 1) Verificar Python
echo [1/10] Verificando Python 3.10+...
python --version >nul 2>&1
if %errorlevel% neq 0 (
  echo ❌ Python no encontrado. Instala Python 3.10+ desde https://python.org
  pause
  exit /b 1
)
for /f "tokens=2 delims= " %%v in ('python --version') do set PYVER=%%v
echo ✅ Python %PYVER%

REM 2) Crear venv
echo [2/10] Configurando entorno virtual...
if not exist ".venv" (
  echo Creando entorno virtual .venv...
  python -m venv .venv
) else (
  echo .venv ya existe
)

REM 3) Activar venv
echo [3/10] Activando entorno virtual...
call .venv\Scripts\activate.bat
if %errorlevel% neq 0 (
  echo ❌ No se pudo activar el entorno virtual
  pause
  exit /b 1
)

REM 4) Actualizar herramientas base
echo [4/10] Actualizando pip/setuptools/wheel...
python -m pip install --upgrade pip setuptools wheel

REM 5) Númerico base
echo [5/10] Instalando núcleo numérico...
pip install numpy
pip install pandas
pip install scipy

REM 6) Ciencia de datos / técnicas
echo [6/10] Instalando librerías científicas...
pip install statsmodels scikit-learn xgboost joblib

REM 7) TA-Lib (opcional, requiere wheel precompilado)
echo [7/10] TA-Lib (opcional).
echo - Si tienes el wheel, colócalo en .\wheels y lo instalamos.
set TALIB_WHL=
for %%f in ("wheels\TA_Lib*.whl") do set TALIB_WHL=%%f
if not "%TALIB_WHL%"=="" (
  echo Instalando %%~nxf...
  pip install "%TALIB_WHL%"
) else (
  echo ⚠️  No se encontró wheels\TA_Lib*.whl
  echo     Descarga desde: https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
  echo     Ejemplo: TA_Lib‑0.4.24‑cp310‑cp310‑win_amd64.whl
)

REM 8) Dependencias del bot, bróker y web
echo [8/10] Instalando dependencias del bot...
pip install MetaTrader5
pip install python-dotenv PyYAML pytz requests aiohttp websocket-client
pip install openai
pip install streamlit
pip install plotly matplotlib seaborn
pip install psutil watchdog colorlog tqdm schedule
pip install ta
pip install backtrader vectorbt

REM 9) TwelveData SDK (opcional)
echo [9/10] Instalando SDK opcional de TwelveData...
pip install twelvedata

REM 10) Estructura de carpetas
echo [10/10] Creando estructura de carpetas...
if not exist "logs" mkdir logs
if not exist "storage" mkdir storage
if not exist "storage\models" mkdir storage\models
if not exist "storage\backtest" mkdir storage\backtest
if not exist "data" mkdir data
if not exist "data\cache" mkdir data\cache
if not exist "wheels" mkdir wheels

REM Verificación rápida de imports clave
echo.
echo Verificando imports clave...
python - <<PY
try:
    import numpy, pandas, scipy, statsmodels, sklearn
    import MetaTrader5, yaml, pytz, requests
    print('✅ Imports OK')
except Exception as e:
    print('⚠️  Advertencia en imports:', e)
PY

echo.
echo ============================================
echo   ✅ INSTALACIÓN COMPLETADA
echo ============================================
echo.
echo Próximos pasos:
echo 1) Edita configs\.env (TWELVEDATA_API_KEY, MT5_*, TELEGRAM_*)
echo 2) Revisa configs\settings.yaml (umbrales/horarios)
echo 3) Verifica:  python main_trader.py --check --config configs\.env
echo 4) Demo:      python main_trader.py --mode demo --config configs\.env
echo.
pause
