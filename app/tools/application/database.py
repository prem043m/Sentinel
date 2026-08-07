"""JSON persistence for discovered and trusted applications."""

from __future__ import annotations

import json
import logging
from dataclasses import replace
from pathlib import Path
from typing import Iterable

from app.tools.application.models import Application, ApplicationSource, build_application_id

logger = logging.getLogger("SentinelAI.ApplicationDatabase")


def default_database_path() -> Path:
    """Return the default on-disk database location."""
    return Path.home() / ".sentinelai" / "applications.json"


def bootstrap_applications() -> tuple[Application, ...]:
    """Trusted seed applications preserved for backward compatibility."""
    seeded = [
        ("Calculator", "calc.exe", ("calculator",), None),
        ("Notepad", "notepad.exe", ("notepad",), None),
        (
            "Google Chrome",
            "chrome.exe",
            ("chrome", "google chrome"),
            {
                "fallback_paths": [
                    r"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                    r"C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
                ]
            },
        ),
        (
            "Microsoft Edge",
            "msedge.exe",
            ("edge", "microsoft edge"),
            {
                "fallback_paths": [
                    r"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
                    r"C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
                ]
            },
        ),
        (
            "File Explorer",
            "explorer.exe",
            ("explorer", "file explorer", "files"),
            {"fallback_paths": [r"C:\\Windows\\explorer.exe"]},
        ),
        (
            "Visual Studio Code",
            "code.cmd",
            ("vs code", "vscode", "visual studio code"),
            {
                "fallback_paths": [
                    r"C:\\Users\\%USERNAME%\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe",
                    r"C:\\Program Files\\Microsoft VS Code\\Code.exe",
                    r"C:\\Program Files (x86)\\Microsoft VS Code\\Code.exe",
                ]
            },
        ),
    ]

    applications: list[Application] = []
    for name, path, aliases, metadata in seeded:
        applications.append(
            Application(
                id=build_application_id(name, path, ApplicationSource.REGISTRY),
                name=name,
                path=path,
                aliases=aliases,
                approved=True,
                source=ApplicationSource.REGISTRY,
                metadata=metadata or {},
            )
        )
    return tuple(applications)


class ApplicationDatabase:
    """Persistence boundary for application records."""

    def __init__(
        self,
        file_path: str | Path | None = None,
        seed: Iterable[Application] | None = None,
    ) -> None:
        self._file_path = Path(file_path) if file_path is not None else None
        self._applications: dict[str, Application] = {}
        self._seed = tuple(seed or ())
        self.load()

    @property
    def file_path(self) -> Path | None:
        return self._file_path

    def load(self) -> tuple[Application, ...]:
        """Load the database from disk or initialize from the seed set."""
        self._applications.clear()

        if self._file_path is not None and self._file_path.exists():
            payload = json.loads(self._file_path.read_text(encoding="utf-8"))
            for item in payload.get("applications", []):
                application = Application.from_dict(item)
                self._applications[application.id] = application
            return self.all()

        for application in self._seed:
            self._applications[application.id] = application

        self.save()
        return self.all()

    def save(self) -> None:
        """Persist the current database state to disk when enabled."""
        if self._file_path is None:
            return

        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"applications": [application.to_dict() for application in self.all()]}
        temporary_path = self._file_path.with_suffix(f"{self._file_path.suffix}.tmp")
        temporary_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        temporary_path.replace(self._file_path)

    def all(self) -> tuple[Application, ...]:
        return tuple(sorted(self._applications.values(), key=lambda application: application.name.casefold()))

    def add(self, application: Application) -> Application:
        """Add or merge an application record."""
        existing = self._find_duplicate(application)
        if existing is not None:
            merged = self._merge(existing, application)
            self._applications[existing.id] = merged
            self.save()
            return merged

        self._applications[application.id] = application
        self.save()
        return application

    def update(self, application: Application) -> Application:
        self._applications[application.id] = application
        self.save()
        return application

    def remove(self, application_id: str) -> bool:
        removed = self._applications.pop(application_id, None) is not None
        if removed:
            self.save()
        return removed

    def mark_approved(self, application_id: str) -> Application | None:
        return self._set_approval(application_id, True)

    def mark_unapproved(self, application_id: str) -> Application | None:
        return self._set_approval(application_id, False)

    def get(self, application_id: str) -> Application | None:
        return self._applications.get(application_id)

    def _set_approval(self, application_id: str, approved: bool) -> Application | None:
        application = self._applications.get(application_id)
        if application is None:
            return None

        updated = replace(application, approved=approved)
        self._applications[application_id] = updated
        self.save()
        return updated

    def _find_duplicate(self, application: Application) -> Application | None:
        normalized_path = self._normalize(application.path)
        normalized_name = self._normalize(application.name)

        for existing in self._applications.values():
            if self._normalize(existing.path) == normalized_path:
                return existing

            candidate_names = {self._normalize(existing.name), *(self._normalize(alias) for alias in existing.aliases)}
            if normalized_name in candidate_names:
                return existing

        return None

    def _merge(self, existing: Application, incoming: Application) -> Application:
        aliases = self._merge_aliases(existing.aliases, incoming.aliases)
        metadata = dict(existing.metadata)
        metadata.update(dict(incoming.metadata))
        return replace(
            existing,
            name=incoming.name or existing.name,
            path=incoming.path or existing.path,
            aliases=aliases,
            publisher=incoming.publisher or existing.publisher,
            version=incoming.version or existing.version,
            approved=existing.approved or incoming.approved,
            last_seen=max(existing.last_seen, incoming.last_seen),
            source=incoming.source or existing.source,
            metadata=metadata,
            icon_path=incoming.icon_path or existing.icon_path,
        )

    @staticmethod
    def _merge_aliases(*alias_groups: tuple[str, ...]) -> tuple[str, ...]:
        merged: list[str] = []
        for aliases in alias_groups:
            for alias in aliases:
                cleaned = alias.strip()
                if cleaned and cleaned.casefold() not in {value.casefold() for value in merged}:
                    merged.append(cleaned)
        return tuple(merged)

    @staticmethod
    def _normalize(value: str) -> str:
        return " ".join(value.casefold().split())