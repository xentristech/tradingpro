@echo off
echo ============================================================
echo VERIFICANDO POSICIONES ABIERTAS EN MT5
echo ============================================================
echo.

cd /d "C:\Users\user\OneDrive\Escritorio\Proyectos\Xentristech\Developer\algo-trader-mvp-v3\algo-trader-mvp-v2"

echo Activando entorno virtual...
call .venv\Scripts\activate.bat

echo.
echo Ejecutando verificador de posiciones...
echo.

python -c "import MetaTrader5 as mt5; from datetime import datetime; print('Conectando a MT5...'); initialized = mt5.initialize(); print(f'Conectado: {initialized}'); account = mt5.account_info() if initialized else None; print(f'Cuenta: {account.login if account else 'No conectado'}'); print(f'Balance: ${account.balance:.2f}' if account else ''); positions = mt5.positions_get() if initialized else []; print(f''); print(f'POSICIONES ABIERTAS: {len(positions) if positions else 0}'); print('='*40); [print(f'{p.symbol} #{p.ticket}: {p.type} {p.volume} lotes, Profit: ${p.profit:.2f}') for p in positions] if positions else print('No hay posiciones abiertas'); mt5.shutdown() if initialized else None"

echo.
echo ============================================================
pause
