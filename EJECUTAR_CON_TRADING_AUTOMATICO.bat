@echo off
title ALGO TRADER V3 - SISTEMA CON TRADING AUTOMATICO
color 0A

echo.
echo ========================================================================
echo                    ALGO TRADER V3 - TRADING AUTOMATICO
echo ========================================================================
echo.
echo  ⚠️  ATENCION: Este modo ejecutara trades reales en MetaTrader 5
echo      Las senales generadas se ejecutaran automaticamente
echo.
echo  🔧 Configuracion:
echo      • Auto-ejecucion: ACTIVADA
echo      • Simbolos: XAUUSD, EURUSD, GBPUSD, BTCUSD
echo      • Notificaciones: Telegram activas
echo      • Gestion de riesgo: 2%% por trade
echo.
echo ========================================================================
echo.

set /p confirm="¿Estas seguro de activar el trading automatico? (yes/no): "
if /i not "%confirm%"=="yes" (
    echo.
    echo Operacion cancelada por seguridad
    pause
    exit /b
)

echo.
echo ✅ Iniciando sistema con trading automatico...
echo.

REM Cambiar al directorio del script
cd /d "%~dp0"

REM Ejecutar el generador con auto-ejecución
python src/signals/advanced_signal_generator.py --auto-execute --symbols XAUUSD EURUSD GBPUSD BTCUSD

echo.
echo Sistema detenido
pause