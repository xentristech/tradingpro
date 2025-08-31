@echo off
title VERIFICACION COMPLETA - Algo Trader V3
color 0E

cls
echo ================================================================
echo                 VERIFICACION COMPLETA DEL SISTEMA
echo                         ALGO TRADER V3
echo ================================================================
echo.
echo Este proceso verificara que todo este funcionando correctamente
echo.
echo ================================================================
echo.

:: Verificación rápida primero
echo [PASO 1/3] Ejecutando verificacion rapida...
echo ------------------------------------------------
python QUICK_CHECK.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ⚠️ La verificacion rapida detecto problemas
    echo.
) else (
    echo.
    echo ✅ Verificacion rapida completada
    echo.
)

echo.
echo ================================================================
echo.

:: Preguntar si quiere diagnóstico completo
set /p diag="Deseas ejecutar el diagnostico completo? (S/N): "
if /i "%diag%"=="S" (
    echo.
    echo [PASO 2/3] Ejecutando diagnostico completo...
    echo ------------------------------------------------
    python DIAGNOSTICO_COMPLETO.py
    echo.
    echo ✅ Diagnostico completo finalizado
    echo.
)

echo.
echo ================================================================
echo.

:: Preguntar si quiere aplicar correcciones
echo ACCIONES DISPONIBLES:
echo.
echo 1. Actualizar seguridad (corrige API key expuesta)
echo 2. Aplicar mejoras del sistema
echo 3. Iniciar monitor en tiempo real
echo 4. Iniciar sistema de trading
echo 5. Ver informe de estado
echo 6. Salir
echo.

:menu
set /p opcion="Selecciona una opcion (1-6): "

if "%opcion%"=="1" (
    echo.
    echo Ejecutando actualizacion de seguridad...
    call ACTUALIZAR_SEGURIDAD_URGENTE.bat
    goto :menu
)

if "%opcion%"=="2" (
    echo.
    echo Aplicando mejoras del sistema...
    call EJECUTAR_MEJORAS.bat
    goto :menu
)

if "%opcion%"=="3" (
    echo.
    echo Iniciando monitor...
    start MONITOR.bat
    goto :menu
)

if "%opcion%"=="4" (
    echo.
    echo Iniciando sistema de trading...
    call EJECUTAR_TODO_PRO.bat
    goto :menu
)

if "%opcion%"=="5" (
    echo.
    echo Abriendo informe de estado...
    start notepad INFORME_ESTADO_SISTEMA.md
    goto :menu
)

if "%opcion%"=="6" (
    echo.
    echo Saliendo...
    goto :end
)

echo Opcion no valida
goto :menu

:end
echo.
echo ================================================================
echo.
echo Verificacion completada.
echo.
echo Archivos de diagnostico disponibles:
echo - INFORME_ESTADO_SISTEMA.md (resumen completo)
echo - DIAGNOSTICO_RESULTADO.json (detalles tecnicos)
echo.
echo ================================================================
echo.
pause
