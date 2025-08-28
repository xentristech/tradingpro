"""
Toggle Settings - Actualiza valores en configs/.env de forma segura.
Uso:
  python tools/toggle_settings.py --key ALLOW_WEEKENDS --value true --config configs/.env
  python tools/toggle_settings.py --key VOLATILITY_MAX --value 0.06
"""
import os
import sys
import argparse
from pathlib import Path


def set_key_value(env_path: Path, key: str, value: str):
    if not env_path.exists():
        env_path.write_text(f"{key}={value}\n", encoding='utf-8')
        return
    # Leer y reemplazar
    lines = env_path.read_text(encoding='utf-8', errors='ignore').splitlines()
    found = False
    new_lines = []
    for line in lines:
        if line.strip().startswith(f"{key}="):
            new_lines.append(f"{key}={value}")
            found = True
        else:
            new_lines.append(line)
    if not found:
        new_lines.append(f"{key}={value}")
    env_path.write_text("\n".join(new_lines) + "\n", encoding='utf-8')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--config', default='configs/.env')
    ap.add_argument('--key', required=True)
    ap.add_argument('--value', required=True)
    args = ap.parse_args()

    env_path = Path(args.config)
    set_key_value(env_path, args.key, args.value)
    print(f"Set {args.key}={args.value} en {env_path}")


if __name__ == '__main__':
    main()

