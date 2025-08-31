@echo off
cls
echo ========================================================
echo          REORGANIZACION AUTOMATICA DEL PROYECTO
echo                    ALGO TRADER V3
echo ========================================================
echo.
echo Este script reorganizara completamente tu proyecto:
echo - Creara una estructura profesional en /src
echo - Movera archivos a sus ubicaciones correctas
echo - Eliminara duplicados
echo - Creara backups de seguridad
echo - Generara documentacion actualizada
echo.
echo ========================================================
echo.

REM Verificar Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no esta instalado o no esta en el PATH
    echo Por favor instala Python 3.10+ desde python.org
    pause
    exit /b 1
)

echo [OK] Python detectado
echo.

REM Ejecutar el script de reorganizacion
echo Iniciando reorganizacion...
echo.
python REORGANIZE_PROJECT.py

echo.
echo ========================================================
echo.
echo Proceso completado. Revisa REORGANIZATION_REPORT.txt
echo.
pause