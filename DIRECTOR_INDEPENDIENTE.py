#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
DIRECTOR DE OPERACIONES INDEPENDIENTE
====================================
Ejecuta el Director en paralelo al sistema principal
Analiza posiciones cada 30 segundos y genera logs detallados
"""

import time
import logging
from datetime import datetime
from pathlib import Path
import sys

# Configurar logging específico del Director
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Logger específico del Director
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - DIRECTOR - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'director_operations.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('director')

def main():
    print("=" * 60)
    print("    DIRECTOR DE OPERACIONES - MODO INDEPENDIENTE")
    print("=" * 60)
    print(f"Inicio: {datetime.now().strftime('%H:%M:%S')}")
    print()
    
    # Importar dependencias
    project_root = Path(__file__).parent
    sys.path.append(str(project_root))
    
    try:
        from src.director.operations_director import OperationsDirector
        from src.utils.trade_history_logger import trade_logger
        
        print("Inicializando Director...")
        director = OperationsDirector()
        logger.info("Director de Operaciones iniciado de forma independiente")
        
        print("CONFIGURACION:")
        print("- Analisis cada: 30 segundos")
        print("- Log detallado: logs/director_operations.log")
        print("- Historial backtesting: Activado")
        print("- Telegram: Activado")
        print()
        print("Presiona Ctrl+C para detener")
        print("-" * 40)
        
        cycle_count = 0
        
        while True:
            try:
                cycle_count += 1
                timestamp = datetime.now().strftime('%H:%M:%S')
                
                print(f"[DIRECTOR #{cycle_count:03d}] {timestamp} - Analizando operaciones...")
                logger.info(f"Ciclo #{cycle_count} - Iniciando analisis de operaciones")
                
                # Ejecutar análisis del Director
                results = director.analyze_single_cycle()
                
                if results.get('total_positions', 0) > 0:
                    total_pos = results['total_positions']
                    adjustments = results.get('tp_adjustments', 0)
                    
                    print(f"  -> {total_pos} posiciones analizadas")
                    logger.info(f"Posiciones analizadas: {total_pos}")
                    
                    if adjustments > 0:
                        print(f"  -> AJUSTES TP REALIZADOS: {adjustments}")
                        logger.info(f"TP ajustados: {adjustments}")
                        
                        # Log detallado de cada ajuste
                        for adjustment in results.get('adjustments_details', []):
                            ticket = adjustment.get('ticket', 'N/A')
                            adj_type = adjustment.get('type', 'N/A')
                            old_tp = adjustment.get('old_tp', 0)
                            new_tp = adjustment.get('new_tp', 0)
                            reason = adjustment.get('reason', 'N/A')
                            
                            print(f"    * {ticket}: {adj_type} | {old_tp:.5f} -> {new_tp:.5f}")
                            print(f"      Razon: {reason}")
                            
                            logger.info(
                                f"AJUSTE: Ticket {ticket} | {adj_type} | "
                                f"TP: {old_tp:.5f} -> {new_tp:.5f} | Razon: {reason}"
                            )
                            
                            # Registrar para backtesting
                            trade_logger.log_tp_adjustment({
                                'ticket': ticket,
                                'symbol': adjustment.get('symbol', ''),
                                'adjustment_type': adj_type,
                                'old_tp': old_tp,
                                'new_tp': new_tp,
                                'reason': reason,
                                'ai_analysis': adjustment.get('ai_analysis', ''),
                                'market_analysis': adjustment.get('market_data', {}),
                                'current_price': adjustment.get('current_price', 0)
                            })
                    else:
                        print(f"  -> Sin ajustes necesarios")
                        logger.debug("No se requieren ajustes TP")
                        
                else:
                    print(f"  -> No hay posiciones activas")
                    logger.debug("No hay posiciones para analizar")
                
                # Esperar 30 segundos
                print(f"  -> Proximo analisis en 30s...")
                print()
                time.sleep(30)
                
            except KeyboardInterrupt:
                print()
                print("Director detenido por usuario")
                logger.info("Director detenido por usuario")
                break
                
            except Exception as e:
                print(f"  -> ERROR: {e}")
                logger.error(f"Error en ciclo {cycle_count}: {e}")
                print(f"  -> Continuando en 30s...")
                time.sleep(30)
                
    except ImportError as e:
        print(f"ERROR: No se pudo importar Director: {e}")
        print("Verifica que src/director/operations_director.py exista")
        
    except Exception as e:
        print(f"ERROR: {e}")
        logger.error(f"Error critico: {e}")
        
    finally:
        print("Director finalizado")

if __name__ == "__main__":
    main()