@echo off
echo ============================================================
echo    ALGO TRADER V3 - RISK MANAGER SYSTEM
echo    Breakeven + Trailing Stop Inteligente
echo ============================================================
echo.

echo [1] Iniciando Risk Manager...
start "Risk Manager" cmd /c ".venv\Scripts\python.exe src\risk\advanced_risk_manager.py"
timeout /t 2 >nul

echo [2] Iniciando Dashboard de Monitoreo...
start "Risk Dashboard" cmd /c ".venv\Scripts\streamlit.exe run risk_manager_dashboard.py --server.port 8520"
timeout /t 2 >nul

echo [3] Iniciando Bot de Trading Principal...
start "Trading Bot" cmd /c ".venv\Scripts\python.exe START_WITH_RISK_MANAGER.py"

echo.
echo ============================================================
echo    SISTEMA INICIADO EXITOSAMENTE
echo ============================================================
echo.
echo Componentes ejecutandose:
echo   - Risk Manager (Breakeven + Trailing)
echo   - Dashboard en http://localhost:8520
echo   - Bot de Trading con IA
echo.
echo Presiona cualquier tecla para abrir el dashboard...
pause >nul

start http://localhost:8520

echo.
echo Para detener el sistema, cierra todas las ventanas
echo o presiona Ctrl+C en cada una.
echo.
pause
