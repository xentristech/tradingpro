"""
Test del Emergency Risk Manager v2.0
"""

from EMERGENCY_RISK_MANAGER import EmergencyRiskManager
import MetaTrader5 as mt5

def test_risk_manager():
    print('TESTING EMERGENCY RISK MANAGER...')
    print('=' * 60)

    # Crear instancia del gestor
    risk_manager = EmergencyRiskManager()

    # Conectar a MT5
    if risk_manager.connect_mt5():
        print('\nConexion MT5 exitosa!')
        
        # Obtener posiciones actuales
        positions = mt5.positions_get()
        if positions:
            print(f'\nAnalizando {len(positions)} posiciones actuales...\n')
            
            for position in positions:
                risk_analysis = risk_manager.analyze_position_risk(position)
                
                print(f'Posicion #{risk_analysis["ticket"]}:')
                print(f'  Simbolo: {risk_analysis["symbol"]}')
                print(f'  Tipo: {risk_analysis["type"]}')
                print(f'  Volumen: {risk_analysis["volume"]}')
                print(f'  P&L Actual: ${risk_analysis["current_profit"]:+.2f}')
                print(f'  % Perdida: {risk_analysis["loss_percent"]:.2f}%')
                print(f'  Nivel de Riesgo: {risk_analysis["risk_level"]}')
                print(f'  Debe cerrar: {"SI" if risk_analysis["should_close"] else "NO"}')
                print(f'  Trailing stop: {"SI" if risk_analysis["should_trail"] else "NO"}')
                print()
        else:
            print('No hay posiciones abiertas actualmente')
        
        # Mostrar resumen de riesgo diario
        daily_risk = risk_manager.calculate_daily_risk()
        if daily_risk:
            print('RESUMEN DE RIESGO DIARIO:')
            print(f'  Balance actual: ${daily_risk["current_balance"]:.2f}')
            print(f'  Balance inicial del dia: ${daily_risk["daily_start_balance"]:.2f}')
            print(f'  P&L diario: ${daily_risk["daily_pnl"]:+.2f}')
            print(f'  Drawdown actual: {daily_risk["current_drawdown"]:.2f}%')
            print(f'  Nivel de riesgo: {daily_risk["risk_level"]}')
            print(f'  Posiciones cerradas hoy: {daily_risk["closed_positions_today"]}')
        
        mt5.shutdown()
        
        print('\n' + '=' * 60)
        print('Test completado. El sistema esta listo para monitoreo continuo.')
        print('Use: python EMERGENCY_RISK_MANAGER.py para iniciar monitoreo')
    else:
        print('Error conectando a MT5')

if __name__ == "__main__":
    test_risk_manager()