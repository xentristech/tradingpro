@echo off
echo ========================================
echo    VERIFICANDO CONEXION EXNESS MT5
echo ========================================
echo.
echo Cuenta: 197678662
echo Server: Exness-MT5Trial11
echo.

cd /d "%~dp0"
.venv\Scripts\python.exe verificar_conexion_exness.py

echo.
pause
