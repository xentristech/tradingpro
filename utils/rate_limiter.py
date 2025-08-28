"""
Rate Limiter - Control de límites de tasa para APIs
Previene exceder límites de API y maneja throttling
"""
import time
import threading
from collections import defaultdict, deque
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

@dataclass
class RateLimitConfig:
    """Configuración de límite de tasa"""
    calls_per_minute: int
    calls_per_hour: int
    calls_per_day: int
    burst_size: int  # Máximo de llamadas en ráfaga
    cooldown_seconds: float  # Tiempo entre llamadas

class RateLimiter:
    """
    Sistema de control de límite de tasa para múltiples APIs
    Implementa token bucket algorithm con sliding window
    """
    
    def __init__(self):
        """Inicializa el rate limiter con configuraciones por defecto"""
        self._lock = threading.RLock()
        self._call_history = defaultdict(deque)
        self._last_call = defaultdict(float)
        self._token_buckets = {}
        
        # Configuraciones por API
        self.configs = {
            'twelvedata': RateLimitConfig(
                calls_per_minute=8,  # API gratuita: 8/min
                calls_per_hour=400,
                calls_per_day=800,
                burst_size=3,
                cooldown_seconds=7.5  # 60/8 = 7.5 segundos
            ),
            'ollama': RateLimitConfig(
                calls_per_minute=30,  # Local, más permisivo
                calls_per_hour=1000,
                calls_per_day=10000,
                burst_size=5,
                cooldown_seconds=2.0
            ),
            'telegram': RateLimitConfig(
                calls_per_minute=30,
                calls_per_hour=1000,
                calls_per_day=10000,
                burst_size=5,
                cooldown_seconds=2.0
            ),
            'mt5': RateLimitConfig(
                calls_per_minute=60,  # No hay límite real, pero evitamos spam
                calls_per_hour=3600,
                calls_per_day=50000,
                burst_size=10,
                cooldown_seconds=1.0
            ),
            'openai': RateLimitConfig(
                calls_per_minute=20,  # Tier gratuito
                calls_per_hour=100,
                calls_per_day=1000,
                burst_size=3,
                cooldown_seconds=3.0
            )
        }
        
        # Inicializar token buckets
        for api_name, config in self.configs.items():
            self._token_buckets[api_name] = {
                'tokens': config.burst_size,
                'max_tokens': config.burst_size,
                'refill_rate': config.calls_per_minute / 60.0,  # tokens por segundo
                'last_refill': time.time()
            }
        
        # Estadísticas
        self.stats = defaultdict(lambda: {
            'total_calls': 0,
            'blocked_calls': 0,
            'total_wait_time': 0.0
        })
        
        logger.info("RateLimiter inicializado con configuraciones predefinidas")
    
    def can_call(self, api_name: str, cost: float = 1.0) -> Tuple[bool, float]:
        """
        Verifica si se puede hacer una llamada a la API
        
        Args:
            api_name: Nombre de la API
            cost: Costo en tokens de la llamada (por defecto 1.0)
            
        Returns:
            Tuple (puede_llamar, tiempo_espera_segundos)
        """
        if api_name not in self.configs:
            logger.warning(f"API {api_name} no configurada, permitiendo llamada")
            return True, 0.0
        
        config = self.configs[api_name]
        current_time = time.time()
        
        with self._lock:
            # Refill tokens
            self._refill_tokens(api_name)
            
            bucket = self._token_buckets[api_name]
            
            # Verificar tokens disponibles
            if bucket['tokens'] >= cost:
                return True, 0.0
            
            # Calcular tiempo de espera para obtener tokens suficientes
            tokens_needed = cost - bucket['tokens']
            wait_time = tokens_needed / bucket['refill_rate']
            
            # Verificar límites por ventana de tiempo
            wait_time_window = self._check_time_windows(api_name, config)
            wait_time = max(wait_time, wait_time_window)
            
            return False, wait_time
    
    def _refill_tokens(self, api_name: str):
        """Rellena tokens basado en el tiempo transcurrido"""
        bucket = self._token_buckets[api_name]
        current_time = time.time()
        
        time_elapsed = current_time - bucket['last_refill']
        tokens_to_add = time_elapsed * bucket['refill_rate']
        
        bucket['tokens'] = min(
            bucket['tokens'] + tokens_to_add,
            bucket['max_tokens']
        )
        bucket['last_refill'] = current_time
    
    def _check_time_windows(self, api_name: str, config: RateLimitConfig) -> float:
        """
        Verifica límites en ventanas de tiempo (minuto, hora, día)
        
        Returns:
            Tiempo de espera necesario en segundos
        """
        current_time = time.time()
        history = self._call_history[api_name]
        
        # Limpiar historial antiguo (más de 24 horas)
        cutoff_time = current_time - 86400  # 24 horas
        while history and history[0] < cutoff_time:
            history.popleft()
        
        # Verificar límite por minuto
        minute_ago = current_time - 60
        calls_last_minute = sum(1 for t in history if t > minute_ago)
        if calls_last_minute >= config.calls_per_minute:
            oldest_in_minute = next((t for t in history if t > minute_ago), current_time)
            return 60 - (current_time - oldest_in_minute) + 0.1
        
        # Verificar límite por hora
        hour_ago = current_time - 3600
        calls_last_hour = sum(1 for t in history if t > hour_ago)
        if calls_last_hour >= config.calls_per_hour:
            oldest_in_hour = next((t for t in history if t > hour_ago), current_time)
            return 3600 - (current_time - oldest_in_hour) + 0.1
        
        # Verificar límite por día
        day_ago = current_time - 86400
        calls_last_day = sum(1 for t in history if t > day_ago)
        if calls_last_day >= config.calls_per_day:
            oldest_in_day = next((t for t in history if t > day_ago), current_time)
            return 86400 - (current_time - oldest_in_day) + 0.1
        
        # Verificar cooldown
        if api_name in self._last_call:
            time_since_last = current_time - self._last_call[api_name]
            if time_since_last < config.cooldown_seconds:
                return config.cooldown_seconds - time_since_last
        
        return 0.0
    
    def wait_if_needed(self, api_name: str, cost: float = 1.0) -> bool:
        """
        Espera si es necesario antes de hacer la llamada
        
        Args:
            api_name: Nombre de la API
            cost: Costo en tokens
            
        Returns:
            True si se puede proceder, False si se excedió tiempo máximo de espera
        """
        max_wait_time = 60.0  # Máximo 60 segundos de espera
        
        can_proceed, wait_time = self.can_call(api_name, cost)
        
        if can_proceed:
            return True
        
        if wait_time > max_wait_time:
            logger.warning(f"Tiempo de espera excesivo para {api_name}: {wait_time:.2f}s")
            self.stats[api_name]['blocked_calls'] += 1
            return False
        
        logger.info(f"Rate limit alcanzado para {api_name}, esperando {wait_time:.2f}s")
        self.stats[api_name]['total_wait_time'] += wait_time
        time.sleep(wait_time)
        
        return True
    
    def register_call(self, api_name: str, cost: float = 1.0):
        """
        Registra una llamada exitosa a la API
        
        Args:
            api_name: Nombre de la API
            cost: Costo en tokens de la llamada
        """
        if api_name not in self.configs:
            return
        
        current_time = time.time()
        
        with self._lock:
            # Consumir tokens
            if api_name in self._token_buckets:
                self._refill_tokens(api_name)
                self._token_buckets[api_name]['tokens'] -= cost
            
            # Registrar en historial
            self._call_history[api_name].append(current_time)
            self._last_call[api_name] = current_time
            
            # Actualizar estadísticas
            self.stats[api_name]['total_calls'] += 1
        
        logger.debug(f"Llamada registrada para {api_name} (cost: {cost})")
    
    def get_remaining_calls(self, api_name: str) -> Dict[str, int]:
        """
        Obtiene el número de llamadas restantes para cada período
        
        Args:
            api_name: Nombre de la API
            
        Returns:
            Dict con llamadas restantes por período
        """
        if api_name not in self.configs:
            return {}
        
        config = self.configs[api_name]
        current_time = time.time()
        
        with self._lock:
            history = self._call_history[api_name]
            
            minute_ago = current_time - 60
            hour_ago = current_time - 3600
            day_ago = current_time - 86400
            
            calls_last_minute = sum(1 for t in history if t > minute_ago)
            calls_last_hour = sum(1 for t in history if t > hour_ago)
            calls_last_day = sum(1 for t in history if t > day_ago)
            
            return {
                'per_minute': max(0, config.calls_per_minute - calls_last_minute),
                'per_hour': max(0, config.calls_per_hour - calls_last_hour),
                'per_day': max(0, config.calls_per_day - calls_last_day),
                'tokens': self._token_buckets[api_name]['tokens']
            }
    
    def get_stats(self, api_name: Optional[str] = None) -> Dict:
        """
        Obtiene estadísticas de uso
        
        Args:
            api_name: Nombre de la API (None para todas)
            
        Returns:
            Estadísticas de uso
        """
        if api_name:
            return {
                **self.stats[api_name],
                'remaining': self.get_remaining_calls(api_name)
            }
        
        return {
            name: {
                **stats,
                'remaining': self.get_remaining_calls(name)
            }
            for name, stats in self.stats.items()
        }
    
    def reset_limits(self, api_name: str):
        """
        Resetea los límites para una API (útil para testing)
        
        Args:
            api_name: Nombre de la API
        """
        with self._lock:
            if api_name in self._call_history:
                self._call_history[api_name].clear()
            
            if api_name in self._token_buckets:
                config = self.configs[api_name]
                self._token_buckets[api_name] = {
                    'tokens': config.burst_size,
                    'max_tokens': config.burst_size,
                    'refill_rate': config.calls_per_minute / 60.0,
                    'last_refill': time.time()
                }
            
            if api_name in self._last_call:
                del self._last_call[api_name]
            
        logger.info(f"Límites reseteados para {api_name}")
    
    def update_config(self, api_name: str, config: RateLimitConfig):
        """
        Actualiza la configuración de límites para una API
        
        Args:
            api_name: Nombre de la API
            config: Nueva configuración
        """
        with self._lock:
            self.configs[api_name] = config
            
            # Actualizar token bucket
            self._token_buckets[api_name] = {
                'tokens': config.burst_size,
                'max_tokens': config.burst_size,
                'refill_rate': config.calls_per_minute / 60.0,
                'last_refill': time.time()
            }
        
        logger.info(f"Configuración actualizada para {api_name}")


# Decorador para aplicar rate limiting
def rate_limited(api_name: str, cost: float = 1.0):
    """
    Decorador para aplicar rate limiting a funciones
    
    Args:
        api_name: Nombre de la API
        cost: Costo en tokens de la llamada
    
    Uso:
        @rate_limited('twelvedata')
        def get_market_data():
            # código de la función
    """
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            # Buscar rate_limiter en self o crear uno global
            if hasattr(self, 'rate_limiter'):
                limiter = self.rate_limiter
            else:
                # Usar instancia global si existe
                if not hasattr(rate_limited, '_global_limiter'):
                    rate_limited._global_limiter = RateLimiter()
                limiter = rate_limited._global_limiter
            
            # Esperar si es necesario
            if not limiter.wait_if_needed(api_name, cost):
                logger.warning(f"Rate limit excedido para {api_name}, omitiendo llamada")
                return None
            
            try:
                # Ejecutar función
                result = func(self, *args, **kwargs)
                
                # Registrar llamada exitosa
                limiter.register_call(api_name, cost)
                
                return result
                
            except Exception as e:
                # No contar llamadas fallidas contra el límite
                logger.error(f"Error en llamada a {api_name}: {e}")
                raise
        
        return wrapper
    return decorator
