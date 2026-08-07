"""Best-effort discovery of installed applications on Windows."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Iterable

from app.tools.application.models import Application, ApplicationSource, build_application_id

logger = logging.getLogger("SentinelAI.ApplicationScanner")

_EXECUTABLE_EXTENSIONS = {".exe", ".cmd", ".bat", ".lnk"}


class ApplicationScanner:
    """Discover applications without granting trust."""

    def __init__(
        self,
        search_roots: Iterable[str | Path] | None = None,
        max_depth: int = 2,
        max_results: int = 250,
        max_entries_per_directory: int = 200,
    ) -> None:
        self._search_roots = tuple(Path(root) for root in search_roots) if search_roots is not None else self._default_roots()
        self._max_depth = max_depth
        self._max_results = max_results
        self._max_entries_per_directory = max_entries_per_directory

    def discover(self) -> tuple[Application, ...]:
        discovered: dict[str, Application] = {}

        for root in self._search_roots:
            for application in self._scan_root(root):
                discovered[application.id] = application
                if len(discovered) >= self._max_results:
                    return tuple(sorted(discovered.values(), key=lambda application: application.name.casefold()))

        return tuple(sorted(discovered.values(), key=lambda application: application.name.casefold()))

    def _scan_root(self, root: Path) -> list[Application]:
        applications: list[Application] = []
        if not root.exists():
            return applications

        try:
            for path in self._iter_candidate_paths(root):
                source = self._infer_source(path, root)
                name = self._humanize_name(path.stem)
                aliases = self._derive_aliases(name)
                applications.append(
                    Application(
                        id=build_application_id(name, str(path), source),
                        name=name,
                        path=str(path),
                        aliases=aliases,
                        approved=False,
                        source=source,
                        metadata={"discovered_by": "scanner", "root": str(root)},
                    )
                )
        except OSError as exc:
            logger.debug("Skipping application scan root '%s': %s", root, exc)

        return applications

    def _iter_candidate_paths(self, root: Path):
        if root.is_file():
            if root.suffix.lower() in _EXECUTABLE_EXTENSIONS:
                yield root
            return

        root_parts = len(root.parts)
        stack: list[Path] = [root]

        while stack:
            current_path = stack.pop()
            depth = len(current_path.parts) - root_parts
            if depth > self._max_depth:
                continue

            try:
                entries = list(current_path.iterdir())[: self._max_entries_per_directory]
            except OSError:
                continue

            for entry in entries:
                if entry.is_file():
                    if entry.suffix.lower() in _EXECUTABLE_EXTENSIONS:
                        yield entry
                    continue

                if entry.is_dir() and depth < self._max_depth:
                    stack.append(entry)

    @staticmethod
    def _derive_aliases(name: str) -> tuple[str, ...]:
        compact = "".join(character for character in name.casefold() if character.isalnum())
        normalized = name.casefold()
        aliases = [normalized]
        if compact and compact not in aliases:
            aliases.append(compact)
        return tuple(dict.fromkeys(alias.strip() for alias in aliases if alias.strip()))

    @staticmethod
    def _humanize_name(stem: str) -> str:
        cleaned = stem.replace("_", " ").replace("-", " ").strip()
        return cleaned.title() if cleaned else stem

    @staticmethod
    def _infer_source(path: Path, root: Path) -> ApplicationSource:
        root_name = root.name.casefold()
        if "program files" in root_name:
            return ApplicationSource.PROGRAM_FILES_X86 if "(x86)" in str(root) else ApplicationSource.PROGRAM_FILES
        if "start menu" in str(root).casefold():
            return ApplicationSource.START_MENU
        if "desktop" in root_name:
            return ApplicationSource.DESKTOP
        if "path" in root_name:
            return ApplicationSource.PATH
        return ApplicationSource.UNKNOWN

    @staticmethod
    def _default_roots() -> tuple[Path, ...]:
        roots: list[Path] = []

        def add_env_path(variable: str, *segments: str) -> None:
            value = os.environ.get(variable)
            if value:
                roots.append(Path(value, *segments))

        add_env_path("ProgramFiles")
        add_env_path("ProgramFiles(x86)")
        add_env_path("ProgramData", "Microsoft", "Windows", "Start Menu", "Programs")
        add_env_path("APPDATA", "Microsoft", "Windows", "Start Menu", "Programs")

        return tuple(dict.fromkeys(roots))