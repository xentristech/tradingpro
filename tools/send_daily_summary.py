"""
Send Daily Summary Now
Lee estado desde data/system_state.json y envía resumen diario a Telegram.
Uso: python tools/send_daily_summary.py --config configs/.env
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', default='configs/.env')
    args = ap.parse_args()

    # Asegurar cwd = raíz del proyecto
    project_root = Path(__file__).resolve().parents[1]
    os.chdir(project_root)

    # Cargar .env
    try:
        from dotenv import load_dotenv
        if Path(args.config).exists():
            load_dotenv(args.config)
    except Exception:
        pass

    # Cargar estado
    state_path = Path('data/system_state.json')
    if not state_path.exists():
        print('No existe data/system_state.json. Ejecuta el bot primero para generar estado.')
        sys.exit(1)
    with open(state_path, 'r') as f:
        st = json.load(f)

    stats = st.get('stats', {})
    # Calcular win rate
    total = stats.get('trades_total', 0)
    won = stats.get('trades_won', 0)
    stats['win_rate'] = (won/total) if total else 0.0
    # Adjuntar PnL por símbolo
    pnl_by_symbol = st.get('pnl_by_symbol', {})
    if pnl_by_symbol:
        stats['pnl_by_symbol'] = pnl_by_symbol

    # Adjuntar métricas sencillas si hay market_data (global)
    md = st.get('market_data', {})
    symbol = os.getenv('SYMBOL')
    if symbol and symbol in md:
        raw = (md[symbol] or {}).get('raw') or {}
        tfs = (os.getenv('TIMEFRAMES', '5min,15min,1h').split(','))
        primary_tf = tfs[0].strip()
        closes = (((raw.get(primary_tf) or {}).get('price') or {}).get('close') or [])
        if len(closes) > 10:
            try:
                import numpy as np
                rets = [(closes[i]/closes[i-1]-1.0) for i in range(1, len(closes))]
                var_percentile = (1-0.95) * 100
                stats['var_95'] = abs(float(np.percentile(np.array(rets), var_percentile))) * abs(stats.get('profit_total', 0))
                rf = 0.02/252
                ex = np.array(rets) - rf
                stats['sharpe_ratio'] = float(np.mean(ex)/np.std(ex) * np.sqrt(252)) if np.std(ex) else 0.0
            except Exception:
                pass

    # Enviar mensaje
    from notifiers.telegram import TelegramNotifier
    notifier = TelegramNotifier()
    ok = notifier.send_daily_summary(stats)
    print('Resumen diario enviado' if ok else 'No se pudo enviar el resumen (Telegram no configurado)')

if __name__ == '__main__':
    main()

