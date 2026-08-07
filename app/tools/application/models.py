"""Immutable application models for discovery, trust, and launch."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping
from uuid import NAMESPACE_URL, uuid5


class ApplicationSource(str, Enum):
    """Where an application record originated from."""

    START_MENU = "start_menu"
    PATH = "path"
    PROGRAM_FILES = "program_files"
    PROGRAM_FILES_X86 = "program_files_x86"
    REGISTRY = "registry"
    DESKTOP = "desktop"
    UNKNOWN = "unknown"


def build_application_id(name: str, path: str, source: ApplicationSource) -> str:
    """Build a stable ID for an application record."""
    key = f"{name.strip().casefold()}|{path.strip().casefold()}|{source.value}"
    return str(uuid5(NAMESPACE_URL, key))


def _normalize_aliases(aliases: tuple[str, ...] | list[str] | None) -> tuple[str, ...]:
    if not aliases:
        return ()

    normalized: list[str] = []
    for alias in aliases:
        cleaned = str(alias).strip()
        if cleaned and cleaned.casefold() not in {value.casefold() for value in normalized}:
            normalized.append(cleaned)
    return tuple(normalized)


@dataclass(frozen=True, slots=True)
class Application:
    """A discoverable application record stored in the application registry."""

    id: str
    name: str
    path: str
    aliases: tuple[str, ...] = field(default_factory=tuple)
    publisher: str | None = None
    version: str | None = None
    approved: bool = False
    last_seen: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source: ApplicationSource = ApplicationSource.UNKNOWN
    metadata: Mapping[str, Any] = field(default_factory=dict)
    icon_path: str | None = None

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("Application id must not be empty.")
        if not self.name.strip():
            raise ValueError("Application name must not be empty.")
        if not self.path.strip():
            raise ValueError("Application path must not be empty.")
        if self.last_seen.tzinfo is None:
            raise ValueError("Application last_seen must be timezone-aware.")

        object.__setattr__(self, "aliases", _normalize_aliases(self.aliases))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def to_dict(self) -> dict[str, Any]:
        """Serialize the application to JSON-safe data."""
        return {
            "id": self.id,
            "name": self.name,
            "aliases": list(self.aliases),
            "path": self.path,
            "publisher": self.publisher,
            "version": self.version,
            "approved": self.approved,
            "last_seen": self.last_seen.isoformat(),
            "source": self.source.value,
            "metadata": dict(self.metadata),
            "icon_path": self.icon_path,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Application":
        """Deserialize an application from JSON-safe data."""
        last_seen_raw = str(data.get("last_seen") or datetime.now(timezone.utc).isoformat())
        last_seen = datetime.fromisoformat(last_seen_raw)
        if last_seen.tzinfo is None:
            last_seen = last_seen.replace(tzinfo=timezone.utc)

        source_raw = str(data.get("source") or ApplicationSource.UNKNOWN.value)
        source = ApplicationSource(source_raw) if source_raw in ApplicationSource._value2member_map_ else ApplicationSource.UNKNOWN

        return cls(
            id=str(data.get("id") or ""),
            name=str(data.get("name") or ""),
            aliases=tuple(data.get("aliases") or ()),
            path=str(data.get("path") or ""),
            publisher=data.get("publisher") or None,
            version=data.get("version") or None,
            approved=bool(data.get("approved", False)),
            last_seen=last_seen,
            source=source,
            metadata=dict(data.get("metadata") or {}),
            icon_path=data.get("icon_path") or None,
        )

    def with_updates(self, **changes: Any) -> "Application":
        """Return a new application with updated fields."""
        return replace(self, **changes)