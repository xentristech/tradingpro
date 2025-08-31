@echo off
echo ========================================
echo   SISTEMA DE MEJORAS - ALGO TRADER V3
echo ========================================
echo.

echo Este script implementara las siguientes mejoras:
echo.
echo 1. Limpieza y organizacion de archivos
echo 2. Configuracion de seguridad mejorada
echo 3. Sistema de logging avanzado
echo 4. Gestion de procesos optimizada
echo 5. Sistema de respaldo automatico
echo 6. Validacion de dependencias
echo 7. Optimizacion de base de datos
echo 8. Sistema de monitoreo
echo.
echo ADVERTENCIA: Este proceso reorganizara tu proyecto.
echo Se recomienda hacer un backup manual antes de continuar.
echo.

set /p confirm="Deseas continuar? (S/N): "
if /i "%confirm%" neq "S" goto :end

echo.
echo [1/3] Creando backup de seguridad...
python -c "import shutil, datetime; shutil.make_archive(f'backup_{datetime.datetime.now().strftime('%%Y%%m%%d_%%H%%M%%S')}', 'zip', '.')"

echo.
echo [2/3] Ejecutando mejoras del sistema...
python SYSTEM_IMPROVEMENT.py

echo.
echo [3/3] Verificando resultados...
if exist IMPROVEMENT_REPORT.json (
    echo.
    echo ✅ Mejoras completadas exitosamente!
    echo.
    echo Revisa IMPROVEMENT_REPORT.json para ver los detalles.
    echo.
    type IMPROVEMENT_REPORT.json
) else (
    echo.
    echo ❌ Error durante las mejoras. Revisa los logs.
)

:end
echo.
pause
