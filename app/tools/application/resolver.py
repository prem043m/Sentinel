"""Name resolution for trusted applications."""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import get_close_matches
from typing import Iterable

from app.tools.application.models import Application


@dataclass(frozen=True, slots=True)
class ApplicationResolver:
    """Resolve a user-facing request to a trusted application."""

    fuzzy_cutoff: float = 0.78

    def resolve(self, query: str, applications: Iterable[Application]) -> Application | None:
        normalized_query = self._normalize(query)
        if not normalized_query:
            return None

        candidates: list[tuple[str, Application]] = []
        for application in applications:
            candidates.append((self._normalize(application.name), application))
            for alias in application.aliases:
                candidates.append((self._normalize(alias), application))

        exact_matches = [application for key, application in candidates if key == normalized_query]
        if exact_matches:
            return exact_matches[0]

        substring_matches = [application for key, application in candidates if normalized_query in key or key in normalized_query]
        if substring_matches:
            return substring_matches[0]

        lookup = {key: application for key, application in candidates}
        close_match = get_close_matches(normalized_query, list(lookup.keys()), n=1, cutoff=self.fuzzy_cutoff)
        if close_match:
            return lookup[close_match[0]]

        return None

    @staticmethod
    def _normalize(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()