@echo off
cls
color 0A
title EJECUTAR BOT - CORREGIDO

echo ================================================================================
echo                    ALGO TRADER BOT - VERSION CORREGIDA
echo ================================================================================
echo.

cd /d "C:\Users\user\Desktop\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2"

echo [1/3] Buscando Python en el sistema...
echo.

set PYTHON_FOUND=0

REM Buscar Python en diferentes ubicaciones
if exist "C:\Users\user\AppData\Local\Programs\Python\Python313\python.exe" (
    set PYTHON_PATH=C:\Users\user\AppData\Local\Programs\Python\Python313\python.exe
    set PYTHON_FOUND=1
    echo [OK] Python encontrado en: Usuario local
) else if exist "C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe" (
    set PYTHON_PATH=C:\Users\user\AppData\Local\Programs\Python\Python312\python.exe
    set PYTHON_FOUND=1
    echo [OK] Python encontrado en: Python 3.12
) else if exist "C:\Users\user\AppData\Local\Programs\Python\Python311\python.exe" (
    set PYTHON_PATH=C:\Users\user\AppData\Local\Programs\Python\Python311\python.exe
    set PYTHON_FOUND=1
    echo [OK] Python encontrado en: Python 3.11
) else if exist "C:\Users\user\AppData\Local\Programs\Python\Python310\python.exe" (
    set PYTHON_PATH=C:\Users\user\AppData\Local\Programs\Python\Python310\python.exe
    set PYTHON_FOUND=1
    echo [OK] Python encontrado en: Python 3.10
) else if exist "C:\Python313\python.exe" (
    set PYTHON_PATH=C:\Python313\python.exe
    set PYTHON_FOUND=1
    echo [OK] Python encontrado en: C:\Python313
) else if exist "C:\Python312\python.exe" (
    set PYTHON_PATH=C:\Python312\python.exe
    set PYTHON_FOUND=1
    echo [OK] Python encontrado en: C:\Python312
) else if exist "C:\Python311\python.exe" (
    set PYTHON_PATH=C:\Python311\python.exe
    set PYTHON_FOUND=1
    echo [OK] Python encontrado en: C:\Python311
) else if exist "C:\Python310\python.exe" (
    set PYTHON_PATH=C:\Python310\python.exe
    set PYTHON_FOUND=1
    echo [OK] Python encontrado en: C:\Python310
)

if %PYTHON_FOUND%==0 (
    REM Intentar con python del PATH
    where python >nul 2>&1
    if %errorlevel% equ 0 (
        set PYTHON_PATH=python
        set PYTHON_FOUND=1
        echo [OK] Python encontrado en el PATH
    )
)

if %PYTHON_FOUND%==0 (
    echo.
    echo ================================================================================
    echo                         ERROR: PYTHON NO ENCONTRADO
    echo ================================================================================
    echo.
    echo No se pudo encontrar Python en tu sistema.
    echo.
    echo SOLUCION:
    echo   1. Descarga Python desde: https://python.org/downloads/
    echo   2. Durante la instalacion, marca "Add Python to PATH"
    echo   3. Reinicia esta ventana
    echo   4. Ejecuta este script nuevamente
    echo.
    pause
    exit
)

echo.
echo [2/3] Verificando entorno virtual...

if not exist ".venv\Scripts\python.exe" (
    echo Creando entorno virtual...
    %PYTHON_PATH% -m venv .venv
    echo Instalando dependencias basicas...
    .venv\Scripts\pip.exe install --upgrade pip >nul 2>&1
    .venv\Scripts\pip.exe install MetaTrader5 python-dotenv pandas numpy requests openai pyyaml pytz >nul 2>&1
    echo [OK] Entorno virtual creado
) else (
    echo [OK] Entorno virtual existe
)

echo.
echo [3/3] Ejecutando bot...
echo.
echo ================================================================================
echo                         BOT INICIANDO
echo ================================================================================
echo.

REM Ejecutar con el Python del entorno virtual
.venv\Scripts\python.exe FINAL_BOT.py

if %errorlevel% neq 0 (
    echo.
    echo ================================================================================
    echo                    ERROR AL EJECUTAR EL BOT
    echo ================================================================================
    echo.
    echo Posibles causas:
    echo   - Faltan librerias
    echo   - Error en el codigo
    echo   - MT5 no esta conectado
    echo.
    echo Intentando instalar librerias faltantes...
    .venv\Scripts\pip.exe install -r requirements.txt
    echo.
    echo Intenta ejecutar nuevamente
)

echo.
pause
