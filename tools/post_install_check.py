"""
Post-Installation Verifier
Valida la instalación probando: MT5, TwelveData, Telegram y genera un snapshot.

Uso:
  python tools/post_install_check.py --config configs/.env --symbol BTCUSDm --interval 15min
"""
import os
import sys
import json
import time
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class CheckResult:
    ok: bool
    message: str


def load_env(config: str) -> None:
    try:
        from dotenv import load_dotenv
        if Path(config).exists():
            load_dotenv(config)
    except Exception:
        pass


def check_mt5() -> CheckResult:
    try:
        from utils.mt5_connection import MT5ConnectionManager
        mgr = MT5ConnectionManager(max_retries=1, retry_delay=2)
        if not mgr.connect():
            return CheckResult(False, "MT5: no se pudo conectar. Verifica MT5_PATH/LOGIN/PASSWORD/SERVER y que MT5 esté instalado.")
        info = mgr.get_account_info()
        login = getattr(info, 'login', 'N/A') if info else 'N/A'
        balance = getattr(info, 'balance', 0.0) if info else 0.0
        mgr.disconnect()
        return CheckResult(True, f"MT5: conectado (login {login}, balance ${balance:.2f})")
    except Exception as e:
        return CheckResult(False, f"MT5: error {e}")


def check_twelvedata(symbol: str, interval: str) -> CheckResult:
    try:
        from data.twelvedata import time_series
        ts = time_series(symbol, interval, outputsize=50)
        closes = ts.get('close') or []
        if closes:
            return CheckResult(True, f"TwelveData: OK ({len(closes)} velas en {interval})")
        return CheckResult(False, "TwelveData: sin datos. Verifica TWELVEDATA_API_KEY o símbolo/exchange")
    except Exception as e:
        return CheckResult(False, f"TwelveData: error {e}")


def check_telegram() -> CheckResult:
    try:
        from notifiers.telegram import TelegramNotifier
        nt = TelegramNotifier()
        if not nt.enabled:
            return CheckResult(False, "Telegram: no configurado (TOKEN/CHAT_ID faltan)")
        ok = nt.send_message("✅ Post-install check: Telegram operativo")
        return CheckResult(True, "Telegram: mensaje enviado") if ok else CheckResult(False, "Telegram: fallo al enviar")
    except Exception as e:
        return CheckResult(False, f"Telegram: error {e}")


def generate_snapshot(config: str, symbol: str, interval: str) -> CheckResult:
    try:
        charts = Path('charts'); charts.mkdir(parents=True, exist_ok=True)
        cmd = [sys.executable, 'market_snapshot.py', '--config', config, '--symbol', symbol, '--interval', interval, '--lookback', '120']
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)
        if res.returncode == 0 and (charts / 'market_snapshot.png').exists():
            return CheckResult(True, 'Snapshot: charts/market_snapshot.png generado')
        return CheckResult(False, f"Snapshot: fallo (rc={res.returncode}). {res.stderr[:160]}")
    except Exception as e:
        return CheckResult(False, f"Snapshot: error {e}")


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', default='configs/.env')
    ap.add_argument('--symbol', default=os.getenv('SYMBOL', 'BTCUSDm'))
    ap.add_argument('--interval', default='15min')
    args = ap.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    os.chdir(project_root)
    load_env(args.config)

    print('\n=== Verificador Post-Instalación ===')
    results = []

    # 1) MT5
    print('1) Probando MetaTrader 5...')
    results.append(check_mt5())

    # 2) TwelveData
    print('2) Probando TwelveData...')
    results.append(check_twelvedata(args.symbol, args.interval))

    # 3) Telegram
    print('3) Probando Telegram...')
    results.append(check_telegram())

    # 4) Snapshot
    print('4) Generando snapshot de mercado...')
    results.append(generate_snapshot(args.config, args.symbol, args.interval))

    print('\n--- Resultados ---')
    ok_all = True
    for r in results:
        status = 'OK ' if r.ok else 'ERR'
        print(f'[{status}] {r.message}')
        if not r.ok:
            ok_all = False

    print('\nSugerencias:')
    print('- Asegura MT5 y credenciales en configs/.env (MT5_PATH/LOGIN/PASSWORD/SERVER)')
    print('- Revisa TWELVEDATA_API_KEY y TWELVEDATA_EXCHANGE (ej. Binance)')
    print('- Configura TELEGRAM_TOKEN y TELEGRAM_CHAT_ID para alertas')
    print('\nEstado final:', '✅ Todo correcto' if ok_all else '⚠️  Revisar puntos con error')


if __name__ == '__main__':
    main()

