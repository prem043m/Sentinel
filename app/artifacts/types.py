"""Core artifact types for SentinelAI."""

from __future__ import annotations

from enum import Enum


class ArtifactType(str, Enum):
    """Supported artifact types produced or consumed across SentinelAI."""

    FILE = "file"
    DIRECTORY = "directory"
    WEB_PAGE = "web_page"
    SEARCH_RESULTS = "search_results"
    APPLICATION = "application"
    CHAT = "chat"
    TERMINAL = "terminal"
    IMAGE = "image"
    DOCUMENT = "document"
