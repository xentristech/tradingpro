@echo off
cls
color 0A
cd /d "%~dp0"

echo.
echo ============================================
echo      ALGO TRADER v3.0 - EXNESS DEMO
echo ============================================
echo.
echo Cuenta: 197678662
echo Servidor: Exness-MT5Trial11
echo Simbolo: BTCUSDm
echo Modo: DEMO (Seguro)
echo.
echo ============================================
echo.
echo Iniciando bot de trading...
echo.

if exist ".venv\Scripts\python.exe" (
    echo Usando entorno virtual...
    .venv\Scripts\python.exe run_simple.py
) else (
    echo Usando Python global...
    python run_simple.py
)

echo.
echo ============================================
echo Bot detenido
echo ============================================
echo.
pause
