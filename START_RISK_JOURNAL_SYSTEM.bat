@echo off
echo ====================================================================
echo    ALGO TRADER V3 - SISTEMA COMPLETO CON JOURNAL Y GESTION DE RIESGO
echo ====================================================================
echo.

REM Verificar si Python está disponible
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python no encontrado. Instala Python 3.9+
    pause
    exit /b
)

echo Verificando dependencias...
echo.

REM Instalar dependencias del journal si es necesario
pip install -r requirements_journal.txt --quiet 2>nul

echo Iniciando sistema completo...
echo.
echo FUNCIONES ACTIVAS:
echo - Journal de trading inteligente
echo - Monitor de riesgo en tiempo real  
echo - Alertas Telegram + sonido local
echo - Exportacion a Google Sheets
echo - Dashboard interactivo
echo - Metricas avanzadas (Sharpe, Sortino, etc)
echo.
echo Presiona Ctrl+C para detener en cualquier momento
echo ====================================================================
echo.

REM Iniciar el sistema principal
python START_WITH_RISK_JOURNAL.py

echo.
echo ====================================================================
echo Sistema detenido. Presiona cualquier tecla para cerrar.
pause >nul