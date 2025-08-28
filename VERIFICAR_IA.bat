@echo off
cls
color 0E
title VERIFICACION DE IA - OLLAMA

echo ================================================================================
echo                    VERIFICACION DEL SISTEMA DE IA (OLLAMA)
echo ================================================================================
echo.
echo El bot usa OLLAMA con DeepSeek-R1 para tomar decisiones de trading
echo.
echo Este script verificara:
echo   - Si Ollama esta instalado
echo   - Si esta ejecutandose
echo   - Si el modelo esta descargado
echo   - Si la IA responde correctamente
echo.
echo --------------------------------------------------------------------------------
pause

cd /d "C:\Users\user\Desktop\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2"

.venv\Scripts\python.exe verificar_ia.py

pause
