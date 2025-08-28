@echo off
echo ================================================
echo   ENHANCED TRADING BOT V2 - LAUNCHER
echo   Sistema Avanzado con Deteccion de Cambios
echo ================================================
echo.

REM Activar entorno virtual
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
    echo [OK] Entorno virtual activado
) else (
    echo [WARN] Entorno virtual no encontrado
)

echo.
echo Seleccione modo de ejecucion:
echo 1. DEMO (Recomendado para pruebas)
echo 2. LIVE (CUIDADO: Operaciones reales)
echo.
set /p mode="Ingrese opcion (1 o 2): "

if "%mode%"=="2" (
    echo.
    echo ====================================
    echo   ADVERTENCIA: MODO LIVE ACTIVADO
    echo   Se ejecutaran operaciones REALES
    echo ====================================
    echo.
    set /p confirm="Esta seguro? (escriba SI para continuar): "
    if not "%confirm%"=="SI" (
        echo Operacion cancelada
        pause
        exit
    )
    
    REM Actualizar .env para modo live
    powershell -Command "(gc configs\.env) -replace 'LIVE_TRADING=false', 'LIVE_TRADING=true' | Out-File -encoding UTF8 configs\.env"
    echo [OK] Modo LIVE activado
) else (
    REM Asegurar modo demo
    powershell -Command "(gc configs\.env) -replace 'LIVE_TRADING=true', 'LIVE_TRADING=false' | Out-File -encoding UTF8 configs\.env"
    echo [OK] Modo DEMO activado
)

echo.
echo ================================================
echo Iniciando Enhanced Trading Bot V2...
echo ================================================
echo.
echo Caracteristicas nuevas:
echo - Deteccion de cambios criticos en tiempo real
echo - Analisis multi-temporal avanzado
echo - Gestion de riesgo adaptativa
echo - Sistema de alertas proactivas
echo.
echo Presione Ctrl+C para detener el bot
echo ================================================
echo.

python enhanced_trading_bot_v2.py

echo.
echo Bot detenido
pause
