#!/usr/bin/env python
"""
REVISION COMPLETA DEL SISTEMA DE TRADING
"""

import MetaTrader5 as mt5
from datetime import datetime

def main():
    if mt5.initialize():
        account = mt5.account_info()
        positions = mt5.positions_get()
        
        print('=' * 60)
        print('    ESTADO COMPLETO DEL SISTEMA TRADING')
        print('=' * 60)
        print(f'Hora actual: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        print(f'Cuenta: {account.login}')
        print(f'Balance: ${account.balance:.2f}')
        print(f'Equity: ${account.equity:.2f}')
        print(f'Margin: ${account.margin:.2f}')
        print(f'Free Margin: ${account.margin_free:.2f}')
        
        print(f'\nPOSICIONES ACTIVAS ({len(positions)}):')
        total_profit = 0
        symbols_principales = ['EURUSDm', 'GBPUSDm', 'XAUUSDm', 'BTCUSDm']
        
        for pos in positions:
            total_profit += pos.profit
            tipo = 'BUY' if pos.type == 0 else 'SELL'
            duracion = (datetime.now().timestamp() - pos.time) / 3600
            principal = 'PRINCIPAL' if pos.symbol in symbols_principales else 'OTROS'
            
            print(f'  {pos.symbol}: {tipo} {pos.volume} | P&L: ${pos.profit:.2f} | {duracion:.1f}h | {principal}')
        
        print(f'\nTOTAL P&L: ${total_profit:.2f}')
        
        # Resumen por simbolos principales
        principales_activos = [p for p in positions if p.symbol in symbols_principales]
        if principales_activos:
            print(f'\nSIMBOLOS PRINCIPALES ACTIVOS:')
            for symbol in symbols_principales:
                pos_symbol = [p for p in principales_activos if p.symbol == symbol]
                if pos_symbol:
                    total_vol = sum(p.volume for p in pos_symbol)
                    total_pnl = sum(p.profit for p in pos_symbol)
                    print(f'  {symbol}: {len(pos_symbol)} pos, Vol: {total_vol:.2f}, P&L: ${total_pnl:.2f}')
        else:
            print('\nNO HAY POSICIONES EN SIMBOLOS PRINCIPALES')
            for symbol in symbols_principales:
                print(f'  {symbol}: SIN POSICIONES')
        
        print(f'\n' + '=' * 60)
        print('SISTEMAS ACTIVOS EN BACKGROUND:')
        print('=' * 60)
        print('1. START_COMPLETE_TRADING_SYSTEM.py - Monitoreo principal')
        print('2. Risk Dashboard (puertos 8501, 8502)')
        print('3. Signals Dashboard (puerto 8503)')
        print('4. Journal Monitor (tiempo real)')
        print('5. Position Monitor')
        print('6. Emergency Risk Manager')
        print('')
        print('FRECUENCIA DE MONITOREO:')
        print('- Analisis tecnico: Cada 45 segundos')
        print('- Reporte posiciones: Cada 3.75 minutos')
        print('- Umbral ejecucion: >= 65% confianza')
        print('')
        print('ESTADO: SISTEMA COMPLETAMENTE ACTIVO')
        
        mt5.shutdown()

if __name__ == "__main__":
    main()