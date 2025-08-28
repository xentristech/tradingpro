@echo off
cd /d "%~dp0"
echo.
echo ========================================
echo     TEST DE CONEXION MT5 - EXNESS
echo ========================================
echo.

if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe test_mt5_exness.py
) else (
    python test_mt5_exness.py
)

pause
