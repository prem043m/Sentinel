"""Prompt formatting for retained session context and resolved artifacts."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from app.context.models import ContextEntry, ContextRole

if TYPE_CHECKING:
    from app.context.resolver import ResolvedContext


class ContextFormatter:
    """Converts context entries and resolved artifacts into a stable LLM prompt."""

    _CHAT_INSTRUCTIONS = (
        "You are SentinelAI's chat assistant. Use the session context and any provided "
        "relevant artifacts to answer the current user request. Do not repeat the context "
        "labels, do not echo the prompt, and do not mention internal implementation details."
    )

    def build_context(
        self,
        entries: Iterable[ContextEntry],
        current_user_request: str | None = None,
    ) -> str:
        """Format prior conversation, tool output, and the current request."""
        entries_list = list(entries)
        conversation = [entry for entry in entries_list if entry.role in {ContextRole.USER, ContextRole.ASSISTANT}]
        # Cap to last 10 messages (approx 5 exchanges) to control token size
        conversation = conversation[-10:]

        tools = [entry for entry in entries_list if entry.role is ContextRole.TOOL]
        # Cap to last 5 tool outputs to prevent token bloat
        tools = tools[-5:]

        systems = [entry for entry in entries_list if entry.role is ContextRole.SYSTEM]
        parts: list[str] = ["[SESSION CONTEXT]"]

        if systems:
            parts.extend(["", "System"])
            parts.extend(entry.content for entry in systems)
        if conversation:
            parts.extend(["", "Conversation"])
            for entry in conversation:
                label = "User" if entry.role is ContextRole.USER else "Assistant"
                parts.extend([f"{label}:", entry.content])
        if tools:
            parts.extend(["", "Tool Output"])
            for entry in tools:
                label = str(entry.metadata.get("label") or entry.metadata.get("path") or entry.metadata.get("tool") or "Tool")
                parts.extend([f"{label}:", entry.content])
        if current_user_request is not None:
            parts.extend(["", "Current User Request", current_user_request])
        return "\n".join(parts)

    def build_resolved_context(
        self,
        resolved: ResolvedContext,
        current_user_request: str | None = None,
    ) -> str:
        """Format resolved context history along with any relevant artifacts."""
        parts: list[str] = []

        # 1. Format relevant artifacts
        if resolved.artifacts:
            parts.append("[RELEVANT ARTIFACTS]")
            for art in resolved.artifacts:
                parts.extend([
                    f"ID: {art.id}",
                    f"Type: {art.type.value}",
                    f"Name: {art.name}",
                    "Content:",
                    art.content,
                    ""  # blank spacer line
                ])

        # 2. Format standard conversation context
        parts.append(self.build_context(resolved.conversation_history, current_user_request))
        return "\n".join(parts)

    def build_chat_prompt(
        self,
        entries: Iterable[ContextEntry],
        current_user_request: str,
    ) -> str:
        """Build the legacy chat prompt from session context and the request."""
        context = self.build_context(entries, current_user_request)
        return f"{self._CHAT_INSTRUCTIONS}\n\n{context}"

    def build_chat_prompt_resolved(
        self,
        resolved: ResolvedContext,
        current_user_request: str,
    ) -> str:
        """Build the full chat prompt using resolved history and artifacts."""
        context = self.build_resolved_context(resolved, current_user_request)
        return f"{self._CHAT_INSTRUCTIONS}\n\n{context}"
