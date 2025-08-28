"""
Unified CLI for Algo Trader v3

Commands (requires Python 3.10+):
  - config get/set/validate
  - trade run/check/snapshot/summary

Typer is preferred; if not installed, falls back to argparse subset.
"""
from __future__ import annotations

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).parent
os.chdir(PROJECT_ROOT)


def _load_settings(path: str = 'configs/settings.yaml'):
    from configs.settings_loader import load_settings
    return load_settings(path)


def _read_yaml(path: Path) -> dict:
    import yaml
    if not path.exists():
        return {}
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def _write_yaml_atomic(path: Path, data: dict):
    import yaml, tempfile
    tmp_dir = path.parent
    with tempfile.NamedTemporaryFile('w', delete=False, dir=tmp_dir, prefix=path.name, suffix='.tmp', encoding='utf-8') as tf:
        yaml.safe_dump(data, tf, sort_keys=False, allow_unicode=True)
        tmp_name = tf.name
    backup = path.with_suffix(path.suffix + '.bak')
    if path.exists():
        shutil.copy2(path, backup)
    os.replace(tmp_name, path)


def _set_in_dict(d: dict, key: str, value):
    # supports dot.notation for shallow nesting
    parts = key.split('.') if key else []
    cur = d
    for p in parts[:-1]:
        if p not in cur or not isinstance(cur[p], dict):
            cur[p] = {}
        cur = cur[p]
    if parts:
        cur[parts[-1]] = value
    return d


def _get_from_dict(d: dict, key: Optional[str]):
    if not key:
        return d
    cur = d
    for p in key.split('.'):
        if not isinstance(cur, dict) or p not in cur:
            return None
        cur = cur[p]
    return cur


def _run_subprocess(args: list[str]) -> int:
    return subprocess.call([sys.executable, *args])


def _trade_run(mode: str = 'demo', config: str = 'configs/.env'):
    # Import and run natively to avoid spawning if possible
    from main_trader import AlgoTrader
    trader = AlgoTrader(mode=mode, config_path=config)
    if not trader.initialize():
        print('❌ Fallo en la inicialización del sistema')
        sys.exit(1)
    trader.run()


def _trade_check(config: str = 'configs/.env'):
    from main_trader import AlgoTrader
    trader = AlgoTrader(mode='demo', config_path=config, check_only=True)
    ok = trader.initialize()
    print('✅ Verificación completada exitosamente' if ok else '❌ Verificación fallida')


def _trade_snapshot(config: str, symbol: Optional[str], interval: str, lookback: int):
    # Defer to script to reuse plotting path
    args = ['market_snapshot.py', '--config', config, '--interval', interval, '--lookback', str(lookback)]
    if symbol:
        args += ['--symbol', symbol]
    sys.exit(_run_subprocess(args))


def _trade_summary(config: str):
    sys.exit(_run_subprocess(['tools/send_daily_summary.py', '--config', config]))


def main():  # argparse fallback + Typer if available
    try:
        import typer
        from typing_extensions import Annotated

        app = typer.Typer(name='algo', help='Algo Trader v3 CLI')

        cfg = typer.Typer(help='Config commands')
        app.add_typer(cfg, name='config')

        @cfg.command('get')
        def config_get(key: Annotated[Optional[str], typer.Argument(help='Key (dot notation), or omit for all')] = None,
                       path: Annotated[str, typer.Option('--path', help='Settings file path')] = 'configs/settings.yaml'):
            data = _read_yaml(Path(path))
            val = _get_from_dict(data, key)
            print(json.dumps(val if key else data, indent=2, ensure_ascii=False))

        @cfg.command('set')
        def config_set(key: Annotated[str, typer.Argument(help='Key (dot notation)')],
                       value: Annotated[str, typer.Argument(help='Value (JSON literal or string)')],
                       path: Annotated[str, typer.Option('--path', help='Settings file path')] = 'configs/settings.yaml'):
            # Parse JSON literal if possible
            try:
                parsed = json.loads(value)
            except Exception:
                parsed = value
            p = Path(path)
            data = _read_yaml(p)
            _set_in_dict(data, key, parsed)
            # Validate via Pydantic
            _ = _load_settings(path)
            _write_yaml_atomic(p, data)
            print(f'✅ Set {key} in {path}')

        @cfg.command('validate')
        def config_validate(path: Annotated[str, typer.Option('--path', help='Settings file path')] = 'configs/settings.yaml'):
            _ = _load_settings(path)
            print('✅ Settings válidos')

        trade = typer.Typer(help='Trading commands')
        app.add_typer(trade, name='trade')

        @trade.command('run')
        def trade_run(mode: Annotated[str, typer.Option('--mode', case_sensitive=False)] = 'demo',
                      config: Annotated[str, typer.Option('--config')] = 'configs/.env'):
            _trade_run(mode, config)

        @trade.command('check')
        def trade_check(config: Annotated[str, typer.Option('--config')] = 'configs/.env'):
            _trade_check(config)

        @trade.command('snapshot')
        def trade_snapshot(config: Annotated[str, typer.Option('--config')] = 'configs/.env',
                           symbol: Annotated[Optional[str], typer.Option('--symbol')] = None,
                           interval: Annotated[str, typer.Option('--interval')] = '15min',
                           lookback: Annotated[int, typer.Option('--lookback')] = 200):
            _trade_snapshot(config, symbol, interval, lookback)

        @trade.command('summary')
        def trade_summary(config: Annotated[str, typer.Option('--config')] = 'configs/.env'):
            _trade_summary(config)

        app()
        return
    except Exception:
        # Fallback argparse
        import argparse
        parser = argparse.ArgumentParser(description='Algo Trader v3 CLI (fallback)')
        sub = parser.add_subparsers(dest='cmd')

        pget = sub.add_parser('config-get')
        pget.add_argument('key', nargs='?')
        pget.add_argument('--path', default='configs/settings.yaml')

        pset = sub.add_parser('config-set')
        pset.add_argument('key')
        pset.add_argument('value')
        pset.add_argument('--path', default='configs/settings.yaml')

        pval = sub.add_parser('config-validate')
        pval.add_argument('--path', default='configs/settings.yaml')

        prun = sub.add_parser('trade-run')
        prun.add_argument('--mode', default='demo')
        prun.add_argument('--config', default='configs/.env')

        pchk = sub.add_parser('trade-check')
        pchk.add_argument('--config', default='configs/.env')

        psnap = sub.add_parser('trade-snapshot')
        psnap.add_argument('--config', default='configs/.env')
        psnap.add_argument('--symbol')
        psnap.add_argument('--interval', default='15min')
        psnap.add_argument('--lookback', type=int, default=200)

        psum = sub.add_parser('trade-summary')
        psum.add_argument('--config', default='configs/.env')

        args = parser.parse_args()
        if args.cmd == 'config-get':
            data = _read_yaml(Path(args.path))
            print(json.dumps(_get_from_dict(data, args.key) if args.key else data, indent=2, ensure_ascii=False))
        elif args.cmd == 'config-set':
            try:
                parsed = json.loads(args.value)
            except Exception:
                parsed = args.value
            p = Path(args.path)
            data = _read_yaml(p)
            _set_in_dict(data, args.key, parsed)
            _ = _load_settings(args.path)
            _write_yaml_atomic(p, data)
            print(f'✅ Set {args.key} in {args.path}')
        elif args.cmd == 'config-validate':
            _ = _load_settings(args.path)
            print('✅ Settings válidos')
        elif args.cmd == 'trade-run':
            _trade_run(args.mode, args.config)
        elif args.cmd == 'trade-check':
            _trade_check(args.config)
        elif args.cmd == 'trade-snapshot':
            _trade_snapshot(args.config, args.symbol, args.interval, args.lookback)
        elif args.cmd == 'trade-summary':
            _trade_summary(args.config)
        else:
            parser.print_help()


if __name__ == '__main__':
    main()

