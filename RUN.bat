@echo off
cls
color 0A
title ALGO TRADER BOT - EJECUTANDO

echo ================================================================================
echo                        ALGO TRADER BOT v3.0
echo                         INICIANDO SISTEMA
echo ================================================================================
echo.
echo Configuracion actual:
echo   - Cuenta MT5: 197678662
echo   - Servidor: Exness-MT5Trial11
echo   - Simbolo: BTCUSDm
echo   - Modo: DEMO (Seguro)
echo   - IA: DeepSeek-R1 (si Ollama esta activo)
echo.
echo --------------------------------------------------------------------------------
echo.
echo [1/3] Verificando entorno...

cd /d "C:\Users\user\Desktop\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2"

REM Verificar Python
if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Entorno virtual no encontrado
    pause
    exit
)
echo [OK] Python encontrado

REM Verificar archivo .env
if not exist "configs\.env" (
    echo ERROR: Archivo de configuracion no encontrado
    pause
    exit
)
echo [OK] Configuracion encontrada

echo.
echo [2/3] Iniciando MetaTrader 5...

REM Verificar si MT5 esta corriendo
tasklist /FI "IMAGENAME eq terminal64.exe" 2>NUL | find /I /N "terminal64.exe" >NUL
if "%ERRORLEVEL%"=="0" (
    echo [OK] MetaTrader 5 ya esta ejecutandose
) else (
    echo Abriendo MetaTrader 5...
    if exist "C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe" (
        start "" "C:\Program Files\MetaTrader 5 EXNESS\terminal64.exe"
        echo Esperando 10 segundos para que MT5 se conecte...
        timeout /t 10 >nul
    ) else (
        echo ADVERTENCIA: MT5 no encontrado, abrelo manualmente
    )
)

echo.
echo [3/3] Ejecutando bot de trading...
echo.
echo ================================================================================
echo                         BOT EJECUTANDOSE
echo ================================================================================
echo.
echo El bot ahora:
echo   - Analiza el mercado cada 20-30 segundos
echo   - Usa IA para evaluar senales (si Ollama esta activo)
echo   - Ejecuta trades automaticamente
echo   - Aplica gestion de riesgo
echo.
echo Presiona Ctrl+C para detener
echo --------------------------------------------------------------------------------
echo.

REM Ejecutar el bot principal
.venv\Scripts\python.exe FINAL_BOT.py

echo.
echo ================================================================================
echo                         BOT DETENIDO
echo ================================================================================
echo.
pause
