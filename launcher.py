#!/usr/bin/env python
"""
ALGO TRADER V3 - LAUNCHER UNIFICADO
====================================
Sistema principal de inicio y gestión
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

class AlgoTraderLauncher:
    def __init__(self):
        self.base_path = Path(__file__).parent
        self.processes = {}
        
    def start_system(self, mode='demo'):
        """Inicia el sistema completo"""
        print(f"🚀 Iniciando Algo Trader en modo {mode.upper()}")
        
        # 1. Verificar dependencias
        self.check_dependencies()
        
        # 2. Iniciar servicios core
        self.start_core_services()
        
        # 3. Iniciar dashboards
        self.start_dashboards()
        
        # 4. Iniciar bot de trading
        self.start_trading_bot(mode)
        
        print("✅ Sistema iniciado completamente")
        
    def check_dependencies(self):
        """Verifica que todas las dependencias estén instaladas"""
        try:
            import MetaTrader5
            import pandas
            import streamlit
            print("✅ Dependencias verificadas")
        except ImportError as e:
            print(f"❌ Falta dependencia: {e}")
            sys.exit(1)
    
    def start_core_services(self):
        """Inicia los servicios principales"""
        # Iniciar sistema de ticks
        tick_system = self.base_path / 'src' / 'data' / 'TICK_SYSTEM_FINAL.py'
        if tick_system.exists():
            self.processes['tick_system'] = subprocess.Popen(
                [sys.executable, str(tick_system)],
                cwd=str(self.base_path)
            )
            print("✅ Sistema de ticks iniciado")
    
    def start_dashboards(self):
        """Inicia los dashboards web"""
        dashboards = [
            ('revolutionary_dashboard_final.py', 8512),
            ('chart_simulation_reviewed.py', 8516),
            ('tradingview_professional_chart.py', 8517)
        ]
        
        for dashboard, port in dashboards:
            dashboard_path = self.base_path / 'src' / 'ui' / 'dashboards' / dashboard
            if dashboard_path.exists():
                self.processes[dashboard] = subprocess.Popen(
                    [sys.executable, str(dashboard_path)],
                    cwd=str(self.base_path)
                )
                print(f"✅ Dashboard iniciado en puerto {port}")
    
    def start_trading_bot(self, mode):
        """Inicia el bot de trading"""
        os.environ['TRADING_MODE'] = mode.upper()
        
        bot_path = self.base_path / 'src' / 'trading' / 'main_trader.py'
        if bot_path.exists():
            self.processes['trading_bot'] = subprocess.Popen(
                [sys.executable, str(bot_path)],
                cwd=str(self.base_path)
            )
            print(f"✅ Bot de trading iniciado en modo {mode}")
    
    def stop_system(self):
        """Detiene todos los procesos"""
        print("⏹️ Deteniendo sistema...")
        
        for name, process in self.processes.items():
            if process and process.poll() is None:
                process.terminate()
                print(f"✅ {name} detenido")
        
        print("✅ Sistema detenido completamente")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Algo Trader V3 Launcher')
    parser.add_argument('--mode', choices=['demo', 'paper', 'live'], 
                       default='demo', help='Modo de trading')
    parser.add_argument('--action', choices=['start', 'stop', 'restart'], 
                       default='start', help='Acción a realizar')
    
    args = parser.parse_args()
    launcher = AlgoTraderLauncher()
    
    if args.action == 'start':
        launcher.start_system(args.mode)
    elif args.action == 'stop':
        launcher.stop_system()
    elif args.action == 'restart':
        launcher.stop_system()
        launcher.start_system(args.mode)
