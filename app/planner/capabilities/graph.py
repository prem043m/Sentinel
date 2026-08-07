"""Capability graph mapping artifact producers to consumers."""

from __future__ import annotations

from app.artifacts.types import ArtifactType
from app.planner.capabilities.models import IntentCapability
from app.planner.capabilities.registry import CapabilityRegistry


class CapabilityGraph:
    """Dependency graph connecting intent capabilities via produced and consumed artifacts."""

    def __init__(self, registry: CapabilityRegistry) -> None:
        self._registry = registry

    def producers_for(self, artifact_type: ArtifactType) -> tuple[IntentCapability, ...]:
        """Return intents that produce a given artifact type."""
        return self._registry.find_by_artifact(artifact_type, mode="produces")

    def consumers_for(self, artifact_type: ArtifactType) -> tuple[IntentCapability, ...]:
        """Return intents that consume a given artifact type."""
        return self._registry.find_by_artifact(artifact_type, mode="consumes")

    def next_possible_intents(self, current_artifact_types: tuple[ArtifactType, ...]) -> tuple[IntentCapability, ...]:
        """Return intents whose preconditions or consumed artifacts can be satisfied by current artifacts."""
        possible: list[IntentCapability] = []
        for intent in self._registry.all_intents():
            if not intent.consumes_artifacts:
                continue
            if any(artifact in current_artifact_types for artifact in intent.consumes_artifacts):
                possible.append(intent)
        return tuple(possible)

    def path_between_artifacts(
        self,
        source_artifact: ArtifactType,
        target_artifact: ArtifactType,
    ) -> tuple[tuple[IntentCapability, ...], ...]:
        """Find simple one-step or multi-step intent paths connecting source to target artifact."""
        producers = self.producers_for(target_artifact)
        paths: list[tuple[IntentCapability, ...]] = []

        for producer in producers:
            if source_artifact in producer.consumes_artifacts or not producer.consumes_artifacts:
                paths.append((producer,))

        return tuple(paths)
