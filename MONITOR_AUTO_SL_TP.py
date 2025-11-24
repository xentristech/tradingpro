#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monitor automático de posiciones con corrección de SL/TP
"""

import MetaTrader5 as mt5
import time
from datetime import datetime
import sys

class PositionMonitor:
    def __init__(self):
        self.check_interval = 10  # segundos
        self.sl_distance_pips = 100  # pips para SL
        self.tp_distance_pips = 150  # pips para TP
        
    def connect(self):
        """Conecta a MT5"""
        if not mt5.initialize():
            print("[ERROR] No se pudo conectar a MT5")
            return False
            
        account_info = mt5.account_info()
        if account_info:
            print(f"[OK] Conectado - Cuenta: {account_info.login}")
            print(f"     Balance: ${account_info.balance:.2f}")
            print(f"     Servidor: {account_info.server}")
            return True
        return False
    
    def fix_position(self, position):
        """Corrige una posición sin SL/TP"""
        symbol_info = mt5.symbol_info(position.symbol)
        if not symbol_info:
            return False
            
        price = position.price_current
        point = symbol_info.point
        
        # Ajustar distancias según el símbolo
        if "GOLD" in position.symbol.upper() or "XAU" in position.symbol.upper():
            sl_points = 100
            tp_points = 150
        elif "BTC" in position.symbol.upper():
            sl_points = 500
            tp_points = 1000
        else:  # Forex
            sl_points = 50
            tp_points = 100
            
        # Calcular niveles
        if position.type == 0:  # BUY
            sl_price = price - (sl_points * point)
            tp_price = price + (tp_points * point)
        else:  # SELL
            sl_price = price + (sl_points * point)
            tp_price = price - (tp_points * point)
            
        sl_price = round(sl_price, symbol_info.digits)
        tp_price = round(tp_price, symbol_info.digits)
        
        # Crear request
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "symbol": position.symbol,
            "position": position.ticket,
            "sl": sl_price,
            "tp": tp_price,
            "magic": 234000,
            "comment": "Auto SL/TP"
        }
        
        result = mt5.order_send(request)
        
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"       [FIXED] SL: {sl_price:.5f} | TP: {tp_price:.5f}")
            return True
        else:
            if result:
                print(f"       [ERROR] Code: {result.retcode}")
            return False
    
    def check_positions(self):
        """Verifica y corrige posiciones"""
        positions = mt5.positions_get()
        
        if not positions:
            return 0
            
        fixed_count = 0
        print(f"\n   [SCAN] {len(positions)} posiciones encontradas")
        
        for pos in positions:
            needs_fix = False
            status = []
            
            if pos.sl == 0:
                status.append("Sin SL")
                needs_fix = True
            if pos.tp == 0:
                status.append("Sin TP")
                needs_fix = True
                
            if needs_fix:
                print(f"   [{pos.ticket}] {pos.symbol} - {' | '.join(status)}")
                if self.fix_position(pos):
                    fixed_count += 1
                    
        return fixed_count
    
    def run(self):
        """Ejecuta el monitor continuo"""
        print("\n" + "="*60)
        print("     MONITOR AUTOMATICO SL/TP - ACTIVO")
        print("="*60)
        print(f"Intervalo: {self.check_interval} segundos")
        print("Presiona Ctrl+C para detener\n")
        
        if not self.connect():
            return
            
        cycle = 0
        total_fixed = 0
        
        try:
            while True:
                cycle += 1
                print(f"[Ciclo {cycle:03d}] {datetime.now().strftime('%H:%M:%S')}", end="")
                
                fixed = self.check_positions()
                if fixed > 0:
                    total_fixed += fixed
                    print(f"   --> {fixed} posiciones corregidas!")
                else:
                    print("   [OK] Todas las posiciones protegidas")
                    
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            print(f"\n\n[STOP] Monitor detenido")
            print(f"Total corregidas: {total_fixed} posiciones")
        finally:
            mt5.shutdown()

def main():
    monitor = PositionMonitor()
    monitor.run()

if __name__ == "__main__":
    main()