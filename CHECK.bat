@echo off
cls
echo ============================================================
echo       VERIFICACION RAPIDA - MT5 Y BOT
echo ============================================================
echo.
echo Verificando procesos...
echo.

echo METATRADER 5:
tasklist | findstr terminal64
echo.

echo PROCESOS PYTHON (Bot):
tasklist | findstr python
echo.

echo ============================================================
echo Si ves terminal64.exe arriba, MT5 esta ejecutandose
echo Si ves python.exe arriba, el bot esta activo
echo ============================================================
echo.

pause
