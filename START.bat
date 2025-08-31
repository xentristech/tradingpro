@echo off
cls
title ALGO TRADER V3 - INICIO RAPIDO
color 0E

echo.
echo     ___    __    __________     ________  ____  ___    ____  __________  
echo    /   \  /  /  / _______ /    /_  __  / / __ \/   \  / __ \/ _______ /
echo   / /\ / /  /  / / ____  /      / / / / / /_/ / /\ / / / / / / ____
echo  / ____ /  /__/ / /__/ /       / / / / /  _  / ____ / /_/ / / /____ /
echo /_/  /_/______/________/       /_/ /_/ /_/ /_/_/  /_/_____/________/
echo.
echo                           V3.0 PROFESSIONAL
echo                    TELEGRAM + IA + SEÑALES ACTIVAS
echo.
echo ================================================================
echo.

timeout /t 2 >nul

echo [%TIME%] INICIANDO SISTEMA COMPLETO...
echo.

REM Verificar Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    py execute_all_pro.py --auto
) else (
    python execute_all_pro.py --auto
)

exit