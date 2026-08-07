"""Session-only owner of context entries observed from the execution pipeline."""

from __future__ import annotations

import logging
from typing import Any

from app.artifacts.models import Artifact, ExecutionArtifactType
from app.artifacts.store import ArtifactStore
from app.context.formatter import ContextFormatter
from app.context.models import ContextEntry, ContextRole, ContextSource
from app.context.policy import ContextPolicy
from app.context.resolver import ContextResolver, ResolvedContext
from app.context.window import ContextWindow
from app.core.request_context import get_request_id
from app.tools.result import ExecutionResult

logger = logging.getLogger("SentinelAI.ContextManager")



class ContextManager:
    """Stores bounded, policy-filtered context for one controller session.

    The manager observes user input, assistant replies, and successful tool
    results. It neither calls an LLM nor changes plans, policies, or execution.
    """

    def __init__(
        self,
        policy: ContextPolicy | None = None,
        window: ContextWindow | None = None,
        formatter: ContextFormatter | None = None,
    ) -> None:
        self._policy = policy or ContextPolicy()
        self._window = window or ContextWindow()
        self._formatter = formatter or ContextFormatter()
        self._entries: list[ContextEntry] = []
        self.artifact_store = ArtifactStore()
        self.resolver = ContextResolver()
        self._artifact_counter = 0

    def add_user_message(self, content: str, metadata: dict[str, Any] | None = None) -> ContextEntry | None:
        return self._add(content, ContextRole.USER, ContextSource.USER, metadata)

    def add_assistant_message(self, content: str, metadata: dict[str, Any] | None = None) -> ContextEntry | None:
        return self._add(content, ContextRole.ASSISTANT, ContextSource.ASSISTANT, metadata)

    def add_tool_result(
        self,
        result: ExecutionResult | str,
        plan: Any | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ContextEntry | None:
        """Store a bounded summary of a successful, non-exceptional tool result."""
        if isinstance(result, str):
            return self._add(result, ContextRole.TOOL, ContextSource.TOOL, metadata)
        if not getattr(result, "success", False):
            logger.debug("Discarded unsuccessful tool result from session context.")
            return None
        
        self.capture(result, plan)

        tool_metadata: dict[str, Any] = {
            "tool": getattr(plan, "tool", "tool"),
            "intent": getattr(plan, "intent", ""),
            **(metadata or {}),
        }
        data = getattr(result, "data", None) or {}
        for key in ("path", "url", "query", "name"):
            if isinstance(data.get(key), str):
                tool_metadata[key] = data[key]
        content = result.message
        if isinstance(data.get("content"), str):
            content = f"{result.message}\n\n{data['content']}"
            tool_metadata["label"] = data.get("path", "File content")
        return self._add(content, ContextRole.TOOL, ContextSource.TOOL, tool_metadata)

    def capture(self, result: ExecutionResult, plan: Any) -> Artifact | None:
        """Capture a successful execution result as an artifact in the store.

        Args:
            result: The execution result returned by a tool.
            plan: The plan that was executed.

        Returns:
            The captured Artifact, or None if not successful or invalid.
        """
        if not getattr(result, "success", False):
            return None
        if plan is None:
            logger.debug("Cannot capture artifact: plan is None.")
            return None

        tool = getattr(plan, "tool", "")
        intent = getattr(plan, "intent", "")
        if tool == "llm" or intent == "chat":
            return None
        data = getattr(result, "data", None) or {}

        artifact_type = ExecutionArtifactType.TEXT
        name = f"{tool} output"
        content = result.message
        metadata: dict[str, Any] = {
            "tool": tool,
            "intent": intent,
        }

        # Filesystem Tool
        if tool == "filesystem":
            if intent == "read_file":
                path = data.get("path") or plan.parameters.get("path", "")
                name = path.split("/")[-1].split("\\")[-1] or "file"
                content = data.get("content") or result.message
                metadata["path"] = path
                
                # Determine type from file extension
                ext = name.split(".")[-1].lower() if "." in name else ""
                if ext in ("py", "js", "ts", "cpp", "c", "h", "java", "go", "rs", "sh", "bat", "ps1", "html", "css"):
                    artifact_type = ExecutionArtifactType.CODE
                elif ext == "json":
                    artifact_type = ExecutionArtifactType.JSON
                else:
                    artifact_type = ExecutionArtifactType.TEXT
            elif intent == "list_directory":
                path = data.get("path") or plan.parameters.get("path", "")
                name = f"Directory contents of '{path.split('/')[-1].split('\\')[-1]}'"
                contents = data.get("directory_contents", [])
                if contents:
                    content = "\n".join(
                        f"- {item.get('name')} ({'Directory' if item.get('is_directory') else f'{item.get('size', 0)} bytes'})"
                        for item in contents
                    )
                else:
                    content = "Empty directory."
                metadata["path"] = path
                artifact_type = ExecutionArtifactType.DIRECTORY

        # Browser Tool
        elif tool == "browser":
            if intent == "search_web":
                query = data.get("query") or plan.parameters.get("query", "")
                name = f"Search query: '{query}'"
                content = f"Search query: '{query}'\nURL: {data.get('url', '')}"
                metadata["query"] = query
                metadata["url"] = data.get("url")
                artifact_type = ExecutionArtifactType.SEARCH_RESULTS
            elif intent == "open_url":
                url = data.get("url") or plan.parameters.get("url", "")
                name = url
                content = f"Opened URL: {url}"
                metadata["url"] = url
                artifact_type = ExecutionArtifactType.WEBPAGE

        # Application Tool
        elif tool == "application":
            app_name = data.get("name") or plan.parameters.get("name", "")
            name = app_name
            content = result.message
            metadata["name"] = app_name
            artifact_type = ExecutionArtifactType.APPLICATION


        self._artifact_counter += 1
        artifact_id = f"ART-{self._artifact_counter:03d}"

        artifact = Artifact(
            id=artifact_id,
            request_id=get_request_id(),
            type=artifact_type,
            name=name,
            content=content,
            metadata=metadata,
        )

        self.artifact_store.save(artifact)
        return artifact

    def build_context(self, current_user_request: str | None = None) -> str:
        """Return formatted context, keeping the current request out of history."""
        entries = self.history()
        if current_user_request is not None and entries and entries[-1].role is ContextRole.USER and entries[-1].content == current_user_request:
            entries = entries[:-1]
        return self._formatter.build_context(entries, current_user_request)

    def build_chat_prompt(self, current_user_request: str) -> str:
        """Return a full chat prompt with explicit assistant instructions."""
        entries = self.history()
        if entries and entries[-1].role is ContextRole.USER and entries[-1].content == current_user_request:
            entries = entries[:-1]
        return self._formatter.build_chat_prompt(entries, current_user_request)

    def resolve_context(self, user_query: str) -> ResolvedContext:
        """Resolve and rank context (history and artifacts) for a user query."""
        return self.resolver.resolve(user_query, self.history(), self.artifact_store.list_all())

    def build_chat_prompt_resolved(self, resolved: ResolvedContext, current_user_request: str) -> str:
        """Return a full chat prompt including resolved artifacts."""
        return self._formatter.build_chat_prompt_resolved(resolved, current_user_request)

    def history(self) -> tuple[ContextEntry, ...]:
        """Return an immutable snapshot in insertion order."""
        return tuple(self._entries)

    def clear(self) -> None:
        """Discard all session context."""
        self._entries.clear()
        self.artifact_store.clear()
        self._artifact_counter = 0

    def trim(self) -> None:
        """Apply configured window limits to the current session."""
        self._entries = self._window.trim(self._entries)

    def _add(self, content: str, role: ContextRole, source: ContextSource, metadata: dict[str, Any] | None) -> ContextEntry | None:
        if not self._policy.allows(content, role=role, source=source, metadata=metadata):
            logger.info("Context entry rejected by policy (role=%s, source=%s).", role.value, source.value)
            return None
        entry = ContextEntry(role=role, source=source, content=content, metadata=metadata or {})
        self._entries.append(entry)
        self.trim()
        return entry
