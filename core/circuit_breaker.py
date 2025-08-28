"""
Circuit Breaker Pattern Implementation
Previene cascadas de errores y protege el sistema
"""
import time
import threading
from enum import Enum
from typing import Callable, Optional, Any, Dict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Estados del circuit breaker"""
    CLOSED = "closed"      # Funcionando normalmente
    OPEN = "open"          # Circuito abierto, rechazando llamadas
    HALF_OPEN = "half_open"  # Probando si el servicio se recuperó

class CircuitBreaker:
    """
    Implementación del patrón Circuit Breaker
    
    Protege contra fallos en cascada cortando el circuito
    cuando se detectan demasiados errores
    """
    
    def __init__(self,
                 name: str,
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 expected_exception: type = Exception):
        """
        Args:
            name: Nombre del circuit breaker
            failure_threshold: Número de fallos antes de abrir el circuito
            recovery_timeout: Segundos antes de intentar recuperación
            expected_exception: Tipo de excepción que cuenta como fallo
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        # Estado
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.success_count = 0
        
        # Estadísticas
        self.total_calls = 0
        self.total_failures = 0
        self.total_successes = 0
        self.circuit_opened_count = 0
        
        # Thread safety
        self.lock = threading.RLock()
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Ejecutar función a través del circuit breaker
        
        Args:
            func: Función a ejecutar
            *args, **kwargs: Argumentos para la función
            
        Returns:
            Resultado de la función
            
        Raises:
            CircuitOpenException: Si el circuito está abierto
            Exception: Si la función falla
        """
        with self.lock:
            self.total_calls += 1
            
            # Verificar estado del circuito
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    logger.info(f"Circuit {self.name} en modo HALF_OPEN")
                else:
                    raise CircuitOpenException(
                        f"Circuit {self.name} está ABIERTO"
                    )
        
        # Intentar ejecutar la función
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
            
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Verificar si deberíamos intentar recuperación"""
        if not self.last_failure_time:
            return False
        
        elapsed = time.time() - self.last_failure_time
        return elapsed >= self.recovery_timeout
    
    def _on_success(self):
        """Manejar llamada exitosa"""
        with self.lock:
            self.total_successes += 1
            
            if self.state == CircuitState.HALF_OPEN:
                # Recuperación exitosa
                self.success_count += 1
                
                if self.success_count >= 2:  # Requiere 2 éxitos consecutivos
                    self.state = CircuitState.CLOSED
                    self.failure_count = 0
                    self.success_count = 0
                    logger.info(f"Circuit {self.name} CERRADO (recuperado)")
            
            elif self.state == CircuitState.CLOSED:
                # Reset contador de fallos en llamada exitosa
                self.failure_count = 0
    
    def _on_failure(self):
        """Manejar fallo en llamada"""
        with self.lock:
            self.total_failures += 1
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                # Fallo durante recuperación, volver a abrir
                self.state = CircuitState.OPEN
                self.success_count = 0
                logger.warning(f"Circuit {self.name} ABIERTO nuevamente (fallo en recuperación)")
                
            elif self.state == CircuitState.CLOSED:
                # Verificar si debemos abrir el circuito
                if self.failure_count >= self.failure_threshold:
                    self.state = CircuitState.OPEN
                    self.circuit_opened_count += 1
                    logger.error(
                        f"Circuit {self.name} ABIERTO "
                        f"(threshold {self.failure_threshold} alcanzado)"
                    )
    
    def reset(self):
        """Resetear el circuit breaker manualmente"""
        with self.lock:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.success_count = 0
            self.last_failure_time = None
            logger.info(f"Circuit {self.name} reseteado manualmente")
    
    def get_status(self) -> Dict:
        """Obtener estado del circuit breaker"""
        with self.lock:
            return {
                'name': self.name,
                'state': self.state.value,
                'failure_count': self.failure_count,
                'total_calls': self.total_calls,
                'total_failures': self.total_failures,
                'total_successes': self.total_successes,
                'success_rate': (
                    self.total_successes / self.total_calls * 100
                    if self.total_calls > 0 else 0
                ),
                'circuit_opened_count': self.circuit_opened_count,
                'last_failure': (
                    datetime.fromtimestamp(self.last_failure_time).isoformat()
                    if self.last_failure_time else None
                )
            }

class CircuitOpenException(Exception):
    """Excepción cuando el circuito está abierto"""
    pass

class CircuitBreakerManager:
    """Gestor centralizado de circuit breakers"""
    
    def __init__(self):
        self.breakers = {}
        self.lock = threading.Lock()
        
        # Crear circuit breakers por defecto
        self._create_default_breakers()
    
    def _create_default_breakers(self):
        """Crear circuit breakers para servicios conocidos"""
        # API de datos
        self.add_breaker(
            'twelvedata',
            failure_threshold=3,
            recovery_timeout=60
        )
        
        # Broker
        self.add_breaker(
            'mt5',
            failure_threshold=5,
            recovery_timeout=30
        )
        
        # IA
        self.add_breaker(
            'ollama',
            failure_threshold=3,
            recovery_timeout=120
        )
        
        # Notificaciones
        self.add_breaker(
            'telegram',
            failure_threshold=10,
            recovery_timeout=60
        )
    
    def add_breaker(self, 
                   name: str,
                   failure_threshold: int = 5,
                   recovery_timeout: int = 60,
                   expected_exception: type = Exception) -> CircuitBreaker:
        """Añadir nuevo circuit breaker"""
        with self.lock:
            breaker = CircuitBreaker(
                name,
                failure_threshold,
                recovery_timeout,
                expected_exception
            )
            self.breakers[name] = breaker
            return breaker
    
    def get_breaker(self, name: str) -> Optional[CircuitBreaker]:
        """Obtener circuit breaker por nombre"""
        return self.breakers.get(name)
    
    def call_with_breaker(self, 
                         breaker_name: str,
                         func: Callable,
                         *args, 
                         **kwargs) -> Any:
        """Ejecutar función con circuit breaker"""
        breaker = self.get_breaker(breaker_name)
        if not breaker:
            # Si no hay breaker, ejecutar directamente
            return func(*args, **kwargs)
        
        return breaker.call(func, *args, **kwargs)
    
    def reset_all(self):
        """Resetear todos los circuit breakers"""
        with self.lock:
            for breaker in self.breakers.values():
                breaker.reset()
    
    def get_all_status(self) -> Dict[str, Dict]:
        """Obtener estado de todos los breakers"""
        with self.lock:
            return {
                name: breaker.get_status()
                for name, breaker in self.breakers.items()
            }

# Manager global
circuit_manager = CircuitBreakerManager()

# Decorador para aplicar circuit breaker
def circuit_breaker(name: str):
    """Decorador para aplicar circuit breaker a una función"""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            return circuit_manager.call_with_breaker(
                name, func, *args, **kwargs
            )
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    
    return decorator
