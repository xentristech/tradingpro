@echo off
cls
color 0A
echo ================================================================
echo                    ORGANIZADOR MAESTRO
echo                     ALGO TRADER V3
echo           Sistema Completo de Reorganizacion
echo ================================================================
echo.
echo Este proceso ejecutara TODA la reorganizacion del proyecto:
echo.
echo [1] LIMPIEZA - Eliminar archivos obsoletos y duplicados
echo [2] REORGANIZACION - Estructurar carpetas profesionalmente  
echo [3] INSTALACION - Verificar e instalar dependencias
echo [4] LANZAMIENTO - Iniciar el sistema
echo.
echo ================================================================
echo.

:MENU
echo Selecciona una opcion:
echo.
echo 1. Ejecutar TODO el proceso (recomendado)
echo 2. Solo Limpiar archivos obsoletos
echo 3. Solo Reorganizar estructura
echo 4. Solo Instalar dependencias
echo 5. Iniciar el sistema
echo 6. Salir
echo.

set /p opcion="Ingresa tu opcion (1-6): "

if "%opcion%"=="1" goto TODO
if "%opcion%"=="2" goto LIMPIAR
if "%opcion%"=="3" goto REORGANIZAR
if "%opcion%"=="4" goto INSTALAR
if "%opcion%"=="5" goto INICIAR
if "%opcion%"=="6" goto SALIR

echo Opcion invalida. Por favor selecciona 1-6
goto MENU

:TODO
echo.
echo ================================================================
echo           PASO 1/3: LIMPIANDO ARCHIVOS OBSOLETOS
echo ================================================================
python CLEAN_AND_OPTIMIZE.py
if %errorlevel% neq 0 goto ERROR

echo.
echo ================================================================
echo          PASO 2/3: REORGANIZANDO ESTRUCTURA
echo ================================================================
python REORGANIZE_PROJECT.py
if %errorlevel% neq 0 goto ERROR

echo.
echo ================================================================
echo          PASO 3/3: INSTALANDO DEPENDENCIAS
echo ================================================================
python INSTALL.py
if %errorlevel% neq 0 goto ERROR

echo.
echo ================================================================
echo              PROCESO COMPLETADO EXITOSAMENTE
echo ================================================================
echo.
echo El proyecto ha sido completamente reorganizado.
echo.
echo Que deseas hacer ahora?
echo 1. Iniciar el sistema
echo 2. Ver documentacion
echo 3. Salir
echo.
set /p siguiente="Selecciona (1-3): "

if "%siguiente%"=="1" goto INICIAR
if "%siguiente%"=="2" goto DOCS
if "%siguiente%"=="3" goto SALIR

:LIMPIAR
echo.
echo Limpiando archivos obsoletos...
python CLEAN_AND_OPTIMIZE.py
pause
goto MENU

:REORGANIZAR
echo.
echo Reorganizando estructura del proyecto...
python REORGANIZE_PROJECT.py
pause
goto MENU

:INSTALAR
echo.
echo Instalando dependencias...
python INSTALL.py
pause
goto MENU

:INICIAR
echo.
echo ================================================================
echo                   INICIANDO ALGO TRADER V3
echo ================================================================
echo.
echo Selecciona el modo de ejecucion:
echo 1. DEMO (recomendado para empezar)
echo 2. PAPER (trading simulado)
echo 3. LIVE (dinero real - CUIDADO)
echo.
set /p modo="Modo (1-3): "

if "%modo%"=="1" set TRADING_MODE=demo
if "%modo%"=="2" set TRADING_MODE=paper
if "%modo%"=="3" set TRADING_MODE=live

echo.
echo Iniciando en modo %TRADING_MODE%...
python launcher.py --mode %TRADING_MODE% --action start
pause
goto FIN

:DOCS
echo.
echo Abriendo documentacion...
if exist README.md (
    start README.md
) else (
    echo README.md no encontrado
)
pause
goto MENU

:ERROR
echo.
echo ================================================================
echo                    ERROR EN EL PROCESO
echo ================================================================
echo.
echo Hubo un error durante la ejecucion.
echo Por favor revisa los mensajes anteriores.
echo.
pause
goto MENU

:SALIR
echo.
echo Gracias por usar Algo Trader V3
echo.
pause

:FIN
exit