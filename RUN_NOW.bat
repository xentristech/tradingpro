@echo off
echo ========================================
echo     EJECUTANDO ALGO TRADER BOT
echo ========================================
echo.
echo Fecha/Hora: %date% %time%
echo.

cd /d "C:\Users\user\Desktop\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2"

echo Verificando conexion MT5...
echo.
.venv\Scripts\python.exe -c "import os; from dotenv import load_dotenv; load_dotenv('configs/.env'); print('Login MT5:', os.getenv('MT5_LOGIN')); print('Server:', os.getenv('MT5_SERVER')); print('Symbol:', os.getenv('SYMBOL')); print('Live Trading:', os.getenv('LIVE_TRADING'))"

echo.
echo ========================================
echo Iniciando bot principal...
echo ========================================
echo.

.venv\Scripts\python.exe FINAL_BOT.py

if errorlevel 1 (
    echo.
    echo ERROR: El bot encontro un problema
    echo Revisa los logs en la carpeta logs\
) else (
    echo.
    echo Bot finalizado correctamente
)

pause
