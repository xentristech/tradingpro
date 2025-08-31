#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DETECTOR SIMPLE DE POSICIONES ABIERTAS EN MT5
Conecta directamente a MT5 y muestra todas las posiciones
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Configurar encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Configurar path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

def detect_positions():
    print("=" * 70)
    print("         DETECTOR DE POSICIONES ABIERTAS MT5")
    print("=" * 70)
    print(f"Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        import MetaTrader5 as mt5
        
        print("1. Conectando con MT5...")
        
        # Inicializar MT5 (usa la sesión activa)
        if not mt5.initialize():
            error_info = mt5.last_error()
            print(f"   ERROR inicializando MT5: {error_info}")
            print("   SOLUCION: Asegúrate de que MT5 esté abierto y logueado")
            return
        
        # Obtener información de cuenta
        account_info = mt5.account_info()
        if account_info is None:
            print("   ERROR: No se puede obtener información de cuenta")
            print("   SOLUCION: Verifica que estés logueado en MT5")
            mt5.shutdown()
            return
        
        print(f"   [OK] MT5 conectado exitosamente")
        print(f"   Cuenta: {account_info.login}")
        print(f"   Servidor: {account_info.server}")
        print(f"   Balance: ${account_info.balance:.2f}")
        print(f"   Equity: ${account_info.equity:.2f}")
        print()
        
        print("2. Escaneando posiciones abiertas...")
        
        # Obtener todas las posiciones
        positions = mt5.positions_get()
        
        if not positions:
            print("   [INFO] No se encontraron posiciones abiertas")
            print("   Para probar: Abre una posición manualmente en MT5 sin SL/TP")
        else:
            print(f"   [FOUND] {len(positions)} posiciones encontradas")
            print()
            
            positions_without_protection = 0
            
            for i, position in enumerate(positions, 1):
                symbol = position.symbol
                ticket = position.ticket
                pos_type = "BUY" if position.type == 0 else "SELL"
                volume = position.volume
                entry_price = position.price_open
                current_price = position.price_current
                profit = position.profit
                
                # Verificar protección
                has_sl = position.sl != 0.0
                has_tp = position.tp != 0.0
                
                print(f"   --- POSICION #{i} ---")
                print(f"   Simbolo: {symbol}")
                print(f"   Ticket: #{ticket}")
                print(f"   Tipo: {pos_type}")
                print(f"   Volumen: {volume} lotes")
                print(f"   Precio Entrada: {entry_price:.5f}")
                print(f"   Precio Actual: {current_price:.5f}")
                print(f"   P&L: {profit:.2f} USD")
                
                # Estado de protección
                if has_sl:
                    print(f"   Stop Loss: {position.sl:.5f} [OK]")
                else:
                    print(f"   Stop Loss: NO CONFIGURADO [RIESGO]")
                
                if has_tp:
                    print(f"   Take Profit: {position.tp:.5f} [OK]")
                else:
                    print(f"   Take Profit: NO CONFIGURADO [RIESGO]")
                
                # ¿Necesita corrección?
                needs_correction = not has_sl or not has_tp
                
                if needs_correction:
                    positions_without_protection += 1
                    print(f"   *** ALERTA: POSICION SIN PROTECCION COMPLETA ***")
                    
                    # Calcular SL/TP recomendados (simple)
                    try:
                        atr_estimated = entry_price * 0.015  # 1.5% ATR estimado
                        
                        if pos_type == 'BUY':
                            rec_sl = entry_price - (atr_estimated * 2.0)
                            rec_tp = entry_price + (atr_estimated * 3.0)
                        else:  # SELL
                            rec_sl = entry_price + (atr_estimated * 2.0)
                            rec_tp = entry_price - (atr_estimated * 3.0)
                        
                        atr = atr_estimated
                        
                        print(f"   RECOMENDADO:")
                        if not has_sl:
                            print(f"   - Stop Loss: {rec_sl:.5f}")
                        if not has_tp:
                            print(f"   - Take Profit: {rec_tp:.5f}")
                        print(f"   - ATR usado: {atr:.5f}")
                        print(f"   - Riesgo/Beneficio: 2:3 ATR")
                        
                    except Exception as e:
                        print(f"   Error calculando recomendaciones: {e}")
                else:
                    print(f"   [OK] Posicion protegida correctamente")
                
                print()
            
            # Resumen final
            print("=" * 70)
            print("                        RESUMEN")
            print("=" * 70)
            print(f"Total posiciones: {len(positions)}")
            print(f"Sin proteccion: {positions_without_protection}")
            print(f"Protegidas: {len(positions) - positions_without_protection}")
            
            if positions_without_protection > 0:
                print(f"\n*** ATENCION: {positions_without_protection} posiciones SIN PROTECCION ***")
                print("Para activar corrección automática, configura credenciales en configs/.env")
                print("y ejecuta: python START_TRADING_SYSTEM.py")
            else:
                print("\n[OK] Todas las posiciones están protegidas")
        
        # Cerrar MT5
        mt5.shutdown()
        
    except ImportError:
        print("   ERROR: MetaTrader5 library no encontrada")
        print("   SOLUCION: pip install MetaTrader5")
        
    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    detect_positions()