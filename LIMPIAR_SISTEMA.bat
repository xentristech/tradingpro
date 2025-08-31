@echo off
title Limpieza y Optimizacion - Algo Trader V3
color 0B

cls
echo ========================================
echo   LIMPIEZA Y OPTIMIZACION DEL SISTEMA
echo ========================================
echo.
echo Este proceso:
echo - Limpiara logs antiguos y vacios
echo - Optimizara la base de datos
echo - Limpiara archivos de cache
echo - Creara configuraciones optimizadas
echo.
echo ========================================
echo.

set /p confirm="Deseas continuar? (S/N): "
if /i "%confirm%" neq "S" goto :end

echo.
echo Ejecutando limpieza y optimizacion...
echo.

python CLEAN_AND_OPTIMIZE.py

echo.
echo ========================================
echo.
echo Proceso completado!
echo.

:end
pause
