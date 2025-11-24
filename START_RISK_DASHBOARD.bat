@echo off
echo ====================================================================
echo    ALGO TRADER V3 - DASHBOARD DE RIESGO EN TIEMPO REAL
echo ====================================================================
echo.

REM Verificar Streamlit
python -c "import streamlit" 2>nul
if errorlevel 1 (
    echo Instalando Streamlit...
    pip install streamlit plotly
)

echo Iniciando dashboard de riesgo...
echo.
echo El dashboard se abrira automaticamente en:
echo http://localhost:8501
echo.
echo Presiona Ctrl+C para detener
echo ====================================================================

REM Iniciar dashboard con Streamlit
streamlit run risk_dashboard.py --server.port 8501 --server.headless false

pause