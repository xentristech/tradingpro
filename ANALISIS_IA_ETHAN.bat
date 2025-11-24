@echo off
cls
color 0A
echo ============================================================
echo    SISTEMA DE ANALISIS CON IA - TRADING PRO v3.0
echo ============================================================
echo.

REM Configurar nombre del operador
set OPERATOR_NAME=ETHAN

cd /d "C:\Users\user\OneDrive\Escritorio\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2"

echo Activando entorno virtual...
call .venv\Scripts\activate.bat

echo.
echo Iniciando analisis personalizado para %OPERATOR_NAME%...
echo.

python ANALISIS_MERCADO_IA_PERSONAL.py

pause
