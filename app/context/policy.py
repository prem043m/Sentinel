"""Admission policy for sensitive or unsuitable session context."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from app.context.models import ContextRole, ContextSource


@dataclass(frozen=True, slots=True)
class ContextPolicy:
    """Decides whether content is safe and useful to retain in a session.

    This intentionally conservative policy protects the prompt from accidental
    secret disclosure, binary data, stack traces, and noisy debug output.
    """

    max_content_characters: int = 10_000

    _SENSITIVE_KEYS = frozenset({"password", "secret", "token", "api_key", "apikey", "credential"})
    _SENSITIVE_PATTERN = re.compile(
        r"(?:password|secret|api[_-]?key|access[_-]?token|bearer\s+)\s*[:=]",
        re.IGNORECASE,
    )
    _STACK_TRACE_PATTERN = re.compile(r"(?:traceback \(most recent call last\)|\bfile \".+\", line \d+)", re.IGNORECASE)
    _DEBUG_PATTERN = re.compile(r"^\s*(?:debug|trace)\s*(?:\[|:|-)", re.IGNORECASE | re.MULTILINE)

    def allows(
        self,
        content: object,
        *,
        role: ContextRole,
        source: ContextSource,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Return whether content may be stored for this session."""
        if not isinstance(content, str) or not content.strip() or "\x00" in content:
            return False
        if len(content) > self.max_content_characters:
            return False
        if self._SENSITIVE_PATTERN.search(content) or self._STACK_TRACE_PATTERN.search(content):
            return False
        if source is ContextSource.TOOL and self._DEBUG_PATTERN.search(content):
            return False
        return not any(
            str(key).lower() in self._SENSITIVE_KEYS
            for key in (metadata or {})
        )
