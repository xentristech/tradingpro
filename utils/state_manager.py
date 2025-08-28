"""
State Manager - Sistema unificado de gestión de estado
Gestiona el estado global del sistema de trading
"""
import json
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class TradingState(Enum):
    """Estados del sistema de trading"""
    IDLE = "idle"
    ANALYZING = "analyzing"
    SIGNAL_DETECTED = "signal_detected"
    PLACING_ORDER = "placing_order"
    POSITION_OPEN = "position_open"
    MANAGING_POSITION = "managing_position"
    CLOSING_POSITION = "closing_position"
    ERROR = "error"

@dataclass
class Position:
    """Información de posición"""
    ticket: int
    symbol: str
    type: str  # BUY/SELL
    volume: float
    entry_price: float
    current_price: float
    sl: float
    tp: float
    profit: float
    open_time: datetime
    magic: int = 20250817

@dataclass
class SystemStats:
    """Estadísticas del sistema"""
    start_time: datetime
    cycles: int = 0
    trades_total: int = 0
    trades_won: int = 0
    trades_lost: int = 0
    profit_total: float = 0.0
    max_drawdown: float = 0.0
    errors: int = 0
    last_error: Optional[str] = None
    last_trade_time: Optional[datetime] = None

class StateManager:
    """
    Gestor centralizado de estado del sistema
    Thread-safe y persistente
    """
    
    def __init__(self, state_file: str = "data/system_state.json"):
        """
        Inicializa el gestor de estado
        
        Args:
            state_file: Archivo donde persistir el estado
        """
        self.state_file = Path(state_file)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Estado interno
        self._lock = threading.RLock()
        self._state = {
            'trading_state': TradingState.IDLE.value,
            'positions': {},
            'pending_orders': {},
            'stats': asdict(SystemStats(start_time=datetime.now())),
            'config': {},
            'market_data': {},
            'signals': [],
            'errors': [],
            'pnl_by_symbol': {}
        }
        
        # Cargar estado previo si existe
        self._load_state()
        
        # Thread para auto-guardado
        self._stop_event = threading.Event()
        self._auto_save_thread = threading.Thread(target=self._auto_save_loop)
        self._auto_save_thread.daemon = True
        self._auto_save_thread.start()
        
        logger.info("StateManager inicializado")
    
    def _load_state(self):
        """Carga el estado desde archivo"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    saved_state = json.load(f)
                    
                # Mantener solo datos relevantes
                if 'stats' in saved_state:
                    # Resetear contadores de sesión
                    saved_state['stats']['cycles'] = 0
                    saved_state['stats']['start_time'] = datetime.now().isoformat()
                    
                with self._lock:
                    self._state.update(saved_state)
                    
                logger.info(f"Estado cargado desde {self.state_file}")
        except Exception as e:
            logger.warning(f"No se pudo cargar estado previo: {e}")
    
    def save_state(self):
        """Guarda el estado actual a archivo"""
        try:
            with self._lock:
                # Convertir datetime a string para JSON
                state_copy = self._state.copy()
                
                # Serializar fechas
                if 'stats' in state_copy and 'start_time' in state_copy['stats']:
                    if isinstance(state_copy['stats']['start_time'], datetime):
                        state_copy['stats']['start_time'] = state_copy['stats']['start_time'].isoformat()
                
                if 'stats' in state_copy and 'last_trade_time' in state_copy['stats']:
                    if isinstance(state_copy['stats']['last_trade_time'], datetime):
                        state_copy['stats']['last_trade_time'] = state_copy['stats']['last_trade_time'].isoformat()
                
                # Guardar a archivo
                with open(self.state_file, 'w') as f:
                    json.dump(state_copy, f, indent=2, default=str)
                    
        except Exception as e:
            logger.error(f"Error guardando estado: {e}")
    
    def _auto_save_loop(self):
        """Loop de auto-guardado cada 60 segundos"""
        while not self._stop_event.is_set():
            time.sleep(60)
            self.save_state()
    
    def set_trading_state(self, state: TradingState):
        """Actualiza el estado de trading"""
        with self._lock:
            self._state['trading_state'] = state.value
            logger.debug(f"Estado de trading: {state.value}")
    
    def get_trading_state(self) -> TradingState:
        """Obtiene el estado actual de trading"""
        with self._lock:
            state_str = self._state.get('trading_state', 'idle')
            return TradingState(state_str)
    
    def add_position(self, position: Position):
        """Agrega una posición abierta"""
        with self._lock:
            self._state['positions'][position.ticket] = asdict(position)
            self._state['stats']['trades_total'] += 1
            logger.info(f"Posición añadida: {position.ticket}")
    
    def update_position(self, ticket: int, **kwargs):
        """Actualiza una posición existente"""
        with self._lock:
            if ticket in self._state['positions']:
                self._state['positions'][ticket].update(kwargs)
    
    def remove_position(self, ticket: int, profit: float = 0):
        """Elimina una posición cerrada"""
        with self._lock:
            if ticket in self._state['positions']:
                pos = self._state['positions'].pop(ticket)
                
                # Actualizar estadísticas
                self._state['stats']['profit_total'] += profit
                if profit > 0:
                    self._state['stats']['trades_won'] += 1
                else:
                    self._state['stats']['trades_lost'] += 1
                
                self._state['stats']['last_trade_time'] = datetime.now().isoformat()
                # Acumular PnL por símbolo
                sym = pos.get('symbol') if isinstance(pos, dict) else None
                if sym:
                    self._state.setdefault('pnl_by_symbol', {})
                    self._state['pnl_by_symbol'][sym] = self._state['pnl_by_symbol'].get(sym, 0.0) + float(profit)
                logger.info(f"Posición cerrada: {ticket}, Profit: {profit}")
    
    def get_positions(self) -> Dict[int, Dict]:
        """Obtiene todas las posiciones abiertas"""
        with self._lock:
            return self._state['positions'].copy()
    
    def update_market_data(self, symbol: str, data: Dict[str, Any]):
        """Actualiza datos de mercado"""
        with self._lock:
            if 'market_data' not in self._state:
                self._state['market_data'] = {}
            self._state['market_data'][symbol] = {
                **data,
                'timestamp': datetime.now().isoformat()
            }
    
    def get_market_data(self, symbol: str) -> Optional[Dict]:
        """Obtiene datos de mercado para un símbolo"""
        with self._lock:
            return self._state.get('market_data', {}).get(symbol)
    
    def add_signal(self, signal: Dict[str, Any]):
        """Agrega una señal detectada"""
        with self._lock:
            signal['timestamp'] = datetime.now().isoformat()
            self._state['signals'].append(signal)
            
            # Mantener solo últimas 100 señales
            if len(self._state['signals']) > 100:
                self._state['signals'] = self._state['signals'][-100:]
    
    def get_recent_signals(self, limit: int = 10) -> List[Dict]:
        """Obtiene las señales más recientes"""
        with self._lock:
            return self._state['signals'][-limit:]
    
    def log_error(self, error: str, critical: bool = False):
        """Registra un error en el estado"""
        with self._lock:
            error_entry = {
                'message': str(error),
                'timestamp': datetime.now().isoformat(),
                'critical': critical
            }
            self._state['errors'].append(error_entry)
            self._state['stats']['errors'] += 1
            self._state['stats']['last_error'] = str(error)
            
            # Mantener solo últimos 50 errores
            if len(self._state['errors']) > 50:
                self._state['errors'] = self._state['errors'][-50:]
            
            logger.error(f"Error registrado: {error}")
    
    def update_cycle(self, cycle_number: int):
        """Actualiza el contador de ciclos"""
        with self._lock:
            self._state['stats']['cycles'] = cycle_number
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la sesión actual"""
        with self._lock:
            return self._state['stats'].copy()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Obtiene el estado de salud del sistema"""
        with self._lock:
            positions_count = len(self._state['positions'])
            errors_recent = len([e for e in self._state['errors'][-10:] if e.get('critical')])
            
            return {
                'trading_state': self._state['trading_state'],
                'positions_open': positions_count,
                'cycles': self._state['stats']['cycles'],
                'errors': self._state['stats']['errors'],
                'critical_errors': errors_recent,
                'last_error': self._state['stats'].get('last_error'),
                'uptime': (datetime.now() - datetime.fromisoformat(
                    self._state['stats']['start_time']
                )).total_seconds() if 'start_time' in self._state['stats'] else 0
            }
    
    def update_config(self, config: Dict[str, Any]):
        """Actualiza la configuración en el estado"""
        with self._lock:
            self._state['config'].update(config)
    
    def get_config(self) -> Dict[str, Any]:
        """Obtiene la configuración actual"""
        with self._lock:
            return self._state['config'].copy()
    
    def reset_session_stats(self):
        """Resetea las estadísticas de sesión"""
        with self._lock:
            self._state['stats']['cycles'] = 0
            self._state['stats']['start_time'] = datetime.now().isoformat()
            self._state['errors'] = []
            logger.info("Estadísticas de sesión reseteadas")
    
    def shutdown(self):
        """Cierra el StateManager de forma segura"""
        logger.info("Cerrando StateManager...")
        self._stop_event.set()
        self.save_state()
        if self._auto_save_thread.is_alive():
            self._auto_save_thread.join(timeout=2)
        logger.info("StateManager cerrado")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.shutdown()
