"""Immutable data models used by the session context engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping
from uuid import uuid4


class ContextRole(str, Enum):
    """The conversational role represented by a context entry."""

    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    SYSTEM = "system"


class ContextSource(str, Enum):
    """The subsystem that supplied a context entry."""

    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    SYSTEM = "system"
    MEMORY = "memory"
    CODE = "code"
    TERMINAL = "terminal"


@dataclass(frozen=True, slots=True)
class ContextEntry:
    """A single, session-scoped item available to a future LLM request.

    Metadata is copied into an immutable mapping to preserve the entry's
    snapshot semantics. Entries are deliberately not persisted.
    """

    role: ContextRole
    source: ContextSource
    content: str
    metadata: Mapping[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not isinstance(self.content, str):
            raise TypeError("ContextEntry content must be a string.")
        if self.timestamp.tzinfo is None:
            raise ValueError("ContextEntry timestamp must be timezone-aware.")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
