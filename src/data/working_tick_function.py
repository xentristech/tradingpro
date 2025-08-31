
def get_working_tick_data(symbol, count=100):
    """Función que realmente funciona con MT5"""
    try:
        if not mt5.initialize():
            return None
        
        # Método 1: Usar symbol_info_tick para datos actuales
        current_tick = mt5.symbol_info_tick(symbol)
        
        if current_tick:
            print(f"Tick actual {symbol}: Bid {current_tick.bid}, Ask {current_tick.ask}")
        
        # Método 2: Usar copy_rates para simular ticks desde barras M1
        rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, count)
        
        if rates is not None and len(rates) > 0:
            # Convertir barras a "ticks" simulados
            simulated_ticks = []
            
            for rate in rates:
                # Crear tick simulado desde datos OHLC
                tick = {
                    'time': rate['time'],
                    'bid': rate['close'] - 0.00005,  # Aproximar bid
                    'ask': rate['close'] + 0.00005,  # Aproximar ask
                    'volume': rate['tick_volume'],
                    'flags': 0,
                    'close': rate['close']
                }
                simulated_ticks.append(tick)
            
            return simulated_ticks
        
        return None
        
    except Exception as e:
        print(f"Error: {e}")
        return None
