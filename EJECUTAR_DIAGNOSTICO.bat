@echo off
title Diagnostico Completo - Algo Trader V3
color 0E

echo ========================================
echo   DIAGNOSTICO COMPLETO DEL SISTEMA
echo        ALGO TRADER V3
echo ========================================
echo.
echo Este proceso verificara:
echo.
echo  1. Variables de entorno (.env)
echo  2. Paquetes Python instalados
echo  3. Conexion con MetaTrader 5
echo  4. API de TwelveData
echo  5. Bot de Telegram
echo  6. Base de datos
echo  7. Procesos activos
echo  8. Puertos del sistema
echo  9. Archivos de logs
echo 10. Archivos criticos del sistema
echo.
echo ========================================
echo.

set /p confirm="Deseas ejecutar el diagnostico completo? (S/N): "
if /i "%confirm%" neq "S" goto :end

echo.
echo Instalando dependencias necesarias...
pip install colorama psutil --quiet

echo.
echo Ejecutando diagnostico...
echo.

python DIAGNOSTICO_COMPLETO.py

echo.
echo ========================================
echo.

if exist DIAGNOSTICO_RESULTADO.json (
    echo Diagnostico completado!
    echo.
    echo Revisa el archivo DIAGNOSTICO_RESULTADO.json para mas detalles
    echo.
) else (
    echo Error durante el diagnostico
)

:end
echo.
pause
