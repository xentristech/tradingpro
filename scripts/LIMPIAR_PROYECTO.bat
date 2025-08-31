@echo off
cls
echo ========================================================
echo         LIMPIEZA Y OPTIMIZACION DEL PROYECTO
echo                  ALGO TRADER V3
echo ========================================================
echo.
echo Este script:
echo - Eliminara archivos obsoletos y duplicados
echo - Limpiara cache de Python
echo - Optimizara requirements.txt
echo - Liberara espacio en disco
echo.
echo NOTA: Los archivos se moveran a /deprecated
echo       (no se eliminaran permanentemente)
echo.
echo ========================================================
echo.

python CLEAN_AND_OPTIMIZE.py

echo.
pause