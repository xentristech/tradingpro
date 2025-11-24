#!/usr/bin/env python
"""
QUANTUM TRADING SYSTEM - Sistema Completo de Trading Cuántico
==============================================================
Sistema profesional que integra:
✅ TwelveData API (datos limpios de mercado)
✅ Quantum Action Core (indicador basado en física)
✅ Ollama AI (validación inteligente)
✅ MetaTrader 5 (ejecución automática)
✅ Multi-timeframe analysis
✅ Auto-scaling por régimen
✅ 4 modos de Trailing Stop
✅ Risk management profesional

Autor: Xentristech Trading AI
Fecha: 2025-01-16
Version: 1.0.0
"""

import os
import sys
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv

# Configurar encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Cargar variables de entorno
load_dotenv()

# Agregar path del proyecto
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

# Imports del sistema cuántico
from src.signals.quantum_core import QuantumCore, MarketRegime, TrailingMode
from src.signals.quantum_signal_generator import QuantumSignalGenerator, QuantumAnalysis
from src.trading.quantum_mt5_executor import QuantumMT5Executor


class QuantumTradingSystem:
    """
    Sistema Completo de Trading Cuántico

    Arquitectura:
    ┌──────────────┐
    │  TwelveData  │ ← Datos limpios de mercado
    └──────┬───────┘
           ↓
    ┌──────────────┐
    │ Quantum Core │ ← Cálculo de Acción A(t), Niveles, Bandas
    └──────┬───────┘
           ↓
    ┌──────────────┐
    │  Ollama AI   │ ← Validación inteligente
    └──────┬───────┘
           ↓
    ┌──────────────┐
    │  MT5 Executor│ ← Trading automático
    └──────────────┘
    """

    def __init__(
        self,
        symbols: List[str] = None,
        trading_enabled: bool = False,
        use_ai_validation: bool = True,
        multi_timeframe: bool = True,
        auto_scaling: bool = True,
        cycle_interval: int = 60
    ):
        """
        Inicializar Sistema Cuántico

        Args:
            symbols: Lista de símbolos a operar
            trading_enabled: Activar trading automático
            use_ai_validation: Validar con Ollama
            multi_timeframe: Análisis multi-timeframe
            auto_scaling: Auto-scaling por régimen
            cycle_interval: Intervalo de ciclos (segundos)
        """
        self.symbols = symbols or [
            'BTC/USD',
            'ETH/USD',
            'EUR/USD',
            'GBP/USD',
            'XAU/USD'
        ]
        self.trading_enabled = trading_enabled
        self.cycle_interval = cycle_interval

        # Componentes del sistema
        self.signal_generator = QuantumSignalGenerator(
            use_ai_validation=use_ai_validation,
            multi_timeframe=multi_timeframe,
            auto_scaling=auto_scaling
        )

        if self.trading_enabled:
            self.executor = QuantumMT5Executor(
                default_lot=0.01,
                use_breakeven=True,
                use_trailing=True
            )
        else:
            self.executor = None

        # Estadísticas
        self.cycles_run = 0
        self.signals_generated = 0
        self.positions_opened = 0

        self.logger = logging.getLogger(__name__)
        self.logger.info("="*70)
        self.logger.info("QUANTUM TRADING SYSTEM INITIALIZED")
        self.logger.info("="*70)
        self.logger.info(f"Symbols: {', '.join(self.symbols)}")
        self.logger.info(f"Trading: {'ENABLED' if trading_enabled else 'DISABLED (ANALYSIS ONLY)'}")
        self.logger.info(f"AI Validation: {use_ai_validation}")
        self.logger.info(f"Multi-Timeframe: {multi_timeframe}")
        self.logger.info(f"Auto-Scaling: {auto_scaling}")
        self.logger.info("="*70)


    def analyze_market(self) -> Dict[str, QuantumAnalysis]:
        """
        Analizar el mercado completo

        Returns:
            Dict {symbol: QuantumAnalysis}
        """
        analyses = {}

        self.logger.info(f"\n🔍 ANALYZING MARKET - Cycle #{self.cycles_run + 1}")
        self.logger.info("="*70)

        for symbol in self.symbols:
            try:
                analysis = self.signal_generator.analyze_symbol(symbol, interval='1h')

                if analysis:
                    analyses[symbol] = analysis

                    # Mostrar análisis
                    if analysis.signal.action != "WAIT":
                        self.signal_generator.display_analysis(analysis)

                time.sleep(0.5)  # Rate limiting

            except Exception as e:
                self.logger.error(f"Error analyzing {symbol}: {e}")
                continue

        return analyses


    def execute_signals(self, analyses: Dict[str, QuantumAnalysis]):
        """
        Ejecutar señales de trading

        Args:
            analyses: Dict de análisis por símbolo
        """
        if not self.trading_enabled or not self.executor:
            self.logger.info("ℹ️ Trading disabled - Signals generated but not executed")
            return

        self.logger.info("")
        self.logger.info("="*70)
        self.logger.info("💼 TRADING EXECUTION CHECK")
        self.logger.info("="*70)

        buy_signals_count = sum(1 for a in analyses.values() if a.signal.action == "BUY")
        self.logger.info(f"   Total symbols analyzed: {len(analyses)}")
        self.logger.info(f"   BUY signals detected: {buy_signals_count}")

        if buy_signals_count == 0:
            self.logger.info("   ℹ️ No BUY signals - Waiting for opportunities...")
            self.logger.info("="*70)
            return

        for symbol, analysis in analyses.items():
            try:
                # Solo ejecutar señales BUY
                if analysis.signal.action == "BUY":
                    # Verificar que tenga alta confianza
                    min_confidence = 70
                    self.logger.info(f"")
                    self.logger.info(f"🎯 {symbol}: BUY signal detected!")
                    self.logger.info(f"   Level: {analysis.signal.metrics.level}")
                    self.logger.info(f"   Confidence: {analysis.signal.confidence:.1f}%")
                    self.logger.info(f"   AI Confidence: {analysis.ai_confidence:.1f}%")

                    if analysis.signal.confidence >= min_confidence:
                        self.logger.info(f"   ✅ Confidence OK - Attempting to open position...")

                        ticket = self.executor.open_quantum_position(
                            analysis,
                            trailing_mode=TrailingMode.LEVEL  # Adaptive
                        )

                        if ticket:
                            self.positions_opened += 1
                            self.logger.info(f"✅ Position opened: {symbol} Ticket#{ticket}")
                        else:
                            self.logger.error(f"❌ Failed to open position for {symbol}")
                    else:
                        self.logger.info(
                            f"   ⚠️ Confidence too low: {analysis.signal.confidence:.1f}% < {min_confidence}%"
                        )
                        self.logger.info(f"   Skipping {symbol}")

            except Exception as e:
                self.logger.error(f"Error executing signal for {symbol}: {e}")

        self.logger.info("="*70)


    def manage_positions(self, analyses: Dict[str, QuantumAnalysis]):
        """
        Gestionar posiciones abiertas

        Args:
            analyses: Análisis actuales
        """
        if not self.trading_enabled or not self.executor:
            return

        try:
            self.logger.info("\n🔧 MANAGING POSITIONS...")
            self.executor.monitor_and_manage_positions(analyses)

        except Exception as e:
            self.logger.error(f"Error managing positions: {e}")


    def display_statistics(self):
        """Mostrar estadísticas del sistema"""
        self.logger.info("\n📊 QUANTUM SYSTEM STATISTICS")
        self.logger.info("="*70)
        self.logger.info(f"Cycles run: {self.cycles_run}")
        self.logger.info(f"Signals generated: {self.signals_generated}")
        self.logger.info(f"Positions opened: {self.positions_opened}")

        if self.executor:
            stats = self.executor.get_statistics()
            self.logger.info(f"\n💼 ACTIVE POSITIONS:")
            self.logger.info(f"   Open: {stats.get('open_positions', 0)}")
            self.logger.info(f"   Total P/L: ${stats.get('total_profit', 0):.2f}")
            if stats.get('symbols'):
                self.logger.info(f"   Symbols: {', '.join(stats['symbols'])}")

        self.logger.info("="*70)


    def run_single_cycle(self):
        """Ejecutar un ciclo completo del sistema"""
        try:
            self.cycles_run += 1

            # 1. Analizar mercado
            analyses = self.analyze_market()

            # 2. Contar señales
            buy_signals = sum(1 for a in analyses.values() if a.signal.action == "BUY")
            exit_signals = sum(1 for a in analyses.values() if a.signal.action == "EXIT")
            self.signals_generated += buy_signals + exit_signals

            # 3. Ejecutar señales de entrada (siempre mostrar check, incluso si no hay señales)
            self.execute_signals(analyses)

            # 4. Gestionar posiciones existentes
            self.manage_positions(analyses)

            # 5. Estadísticas
            if self.cycles_run % 10 == 0:
                self.display_statistics()

        except Exception as e:
            self.logger.error(f"Error in cycle: {e}")


    def run_continuous(self):
        """Ejecutar sistema en modo continuo"""
        self.logger.info(f"\n🚀 STARTING CONTINUOUS MODE")
        self.logger.info(f"⏰ Cycle interval: {self.cycle_interval} seconds")
        self.logger.info("Press Ctrl+C to stop\n")

        try:
            while True:
                cycle_start = datetime.now()

                # Ejecutar ciclo
                self.run_single_cycle()

                # Calcular tiempo de espera
                elapsed = (datetime.now() - cycle_start).total_seconds()
                wait_time = max(0, self.cycle_interval - elapsed)

                if wait_time > 0:
                    self.logger.info(f"\n⏰ Next cycle in {wait_time:.0f} seconds...")
                    time.sleep(wait_time)

        except KeyboardInterrupt:
            self.logger.info("\n\n🛑 System stopped by user")
            self.display_statistics()

        finally:
            if self.executor:
                self.executor.shutdown()


    def shutdown(self):
        """Apagar sistema de forma segura"""
        self.logger.info("\n🔴 SHUTTING DOWN QUANTUM SYSTEM...")

        if self.executor:
            self.executor.shutdown()

        self.logger.info("System shutdown complete")


def main():
    """Función principal"""
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/quantum_trading_system.log', encoding='utf-8')
        ]
    )

    # Banner
    print("\n" + "="*70)
    print("██████╗ ██╗   ██╗ █████╗ ███╗   ██╗████████╗██╗   ██╗███╗   ███╗")
    print("██╔═══██╗██║   ██║██╔══██╗████╗  ██║╚══██╔══╝██║   ██║████╗ ████║")
    print("██║   ██║██║   ██║███████║██╔██╗ ██║   ██║   ██║   ██║██╔████╔██║")
    print("██║▄▄ ██║██║   ██║██╔══██║██║╚██╗██║   ██║   ██║   ██║██║╚██╔╝██║")
    print("╚██████╔╝╚██████╔╝██║  ██║██║ ╚████║   ██║   ╚██████╔╝██║ ╚═╝ ██║")
    print(" ╚══▀▀═╝  ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝   ╚═╝    ╚═════╝ ╚═╝     ╚═╝")
    print("                  TRADING SYSTEM v1.0.0")
    print("="*70)
    print("Sistema de Trading basado en Quantum Action")
    print("Autor: Xentristech Trading AI")
    print("="*70)

    # Verificar variables de entorno
    if not os.getenv("TWELVEDATA_API_KEY"):
        print("\n⚠️ WARNING: TWELVEDATA_API_KEY not found in environment")
        print("   Please set it in .env file")
        return

    # Preguntar modo de operación
    print("\n🎯 SELECT OPERATION MODE:")
    print("1. Analysis Only (No Trading)")
    print("2. Live Trading (Automatic Execution)")
    print("3. Single Cycle Test")

    try:
        mode = input("\nEnter mode (1-3): ").strip()

        if mode == "1":
            trading_enabled = False
            continuous = True
        elif mode == "2":
            trading_enabled = True
            continuous = True
            print("\n⚠️ LIVE TRADING ENABLED - ARE YOU SURE? (yes/no)")
            confirm = input().strip().lower()
            if confirm != "yes":
                print("Aborted")
                return
        elif mode == "3":
            trading_enabled = False
            continuous = False
        else:
            print("Invalid mode")
            return

        # Crear sistema
        system = QuantumTradingSystem(
            trading_enabled=trading_enabled,
            use_ai_validation=True,
            multi_timeframe=True,
            auto_scaling=True
        )

        # Ejecutar
        if continuous:
            system.run_continuous()
        else:
            system.run_single_cycle()
            system.display_statistics()
            system.shutdown()

    except KeyboardInterrupt:
        print("\n\n🛑 Interrupted by user")
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()
