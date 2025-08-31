@echo off
cls
color 0C
echo ================================================================
echo               DETENIENDO TODOS LOS SERVICIOS
echo                      ALGO TRADER V3
echo ================================================================
echo.

echo Deteniendo procesos Python...
taskkill /F /IM python.exe 2>nul
taskkill /F /IM py.exe 2>nul

echo.
echo Limpiando puertos...
netstat -ano | findstr :8508 | findstr LISTENING > temp.txt
netstat -ano | findstr :8512 | findstr LISTENING >> temp.txt
netstat -ano | findstr :8516 | findstr LISTENING >> temp.txt
netstat -ano | findstr :8517 | findstr LISTENING >> temp.txt

for /f "tokens=5" %%a in (temp.txt) do (
    taskkill /F /PID %%a 2>nul
)

del temp.txt 2>nul

echo.
echo ================================================================
echo              TODOS LOS SERVICIOS DETENIDOS
echo ================================================================
echo.
pause