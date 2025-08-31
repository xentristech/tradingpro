#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MONITOR CONTINUO DE POSICIONES MT5
Ciclo automático para detectar y corregir trades sin SL/TP
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime

# Configurar encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Configurar path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

class PositionMonitor:
    def __init__(self, check_interval=30):
        """
        Inicializar monitor
        Args:
            check_interval: Segundos entre verificaciones (default: 30)
        """
        self.check_interval = check_interval
        self.cycle_count = 0
        self.total_corrections = 0
        self.start_time = datetime.now()
        
    def calculate_sl_tp(self, symbol, entry_price, pos_type):
        """Calcular SL/TP usando ATR estimado"""
        try:
            # Usar ATR estimado del 1.5% del precio
            atr = entry_price * 0.015
            
            if pos_type == 'BUY':
                sl = entry_price - (atr * 2.0)  # Riesgo: 2x ATR
                tp = entry_price + (atr * 3.0)  # Beneficio: 3x ATR
            else:  # SELL
                sl = entry_price + (atr * 2.0)
                tp = entry_price - (atr * 3.0)
            
            return sl, tp, atr
            
        except Exception as e:
            print(f"   ERROR calculando SL/TP: {e}")
            return None, None, 0
    
    def monitor_cycle(self, mt5):
        """Ejecutar un ciclo de monitoreo"""
        self.cycle_count += 1
        current_time = datetime.now().strftime('%H:%M:%S')
        
        print(f"\n[Ciclo {self.cycle_count:03d}] {current_time} - Verificando posiciones...")
        
        # Obtener posiciones
        positions = mt5.positions_get()
        
        if not positions:
            print("   [INFO] No hay posiciones abiertas")
            return 0
        
        print(f"   [SCAN] {len(positions)} posiciones encontradas")
        
        corrections_this_cycle = 0
        
        for position in positions:
            symbol = position.symbol
            ticket = position.ticket
            pos_type = "BUY" if position.type == 0 else "SELL"
            entry_price = position.price_open
            
            # Verificar protección
            has_sl = position.sl != 0.0
            has_tp = position.tp != 0.0
            needs_correction = not has_sl or not has_tp
            
            # Status de protección
            sl_status = f"SL:{position.sl:.2f}" if has_sl else "SIN_SL"
            tp_status = f"TP:{position.tp:.2f}" if has_tp else "SIN_TP"
            pnl_status = f"P&L:{position.profit:.2f}"
            
            print(f"   {symbol} #{ticket} {pos_type} | {sl_status} | {tp_status} | {pnl_status}")
            
            if needs_correction:
                print(f"   >> [DETECTADO] Posicion necesita correccion")
                
                # Calcular SL/TP
                new_sl, new_tp, atr = self.calculate_sl_tp(symbol, entry_price, pos_type)
                
                if new_sl is None:
                    print(f"   >> [ERROR] No se pudo calcular SL/TP")
                    continue
                
                # Solo modificar lo que falta
                final_sl = new_sl if not has_sl else position.sl
                final_tp = new_tp if not has_tp else position.tp
                
                print(f"   >> [CALC] SL:{final_sl:.2f} TP:{final_tp:.2f} ATR:{atr:.2f}")
                
                # Preparar request
                request = {
                    "action": mt5.TRADE_ACTION_SLTP,
                    "position": ticket,
                    "symbol": symbol,
                    "sl": final_sl,
                    "tp": final_tp,
                    "magic": 20250817,
                    "comment": f"AutoFix-{self.cycle_count:03d}"
                }
                
                # Ejecutar corrección
                result = mt5.order_send(request)
                
                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    corrections_this_cycle += 1
                    self.total_corrections += 1
                    print(f"   >> [OK] CORREGIDO! SL/TP aplicados correctamente")
                else:
                    error_msg = result.comment if result else "Sin respuesta"
                    print(f"   >> [ERROR] Correccion fallo: {error_msg}")
        
        return corrections_this_cycle
    
    def start_monitoring(self):
        """Iniciar monitoreo continuo"""
        print("=" * 80)
        print("              MONITOR CONTINUO DE POSICIONES MT5")
        print("=" * 80)
        print(f"Inicio: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Intervalo: {self.check_interval} segundos entre verificaciones")
        print(f"Presiona Ctrl+C para detener")
        print("-" * 80)
        
        try:
            import MetaTrader5 as mt5
            
            # Conectar MT5
            if not mt5.initialize():
                print(f"ERROR: No se pudo conectar MT5: {mt5.last_error()}")
                return
            
            # Verificar cuenta
            account_info = mt5.account_info()
            if account_info is None:
                print("ERROR: Sin informacion de cuenta. Abre MT5 primero.")
                mt5.shutdown()
                return
            
            print(f"CONECTADO: Cuenta {account_info.login} | Balance: ${account_info.balance:.2f}")
            
            # Ciclo principal
            while True:
                corrections = self.monitor_cycle(mt5)
                
                # Estadísticas cada 10 ciclos
                if self.cycle_count % 10 == 0:
                    elapsed = (datetime.now() - self.start_time).total_seconds()
                    print(f"\n--- ESTADISTICAS (Ciclo {self.cycle_count}) ---")
                    print(f"Tiempo transcurrido: {elapsed/60:.1f} minutos")
                    print(f"Correcciones totales: {self.total_corrections}")
                    print(f"Promedio: {self.total_corrections/(elapsed/60):.2f} correcciones/min")
                
                print(f"   Esperando {self.check_interval} segundos...")
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            print(f"\n\nMONITOR DETENIDO")
            print(f"Duracion: {elapsed/60:.1f} minutos")
            print(f"Ciclos ejecutados: {self.cycle_count}")
            print(f"Correcciones totales: {self.total_corrections}")
            
        except Exception as e:
            print(f"\nERROR: {e}")
            import traceback
            traceback.print_exc()
            
        finally:
            try:
                mt5.shutdown()
                print("Conexion MT5 cerrada")
            except:
                pass

def main():
    """Función principal - Ejecuta automáticamente con 30 segundos por defecto"""
    import sys
    
    # Verificar si se pasó un argumento de intervalo
    if len(sys.argv) > 1:
        try:
            interval = int(sys.argv[1])
        except ValueError:
            print("Argumento inválido, usando 30 segundos por defecto")
            interval = 30
    else:
        interval = 30  # Intervalo por defecto
    
    print(f"MONITOR CONTINUO - Iniciando con intervalo de {interval} segundos...")
    print("Presiona Ctrl+C para detener")
    time.sleep(1)
    
    try:
        # Crear y iniciar monitor automáticamente
        monitor = PositionMonitor(check_interval=interval)
        monitor.start_monitoring()
        
    except KeyboardInterrupt:
        print("\nMonitor cancelado por el usuario")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()