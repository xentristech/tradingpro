@echo off
title CONFIGURACION RAPIDA - ALGO TRADER V3
color 0E

cls
echo ╔════════════════════════════════════════════════════════════╗
echo ║          CONFIGURACION RAPIDA - ALGO TRADER V3            ║
echo ║                                                            ║
echo ║  Este asistente te ayudara a configurar el sistema        ║
echo ║  en menos de 5 minutos                                    ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

:: Verificar si .env existe
if exist .env (
    echo ✅ Archivo .env encontrado
    echo.
    set /p overwrite="Deseas sobrescribir la configuracion actual? (S/N): "
    if /i "%overwrite%" neq "S" goto :check_config
) else (
    echo ⚠️ Archivo .env no encontrado
    echo ✅ Creando nuevo archivo de configuracion...
    copy .env.example .env >nul 2>&1
)

echo.
echo ════════════════════════════════════════════════════════════
echo PASO 1: CONFIGURACION DE TWELVEDATA API
echo ════════════════════════════════════════════════════════════
echo.
echo Necesitas una API key de TwelveData (GRATIS)
echo.
echo Si no tienes una:
echo 1. Ve a: https://twelvedata.com/apikey
echo 2. Registrate gratis
echo 3. Copia tu API key
echo.
set /p twelve_key="Ingresa tu TwelveData API Key: "

if "%twelve_key%"=="" (
    echo ❌ API Key no puede estar vacia
    echo    El sistema no funcionara sin esta key
    pause
    goto :end
)

:: Verificar si es la key hardcodeada
if "%twelve_key%"=="23d17ce5b7044ad5aef9766770a6252b" (
    echo.
    echo ⚠️ ADVERTENCIA: Estas usando la API key hardcodeada!
    echo    Esta key puede no funcionar o tener limites muy bajos.
    echo    Se recomienda obtener tu propia key en twelvedata.com
    echo.
    pause
)

echo.
echo ════════════════════════════════════════════════════════════
echo PASO 2: CONFIGURACION DE TELEGRAM (Opcional)
echo ════════════════════════════════════════════════════════════
echo.
echo Para recibir señales en Telegram necesitas:
echo 1. Crear un bot con @BotFather
echo 2. Obtener el token del bot
echo 3. Obtener tu Chat ID
echo.
set /p config_telegram="Deseas configurar Telegram? (S/N): "

if /i "%config_telegram%"=="S" (
    echo.
    set /p telegram_token="Ingresa el Token del Bot: "
    set /p telegram_chat="Ingresa tu Chat ID: "
) else (
    echo.
    echo ℹ️ Telegram omitido - podras configurarlo despues
    set telegram_token=
    set telegram_chat=
)

echo.
echo ════════════════════════════════════════════════════════════
echo PASO 3: CONFIGURACION DE METATRADER 5 (Opcional)
echo ════════════════════════════════════════════════════════════
echo.
echo Para trading automatico necesitas MetaTrader 5
echo.
set /p config_mt5="Deseas configurar MT5? (S/N): "

if /i "%config_mt5%"=="S" (
    echo.
    set /p mt5_login="Ingresa tu Login de MT5: "
    set /p mt5_password="Ingresa tu Password de MT5: "
    set /p mt5_server="Ingresa el Servidor (ej: MetaQuotes-Demo): "
) else (
    echo.
    echo ℹ️ MT5 omitido - solo funcionaran las señales
    set mt5_login=
    set mt5_password=
    set mt5_server=
)

echo.
echo ════════════════════════════════════════════════════════════
echo APLICANDO CONFIGURACION...
echo ════════════════════════════════════════════════════════════
echo.

:: Crear archivo Python para actualizar .env
echo import re > update_env.py
echo. >> update_env.py
echo with open('.env', 'r') as f: >> update_env.py
echo     content = f.read() >> update_env.py
echo. >> update_env.py
echo # Actualizar valores >> update_env.py
echo content = re.sub(r'TWELVEDATA_API_KEY=.*', 'TWELVEDATA_API_KEY=%twelve_key%', content) >> update_env.py

if not "%telegram_token%"=="" (
    echo content = re.sub(r'TELEGRAM_TOKEN=.*', 'TELEGRAM_TOKEN=%telegram_token%', content) >> update_env.py
    echo content = re.sub(r'TELEGRAM_CHAT_ID=.*', 'TELEGRAM_CHAT_ID=%telegram_chat%', content) >> update_env.py
)

if not "%mt5_login%"=="" (
    echo content = re.sub(r'MT5_LOGIN=.*', 'MT5_LOGIN=%mt5_login%', content) >> update_env.py
    echo content = re.sub(r'MT5_PASSWORD=.*', 'MT5_PASSWORD=%mt5_password%', content) >> update_env.py
    echo content = re.sub(r'MT5_SERVER=.*', 'MT5_SERVER=%mt5_server%', content) >> update_env.py
)

echo. >> update_env.py
echo with open('.env', 'w') as f: >> update_env.py
echo     f.write(content) >> update_env.py
echo. >> update_env.py
echo print('✅ Configuracion actualizada') >> update_env.py

:: Ejecutar actualizacion
python update_env.py
del update_env.py

echo.
echo ════════════════════════════════════════════════════════════
echo INSTALANDO DEPENDENCIAS...
echo ════════════════════════════════════════════════════════════
echo.

pip install pandas numpy requests python-dotenv --quiet
echo ✅ Dependencias basicas instaladas

if /i "%config_telegram%"=="S" (
    pip install python-telegram-bot --quiet
    echo ✅ Telegram instalado
)

if /i "%config_mt5%"=="S" (
    pip install MetaTrader5 --quiet
    echo ✅ MetaTrader5 instalado
)

:check_config
echo.
echo ════════════════════════════════════════════════════════════
echo VERIFICANDO CONFIGURACION...
echo ════════════════════════════════════════════════════════════
echo.

:: Verificar configuracion
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('TwelveData:', 'OK' if os.getenv('TWELVEDATA_API_KEY') and os.getenv('TWELVEDATA_API_KEY') != 'YOUR_API_KEY_HERE' else 'NO CONFIGURADO')" 2>nul
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('Telegram:', 'OK' if os.getenv('TELEGRAM_TOKEN') and os.getenv('TELEGRAM_TOKEN') != 'YOUR_TOKEN_HERE' else 'NO CONFIGURADO')" 2>nul
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('MT5:', 'OK' if os.getenv('MT5_LOGIN') and os.getenv('MT5_LOGIN') != 'YOUR_LOGIN_HERE' else 'NO CONFIGURADO')" 2>nul

echo.
echo ════════════════════════════════════════════════════════════
echo ✅ CONFIGURACION COMPLETADA
echo ════════════════════════════════════════════════════════════
echo.
echo PROXIMOS PASOS:
echo.
echo 1. Para verificar el estado del sistema:
echo    VER_ESTADO.bat
echo.
echo 2. Para iniciar el sistema de señales:
echo    EJECUTAR_SOLO_SENALES.bat
echo.
echo 3. Para iniciar el sistema completo:
echo    EJECUTAR_TODO_PRO.bat
echo.
echo 4. Para monitoreo en tiempo real:
echo    MONITOR.bat
echo.
echo 5. Para diagnostico completo:
echo    EJECUTAR_DIAGNOSTICO.bat
echo.
echo ════════════════════════════════════════════════════════════
echo.

:end
pause
