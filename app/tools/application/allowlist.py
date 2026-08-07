"""Backward-compatible application allowlist facade.

The production path now uses the application registry. This module
exists only so older imports and tests can continue to resolve the
legacy ``AllowedApplication`` shape.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.tools.application.database import ApplicationDatabase, bootstrap_applications
from app.tools.application.registry import ApplicationRegistry


@dataclass(frozen=True, slots=True)
class AllowedApplication:
    name: str
    executable: str


_COMPAT_REGISTRY = ApplicationRegistry(
    database=ApplicationDatabase(seed=bootstrap_applications()),
)


def lookup(name: str) -> AllowedApplication | None:
    application = _COMPAT_REGISTRY.lookup(name)
    if application is None:
        return None
    return AllowedApplication(name=application.name, executable=application.path)