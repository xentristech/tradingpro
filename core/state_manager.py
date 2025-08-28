"""
State Manager - Gestión unificada del estado del sistema
Maneja el estado global del bot, posiciones y configuración
"""
import json
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class BotState(Enum):
    """Estados posibles del bot"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"
    MAINTENANCE = "maintenance"

class StateManager:
    """
    Gestor centralizado de estado para todo el sistema
    Thread-safe y persistente
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern para instancia única"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Inicializar gestor de estado"""
        if self._initialized:
            return
            
        self._initialized = True
        self.state_file = Path("data/bot_state.json")
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Estado en memoria
        self._state = {
            'bot_state': BotState.STOPPED.value,
            'start_time': None,
            'last_update': None,
            'positions': {},
            'statistics': {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'total_pnl': 0.0,
                'daily_pnl': 0.0,
                'max_drawdown': 0.0,
                'current_balance': 0.0,
                'initial_balance': 0.0
            },
            'settings': {
                'mode': 'demo',
                'symbol': None,
                'risk_per_trade': 0.02,
                'max_positions': 3,
                'min_confidence': 0.75
            },
            'errors': [],
            'health': {
                'mt5_connected': False,
                'telegram_connected': False,
                'ollama_connected': False,
                'data_feed_active': False,
                'last_heartbeat': None
            },
            'performance': {
                'cpu_usage': 0.0,
                'memory_usage': 0.0,
                'api_calls': {
                    'twelvedata': {'count': 0, 'last_call': None},
                    'ollama': {'count': 0, 'last_call': None},
                    'telegram': {'count': 0, 'last_call': None}
                }
            }
        }
        
        # Cargar estado previo si existe
        self.load_state()
        
        # Thread de auto-guardado
        self._stop_autosave = threading.Event()
        self._autosave_thread = threading.Thread(target=self._autosave_loop, daemon=True)
        self._autosave_thread.start()
    
    def _autosave_loop(self):
        """Guardar estado cada 30 segundos"""
        while not self._stop_autosave.wait(30):
            self.save_state()
    
    def get_state(self, key: Optional[str] = None) -> Any:
        """Obtener estado o clave específica"""
        with self._lock:
            if key:
                keys = key.split('.')
                value = self._state
                for k in keys:
                    value = value.get(k)
                return value
            return self._state.copy()
    
    def set_state(self, key: str, value: Any):
        """Actualizar estado"""
        with self._lock:
            keys = key.split('.')
            target = self._state
            for k in keys[:-1]:
                if k not in target:
                    target[k] = {}
                target = target[k]
            target[keys[-1]] = value
            self._state['last_update'] = datetime.now().isoformat()
    
    def update_bot_state(self, state: BotState):
        """Actualizar estado del bot"""
        logger.info(f"Estado del bot: {self.get_state('bot_state')} -> {state.value}")
        self.set_state('bot_state', state.value)
        
        if state == BotState.RUNNING:
            self.set_state('start_time', datetime.now().isoformat())
        elif state == BotState.STOPPED:
            self.set_state('start_time', None)
    
    def is_running(self) -> bool:
        """Verificar si el bot está ejecutándose"""
        return self.get_state('bot_state') == BotState.RUNNING.value
    
    def add_position(self, ticket: str, position: Dict[str, Any]):
        """Añadir nueva posición"""
        with self._lock:
            self._state['positions'][ticket] = {
                **position,
                'opened_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
    
    def update_position(self, ticket: str, updates: Dict[str, Any]):
        """Actualizar posición existente"""
        with self._lock:
            if ticket in self._state['positions']:
                self._state['positions'][ticket].update(updates)
                self._state['positions'][ticket]['updated_at'] = datetime.now().isoformat()
    
    def remove_position(self, ticket: str):
        """Eliminar posición"""
        with self._lock:
            if ticket in self._state['positions']:
                del self._state['positions'][ticket]
    
    def get_positions(self) -> Dict[str, Any]:
        """Obtener todas las posiciones"""
        with self._lock:
            return self._state['positions'].copy()
    
    def update_statistics(self, stats: Dict[str, Any]):
        """Actualizar estadísticas"""
        with self._lock:
            self._state['statistics'].update(stats)
    
    def add_error(self, error: str, severity: str = "warning"):
        """Registrar error"""
        with self._lock:
            error_entry = {
                'timestamp': datetime.now().isoformat(),
                'message': error,
                'severity': severity
            }
            self._state['errors'].append(error_entry)
            
            # Mantener solo últimos 100 errores
            if len(self._state['errors']) > 100:
                self._state['errors'] = self._state['errors'][-100:]
    
    def update_health(self, component: str, status: bool):
        """Actualizar estado de salud de componente"""
        self.set_state(f'health.{component}', status)
        if status:
            self.set_state('health.last_heartbeat', datetime.now().isoformat())
    
    def increment_api_call(self, api: str):
        """Incrementar contador de llamadas API"""
        with self._lock:
            if api in self._state['performance']['api_calls']:
                self._state['performance']['api_calls'][api]['count'] += 1
                self._state['performance']['api_calls'][api]['last_call'] = datetime.now().isoformat()
    
    def save_state(self):
        """Guardar estado a disco"""
        try:
            with self._lock:
                with open(self.state_file, 'w') as f:
                    json.dump(self._state, f, indent=2)
            logger.debug("Estado guardado correctamente")
        except Exception as e:
            logger.error(f"Error guardando estado: {e}")
    
    def load_state(self):
        """Cargar estado desde disco"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    loaded_state = json.load(f)
                
                # Merge con estado actual (preservar estructura)
                with self._lock:
                    self._merge_states(self._state, loaded_state)
                
                logger.info("Estado cargado desde disco")
        except Exception as e:
            logger.warning(f"Error cargando estado: {e}")
    
    def _merge_states(self, base: Dict, update: Dict):
        """Merge recursivo de estados"""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_states(base[key], value)
            else:
                base[key] = value
    
    def reset_daily_stats(self):
        """Resetear estadísticas diarias"""
        with self._lock:
            self._state['statistics']['daily_pnl'] = 0.0
            self._state['errors'] = []
            for api in self._state['performance']['api_calls']:
                self._state['performance']['api_calls'][api]['count'] = 0
    
    def stop(self):
        """Detener el gestor de estado"""
        self.update_bot_state(BotState.STOPPED)
        self._stop_autosave.set()
        self.save_state()
    
    def get_summary(self) -> Dict[str, Any]:
        """Obtener resumen del estado"""
        with self._lock:
            return {
                'state': self._state['bot_state'],
                'uptime': self._calculate_uptime(),
                'positions': len(self._state['positions']),
                'daily_pnl': self._state['statistics']['daily_pnl'],
                'total_pnl': self._state['statistics']['total_pnl'],
                'health': all([
                    self._state['health']['mt5_connected'],
                    self._state['health']['data_feed_active']
                ]),
                'errors': len(self._state['errors'])
            }
    
    def _calculate_uptime(self) -> str:
        """Calcular tiempo de ejecución"""
        if self._state['start_time']:
            start = datetime.fromisoformat(self._state['start_time'])
            delta = datetime.now() - start
            hours, remainder = divmod(delta.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{delta.days}d {hours}h {minutes}m {seconds}s"
        return "0s"
