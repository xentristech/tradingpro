@echo off
cls
color 0E
echo ================================================================================
echo                        VERIFICACION COMPLETA DE OLLAMA
echo ================================================================================
echo.
echo Verificando si Ollama esta instalado y funcionando...
echo.

REM Verificar si ollama existe
where ollama >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Ollama esta instalado
    echo.
    echo Version instalada:
    ollama --version
    echo.
    
    echo Modelos disponibles:
    ollama list
    echo.
    
    echo ================================================================================
    echo Si no ves el modelo deepseek-r1:14b arriba, instalalo con:
    echo    ollama pull deepseek-r1:14b
    echo.
    echo O usa un modelo mas ligero:
    echo    ollama pull llama3
    echo ================================================================================
) else (
    echo [ERROR] Ollama NO esta instalado
    echo.
    echo ================================================================================
    echo                          INSTRUCCIONES DE INSTALACION
    echo ================================================================================
    echo.
    echo 1. Abre tu navegador y ve a:
    echo    https://ollama.ai/download
    echo.
    echo 2. Descarga Ollama para Windows
    echo.
    echo 3. Instala Ollama (doble clic en el instalador)
    echo.
    echo 4. Despues de instalar, abre una terminal nueva y ejecuta:
    echo    ollama serve
    echo.
    echo 5. En otra terminal, descarga un modelo:
    echo    ollama pull llama3
    echo    (o para mejor rendimiento en trading):
    echo    ollama pull deepseek-r1:14b
    echo.
    echo 6. Vuelve a ejecutar este script
    echo ================================================================================
)

echo.
pause
