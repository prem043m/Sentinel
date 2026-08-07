"""Central repository for tool and intent capabilities."""

from __future__ import annotations

import logging
from typing import Iterable

from app.artifacts.types import ArtifactType
from app.planner.capabilities.models import (
    CapabilityCategory,
    IntentCapability,
    ParameterType,
    ToolCapability,
)

logger = logging.getLogger("SentinelAI.CapabilityRegistry")


class CapabilityRegistry:
    """Stores and queries ToolCapability and IntentCapability metadata.

    Dependency-injected, mutable in-memory repository with zero global state.
    """

    def __init__(self, capabilities: Iterable[ToolCapability] | None = None) -> None:
        self._tools: dict[str, ToolCapability] = {}
        self._intents: dict[str, IntentCapability] = {}
        if capabilities:
            for capability in capabilities:
                self.register(capability)

    def register(self, capability: ToolCapability) -> None:
        """Register a tool capability. Overwrites existing tool entry if present."""
        self._tools[capability.tool_name] = capability
        for intent in capability.intents:
            self._intents[intent.name] = intent
        logger.info("Registered capability for tool: '%s' (%d intents).", capability.tool_name, len(capability.intents))

    def unregister(self, tool_name: str) -> bool:
        """Unregister a tool capability by tool name."""
        removed = self._tools.pop(tool_name, None)
        if removed is None:
            return False

        for intent in removed.intents:
            self._intents.pop(intent.name, None)
        logger.info("Unregistered capability for tool: '%s'.", tool_name)
        return True

    def lookup_tool(self, tool_name: str) -> ToolCapability | None:
        """Look up a tool capability by tool name."""
        return self._tools.get(tool_name)

    def lookup_intent(self, intent_name: str) -> IntentCapability | None:
        """Look up an intent capability by intent name."""
        return self._intents.get(intent_name)

    def all_tools(self) -> tuple[ToolCapability, ...]:
        """Return all registered tool capabilities sorted by tool name."""
        return tuple(sorted(self._tools.values(), key=lambda t: t.tool_name))

    def all_intents(self) -> tuple[IntentCapability, ...]:
        """Return all registered intent capabilities sorted by priority and name."""
        return tuple(sorted(self._intents.values(), key=lambda i: (-i.priority, i.name)))

    def group_by_tool(self) -> dict[str, ToolCapability]:
        """Return dictionary mapping tool name to ToolCapability."""
        return dict(self._tools)

    def group_by_intent(self) -> dict[str, IntentCapability]:
        """Return dictionary mapping intent name to IntentCapability."""
        return dict(self._intents)

    def find_by_category(self, category: CapabilityCategory) -> tuple[IntentCapability, ...]:
        """Return intent capabilities matching a functional category."""
        return tuple(intent for intent in self.all_intents() if intent.category is category)

    def find_by_tag(self, tag: str) -> tuple[IntentCapability, ...]:
        """Return intent capabilities matching a specific tag."""
        normalized = tag.strip().lower()
        return tuple(intent for intent in self.all_intents() if normalized in intent.tags)

    def find_by_artifact(
        self,
        artifact_type: ArtifactType,
        *,
        mode: str = "produces",
    ) -> tuple[IntentCapability, ...]:
        """Return intent capabilities that produce or consume a given artifact type."""
        results: list[IntentCapability] = []
        for intent in self.all_intents():
            targets = intent.produces_artifacts if mode == "produces" else intent.consumes_artifacts
            if artifact_type in targets:
                results.append(intent)
        return tuple(results)

    def find_by_parameter_type(self, param_type: ParameterType) -> tuple[IntentCapability, ...]:
        """Return intent capabilities accepting a specific parameter type."""
        return tuple(
            intent
            for intent in self.all_intents()
            if any(param.type is param_type for param in intent.parameters)
        )

    def find_by_risk(self, risk_level: str) -> tuple[IntentCapability, ...]:
        """Return intent capabilities matching a risk level (e.g. 'normal', 'high')."""
        normalized = risk_level.strip().lower()
        return tuple(intent for intent in self.all_intents() if intent.risk_level.lower() == normalized)

    def search(self, query: str) -> tuple[IntentCapability, ...]:
        """Search intent capabilities by query across name, description, tags, and tools."""
        q = query.strip().lower()
        if not q:
            return ()

        matches: list[IntentCapability] = []
        for intent in self.all_intents():
            text = f"{intent.id} {intent.name} {intent.description} {intent.tool_name} {' '.join(intent.tags)}".lower()
            if q in text:
                matches.append(intent)
        return tuple(matches)
