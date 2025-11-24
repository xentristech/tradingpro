#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Monitor completo del sistema de trading
"""

import MetaTrader5 as mt5
import time
from datetime import datetime
import sys

class TradingMonitor:
    def __init__(self):
        self.check_interval = 5  # segundos
        self.positions_monitored = {}
        
    def connect(self):
        """Conecta a MT5"""
        if not mt5.initialize():
            print("[ERROR] No se pudo conectar a MT5")
            return False
            
        account_info = mt5.account_info()
        if account_info:
            print(f"\n[CUENTA CONECTADA]")
            print(f"  Numero: {account_info.login}")
            print(f"  Balance: ${account_info.balance:.2f}")
            print(f"  Equity: ${account_info.equity:.2f}")
            print(f"  Servidor: {account_info.server}")
            print(f"  Apalancamiento: 1:{account_info.leverage}")
            return True
        return False
    
    def check_position_protection(self, position):
        """Verifica si una posicion necesita SL/TP"""
        needs_sl = position.sl == 0
        needs_tp = position.tp == 0
        return needs_sl, needs_tp
    
    def fix_position(self, position):
        """Intenta corregir una posicion sin SL/TP"""
        symbol_info = mt5.symbol_info(position.symbol)
        if not symbol_info:
            return False
            
        price = position.price_current
        point = symbol_info.point
        
        # Configuracion por simbolo
        if "XAU" in position.symbol.upper() or "GOLD" in position.symbol.upper():
            sl_points = 100  # 100 puntos para oro
            tp_points = 200  # 200 puntos para oro
        elif "BTC" in position.symbol.upper():
            sl_points = 1000  # 1000 puntos para BTC
            tp_points = 2000  # 2000 puntos para BTC
        else:  # Forex
            sl_points = 50   # 50 puntos
            tp_points = 100  # 100 puntos
            
        # Calcular niveles
        if position.type == 0:  # BUY
            sl_price = price - (sl_points * point)
            tp_price = price + (tp_points * point)
        else:  # SELL
            sl_price = price + (sl_points * point)
            tp_price = price - (tp_points * point)
            
        sl_price = round(sl_price, symbol_info.digits)
        tp_price = round(tp_price, symbol_info.digits)
        
        # Solo configurar lo que falta
        if position.sl == 0:
            sl_to_set = sl_price
        else:
            sl_to_set = position.sl
            
        if position.tp == 0:
            tp_to_set = tp_price
        else:
            tp_to_set = position.tp
        
        # Crear request
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "symbol": position.symbol,
            "position": position.ticket,
            "sl": sl_to_set,
            "tp": tp_to_set,
            "magic": 234000,
            "comment": "Monitor Auto"
        }
        
        result = mt5.order_send(request)
        
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"    [CORREGIDO] SL: {sl_to_set:.5f} | TP: {tp_to_set:.5f}")
            return True
        else:
            if result:
                print(f"    [ERROR] Codigo: {result.retcode}")
                if result.comment:
                    print(f"    Comentario: {result.comment}")
            return False
    
    def monitor_cycle(self):
        """Un ciclo de monitoreo"""
        positions = mt5.positions_get()
        
        if not positions:
            return {"total": 0, "protected": 0, "unprotected": 0, "fixed": 0}
            
        stats = {
            "total": len(positions),
            "protected": 0,
            "unprotected": 0,
            "fixed": 0
        }
        
        print(f"\n[POSICIONES: {len(positions)}]")
        
        for pos in positions:
            needs_sl, needs_tp = self.check_position_protection(pos)
            
            # Mostrar info de la posicion
            print(f"  #{pos.ticket} {pos.symbol} {'BUY' if pos.type == 0 else 'SELL'} {pos.volume}L")
            print(f"    P&L: ${pos.profit:.2f}")
            
            if needs_sl or needs_tp:
                stats["unprotected"] += 1
                
                status = []
                if needs_sl:
                    status.append("Sin SL")
                if needs_tp:
                    status.append("Sin TP")
                    
                print(f"    [ALERTA] {' | '.join(status)}")
                
                # Intentar corregir
                print(f"    Intentando corregir...")
                if self.fix_position(pos):
                    stats["fixed"] += 1
                    print(f"    [OK] Proteccion configurada")
                else:
                    print(f"    [FALLO] No se pudo configurar")
            else:
                stats["protected"] += 1
                print(f"    [OK] SL: {pos.sl:.5f} | TP: {pos.tp:.5f}")
                
        return stats
    
    def run(self):
        """Ejecuta el monitor continuo"""
        print("\n" + "="*60)
        print("     MONITOR DE TRADING - SISTEMA COMPLETO")
        print("="*60)
        print(f"Verificacion cada: {self.check_interval} segundos")
        print("Presiona Ctrl+C para detener")
        
        if not self.connect():
            return
            
        cycle = 0
        total_fixed = 0
        
        try:
            while True:
                cycle += 1
                print(f"\n[Ciclo {cycle:04d}] {datetime.now().strftime('%H:%M:%S')}")
                print("-" * 40)
                
                # Obtener info actualizada
                account_info = mt5.account_info()
                if account_info:
                    print(f"Balance: ${account_info.balance:.2f} | Equity: ${account_info.equity:.2f} | P&L: ${account_info.profit:.2f}")
                
                # Monitorear posiciones
                stats = self.monitor_cycle()
                
                if stats["total"] == 0:
                    print("[INFO] No hay posiciones abiertas")
                else:
                    print(f"\n[RESUMEN CICLO]")
                    print(f"  Total: {stats['total']}")
                    print(f"  Protegidas: {stats['protected']}")
                    print(f"  Sin proteccion: {stats['unprotected']}")
                    if stats['fixed'] > 0:
                        print(f"  Corregidas este ciclo: {stats['fixed']}")
                        total_fixed += stats['fixed']
                
                # Esperar
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            print(f"\n\n[MONITOR DETENIDO]")
            print(f"Ciclos ejecutados: {cycle}")
            print(f"Total posiciones corregidas: {total_fixed}")
        finally:
            mt5.shutdown()
            print("[MT5] Conexion cerrada")

def main():
    monitor = TradingMonitor()
    monitor.run()

if __name__ == "__main__":
    main()