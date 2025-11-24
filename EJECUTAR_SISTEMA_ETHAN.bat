@echo off
cls
color 0B
title SISTEMA DE TRADING CON IA - ETHAN

echo ============================================================
echo.
echo     _____ _____ _   _    _    _   _ 
echo    ^| ____^|_   _^| ^| ^| ^|  / \  ^| \ ^| ^|
echo    ^|  _^|   ^| ^| ^| ^|_^| ^| / _ \ ^|  \^| ^|
echo    ^| ^|___  ^| ^| ^|  _  ^|/ ___ \^| ^|\  ^|
echo    ^|_____^| ^|_^| ^|_^| ^|_/_/   \_\_^| \_^|
echo.
echo    SISTEMA DE TRADING ELITE CON IA v3.0
echo ============================================================
echo.

REM Configurar el nombre del operador
set OPERATOR_NAME=ETHAN

echo    Bienvenido %OPERATOR_NAME% - Elite Trader
echo.
echo ============================================================
echo.

cd /d "C:\Users\user\OneDrive\Escritorio\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2"

echo [1/3] Activando entorno virtual...
call .venv\Scripts\activate.bat

echo.
echo [2/3] Verificando componentes del sistema...
python -c "import MetaTrader5; print('   [OK] MetaTrader5')" 2>nul || echo    [!] MetaTrader5 no disponible
python -c "import pandas; print('   [OK] Pandas')" 2>nul || echo    [!] Pandas no disponible
python -c "import numpy; print('   [OK] NumPy')" 2>nul || echo    [!] NumPy no disponible

echo.
echo [3/3] Iniciando Sistema Integrado con IA...
echo.
echo ============================================================
echo.

python SISTEMA_INTEGRADO_IA_ETHAN.py

echo.
echo ============================================================
echo    Sistema detenido
echo ============================================================
echo.

pause
