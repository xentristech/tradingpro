"""
QUANTUM MT5 EXECUTOR - Ejecutor de Trading con Quantum Signals
===============================================================
Ejecuta operaciones en MetaTrader 5 basadas en señales cuánticas
Con gestión inteligente de SL/TP, trailing stops y risk management

Autor: Xentristech Trading AI
Fecha: 2025-01-16
"""

import os
import sys
from pathlib import Path
import MetaTrader5 as mt5
from typing import Dict, Optional, List, Tuple
from datetime import datetime
from dataclasses import dataclass
import logging

# Agregar path del proyecto
project_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_dir))

from src.signals.quantum_core import (
    QuantumCore,
    QuantumSignal,
    QuantumMetrics,
    TrailingMode
)
from src.signals.quantum_signal_generator import QuantumAnalysis

logger = logging.getLogger(__name__)


@dataclass
class QuantumPosition:
    """Posición abierta con gestión cuántica"""
    ticket: int
    symbol: str
    type: int  # 0=BUY, 1=SELL
    volume: float
    open_price: float
    sl: float
    tp: float
    timestamp: datetime

    # Quantum metrics
    entry_level: int
    entry_action: float
    trailing_mode: TrailingMode
    h: float  # Cuanto al momento de apertura


class QuantumMT5Executor:
    """
    Ejecutor profesional para MT5 con señales cuánticas

    Funcionalidades:
    - Apertura de posiciones con SL/TP dinámicos
    - 4 modos de Trailing Stop (ATR, h, Band, Level)
    - Auto-correction de SL/TP faltantes
    - Breakeven automático
    - Risk management integrado
    """

    def __init__(
        self,
        default_lot: float = 0.01,
        sl_atr_mult: float = 2.0,
        tp_k_mult: float = 1.0,
        trailing_mult: float = 1.5,
        max_risk_per_trade: float = 0.01,  # 1%
        use_breakeven: bool = True,
        breakeven_trigger: float = 0.001,  # 0.1%
        use_trailing: bool = True
    ):
        """
        Inicializar ejecutor cuántico MT5

        Args:
            default_lot: Lote por defecto
            sl_atr_mult: Multiplicador ATR para SL
            tp_k_mult: Multiplicador k·h para TP
            trailing_mult: Multiplicador para trailing
            max_risk_per_trade: Riesgo máximo por trade (%)
            use_breakeven: Activar breakeven automático
            breakeven_trigger: % de ganancia para activar breakeven
            use_trailing: Activar trailing stop
        """
        self.default_lot = default_lot
        self.sl_atr_mult = sl_atr_mult
        self.tp_k_mult = tp_k_mult
        self.trailing_mult = trailing_mult
        self.max_risk_per_trade = max_risk_per_trade
        self.use_breakeven = use_breakeven
        self.breakeven_trigger = breakeven_trigger
        self.use_trailing = use_trailing

        # Posiciones cuánticas activas
        self.quantum_positions: Dict[int, QuantumPosition] = {}

        # Estado MT5
        self.mt5_connected = False
        self.connect_mt5()

        logger.info(f"QuantumMT5Executor initialized (Lot: {default_lot}, Trailing: {use_trailing})")


    def connect_mt5(self) -> bool:
        """Conectar a MetaTrader 5"""
        try:
            if not mt5.initialize():
                logger.error("❌ Failed to initialize MT5 - Is MT5 running?")
                logger.error(f"   Error: {mt5.last_error()}")
                return False

            account = mt5.account_info()
            if account:
                logger.info(f"✅ MT5 connected - Account: {account.login}, Balance: ${account.balance:.2f}")
                self.mt5_connected = True
                return True
            else:
                logger.error("❌ Failed to get MT5 account info")
                logger.error(f"   Error: {mt5.last_error()}")
                return False

        except Exception as e:
            logger.error(f"❌ MT5 connection error: {e}")
            return False

    def check_mt5_connection(self) -> bool:
        """Verificar si MT5 sigue conectado"""
        try:
            terminal_info = mt5.terminal_info()
            if terminal_info is None:
                logger.warning("⚠️ MT5 terminal not responding - reconnecting...")
                self.mt5_connected = False
                return self.connect_mt5()

            if not terminal_info.connected:
                logger.warning("⚠️ MT5 not connected to server - reconnecting...")
                self.mt5_connected = False
                return self.connect_mt5()

            return True

        except Exception as e:
            logger.error(f"❌ Error checking MT5 connection: {e}")
            self.mt5_connected = False
            return False


    def calculate_dynamic_sl_tp(
        self,
        symbol: str,
        analysis: QuantumAnalysis,
        order_type: int  # 0=BUY, 1=SELL
    ) -> Tuple[float, float]:
        """
        Calcular SL y TP dinámicos basados en Quantum Action

        SL = ATR * multiplier
        TP = Acción + k·h (banda cuántica superior)

        Args:
            symbol: Símbolo
            analysis: Análisis cuántico
            order_type: 0=BUY, 1=SELL

        Returns:
            Tuple(sl_price, tp_price)
        """
        try:
            price = analysis.price
            atr = analysis.atr
            A = analysis.signal.metrics.action
            h = analysis.signal.metrics.h
            k = 2.0  # Puede venir de quantum_core

            if order_type == 0:  # BUY
                sl = price - (self.sl_atr_mult * atr)
                tp = price + (k * h * self.tp_k_mult)
            else:  # SELL
                sl = price + (self.sl_atr_mult * atr)
                tp = price - (k * h * self.tp_k_mult)

            return sl, tp

        except Exception as e:
            logger.error(f"Error calculating SL/TP: {e}")
            return 0, 0


    def calculate_position_size(
        self,
        symbol: str,
        sl_distance: float
    ) -> float:
        """
        Calcular tamaño de posición basado en riesgo

        Usa % fijo del balance para calcular lote óptimo

        Args:
            symbol: Símbolo
            sl_distance: Distancia al SL en precio

        Returns:
            Volumen (lotes)
        """
        try:
            account = mt5.account_info()
            if not account:
                return self.default_lot

            balance = account.balance
            risk_amount = balance * self.max_risk_per_trade

            # Info del símbolo
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                return self.default_lot

            # Valor del tick
            tick_value = symbol_info.trade_tick_value
            tick_size = symbol_info.trade_tick_size

            # Calcular lotes
            if sl_distance > 0 and tick_size > 0:
                ticks = sl_distance / tick_size
                lot = risk_amount / (ticks * tick_value)

                # Normalizar a step del símbolo
                lot_step = symbol_info.volume_step
                lot = round(lot / lot_step) * lot_step

                # Límites
                lot = max(symbol_info.volume_min, min(lot, symbol_info.volume_max))
                lot = max(lot, self.default_lot)  # Mínimo nuestro default

                return lot

            return self.default_lot

        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return self.default_lot


    def open_quantum_position(
        self,
        analysis: QuantumAnalysis,
        trailing_mode: TrailingMode = TrailingMode.ATR
    ) -> Optional[int]:
        """
        Abrir posición basada en señal cuántica

        Args:
            analysis: Análisis cuántico completo
            trailing_mode: Modo de trailing stop

        Returns:
            Ticket de la orden o None si falla
        """
        # Verificar conexión MT5
        if not self.check_mt5_connection():
            logger.error("❌ MT5 not connected - Cannot open position")
            return None

        if analysis.signal.action != "BUY":
            logger.info(f"ℹ️ {analysis.symbol}: Signal is {analysis.signal.action}, not BUY - Skipping")
            return None

        try:
            symbol = analysis.symbol
            price = analysis.price

            logger.info(f"")
            logger.info(f"{'='*70}")
            logger.info(f"🚀 ATTEMPTING TO OPEN POSITION: {symbol}")
            logger.info(f"{'='*70}")
            logger.info(f"   Signal: BUY")
            logger.info(f"   Level: {analysis.signal.metrics.level}")
            logger.info(f"   Confidence: {analysis.signal.confidence:.1f}%")
            logger.info(f"   AI Confidence: {analysis.ai_confidence:.1f}%")
            logger.info(f"   Price: {price}")

            # Calcular SL/TP dinámicos
            sl, tp = self.calculate_dynamic_sl_tp(symbol, analysis, order_type=0)
            logger.info(f"   SL: {sl:.5f}")
            logger.info(f"   TP: {tp:.5f}")

            # Calcular tamaño de posición
            sl_distance = abs(price - sl)
            lot = self.calculate_position_size(symbol, sl_distance)
            logger.info(f"   Lot size: {lot}")
            logger.info(f"   SL distance: {sl_distance:.5f}")

            # Obtener balance actual
            account = mt5.account_info()
            if account:
                logger.info(f"   Balance: ${account.balance:.2f}")
                logger.info(f"   Free Margin: ${account.margin_free:.2f}")

            # Preparar request
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot,
                "type": mt5.ORDER_TYPE_BUY,
                "price": price,
                "sl": sl,
                "tp": tp,
                "magic": 123456,  # Quantum magic number
                "comment": f"Quantum{analysis.signal.metrics.level}",
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            logger.info(f"")
            logger.info(f"📤 Sending order to MT5...")

            # Enviar orden
            result = mt5.order_send(request)

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"❌ Order FAILED!")
                logger.error(f"   Retcode: {result.retcode}")
                logger.error(f"   Comment: {result.comment}")
                logger.error(f"   Request: {request}")
                return None

            ticket = result.order
            logger.info(f"✅ ORDER SUCCESSFUL!")
            logger.info(f"   Ticket: #{ticket}")

            # Guardar posición cuántica
            quantum_pos = QuantumPosition(
                ticket=ticket,
                symbol=symbol,
                type=0,
                volume=lot,
                open_price=result.price,
                sl=sl,
                tp=tp,
                timestamp=datetime.now(),
                entry_level=analysis.signal.metrics.level,
                entry_action=analysis.signal.metrics.action,
                trailing_mode=trailing_mode,
                h=analysis.signal.metrics.h
            )

            self.quantum_positions[ticket] = quantum_pos

            logger.info(
                f"✅ OPENED {symbol}: Ticket={ticket}, "
                f"Lot={lot}, Price={result.price:.5f}, "
                f"SL={sl:.5f}, TP={tp:.5f}, Level={analysis.signal.metrics.level}"
            )

            return ticket

        except Exception as e:
            logger.error(f"Error opening position: {e}")
            return None


    def close_quantum_position(self, ticket: int) -> bool:
        """
        Cerrar posición cuántica

        Args:
            ticket: Ticket de la posición

        Returns:
            True si se cerró exitosamente
        """
        if not self.mt5_connected:
            return False

        try:
            # Seleccionar posición
            position = mt5.positions_get(ticket=ticket)
            if not position:
                logger.warning(f"Position {ticket} not found")
                return False

            pos = position[0]

            # Preparar request de cierre
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": pos.symbol,
                "volume": pos.volume,
                "type": mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY,
                "position": ticket,
                "price": mt5.symbol_info_tick(pos.symbol).bid if pos.type == 0 else mt5.symbol_info_tick(pos.symbol).ask,
                "magic": 123456,
                "comment": "QuantumExit",
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            # Enviar orden
            result = mt5.order_send(request)

            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Close failed: {result.retcode}")
                return False

            # Eliminar de tracking
            if ticket in self.quantum_positions:
                del self.quantum_positions[ticket]

            logger.info(f"✅ CLOSED {pos.symbol}: Ticket={ticket}, Price={result.price:.5f}")
            return True

        except Exception as e:
            logger.error(f"Error closing position {ticket}: {e}")
            return False


    def update_trailing_stop(
        self,
        ticket: int,
        current_analysis: QuantumAnalysis
    ) -> bool:
        """
        Actualizar trailing stop de una posición

        Args:
            ticket: Ticket de la posición
            current_analysis: Análisis actual del mercado

        Returns:
            True si se actualizó
        """
        if ticket not in self.quantum_positions:
            return False

        quantum_pos = self.quantum_positions[ticket]

        try:
            # Obtener posición actual de MT5
            position = mt5.positions_get(ticket=ticket)
            if not position:
                return False

            pos = position[0]
            current_price = mt5.symbol_info_tick(pos.symbol).bid

            # Calcular nuevo trailing stop
            from src.signals.quantum_core import QuantumCore
            quantum = QuantumCore()

            new_sl = quantum.calculate_trailing_stop(
                price=current_price,
                A=current_analysis.signal.metrics.action,
                h=current_analysis.signal.metrics.h,
                atr=current_analysis.atr,
                level=current_analysis.signal.metrics.level,
                mode=quantum_pos.trailing_mode,
                multiplier=self.trailing_mult
            )

            # Solo mover SL si es mejor (más alto para BUY)
            if pos.type == 0:  # BUY
                if new_sl > pos.sl:
                    # Modificar posición
                    request = {
                        "action": mt5.TRADE_ACTION_SLTP,
                        "symbol": pos.symbol,
                        "sl": new_sl,
                        "tp": pos.tp,
                        "position": ticket
                    }

                    result = mt5.order_send(request)

                    if result.retcode == mt5.TRADE_RETCODE_DONE:
                        logger.info(f"✅ TRAILING {pos.symbol}: {pos.sl:.5f} → {new_sl:.5f}")
                        return True

            return False

        except Exception as e:
            logger.error(f"Error updating trailing for {ticket}: {e}")
            return False


    def monitor_and_manage_positions(
        self,
        current_analyses: Dict[str, QuantumAnalysis]
    ):
        """
        Monitorear y gestionar todas las posiciones cuánticas

        Aplica:
        - Trailing stops
        - Breakeven
        - Cierre por señal EXIT

        Args:
            current_analyses: Dict de análisis actuales por símbolo
        """
        if not self.mt5_connected:
            return

        # Obtener todas las posiciones de MT5
        positions = mt5.positions_get()
        if not positions:
            return

        for pos in positions:
            if pos.magic != 123456:  # Solo posiciones cuánticas
                continue

            symbol = pos.symbol
            ticket = pos.ticket

            # Verificar si tenemos análisis actual
            if symbol not in current_analyses:
                continue

            analysis = current_analyses[symbol]

            # 1. Verificar señal EXIT
            if analysis.signal.action == "EXIT":
                logger.warning(f"⚠️ EXIT signal for {symbol}, closing {ticket}")
                self.close_quantum_position(ticket)
                continue

            # 2. Aplicar trailing stop
            if self.use_trailing:
                self.update_trailing_stop(ticket, analysis)

            # 3. Aplicar breakeven
            if self.use_breakeven:
                current_price = mt5.symbol_info_tick(symbol).bid
                if pos.type == 0:  # BUY
                    profit_pct = (current_price - pos.price_open) / pos.price_open
                    if profit_pct >= self.breakeven_trigger and pos.sl < pos.price_open:
                        # Mover a breakeven
                        request = {
                            "action": mt5.TRADE_ACTION_SLTP,
                            "symbol": symbol,
                            "sl": pos.price_open,
                            "tp": pos.tp,
                            "position": ticket
                        }
                        result = mt5.order_send(request)
                        if result.retcode == mt5.TRADE_RETCODE_DONE:
                            logger.info(f"✅ BREAKEVEN {symbol}: Ticket={ticket}")


    def get_statistics(self) -> Dict:
        """Obtener estadísticas de las posiciones cuánticas"""
        if not self.mt5_connected:
            return {}

        positions = mt5.positions_get()
        if not positions:
            return {"open_positions": 0}

        quantum_positions = [p for p in positions if p.magic == 123456]

        total_profit = sum(p.profit for p in quantum_positions)

        return {
            "open_positions": len(quantum_positions),
            "total_profit": total_profit,
            "symbols": list(set(p.symbol for p in quantum_positions))
        }


    def shutdown(self):
        """Desconectar MT5"""
        if self.mt5_connected:
            mt5.shutdown()
            logger.info("MT5 disconnected")


# ========== EJEMPLO DE USO ==========
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Crear ejecutor
    executor = QuantumMT5Executor(
        default_lot=0.01,
        use_breakeven=True,
        use_trailing=True
    )

    # Ejemplo de apertura (necesitarías un análisis real)
    # analysis = QuantumAnalysis(...)
    # ticket = executor.open_quantum_position(analysis)

    # Estadísticas
    stats = executor.get_statistics()
    print(f"\n📊 Quantum Trading Statistics:")
    print(f"   Open positions: {stats.get('open_positions', 0)}")
    print(f"   Total P/L: ${stats.get('total_profit', 0):.2f}")

    executor.shutdown()
