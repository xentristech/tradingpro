@echo off
cls
color 0E
title REPARAR PYTHON

echo ================================================================================
echo                    REPARANDO ENTORNO PYTHON
echo ================================================================================
echo.
echo Detectado: El entorno virtual esta configurado para otro usuario
echo Solucion: Recrear el entorno virtual
echo.
echo --------------------------------------------------------------------------------
pause

cd /d "C:\Users\user\Desktop\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2"

echo.
echo [1/4] Eliminando entorno virtual anterior...
if exist ".venv" (
    rmdir /s /q .venv
    echo [OK] Entorno anterior eliminado
) else (
    echo [OK] No habia entorno anterior
)

echo.
echo [2/4] Creando nuevo entorno virtual...
python -m venv .venv
if %errorlevel% neq 0 (
    echo.
    echo ERROR: No se pudo crear el entorno virtual
    echo.
    echo Intentando con python3...
    python3 -m venv .venv
    if %errorlevel% neq 0 (
        echo.
        echo ERROR: Python no esta instalado correctamente
        echo.
        echo Por favor instala Python desde: https://python.org/downloads/
        pause
        exit
    )
)
echo [OK] Entorno virtual creado

echo.
echo [3/4] Instalando dependencias...
echo      Esto puede tardar varios minutos...
echo.

.venv\Scripts\pip.exe install --upgrade pip >nul 2>&1
echo      pip actualizado...

.venv\Scripts\pip.exe install MetaTrader5 >nul 2>&1
echo      MetaTrader5 instalado...

.venv\Scripts\pip.exe install pandas numpy >nul 2>&1
echo      pandas y numpy instalados...

.venv\Scripts\pip.exe install python-dotenv requests >nul 2>&1
echo      dotenv y requests instalados...

.venv\Scripts\pip.exe install openai pyyaml >nul 2>&1
echo      openai y yaml instalados...

.venv\Scripts\pip.exe install pytz >nul 2>&1
echo      pytz instalado...

echo.
echo [4/4] Verificando instalacion...
.venv\Scripts\python.exe --version
if %errorlevel% equ 0 (
    echo [OK] Python funciona correctamente
) else (
    echo [ERROR] Algo salio mal
)

echo.
echo ================================================================================
echo                    ENTORNO REPARADO
echo ================================================================================
echo.
echo Ahora puedes ejecutar el bot con: GO.bat
echo.
pause
