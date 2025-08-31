"""
Rate Limiting para APIs
Previene exceder límites de las APIs externas
"""
import time
import threading
from collections import deque
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter genérico con ventana deslizante"""
    
    def __init__(self, max_calls: int, time_window: int):
        """
        Args:
            max_calls: Número máximo de llamadas permitidas
            time_window: Ventana de tiempo en segundos
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = deque()
        self.lock = threading.Lock()
    
    def acquire(self, block: bool = True) -> bool:
        """
        Intenta adquirir un slot para hacer una llamada
        
        Args:
            block: Si bloquear hasta que haya un slot disponible
            
        Returns:
            True si se puede hacer la llamada, False si no
        """
        while True:
            with self.lock:
                now = time.time()
                
                # Limpiar llamadas antiguas
                while self.calls and self.calls[0] <= now - self.time_window:
                    self.calls.popleft()
                
                # Verificar si podemos hacer la llamada
                if len(self.calls) < self.max_calls:
                    self.calls.append(now)
                    return True
                
                if not block:
                    return False
                
                # Calcular tiempo de espera
                oldest_call = self.calls[0]
                wait_time = (oldest_call + self.time_window) - now
            
            # Esperar fuera del lock
            if wait_time > 0:
                logger.debug(f"Rate limit alcanzado, esperando {wait_time:.2f}s")
                time.sleep(wait_time)
    
    def reset(self):
        """Resetear el rate limiter"""
        with self.lock:
            self.calls.clear()

class APIRateLimitManager:
    """Gestor centralizado de rate limiting para todas las APIs"""
    
    def __init__(self):
        # Configuración de límites por API
        self.limiters = {
            'twelvedata': RateLimiter(
                max_calls=8,  # API free tier: 8 calls/minute
                time_window=60
            ),
            'telegram': RateLimiter(
                max_calls=30,  # Telegram: 30 msgs/second
                time_window=1
            ),
            'ollama': RateLimiter(
                max_calls=10,  # Local, pero limitamos para no saturar
                time_window=60
            ),
            'mt5': RateLimiter(
                max_calls=100,  # MT5 puede manejar muchas llamadas
                time_window=1
            )
        }
        
        # Estadísticas
        self.stats = {
            api: {
                'total_calls': 0,
                'blocked_calls': 0,
                'last_call': None
            }
            for api in self.limiters
        }
        
        self.lock = threading.Lock()
    
    def acquire(self, api: str, block: bool = True) -> bool:
        """
        Adquirir permiso para llamar a una API
        
        Args:
            api: Nombre de la API
            block: Si esperar cuando se alcanza el límite
            
        Returns:
            True si se puede hacer la llamada
        """
        if api not in self.limiters:
            logger.warning(f"API {api} no tiene rate limiter configurado")
            return True
        
        # Intentar adquirir
        acquired = self.limiters[api].acquire(block)
        
        # Actualizar estadísticas
        with self.lock:
            self.stats[api]['total_calls'] += 1
            if not acquired:
                self.stats[api]['blocked_calls'] += 1
            else:
                self.stats[api]['last_call'] = datetime.now()
        
        if not acquired:
            logger.warning(f"Rate limit bloqueado para {api}")
        
        return acquired
    
    def get_stats(self) -> Dict:
        """Obtener estadísticas de uso"""
        with self.lock:
            return self.stats.copy()
    
    def reset(self, api: Optional[str] = None):
        """Resetear limiters"""
        if api:
            if api in self.limiters:
                self.limiters[api].reset()
                with self.lock:
                    self.stats[api]['blocked_calls'] = 0
        else:
            for api in self.limiters:
                self.limiters[api].reset()
            with self.lock:
                for api in self.stats:
                    self.stats[api]['blocked_calls'] = 0

class RateLimitedAPI:
    """Decorador para aplicar rate limiting a funciones de API"""
    
    def __init__(self, api_name: str, manager: Optional[APIRateLimitManager] = None):
        self.api_name = api_name
        self.manager = manager or _global_manager
    
    def __call__(self, func: Callable):
        def wrapper(*args, **kwargs):
            # Adquirir permiso antes de llamar
            if not self.manager.acquire(self.api_name):
                raise Exception(f"Rate limit excedido para {self.api_name}")
            
            # Ejecutar función
            return func(*args, **kwargs)
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper

# Manager global
_global_manager = APIRateLimitManager()

# Funciones de conveniencia
def acquire_limit(api: str, block: bool = True) -> bool:
    """Adquirir permiso para llamar a una API"""
    return _global_manager.acquire(api, block)

def get_rate_limit_stats() -> Dict:
    """Obtener estadísticas de rate limiting"""
    return _global_manager.get_stats()

def reset_rate_limits(api: Optional[str] = None):
    """Resetear rate limits"""
    _global_manager.reset(api)

# Decoradores pre-configurados
rate_limited_twelvedata = lambda f: RateLimitedAPI('twelvedata')(f)
rate_limited_telegram = lambda f: RateLimitedAPI('telegram')(f)
rate_limited_ollama = lambda f: RateLimitedAPI('ollama')(f)
rate_limited_mt5 = lambda f: RateLimitedAPI('mt5')(f)
