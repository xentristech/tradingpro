@echo off
title ALGO TRADER V3 - SOLO SEÑALES (SIN TRADING)
color 0B

echo.
echo ========================================================================
echo                    ALGO TRADER V3 - MODO SEÑALES UNICAMENTE
echo ========================================================================
echo.
echo  ✅ Modo seguro: Solo genera señales y notificaciones
echo      NO ejecuta trades automaticamente en MT5
echo.
echo  🔧 Configuracion:
echo      • Auto-ejecucion: DESACTIVADA
echo      • Simbolos: XAUUSD, EURUSD, GBPUSD, BTCUSD
echo      • Notificaciones: Solo Telegram
echo      • Trading: Manual (tu decides cuando operar)
echo.
echo ========================================================================
echo.

echo ✅ Iniciando generador de señales (modo seguro)...
echo.

REM Cambiar al directorio del script
cd /d "%~dp0"

REM Ejecutar solo generador de señales (sin auto-ejecución)
python src/signals/advanced_signal_generator.py --symbols XAUUSD EURUSD GBPUSD BTCUSD

echo.
echo Sistema detenido
pause