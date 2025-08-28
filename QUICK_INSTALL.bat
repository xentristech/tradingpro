@echo off
REM Instalación Rápida de Dependencias Mínimas
echo.
echo ============================================
echo   INSTALACION RAPIDA - ALGO TRADER v3.0
echo ============================================
echo.

REM Instalar paquetes esenciales directamente
echo Instalando dependencias esenciales...
echo.

pip install --upgrade pip

echo [1/8] Instalando pandas y numpy...
pip install pandas numpy

echo [2/8] Instalando requests y dotenv...
pip install requests python-dotenv

echo [3/8] Instalando MetaTrader5...
pip install MetaTrader5

echo [4/8] Instalando aiohttp...
pip install aiohttp

echo [5/8] Instalando colorlog...
pip install colorlog

echo [6/8] Instalando PyYAML...
pip install PyYAML

echo [7/8] Instalando pytz...
pip install pytz

echo [8/8] Instalando scikit-learn (opcional)...
pip install scikit-learn xgboost

echo.
echo ============================================
echo   INSTALACION COMPLETADA
echo ============================================
echo.
echo Ejecutando verificacion...
python quick_check.py --config configs/.env

pause
