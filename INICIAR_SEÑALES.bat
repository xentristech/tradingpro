@echo off
cls
echo ============================================================
echo    INICIANDO SISTEMA DE SEÑALES - TRADING PRO v3.0
echo ============================================================
echo.
echo ADVERTENCIA: Este sistema ejecutará operaciones reales
echo.

cd /d "C:\Users\user\OneDrive\Escritorio\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2"

echo [1/3] Activando entorno virtual...
call .venv\Scripts\activate.bat

echo.
echo [2/3] Verificando conexión MT5...
python -c "import MetaTrader5 as mt5; print('MT5 conectado' if mt5.initialize() else 'MT5 no disponible'); mt5.shutdown()"

echo.
echo [3/3] Iniciando generador de señales avanzado...
echo.

python ADVANCED_SIGNAL_GENERATOR.py

pause
