@echo off
cls
color 0E
echo ============================================================
echo                    DETENER ALGO TRADER BOT
echo ============================================================
echo.
echo ADVERTENCIA: Esto detendrá todos los procesos del bot.
echo.
echo ¿Estás seguro que deseas detener el bot?
echo.
pause

echo.
echo Deteniendo procesos Python...
taskkill /F /IM python.exe 2>nul

if %errorlevel% == 0 (
    color 0A
    echo.
    echo ✓ Bot detenido exitosamente
) else (
    echo.
    echo No había procesos activos del bot
)

echo.
pause
