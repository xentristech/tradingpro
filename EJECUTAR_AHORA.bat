@echo off
cls
color 0A
title EJECUTAR BOT AHORA

echo ================================================================================
echo                    EJECUTAR ALGO TRADER BOT - DIRECTO
echo ================================================================================
echo.

cd /d "C:\Users\user\Desktop\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2"

echo VERIFICANDO...
echo.

REM Verificar si existe el entorno virtual
if not exist ".venv\Scripts\python.exe" (
    echo ERROR: No existe el entorno virtual
    echo.
    echo Creando entorno virtual...
    python -m venv .venv
    echo Instalando dependencias...
    .venv\Scripts\pip.exe install -r requirements.txt
)

REM Ejecutar verificación primero
echo --------------------------------------------------------------------------------
echo PASO 1: VERIFICACION DEL SISTEMA
echo --------------------------------------------------------------------------------
.venv\Scripts\python.exe VERIFICAR_TODO.py

echo.
echo --------------------------------------------------------------------------------
echo PASO 2: EJECUTAR BOT
echo --------------------------------------------------------------------------------
echo.
echo Presiona cualquier tecla para ejecutar el bot...
pause >nul

.venv\Scripts\python.exe FINAL_BOT.py

pause
