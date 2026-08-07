"""Request context tracking using contextvars.

Enables storing and retrieving a correlation request ID across all execution
layers without explicitly passing it through every function signature.
"""

from __future__ import annotations

import contextvars
import datetime
import random
from datetime import timezone
from typing import Any, Generator

_REQUEST_ID: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="REQ-system-default")


def get_request_id() -> str:
    """Retrieve the current request's correlation ID.

    Returns:
        The active request ID string.
    """
    return _REQUEST_ID.get()


def set_request_id(request_id: str) -> contextvars.Token[str]:
    """Set the request ID for the current context block.

    Args:
        request_id: The correlation ID to set.

    Returns:
        A token that can be used to restore the previous context.
    """
    return _REQUEST_ID.set(request_id)


def reset_request_id(token: contextvars.Token[str]) -> None:
    """Reset the request ID to its previous value.

    Args:
        token: The token returned by set_request_id.
    """
    _REQUEST_ID.reset(token)


def generate_request_id() -> str:
    """Generate a new request correlation ID.

    Format: REQ-YYYYMMDD-NNNNN (e.g. REQ-20260807-00152)
    """
    now = datetime.datetime.now(timezone.utc)
    date_str = now.strftime("%Y%m%d")
    counter = random.randint(10000, 99999)
    return f"REQ-{date_str}-{counter}"


class request_id_scope:
    """Context manager to scope a request ID.

    Usage:
        with request_id_scope("REQ-12345"):
            # All calls to get_request_id() here return "REQ-12345"
            pass
    """

    def __init__(self, request_id: str) -> None:
        self._request_id = request_id
        self._token: contextvars.Token[str] | None = None

    def __enter__(self) -> str:
        self._token = set_request_id(self._request_id)
        return self._request_id

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: Any) -> None:
        if self._token is not None:
            reset_request_id(self._token)
