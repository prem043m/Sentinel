"""JSONL storage for planner observations."""

from __future__ import annotations

import json
from pathlib import Path

from .models import Observation


class JSONLObservationStorage:
    """Append-only JSONL storage for evaluation observations."""

    def __init__(self, path: Path | str) -> None:
        self._path = Path(path)

    def append(self, observation: Observation) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)

        with self._path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(observation.to_dict(), ensure_ascii=False))
            handle.write("\n")

    def read_all(self) -> list[dict]:
        if not self._path.exists():
            return []

        records: list[dict] = []

        with self._path.open("r", encoding="utf-8") as handle:
            for line in handle:
                stripped = line.strip()
                if not stripped:
                    continue

                records.append(json.loads(stripped))

        return records