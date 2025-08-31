@echo off
title ALGO TRADER V3 - SISTEMA COMPLETO
color 0A
cls

echo ================================================================
echo                    ALGO TRADER V3
echo              SISTEMA DE TRADING ALGORITMICO
echo                     by XentrisTech
echo ================================================================
echo.
echo Iniciando sistema completo...
echo.

REM Intentar con python primero
python execute_all.py 2>nul
if %errorlevel% equ 0 goto END

REM Si falla, intentar con py
py execute_all.py 2>nul
if %errorlevel% equ 0 goto END

REM Si ambos fallan, mostrar error
echo ================================================================
echo                         ERROR
echo ================================================================
echo.
echo Python no esta instalado o no esta en el PATH
echo.
echo Por favor:
echo 1. Instala Python 3.10+ desde https://python.org
echo 2. Durante la instalacion, marca "Add Python to PATH"
echo 3. Reinicia este ejecutor
echo.
echo ================================================================
pause
exit /b 1

:END
exit