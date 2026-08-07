"""Bounded, deterministic context-window management."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from app.context.models import ContextEntry, ContextRole


@dataclass(frozen=True, slots=True)
class ContextWindow:
    """Limits the number and aggregate size of retained context entries."""

    max_user_messages: int = 10
    max_assistant_messages: int = 10
    max_tool_outputs: int = 5
    max_total_characters: int = 30_000

    def __post_init__(self) -> None:
        if min(self.max_user_messages, self.max_assistant_messages, self.max_tool_outputs, self.max_total_characters) < 0:
            raise ValueError("Context window limits must be non-negative.")

    def trim(self, entries: Iterable[ContextEntry]) -> list[ContextEntry]:
        """Return entries that fit the limits, removing oldest entries first."""
        retained = list(entries)
        role_limits = {
            ContextRole.USER: self.max_user_messages,
            ContextRole.ASSISTANT: self.max_assistant_messages,
            ContextRole.TOOL: self.max_tool_outputs,
        }
        for role, limit in role_limits.items():
            while sum(entry.role is role for entry in retained) > limit:
                index = next(i for i, entry in enumerate(retained) if entry.role is role)
                retained.pop(index)

        while sum(len(entry.content) for entry in retained) > self.max_total_characters:
            retained.pop(0)
        return retained
