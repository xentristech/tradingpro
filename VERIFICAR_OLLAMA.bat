@echo off
cls
color 0A
title VERIFICAR OLLAMA (IA)

echo ================================================================================
echo                     VERIFICACION DE OLLAMA (SISTEMA DE IA)
echo ================================================================================
echo.
echo Ollama es el sistema de IA que usa tu bot para:
echo   - Analizar el mercado
echo   - Tomar decisiones de trading
echo   - Filtrar senales falsas
echo   - Gestionar el riesgo
echo.
echo Sin Ollama, el bot NO puede tomar decisiones inteligentes
echo.
echo --------------------------------------------------------------------------------
pause

cd /d "C:\Users\user\Desktop\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2"

echo.
echo Ejecutando verificacion completa...
echo.

.venv\Scripts\python.exe ollama_setup.py

echo.
echo ================================================================================
echo                              QUE HACER AHORA
echo ================================================================================
echo.
echo SI TODO ESTA OK (Ollama funcionando):
echo   - Ejecuta: EJECUTAR_SISTEMA.bat
echo.
echo SI OLLAMA NO ESTA INSTALADO:
echo   1. Ve a: https://ollama.ai/download
echo   2. Descarga e instala Ollama
echo   3. Abre terminal y ejecuta: ollama serve
echo   4. En otra terminal: ollama pull llama3
echo   5. Vuelve a ejecutar este script
echo.
echo SI OLLAMA ESTA INSTALADO PERO NO EJECUTANDOSE:
echo   1. Abre una terminal (CMD o PowerShell)
echo   2. Ejecuta: ollama serve
echo   3. Deja la terminal abierta
echo   4. Ejecuta el bot
echo.
echo ================================================================================
echo.
pause
