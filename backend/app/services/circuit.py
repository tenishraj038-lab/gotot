"""
Circuit breaker implementation for external service calls.
Prevents cascading failures by failing fast after repeated errors.
"""
import asyncio
import logging
import time
from enum import Enum
from functools import wraps
from typing import Callable, Optional

logger = logging.getLogger("gotot.circuit")


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = 0.0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        return self._state

    async def call(self, func: Callable, *args, **kwargs):
        async with self._lock:
            if self._state == CircuitState.OPEN:
                if time.time() - self._last_failure_time >= self.recovery_timeout:
                    logger.info("Circuit %s half-open — testing recovery", self.name)
                    self._state = CircuitState.HALF_OPEN
                else:
                    raise CircuitOpenError(
                        f"Circuit {self.name} is OPEN. "
                        f"Retry in {self.recovery_timeout - (time.time() - self._last_failure_time):.0f}s"
                    )

        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            async with self._lock:
                if self._state == CircuitState.HALF_OPEN:
                    logger.info("Circuit %s closed — recovery successful", self.name)
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
            return result
        except Exception as e:
            async with self._lock:
                self._failure_count += 1
                self._last_failure_time = time.time()
                if self._failure_count >= self.failure_threshold or self._state == CircuitState.HALF_OPEN:
                    self._state = CircuitState.OPEN
                    logger.error(
                        "Circuit %s opened after %d failures", self.name, self._failure_count
                    )
            raise


class CircuitOpenError(Exception):
    pass


_circuits: dict[str, CircuitBreaker] = {}


def get_circuit(name: str, failure_threshold: int = 5, recovery_timeout: float = 30.0) -> CircuitBreaker:
    if name not in _circuits:
        _circuits[name] = CircuitBreaker(name, failure_threshold, recovery_timeout)
    return _circuits[name]
