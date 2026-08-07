"""Timing and latency measurement utilities for SentinelAI.

Enables tracking elapsed time for components and layers throughout the execution
pipeline using contextvars, decorators, and context managers.
"""

from __future__ import annotations

import contextvars
import time
from functools import wraps
from typing import Any, Callable


# Context-local timing registry
_TIMINGS: contextvars.ContextVar[dict[str, float]] = contextvars.ContextVar("request_timings", default={})
_METADATA: contextvars.ContextVar[dict[str, Any]] = contextvars.ContextVar("request_metadata", default={})


def clear_timings() -> None:
    """Reset timings and metadata for the current context."""
    _TIMINGS.set({})
    _METADATA.set({})


def get_timings() -> dict[str, float]:
    """Retrieve all recorded timings for the current request.

    Returns:
        A dictionary mapping timing labels to durations in milliseconds.
    """
    return _TIMINGS.get()


def record_timing(name: str, duration_ms: float) -> None:
    """Add a timing record to the current context.

    Args:
        name: Label for the measured operation.
        duration_ms: Duration in milliseconds.
    """
    timings = _TIMINGS.get().copy()
    # Sum up multiple measurements with same label
    timings[name] = timings.get(name, 0.0) + duration_ms
    _TIMINGS.set(timings)


class timer_scope:
    """Context manager to measure the latency of a code block.

    Usage:
        with timer_scope("Ollama generation"):
            # code to measure
    """

    def __init__(self, name: str) -> None:
        self.name = name
        self._start: float = 0.0

    def __enter__(self) -> timer_scope:
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: Any) -> None:
        elapsed_ms = (time.perf_counter() - self._start) * 1000.0
        record_timing(self.name, elapsed_ms)


def timed(name: str | None = None) -> Callable:
    """Decorator to measure and record the execution duration of a function.

    Usage:
        @timed("policy_evaluation")
        def evaluate(self, plan):
            ...
    """
    def decorator(func: Callable) -> Callable:
        timing_name = name or func.__name__

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                record_timing(timing_name, elapsed_ms)
        return wrapper
    return decorator


def get_metadata() -> dict[str, Any]:
    """Retrieve all recorded request metadata.

    Returns:
        A dictionary containing request metadata.
    """
    return _METADATA.get()


def record_metadata(key: str, value: Any) -> None:
    """Record a piece of request metadata in the active context.

    Args:
        key: The metadata key identifier.
        value: The metadata value to record.
    """
    meta = _METADATA.get().copy()
    meta[key] = value
    _METADATA.set(meta)

