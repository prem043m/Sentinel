"""Trusted application registry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from app.tools.application.database import ApplicationDatabase
from app.tools.application.models import Application
from app.tools.application.resolver import ApplicationResolver


@dataclass(slots=True)
class ApplicationRegistry:
    """Provides approved applications only."""

    database: ApplicationDatabase
    resolver: ApplicationResolver = ApplicationResolver()

    def lookup(self, name: str) -> Application | None:
        """Return an approved application matching *name* if one exists."""
        return self.resolver.resolve(name, self.all())

    def all(self) -> tuple[Application, ...]:
        """Return all approved applications."""
        return tuple(application for application in self.database.all() if application.approved)

    def refresh(self) -> tuple[Application, ...]:
        """Reload data from disk and return the approved applications."""
        self.database.load()
        return self.all()
