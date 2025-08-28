@echo off
cls
color 0B
title VERIFICAR OLLAMA

cd /d "C:\Users\user\Desktop\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2"

echo ========================================================
echo           VERIFICANDO OLLAMA (IA)
echo ========================================================
echo.

.venv\Scripts\python.exe check_ollama.py

echo.
echo ========================================================
echo Si Ollama no esta funcionando:
echo.
echo 1. Instala desde: https://ollama.ai/download
echo 2. Abre una terminal y ejecuta: ollama serve
echo 3. Descarga un modelo: ollama pull llama3
echo 4. Vuelve a ejecutar este script
echo ========================================================
echo.
pause
