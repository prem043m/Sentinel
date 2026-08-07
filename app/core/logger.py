"""Request-correlated logging for SentinelAI.

Exposes a RequestLogger that automatically attaches context details (such as the
correlation request_id) to all log records.
"""

from __future__ import annotations

import logging
from typing import Any

from app.core.request_context import get_request_id


class RequestLogger:
    """Wrapper around standard Logger to ensure request correlation.

    Injects 'request_id' and 'component' into the log record's extra dictionary,
    enabling structured traceability.
    """

    def __init__(self, name: str) -> None:
        self._logger = logging.getLogger(name)
        self.name = name

    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log(logging.DEBUG, msg, *args, **kwargs)

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log(logging.INFO, msg, *args, **kwargs)

    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log(logging.WARNING, msg, *args, **kwargs)

    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log(logging.ERROR, msg, *args, **kwargs)

    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log(logging.CRITICAL, msg, *args, **kwargs)

    def exception(self, msg: str, *args: Any, **kwargs: Any) -> None:
        kwargs["exc_info"] = True
        self._log(logging.ERROR, msg, *args, **kwargs)

    def isEnabledFor(self, level: int) -> bool:
        return self._logger.isEnabledFor(level)

    def _log(self, level: int, msg: str, *args: Any, **kwargs: Any) -> None:
        extra = kwargs.setdefault("extra", {})
        if not isinstance(extra, dict):
            extra = {}
            kwargs["extra"] = extra
        extra.setdefault("request_id", get_request_id())
        extra.setdefault("component", self.name)
        self._logger.log(level, msg, *args, **kwargs)
