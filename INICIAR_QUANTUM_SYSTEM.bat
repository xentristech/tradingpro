@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================================================
echo     QUANTUM TRADING SYSTEM - Sistema de Trading Cuántico
echo ========================================================================
echo.
echo Iniciando sistema basado en Quantum Action...
echo - TwelveData API para datos limpios
echo - Quantum Core (A=EMA(|ΔP|-ATR))
echo - Validación con Ollama AI
echo - Ejecución automática en MT5
echo.
echo ========================================================================
echo.

REM Verificar que Python existe
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ ERROR: Python no encontrado
    echo    Por favor instala Python 3.9 o superior
    pause
    exit /b 1
)

REM Verificar que .env existe
if not exist ".env" (
    echo ⚠️  WARNING: Archivo .env no encontrado
    echo    Creando desde .env.example...
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo ✅ Archivo .env creado
        echo    Por favor edítalo con tus credenciales:
        echo    - TWELVEDATA_API_KEY
        echo    - MT5_LOGIN, MT5_PASSWORD, MT5_SERVER
        echo    - TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID
        echo.
        pause
    ) else (
        echo ❌ ERROR: .env.example no encontrado
        pause
        exit /b 1
    )
)

REM Activar entorno virtual si existe
if exist ".venv\Scripts\activate.bat" (
    echo 🔧 Activando entorno virtual...
    call .venv\Scripts\activate.bat
) else (
    echo ⚠️  No se encontró entorno virtual
    echo    Usando Python global
)

REM Verificar dependencias
echo.
echo 🔍 Verificando dependencias...
python -c "import pandas, numpy, MetaTrader5" >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  Faltan dependencias
    echo    Instalando requirements...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ❌ ERROR instalando dependencias
        pause
        exit /b 1
    )
)

REM Verificar que Ollama está corriendo (opcional)
echo.
echo 🤖 Verificando Ollama AI...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Ollama detectado en localhost:11434
) else (
    echo ⚠️  Ollama no detectado
    echo    El sistema funcionará sin validación AI
    echo    Para habilitar AI, inicia Ollama:
    echo    ollama serve
    echo.
)

REM Crear directorio de logs si no existe
if not exist "logs" (
    mkdir logs
)

REM Ejecutar sistema
echo.
echo ========================================================================
echo     INICIANDO QUANTUM TRADING SYSTEM
echo ========================================================================
echo.

python QUANTUM_TRADING_SYSTEM.py

REM Verificar si hubo error
if %errorlevel% neq 0 (
    echo.
    echo ❌ El sistema terminó con errores
    echo    Revisa los logs en: logs\quantum_trading_system.log
    echo.
    pause
    exit /b %errorlevel%
)

echo.
echo ========================================================================
echo     Sistema detenido correctamente
echo ========================================================================
pause
