@echo off
cls
color 0A
echo ================================================================
echo                  PRUEBA RAPIDA DE TELEGRAM
echo                      ALGO TRADER V3
echo ================================================================
echo.
echo Enviando mensaje de prueba a Telegram...
echo.

python -c "from src.notifiers.telegram_notifier import TelegramNotifier; n = TelegramNotifier(); n.send_alert('success', 'Sistema funcionando correctamente!\nTodos los servicios activos.', True) if n.is_active else print('Error: Telegram no conectado')"

echo.
echo ================================================================
echo.
echo Si recibiste el mensaje en Telegram, el sistema esta listo!
echo.
pause