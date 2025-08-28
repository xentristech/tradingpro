@echo off
cls
color 0B
title SOLUCION RAPIDA - BOT

echo ================================================================================
echo                    SOLUCION RAPIDA AL PROBLEMA DE PYTHON
echo ================================================================================
echo.
echo El entorno virtual esta configurado para otro usuario (Xentris)
echo Vamos a recrearlo para tu usuario (user)
echo.
echo --------------------------------------------------------------------------------
echo.

cd /d "C:\Users\user\Desktop\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2"

echo Paso 1: Eliminando entorno virtual mal configurado...
rmdir /s /q .venv 2>nul
echo [OK] Limpieza completada
echo.

echo Paso 2: Creando nuevo entorno virtual...
python -m venv .venv 2>nul
if not exist ".venv\Scripts\python.exe" (
    python3 -m venv .venv 2>nul
)
if not exist ".venv\Scripts\python.exe" (
    py -m venv .venv 2>nul
)

if not exist ".venv\Scripts\python.exe" (
    echo.
    echo ERROR: No se pudo crear el entorno virtual
    echo.
    echo Ejecuta manualmente:
    echo   1. python -m venv .venv
    echo   2. .venv\Scripts\pip install MetaTrader5 python-dotenv pandas numpy requests
    echo   3. .venv\Scripts\python FINAL_BOT.py
    pause
    exit
)

echo [OK] Entorno creado
echo.

echo Paso 3: Instalando librerias esenciales...
echo        (Esto tardara 1-2 minutos)
echo.

.venv\Scripts\python.exe -m pip install --upgrade pip >nul 2>&1
echo   - pip actualizado

.venv\Scripts\pip.exe install MetaTrader5 >nul 2>&1
echo   - MetaTrader5 instalado

.venv\Scripts\pip.exe install python-dotenv >nul 2>&1
echo   - dotenv instalado

.venv\Scripts\pip.exe install pandas numpy >nul 2>&1
echo   - pandas y numpy instalados

.venv\Scripts\pip.exe install requests >nul 2>&1
echo   - requests instalado

.venv\Scripts\pip.exe install openai >nul 2>&1
echo   - openai instalado

.venv\Scripts\pip.exe install pyyaml pytz >nul 2>&1
echo   - yaml y pytz instalados

echo.
echo [OK] Todas las librerias instaladas
echo.
echo ================================================================================
echo                    EJECUTANDO BOT AHORA
echo ================================================================================
echo.

.venv\Scripts\python.exe FINAL_BOT.py

pause
