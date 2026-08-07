"""Core artifact models for SentinelAI.

Defines the structure of artifacts saved from tool executions and the types of
artifacts supported.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ExecutionArtifactType(str, Enum):
    """Supported types for artifacts produced or consumed during execution."""

    TEXT = "text"
    DIRECTORY = "directory"
    SEARCH_RESULTS = "search_results"
    SUMMARY = "summary"
    TABLE = "table"
    JSON = "json"
    IMAGE = "image"
    CODE = "code"
    WEBPAGE = "webpage"
    FILE = "file"
    APPLICATION = "application"
    CHAT = "chat"
    TERMINAL = "terminal"
    DOCUMENT = "document"


@dataclass(frozen=True, slots=True)
class Artifact:
    """An artifact produced by a tool execution or generated as a system asset.

    Attributes:
        id: Unique identifier for the artifact (e.g. ART-20260807-0001).
        request_id: The request correlation ID during which this was produced.
        type: The category/type of the artifact.
        name: A human-readable label or file path.
        content: The core content or data string representation.
        metadata: Diagnostic or contextual metadata (e.g. path, url, headers).
        timestamp: Creation time in seconds since the epoch.
    """

    id: str
    request_id: str
    type: ExecutionArtifactType
    name: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=lambda: datetime.now(timezone.utc).timestamp())
