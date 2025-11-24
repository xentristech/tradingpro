#!/usr/bin/env python
"""
AI TRADING ASSISTANT - ASISTENTE PERSONAL DE TRADING
=====================================================
Asistente IA conversacional que saluda, analiza señales y mantiene diario de trading
"""

import os
import sys
import time
import json
import MetaTrader5 as mt5
from datetime import datetime, timedelta
from pathlib import Path
import threading
import random

# Configurar encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

class AITradingAssistant:
    """Asistente IA Personal de Trading con Chat Interactivo"""

    def __init__(self):
        self.name = "XentrisBot AI"
        self.company = "XentrisTech"
        self.role = "Programador Senior de Trading Algorítmico"
        self.version = "2.0 Professional"
        self.user_name = None
        self.trading_journal = []
        self.conversation_history = []
        self.mt5_connected = False
        self.current_mood = "optimista"

        # Frases de saludo según hora del día
        self.greetings = {
            'morning': [
                "Buenos días! Soy XentrisBot AI de XentrisTech. Los mercados están activos y mi análisis está corriendo!",
                "Buenos días! XentrisBot AI aquí. Mi sistema está monitoreando 8 pares y detectando velas institucionales.",
                "Buenos días! Soy tu programador de trading de XentrisTech. Listos para cazar señales de entrada?"
            ],
            'afternoon': [
                "Buenas tardes! XentrisBot AI reportando. Mi indicador IVI está escaneando oportunidades.",
                "Buenas tardes! Soy XentrisBot AI de XentrisTech. Los mercados europeos están moviendo, detectando patrones.",
                "Hola! XentrisBot AI aquí. Mi algoritmo está analizando momentum en tiempo real."
            ],
            'evening': [
                "Buenas noches! XentrisBot AI de XentrisTech. Revisando sesión de trading y preparando Asia.",
                "Buenas noches! Soy tu analista de XentrisTech. Mi sistema detectó varios patrones hoy.",
                "Hola! XentrisBot AI reportando. Los mercados asiáticos están por abrir, mi scanner está listo!"
            ]
        }

        # Conectar MT5
        self.connect_mt5()

    def connect_mt5(self):
        """Conectar a MT5"""
        try:
            if mt5.initialize():
                account = mt5.account_info()
                if account:
                    self.mt5_connected = True
                    self.account_balance = account.balance
                    self.account_profit = account.profit
                    return True
        except:
            pass
        return False

    def get_time_greeting(self):
        """Obtener saludo según hora del día"""
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return random.choice(self.greetings['morning'])
        elif 12 <= hour < 19:
            return random.choice(self.greetings['afternoon'])
        else:
            return random.choice(self.greetings['evening'])

    def analyze_current_signals(self):
        """Analizar señales actuales del mercado"""
        signals_summary = {
            'strong_signals': [],
            'moderate_signals': [],
            'market_sentiment': 'NEUTRAL',
            'best_opportunity': None
        }

        if self.mt5_connected:
            # Analizar posiciones abiertas
            positions = mt5.positions_get()
            if positions:
                signals_summary['open_positions'] = len(positions)
                total_profit = sum(p.profit for p in positions)
                signals_summary['total_profit'] = total_profit

                if total_profit > 0:
                    signals_summary['market_sentiment'] = 'POSITIVO'
                    self.current_mood = "optimista"
                else:
                    signals_summary['market_sentiment'] = 'CAUTELOSO'
                    self.current_mood = "cauteloso"

            # Simular análisis de señales
            symbols = ['EURUSD', 'GBPUSD', 'XAUUSD', 'BTCUSD']
            for symbol in symbols:
                # Simulación de análisis
                strength = random.randint(40, 95)
                if strength > 80:
                    signals_summary['strong_signals'].append({
                        'symbol': symbol,
                        'direction': random.choice(['BUY', 'SELL']),
                        'strength': strength
                    })
                elif strength > 60:
                    signals_summary['moderate_signals'].append({
                        'symbol': symbol,
                        'direction': random.choice(['BUY', 'SELL']),
                        'strength': strength
                    })

            if signals_summary['strong_signals']:
                best = max(signals_summary['strong_signals'], key=lambda x: x['strength'])
                signals_summary['best_opportunity'] = best

        return signals_summary

    def add_journal_entry(self, entry_type, content):
        """Agregar entrada al diario de trading"""
        entry = {
            'timestamp': datetime.now(),
            'type': entry_type,
            'content': content,
            'balance': self.account_balance if self.mt5_connected else 0,
            'mood': self.current_mood
        }
        self.trading_journal.append(entry)

        # Guardar en archivo
        self.save_journal()

    def save_journal(self):
        """Guardar diario en archivo"""
        try:
            journal_file = project_dir / 'trading_journal.json'
            journal_data = []

            for entry in self.trading_journal[-100:]:  # Últimas 100 entradas
                journal_data.append({
                    'timestamp': entry['timestamp'].isoformat(),
                    'type': entry['type'],
                    'content': entry['content'],
                    'balance': entry['balance'],
                    'mood': entry['mood']
                })

            with open(journal_file, 'w', encoding='utf-8') as f:
                json.dump(journal_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error guardando diario: {e}")

    def load_journal(self):
        """Cargar diario desde archivo"""
        try:
            journal_file = project_dir / 'trading_journal.json'
            if journal_file.exists():
                with open(journal_file, 'r', encoding='utf-8') as f:
                    journal_data = json.load(f)

                for entry in journal_data:
                    self.trading_journal.append({
                        'timestamp': datetime.fromisoformat(entry['timestamp']),
                        'type': entry['type'],
                        'content': entry['content'],
                        'balance': entry['balance'],
                        'mood': entry['mood']
                    })
                return True
        except:
            pass
        return False

    def chat_response(self, user_input):
        """Generar respuesta conversacional"""
        response = ""
        user_input_lower = user_input.lower()

        # Respuestas contextuales
        if any(word in user_input_lower for word in ['hola', 'hi', 'hey', 'buenos']):
            response = f"Hola {self.user_name}! Qué gusto verte! Cómo te sientes hoy?"

        elif any(word in user_input_lower for word in ['señal', 'signal', 'oportunidad']):
            signals = self.analyze_current_signals()
            if signals['best_opportunity']:
                opp = signals['best_opportunity']
                response = f"Tengo una señal fuerte! {opp['symbol']} muestra {opp['direction']} con {opp['strength']}% de confianza. Quieres que la ejecute?"
            else:
                response = "Por ahora no veo señales fuertes, pero sigo monitoreando. El mercado está tranquilo."

        elif any(word in user_input_lower for word in ['balance', 'dinero', 'cuenta', 'profit']):
            if self.mt5_connected:
                response = f"Tu balance actual es ${self.account_balance:.2f}. "
                if self.account_profit > 0:
                    response += f"Vas ganando ${self.account_profit:.2f} hoy! Excelente trabajo!"
                else:
                    response += f"Ten paciencia, las mejores oportunidades están por venir."
            else:
                response = "No puedo ver tu balance ahora, pero recuerda: el éxito en trading es consistencia!"

        elif any(word in user_input_lower for word in ['consejo', 'tip', 'ayuda', 'sugerencia']):
            tips = [
                "Recuerda siempre usar stop loss. Es tu mejor amigo en el trading!",
                "No arriesgues más del 2% de tu capital en una sola operación.",
                "La paciencia es clave. Espera las mejores oportunidades.",
                "Mantén un diario de trading. Te ayudará a mejorar!",
                "Las emociones son el enemigo del trader. Mantén la calma.",
                "Sigue tu plan de trading, no improvises.",
                "El mercado siempre estará ahí mañana. No te apresures."
            ]
            response = random.choice(tips)

        elif any(word in user_input_lower for word in ['cansado', 'mal', 'perdida', 'triste']):
            response = f"Lo siento {self.user_name}. El trading puede ser difícil a veces. "
            response += "Recuerda que las pérdidas son parte del aprendizaje. "
            response += "Tómate un descanso si lo necesitas. Tu bienestar es lo más importante!"
            self.current_mood = "comprensivo"

        elif any(word in user_input_lower for word in ['bien', 'ganando', 'profit', 'feliz', 'excelente']):
            response = f"Me alegra mucho escuchar eso {self.user_name}! "
            response += "Sigue así! La consistencia es la clave del éxito. "
            response += "Celebra tus victorias pero mantén los pies en la tierra!"
            self.current_mood = "alegre"

        elif any(word in user_input_lower for word in ['diario', 'journal', 'registro']):
            if self.trading_journal:
                last_entry = self.trading_journal[-1]
                response = f"Tu última entrada fue: {last_entry['content']}\n"
                response += "Quieres agregar algo nuevo al diario?"
            else:
                response = "Tu diario está vacío. Qué te gustaría registrar hoy?"

        elif any(word in user_input_lower for word in ['salir', 'adios', 'bye', 'exit']):
            response = f"Hasta luego {self.user_name}! Fue un placer conversar contigo. "
            response += "Que tengas excelentes trades! Nos vemos pronto!"

        else:
            # Respuesta genérica inteligente
            responses = [
                "Interesante lo que dices. Cuéntame más sobre eso.",
                "Entiendo. Cómo te hace sentir eso en tu trading?",
                "Eso es importante. Has considerado cómo afecta tu estrategia?",
                f"Comprendo {self.user_name}. Qué más tienes en mente?",
                "Me gusta tu forma de pensar. Sigamos analizando juntos."
            ]
            response = random.choice(responses)

        # Agregar a historial
        self.conversation_history.append({
            'user': user_input,
            'assistant': response,
            'timestamp': datetime.now()
        })

        return response

    def start_interactive_session(self):
        """Iniciar sesión interactiva con el usuario"""
        # Limpiar pantalla
        os.system('cls' if os.name == 'nt' else 'clear')

        # Banner de bienvenida
        print("=" * 80)
        print("       🤖 AI TRADING ASSISTANT - TU ASISTENTE PERSONAL DE TRADING 🤖")
        print("=" * 80)

        # Saludo inicial
        print(f"\n{self.get_time_greeting()}\n")

        # Pedir nombre si es primera vez
        if not self.user_name:
            print("Soy tu asistente de trading con IA. Cómo te llamas?")
            self.user_name = input("Tu nombre: ").strip()
            if not self.user_name:
                self.user_name = "Trader"

            self.add_journal_entry('LOGIN', f"Sesión iniciada por {self.user_name}")

        print(f"\nHola {self.user_name}! 👋")
        time.sleep(1)

        # Estado inicial
        print("\n📊 Déjame revisar cómo están tus señales de trading...")
        time.sleep(2)

        signals = self.analyze_current_signals()

        print("\n📈 RESUMEN DE MERCADO:")
        print(f"   Sentimiento: {signals['market_sentiment']}")

        if self.mt5_connected:
            print(f"   Balance: ${self.account_balance:.2f}")
            if 'open_positions' in signals:
                print(f"   Posiciones abiertas: {signals['open_positions']}")
                if 'total_profit' in signals:
                    profit_emoji = "✅" if signals['total_profit'] > 0 else "⚠️"
                    print(f"   P&L Total: {profit_emoji} ${signals['total_profit']:.2f}")

        if signals['strong_signals']:
            print(f"\n🔥 SEÑALES FUERTES DETECTADAS:")
            for sig in signals['strong_signals'][:3]:
                print(f"   • {sig['symbol']}: {sig['direction']} ({sig['strength']}%)")

        if signals['best_opportunity']:
            best = signals['best_opportunity']
            print(f"\n⭐ MEJOR OPORTUNIDAD: {best['symbol']} {best['direction']} ({best['strength']}%)")

        print("\n" + "=" * 80)
        print("💬 CHAT INTERACTIVO INICIADO")
        print("Puedes preguntarme sobre:")
        print("  • Señales y oportunidades de trading")
        print("  • Tu balance y rendimiento")
        print("  • Consejos y estrategias")
        print("  • Agregar notas a tu diario de trading")
        print("  • O simplemente conversar!")
        print("\nEscribe 'salir' para terminar la sesión")
        print("=" * 80)

        # Loop de conversación
        while True:
            try:
                print(f"\n{self.user_name} > ", end="")
                user_input = input().strip()

                if not user_input:
                    continue

                # Verificar salida
                if user_input.lower() in ['salir', 'exit', 'quit', 'bye']:
                    response = self.chat_response(user_input)
                    print(f"\n🤖 {self.name}: {response}")

                    # Guardar sesión
                    self.add_journal_entry('LOGOUT', f"Sesión finalizada - Estado: {self.current_mood}")
                    break

                # Procesar entrada para diario
                if user_input.lower().startswith('diario:') or user_input.lower().startswith('journal:'):
                    journal_content = user_input.split(':', 1)[1].strip()
                    self.add_journal_entry('USER_NOTE', journal_content)
                    print(f"\n🤖 {self.name}: He agregado eso a tu diario de trading!")
                    continue

                # Generar respuesta
                response = self.chat_response(user_input)

                # Mostrar respuesta con animación
                print(f"\n🤖 {self.name}: ", end="")
                for char in response:
                    print(char, end="", flush=True)
                    time.sleep(0.02)  # Efecto de escritura
                print()

                # Actualizar señales periódicamente
                if len(self.conversation_history) % 5 == 0:
                    print("\n[Actualizando señales en segundo plano...]")
                    signals = self.analyze_current_signals()

                    if signals['best_opportunity'] and random.random() > 0.7:
                        opp = signals['best_opportunity']
                        print(f"\n⚡ ALERTA: Nueva señal fuerte detectada!")
                        print(f"   {opp['symbol']} {opp['direction']} ({opp['strength']}%)")

            except KeyboardInterrupt:
                print("\n\n👋 Hasta luego! Sesión interrumpida.")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                continue

        # Despedida final
        print("\n" + "=" * 80)
        print("📊 RESUMEN DE TU SESIÓN:")
        print(f"   Mensajes intercambiados: {len(self.conversation_history)}")
        print(f"   Entradas en diario: {len(self.trading_journal)}")
        print(f"   Estado emocional: {self.current_mood}")

        if self.mt5_connected:
            mt5.shutdown()

        print("\n✨ Gracias por usar AI Trading Assistant!")
        print("Que tengas excelentes trades! 📈")
        print("=" * 80)

def main():
    """Función principal"""
    # Cargar diario previo si existe
    assistant = AITradingAssistant()
    assistant.load_journal()

    try:
        # Iniciar sesión interactiva
        assistant.start_interactive_session()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # Guardar estado
        assistant.save_journal()

if __name__ == "__main__":
    main()