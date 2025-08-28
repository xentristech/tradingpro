@echo off
cls
echo ============================================================
echo                 ESTADO DEL BOT - TIEMPO REAL
echo ============================================================
echo.

cd /d "C:\Users\user\Desktop\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2"

echo [1] PROCESOS ACTIVOS:
echo ------------------------------------------------------------
powershell -Command "Get-Process python* -ErrorAction SilentlyContinue | Select-Object Id, ProcessName, StartTime, CPU | Format-Table"

echo.
echo [2] ULTIMOS LOGS:
echo ------------------------------------------------------------
powershell -Command "Get-ChildItem logs\*.out.log | Sort-Object LastWriteTime -Descending | Select-Object -First 5 | Format-Table Name, Length, LastWriteTime -AutoSize"

echo.
echo [3] MONITOR EN VIVO:
echo ------------------------------------------------------------
echo.
.venv\Scripts\python.exe MONITOR.py

pause
