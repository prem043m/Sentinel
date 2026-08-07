"""Artifact storage for session-scoped execution artifacts.

Allows storing and retrieving artifacts produced during the session execution pipeline.
"""

from __future__ import annotations

import logging
from typing import Sequence

from app.artifacts.models import Artifact, ExecutionArtifactType

logger = logging.getLogger("SentinelAI.ArtifactStore")


class ArtifactStore:
    """In-memory session-scoped storage for execution artifacts.

    Owned by :class:`ContextManager` to keep all session context and assets
    unified under one ownership structure.
    """

    def __init__(self) -> None:
        self._artifacts: dict[str, Artifact] = {}

    def save(self, artifact: Artifact) -> None:
        """Store or update an artifact in the session store.

        Args:
            artifact: The artifact instance to store.
        """
        self._artifacts[artifact.id] = artifact
        logger.info(
            "Artifact stored: id=%s, type=%s, name='%s' (%d bytes)",
            artifact.id,
            artifact.type.value,
            artifact.name,
            len(artifact.content),
        )

    def get(self, artifact_id: str) -> Artifact | None:
        """Retrieve an artifact by its unique ID.

        Args:
            artifact_id: The ID of the artifact to fetch.

        Returns:
            The :class:`Artifact` if found, else None.
        """
        artifact = self._artifacts.get(artifact_id)
        if artifact:
            logger.debug("Artifact retrieved: id=%s", artifact_id)
        return artifact

    def list_all(self) -> Sequence[Artifact]:
        """Get all artifacts currently stored in this session.

        Returns:
            A sequence of all stored :class:`Artifact`s, sorted by timestamp.
        """
        return sorted(self._artifacts.values(), key=lambda a: a.timestamp)

    def find_by_type(self, artifact_type: ExecutionArtifactType) -> Sequence[Artifact]:
        """Find all artifacts of a specific type.

        Args:
            artifact_type: The type of artifacts to filter by.

        Returns:
            A sequence of matching :class:`Artifact`s.
        """
        results = [a for a in self._artifacts.values() if a.type == artifact_type]
        return sorted(results, key=lambda a: a.timestamp)

    def find_by_request_id(self, request_id: str) -> Sequence[Artifact]:
        """Find all artifacts produced during a specific request.

        Args:
            request_id: The request correlation ID.

        Returns:
            A sequence of matching :class:`Artifact`s.
        """
        results = [a for a in self._artifacts.values() if a.request_id == request_id]
        return sorted(results, key=lambda a: a.timestamp)

    def clear(self) -> None:
        """Discard all session artifacts."""
        self._artifacts.clear()
        logger.debug("Artifact store cleared.")
