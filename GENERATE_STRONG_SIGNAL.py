"""
GENERADOR DE SEÑAL DE PRUEBA FUERTE
Genera una señal BUY fuerte para probar el sistema de trading automático
"""

import sys
import os
from pathlib import Path
import time

# Configurar path del proyecto
PROJECT_ROOT = Path(__file__).parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from src.signals.advanced_signal_generator import AdvancedSignalGenerator
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s'
)
logger = logging.getLogger(__name__)

def create_strong_test_signal():
    """
    Crear una señal de prueba fuerte para verificar que el sistema ejecute trades
    """
    
    print("="*70)
    print("          GENERADOR DE SEÑAL DE PRUEBA FUERTE")
    print("="*70)
    print("Objetivo: Generar señal BUY fuerte para probar ejecución automática")
    print("Símbolo objetivo: EURUSD")
    print("Confianza objetivo: 85%")
    print("="*70)
    
    try:
        # Crear generador de señales
        signal_generator = AdvancedSignalGenerator(
            telegram_enabled=True,
            auto_trading=True
        )
        
        print("\n1. Inicializando generador de señales...")
        
        # Verificar conexión MT5
        if not signal_generator.mt5_connection:
            print("   ❌ ERROR: No hay conexión MT5 para trading automático")
            return False
            
        print("   ✅ Conexión MT5 activa")
        
        # Generar señal artificial fuerte para EURUSD
        print("\n2. Generando señal artificial fuerte...")
        
        # Crear señal de prueba directamente
        test_signal = {
            'symbol': 'EURUSD',
            'signal': 'BUY',
            'confidence': 0.85,  # 85% confianza
            'entry_price': 1.1740,  # Precio actual aproximado
            'sl': 1.1720,  # Stop Loss 20 pips
            'tp': 1.1790,  # Take Profit 50 pips
            'volume': 0.01,  # Volumen mínimo para prueba
            'reason': 'SEÑAL DE PRUEBA - Testing sistema automático',
            'source': 'MANUAL_TEST',
            'timestamp': time.time()
        }
        
        print(f"   ✅ Señal generada: {test_signal['signal']} {test_signal['symbol']}")
        print(f"   ✅ Confianza: {test_signal['confidence']*100:.1f}%")
        print(f"   ✅ Entry: {test_signal['entry_price']}")
        print(f"   ✅ SL: {test_signal['sl']} | TP: {test_signal['tp']}")
        
        # Intentar ejecutar la señal usando el sistema de trading automático
        print("\n3. Ejecutando señal con sistema de trading...")
        
        # Usar la función interna de ejecución de señales
        success = signal_generator.execute_signal_with_mt5(test_signal)
        
        if success:
            print("   ✅ SEÑAL EJECUTADA EXITOSAMENTE!")
            print("   ✅ Trade abierto en MT5")
            print("   ✅ Notificación enviada por Telegram")
            
            # Verificar posiciones abiertas
            print("\n4. Verificando posición en MT5...")
            if signal_generator.mt5_connection.connection:
                import MetaTrader5 as mt5
                positions = mt5.positions_get(symbol='EURUSD')
                if positions:
                    latest_pos = positions[-1]  # Última posición
                    print(f"   ✅ Posición encontrada: #{latest_pos.ticket}")
                    print(f"   ✅ Símbolo: {latest_pos.symbol}")
                    print(f"   ✅ Tipo: {'BUY' if latest_pos.type == 0 else 'SELL'}")
                    print(f"   ✅ Volumen: {latest_pos.volume}")
                    print(f"   ✅ Precio entrada: {latest_pos.price_open}")
                else:
                    print("   ⚠️ No se encontró la posición (puede haberse cerrado)")
            
            return True
        else:
            print("   ❌ ERROR: No se pudo ejecutar la señal")
            print("   ❌ Verificar logs para más detalles")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR GENERANDO SEÑAL: {e}")
        logger.error(f"Error en generación de señal: {e}")
        return False

def main():
    """Función principal"""
    
    print("""
    ========================================================================
                    GENERADOR DE SEÑAL DE PRUEBA FUERTE v1.0
    ========================================================================
    
    Este script genera una señal BUY fuerte para EURUSD con 85% de confianza
    para probar que el sistema de trading automático funciona correctamente.
    
    La señal se enviará directamente al sistema de ejecución de MT5.
    
    IMPORTANTE: Esto abrirá una posición real en tu cuenta de trading.
    
    ========================================================================
    """)
    
    # Confirmar ejecución
    response = input("¿Deseas generar y ejecutar la señal de prueba? (s/n): ").lower().strip()
    if response not in ['s', 'si', 'y', 'yes']:
        print("Operación cancelada")
        return
    
    # Generar señal
    success = create_strong_test_signal()
    
    if success:
        print("\n" + "="*70)
        print("✅ PRUEBA EXITOSA - SISTEMA DE TRADING FUNCIONANDO")
        print("✅ Señal ejecutada correctamente")
        print("✅ Trade abierto en MT5")
        print("="*70)
        
        print("\nRevisa:")
        print("- MT5 para ver la nueva posición")
        print("- Telegram para la notificación")
        print("- Logs del sistema para detalles")
        
    else:
        print("\n" + "="*70)
        print("❌ PRUEBA FALLIDA - REVISAR SISTEMA")
        print("❌ La señal no se ejecutó correctamente")
        print("="*70)
        
        print("\nPosibles causas:")
        print("- MT5 no conectado")
        print("- Símbol EURUSD no disponible") 
        print("- Fondos insuficientes")
        print("- Error en validación de trading")

if __name__ == "__main__":
    main()