"""
Fix para aplicar SL/TP a posiciones sin protección
Soluciona el error de aplicación de SL/TP
"""
import MetaTrader5 as mt5
from datetime import datetime
import time

def fix_sl_tp_for_position(position):
    """Aplica SL/TP a una posición específica"""
    symbol = position.symbol
    ticket = position.ticket
    
    # Obtener información del símbolo
    symbol_info = mt5.symbol_info(symbol)
    if not symbol_info:
        print(f"❌ No se pudo obtener info de {symbol}")
        return False
    
    # Calcular SL y TP basados en el precio actual
    point = symbol_info.point
    price = position.price_open
    
    if position.type == mt5.ORDER_TYPE_BUY:
        # Para compra
        sl = price - (100 * point)  # 100 pips abajo
        tp = price + (200 * point)  # 200 pips arriba
    else:
        # Para venta
        sl = price + (100 * point)  # 100 pips arriba
        tp = price - (200 * point)  # 200 pips abajo
    
    # Normalizar precios según los dígitos del símbolo
    digits = symbol_info.digits
    sl = round(sl, digits)
    tp = round(tp, digits)
    
    # Preparar la solicitud
    request = {
        "action": mt5.TRADE_ACTION_SLTP,
        "symbol": symbol,
        "position": ticket,
        "sl": sl,
        "tp": tp,
        "magic": 234000,
        "comment": "Fix SL/TP by script"
    }
    
    print(f"\nAplicando SL/TP a posición #{ticket} ({symbol}):")
    print(f"  Precio apertura: {price}")
    print(f"  Stop Loss: {sl}")
    print(f"  Take Profit: {tp}")
    
    # Enviar la orden
    result = mt5.order_send(request)
    
    if result.retcode == mt5.TRADE_RETCODE_DONE:
        print(f"✅ SL/TP aplicado exitosamente")
        return True
    else:
        print(f"❌ Error aplicando SL/TP: {result.retcode}")
        print(f"   Comentario: {result.comment}")
        
        # Diagnóstico de errores comunes
        if result.retcode == 10016:
            print("   📝 Error 10016: Niveles de SL/TP inválidos")
            print("   Verificar stops mínimos del broker")
        elif result.retcode == 10014:
            print("   📝 Error 10014: Volumen inválido")
        elif result.retcode == 10019:
            print("   📝 Error 10019: No hay suficiente dinero")
        
        return False

def main():
    print("""
    ╔════════════════════════════════════════════════════════════╗
    ║           FIX AUTOMÁTICO DE SL/TP                         ║
    ║     Aplica Stop Loss y Take Profit a posiciones           ║
    ╚════════════════════════════════════════════════════════════╝
    """)
    
    # Inicializar MT5
    if not mt5.initialize():
        print("❌ No se pudo inicializar MT5")
        return
    
    # Obtener información de la cuenta
    account_info = mt5.account_info()
    if account_info:
        print(f"\n📊 Cuenta conectada:")
        print(f"   Login: {account_info.login}")
        print(f"   Servidor: {account_info.server}")
        print(f"   Balance: ${account_info.balance:.2f}")
    
    # Obtener posiciones
    positions = mt5.positions_get()
    
    if not positions:
        print("\n✅ No hay posiciones abiertas")
        return
    
    print(f"\n📈 Posiciones encontradas: {len(positions)}")
    
    positions_to_fix = []
    
    # Identificar posiciones sin SL/TP
    for pos in positions:
        needs_fix = False
        status = []
        
        if pos.sl == 0:
            status.append("Sin SL")
            needs_fix = True
        else:
            status.append(f"SL: {pos.sl}")
            
        if pos.tp == 0:
            status.append("Sin TP")
            needs_fix = True
        else:
            status.append(f"TP: {pos.tp}")
        
        print(f"\n#{pos.ticket} {pos.symbol}:")
        print(f"   Volumen: {pos.volume}")
        print(f"   Profit: ${pos.profit:.2f}")
        print(f"   Estado: {', '.join(status)}")
        
        if needs_fix:
            positions_to_fix.append(pos)
            print(f"   ⚠️ NECESITA CORRECCIÓN")
    
    # Aplicar correcciones
    if positions_to_fix:
        print(f"\n{'='*60}")
        print(f"APLICANDO CORRECCIONES A {len(positions_to_fix)} POSICIONES")
        print("="*60)
        
        fixed = 0
        failed = 0
        
        for pos in positions_to_fix:
            if fix_sl_tp_for_position(pos):
                fixed += 1
            else:
                failed += 1
            time.sleep(1)  # Pequeña pausa entre operaciones
        
        print(f"\n{'='*60}")
        print("RESUMEN:")
        print(f"✅ Corregidas: {fixed}")
        print(f"❌ Fallidas: {failed}")
    else:
        print("\n✅ Todas las posiciones tienen SL/TP configurado")
    
    # Cerrar MT5
    mt5.shutdown()

if __name__ == "__main__":
    main()
    input("\nPresiona Enter para salir...")
