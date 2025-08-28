"""
Verificador de SL/TP - Revisa específicamente Stop Loss y Take Profit
"""
import MetaTrader5 as mt5
from datetime import datetime

def check_sl_tp_status():
    """Verifica el estado de SL/TP de todas las posiciones"""
    
    if not mt5.initialize():
        print("❌ Error inicializando MT5")
        return
    
    try:
        positions = mt5.positions_get()
        
        if not positions:
            print("✅ No hay posiciones abiertas")
            return
        
        print("="*70)
        print(" ANÁLISIS DETALLADO DE SL/TP")
        print("="*70)
        print(f"Fecha/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total posiciones: {len(positions)}")
        print()
        
        problems_found = 0
        
        for i, pos in enumerate(positions, 1):
            print(f"[{i}] POSICIÓN #{pos.ticket}")
            print(f"    Symbol: {pos.symbol}")
            print(f"    Tipo: {'BUY' if pos.type == 0 else 'SELL'}")
            print(f"    Volumen: {pos.volume}")
            print(f"    Precio apertura: {pos.price_open}")
            print(f"    Precio actual: {pos.price_current}")
            print(f"    P&L: ${pos.profit:.2f}")
            print(f"    Tiempo apertura: {datetime.fromtimestamp(pos.time)}")
            
            # Verificar SL
            if pos.sl == 0:
                print(f"    ❌ STOP LOSS: NO CONFIGURADO")
                problems_found += 1
            else:
                print(f"    ✅ STOP LOSS: {pos.sl}")
            
            # Verificar TP
            if pos.tp == 0:
                print(f"    ❌ TAKE PROFIT: NO CONFIGURADO")
                problems_found += 1
            else:
                print(f"    ✅ TAKE PROFIT: {pos.tp}")
            
            # Calcular distancia a SL/TP si existen
            if pos.sl != 0:
                sl_distance = abs(pos.price_current - pos.sl)
                sl_pips = sl_distance * (10000 if 'JPY' not in pos.symbol else 100)
                print(f"    📏 Distancia SL: {sl_pips:.1f} pips (${sl_distance * pos.volume * 100000:.2f})")
            
            if pos.tp != 0:
                tp_distance = abs(pos.tp - pos.price_current)
                tp_pips = tp_distance * (10000 if 'JPY' not in pos.symbol else 100)
                print(f"    🎯 Distancia TP: {tp_pips:.1f} pips (${tp_distance * pos.volume * 100000:.2f})")
            
            print("-" * 50)
        
        print("\n" + "="*70)
        print(" RESUMEN")
        print("="*70)
        
        if problems_found > 0:
            print(f"❌ PROBLEMAS ENCONTRADOS: {problems_found}")
            print("🔥 OPERACIONES SIN PROTECCIÓN DETECTADAS")
            print("⚠️  ACCIÓN REQUERIDA INMEDIATA")
        else:
            print("✅ TODAS LAS POSICIONES TIENEN SL/TP CONFIGURADOS")
            print("🛡️  PROTECCIONES COMPLETAS")
        
        print("="*70)
        
        return problems_found
        
    except Exception as e:
        print(f"❌ Error verificando posiciones: {e}")
        return -1
    finally:
        mt5.shutdown()

if __name__ == "__main__":
    problems = check_sl_tp_status()
    
    if problems > 0:
        print(f"\n🚨 ALERTA: {problems} problemas de protección encontrados")
        print("💡 El AI Trade Monitor debería estar gestionando esto...")
    elif problems == 0:
        print("\n✅ Todo correcto - Posiciones protegidas")
    else:
        print("\n❌ Error en verificación")