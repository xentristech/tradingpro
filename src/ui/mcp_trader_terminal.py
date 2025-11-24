#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MCP Trader 24/7 - Consola interactiva básica
--------------------------------------------
Monitorea logs, abre URLs útiles y permite comandos simples.
No es un servidor MCP real; es un terminal de apoyo 24/7.
"""

import os
import sys
import time
import webbrowser
from pathlib import Path
from datetime import datetime

BASE = Path(__file__).resolve().parents[2]
LOGS = BASE / 'logs'
CONFIG = BASE / 'config'


def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


def tail_file(path: Path, lines: int = 20):
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            data = f.readlines()
            return ''.join(data[-lines:])
    except Exception:
        return ''


def list_recent_logs(limit: int = 8):
    if not LOGS.exists():
        return []
    files = [p for p in LOGS.glob('*.log')]
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files[:limit]


def open_useful_urls():
    cfg = CONFIG / 'auto_open_urls.txt'
    urls = []
    if cfg.exists():
        for line in cfg.read_text(encoding='utf-8', errors='ignore').splitlines():
            s = line.strip()
            if s and not s.startswith('#'):
                urls.append(s)
    if not urls:
        urls = [
            'https://xentris.tech',
            'https://www.youtube.com/@XentrisTech',
            'https://www.myfxbook.com',
            'https://www.exness.com',
            'https://news.google.com/search?q=tecnologia&hl=es-419&gl=US&ceid=US:es-419',
        ]
    for u in urls:
        try:
            print(f"Abriendo {u}")
            webbrowser.open(u)
            time.sleep(0.3)
        except Exception:
            pass


def show_header():
    print("=" * 72)
    print(" XENTRISTECH - MCP TRADER 24/7")
    print(" Monitor de sistema y utilidades en tiempo real")
    print("=" * 72)
    print(f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()


def show_status():
    print("[ESTADO] Logs recientes:")
    files = list_recent_logs()
    if not files:
        print("  No hay logs en la carpeta 'logs/'")
        return
    for p in files:
        mtime = datetime.fromtimestamp(p.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        print(f"  - {p.name:35}  {mtime}")


def show_menu():
    print()
    print("Comandos:")
    print("  status                -> Ver estado rápido")
    print("  logs [archivo]        -> Ver últimas líneas de un log")
    print("  urls                  -> Abrir URLs útiles (Xentris, YouTube, Myfxbook, Exness, Noticias)")
    print("  news                  -> Abrir últimas noticias de tecnología")
    print("  help                  -> Mostrar comandos")
    print("  exit                  -> Salir")


def main():
    clear()
    show_header()
    show_status()
    show_menu()

    try:
        while True:
            cmd = input("MCP> ").strip()
            if not cmd:
                continue
            if cmd == 'exit':
                print("Saliendo del MCP Trader 24/7...")
                break
            if cmd == 'help':
                show_menu()
                continue
            if cmd == 'status':
                clear()
                show_header()
                show_status()
                continue
            if cmd.startswith('logs'):
                parts = cmd.split()
                if len(parts) == 1:
                    # listar y mostrar el último
                    files = list_recent_logs(1)
                    if files:
                        p = files[0]
                        print(f"\n== {p.name} (últimas 40 líneas) ==\n")
                        print(tail_file(p, 40))
                    else:
                        print("No hay logs para mostrar")
                else:
                    name = ' '.join(parts[1:]).strip()
                    target = LOGS / name
                    if target.exists():
                        print(f"\n== {target.name} (últimas 60 líneas) ==\n")
                        print(tail_file(target, 60))
                    else:
                        print(f"No se encontró {name} en logs/")
                continue
            if cmd == 'urls':
                open_useful_urls()
                continue
            if cmd == 'news':
                webbrowser.open('https://news.google.com/search?q=tecnologia&hl=es-419&gl=US&ceid=US:es-419')
                continue
            print("Comando no reconocido. Escribe 'help' para ver opciones.")
    except KeyboardInterrupt:
        print("\nInterrumpido por el usuario.")


if __name__ == '__main__':
    main()

