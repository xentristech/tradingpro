#!/usr/bin/env python
"""
EJECUTAR ESCANEO RAPIDO DE OPORTUNIDADES
========================================
"""

from AI_OPPORTUNITY_HUNTER import AIOpportunityHunter
import time

print('🔍 AI OPPORTUNITY HUNTER - ESCANEO RAPIDO')
print('=' * 60)

hunter = AIOpportunityHunter()
opportunities = hunter.run_opportunity_hunt()

print(f'\n📊 RESULTADOS DEL ESCANEO:')
print(f'   Oportunidades encontradas: {len(opportunities)}')

if opportunities:
    best_opp = hunter.get_best_opportunity()
    if best_opp:
        print(f'\n🏆 MEJOR OPORTUNIDAD:')
        print(f'   Symbol: {best_opp["symbol"]}')
        print(f'   Score IA: {best_opp["score"]}%')
        print(f'   Tipo: {best_opp["type"]}')
        print(f'   Direccion: {best_opp["direction"]}')
        print(f'   Precio: ${best_opp["current_price"]:,.2f}')
        print(f'   RSI: {best_opp["rsi"]:.1f}')
        print(f'   Volatilidad: {best_opp["volatility"]:.1f}%')
        print(f'   Riesgo: {best_opp["risk_level"]}/10')
        print(f'   Recomendacion: {best_opp["recommendation"]}')
    
    # Mostrar top 3 oportunidades
    print(f'\n📈 TOP 3 OPORTUNIDADES:')
    for i, opp in enumerate(opportunities[:3], 1):
        direction_icon = '📈' if opp['direction'] == 'ALCISTA' else '📉'
        risk_icon = '🟢' if opp['risk_level'] <= 3 else '🟡' if opp['risk_level'] <= 6 else '🔴'
        print(f'   {i}. {direction_icon} {opp["symbol"]} - Score: {opp["score"]}% {risk_icon}')
        print(f'      ${opp["current_price"]:,.2f} ({opp["price_change"]:+.2f}%) | {opp["type"]}')
else:
    print('   ❌ No se encontraron oportunidades en este ciclo')

print('\n🔄 Para monitoreo continuo, ejecutar el sistema completo')