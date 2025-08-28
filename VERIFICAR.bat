@echo off
cls
color 0E
title VERIFICACION COMPLETA DEL SISTEMA

echo ================================================================================
echo                    VERIFICACION COMPLETA DEL SISTEMA MT5
echo ================================================================================
echo.
echo Este script verificara:
echo   - Que MT5 este instalado
echo   - Que las credenciales sean correctas
echo   - Que pueda conectarse a la cuenta
echo   - Que el simbolo este disponible
echo.
echo --------------------------------------------------------------------------------
echo.
pause

cd /d "C:\Users\user\Desktop\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2"

echo.
echo Ejecutando verificacion completa...
echo.

.venv\Scripts\python.exe VERIFICAR_TODO.py

echo.
echo ================================================================================
echo                         VERIFICACION FINALIZADA
echo ================================================================================
echo.
pause
