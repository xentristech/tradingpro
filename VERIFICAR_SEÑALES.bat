@echo off
cls
echo ============================================================
echo    VERIFICADOR DE SEÑALES - TRADING PRO v3.0
echo ============================================================
echo.

cd /d "C:\Users\user\OneDrive\Escritorio\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2"

echo Activando entorno virtual...
call .venv\Scripts\activate.bat

echo.
echo Ejecutando verificador de señales...
echo.

python verificar_estado_senales.py

pause
