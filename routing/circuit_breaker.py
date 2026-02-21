"""
Circuit Breaker Pattern (Milestone 3)
Implements automatic failover between ML models based on latency
"""
import time
import threading
from enum import Enum
from typing import Callable, Any, Optional
from dataclasses import dataclass
from config import settings


class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker"""
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout_seconds: float = 30.0
    latency_threshold_ms: int = 500


class CircuitBreaker:
    """
    Circuit breaker implementation for ML model failover.
    
    If transformer model latency exceeds 500ms, automatically
    failover to the lightweight baseline model.
    """
    
    def __init__(self, name: str = "default", config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig(
            latency_threshold_ms=settings.CIRCUIT_BREAKER_THRESHOLD_MS
        )
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._lock = threading.RLock()
        
        # Latency tracking
        self._latency_history: list = []
        self._max_latency_history = 100
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state"""
        with self._lock:
            # Check if we should transition from OPEN to HALF_OPEN
            if self._state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self._state = CircuitState.HALF_OPEN
            
            return self._state
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self._last_failure_time is None:
            return True
        
        return (time.time() - self._last_failure_time) >= self.config.timeout_seconds
    
    def record_success(self) -> None:
        """Record a successful call"""
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
                    print(f"Circuit '{self.name}' CLOSED - recovered")
            else:
                self._failure_count = 0
    
    def record_failure(self, latency_ms: float = None) -> None:
        """Record a failed call"""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            
            # Check if latency exceeded threshold
            if latency_ms and latency_ms > self.config.latency_threshold_ms:
                print(f"Circuit '{self.name}' latency {latency_ms}ms exceeded threshold {self.config.latency_threshold_ms}ms")
                self._trigger_open()
            
            # Check if failure count exceeded threshold
            if self._failure_count >= self.config.failure_threshold:
                self._trigger_open()
    
    def _trigger_open(self) -> None:
        """Trigger circuit to open"""
        if self._state != CircuitState.OPEN:
            self._state = CircuitState.OPEN
            print(f"Circuit '{self.name}' OPEN - too many failures or high latency")
    
    def record_latency(self, latency_ms: float) -> None:
        """
        Record latency and check if threshold exceeded.
        
        Args:
            latency_ms: Latency in milliseconds
        """
        with self._lock:
            self._latency_history.append(latency_ms)
            if len(self._latency_history) > self._max_latency_history:
                self._latency_history.pop(0)
            
            # Check average latency
            if len(self._latency_history) >= 10:
                avg_latency = sum(self._latency_history) / len(self._latency_history)
                if avg_latency > self.config.latency_threshold_ms:
                    self.record_failure(latency_ms=avg_latency)
    
    def is_available(self) -> bool:
        """Check if circuit allows requests"""
        return self.state != CircuitState.OPEN
    
    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute a function through the circuit breaker.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Result of function execution
            
        Raises:
            RuntimeError: If circuit is open
        """
        if not self.is_available():
            raise RuntimeError(f"Circuit '{self.name}' is OPEN")
        
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            self.record_latency(latency_ms)
            self.record_success()
            return result
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self.record_failure(latency_ms)
            raise e
    
    async def execute_async(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute an async function through the circuit breaker.
        
        Args:
            func: Async function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Result of async function execution
            
        Raises:
            RuntimeError: If circuit is open
        """
        if not self.is_available():
            raise RuntimeError(f"Circuit '{self.name}' is OPEN")
        
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            latency_ms = (time.time() - start_time) * 1000
            self.record_latency(latency_ms)
            self.record_success()
            return result
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self.record_failure(latency_ms)
            raise e
    
    def reset(self) -> None:
        """Manually reset the circuit breaker"""
        with self._lock:
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._latency_history.clear()


# Global circuit breaker instances
transformer_circuit = CircuitBreaker(
    name="transformer",
    config=CircuitBreakerConfig(latency_threshold_ms=settings.CIRCUIT_BREAKER_THRESHOLD_MS)
)
baseline_circuit = CircuitBreaker(name="baseline")
