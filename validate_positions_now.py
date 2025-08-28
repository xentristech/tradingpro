"""
Validación Inmediata de Posiciones - Ejecuta validación manual de operaciones sin SL/TP
"""
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Configurar path del proyecto
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from enhanced_modules.trade_validator import TradeValidator
from notifiers.telegram_notifier import TelegramNotifier
import MetaTrader5 as mt5

async def validate_positions_manually():
    """Ejecuta validación manual inmediata"""
    print("="*60)
    print(" VALIDACION MANUAL DE POSICIONES")
    print("="*60)
    
    # Cargar configuración
    load_dotenv('configs/.env')
    
    # Inicializar componentes
    telegram_notifier = TelegramNotifier() if os.getenv('TELEGRAM_TOKEN') else None
    validator = TradeValidator(
        twelvedata_api_key=os.getenv('TWELVEDATA_API_KEY'),
        telegram_notifier=telegram_notifier
    )
    
    # Inicializar MT5
    if not mt5.initialize():
        print("[ERROR] Error inicializando MT5")
        return
    
    try:
        # Obtener posiciones
        positions = mt5.positions_get()
        if not positions:
            print("[OK] No hay posiciones para validar")
            return
        
        print(f"[INFO] Analizando {len(positions)} posiciones...")
        
        # Validar cada posición
        for pos in positions:
            print(f"\n--- POSICION #{pos.ticket} ---")
            print(f"Symbol: {pos.symbol}")
            print(f"Tipo: {'BUY' if pos.type == 0 else 'SELL'}")
            print(f"SL: {pos.sl if pos.sl != 0 else 'NO CONFIGURADO'}")
            print(f"TP: {pos.tp if pos.tp != 0 else 'NO CONFIGURADO'}")
            
            # Si no tiene SL/TP, validar inmediatamente
            if pos.sl == 0 or pos.tp == 0:
                print("[ALERTA] SIN PROTECCION - Validando con IA...")
                
                try:
                    analysis = await validator._analyze_position(pos)
                    
                    print(f"Viable: {analysis.is_viable}")
                    print(f"Confianza: {analysis.confidence:.1%}")
                    print(f"Recomendacion: {analysis.recommendation}")
                    
                    if analysis.suggested_sl:
                        print(f"SL Sugerido: {analysis.suggested_sl:.5f}")
                    if analysis.suggested_tp:
                        print(f"TP Sugerido: {analysis.suggested_tp:.5f}")
                    
                    # Enviar notificación por Telegram
                    if telegram_notifier and analysis.recommendation != 'KEEP':
                        print("[TELEGRAM] Enviando notificacion por Telegram...")
                        await validator._send_validation_notification(analysis)
                        print("[OK] Notificacion enviada")
                    
                    print("Razones:")
                    for reason in analysis.reasons:
                        print(f"  • {reason}")
                        
                except Exception as e:
                    print(f"[ERROR] Error validando posicion: {e}")
            else:
                print("[OK] Protecciones OK")
        
        print(f"\n{'='*60}")
        print("[COMPLETADO] VALIDACION MANUAL COMPLETADA")
        
        if telegram_notifier:
            print("[INFO] Revisa Telegram para notificaciones y codigos de validacion")
        
        print("[INFO] Comandos disponibles en Telegram:")
        print("   - APPROVE CODIGO - Aplicar SL/TP sugeridos")
        print("   - CLOSE CODIGO - Cerrar posicion")
        print("   - IGNORE CODIGO - Mantener sin cambios")
        print("="*60)
        
    except Exception as e:
        print(f"[ERROR] Error en validacion: {e}")
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    asyncio.run(validate_positions_manually())