"""Plan model definition."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class PlanOutcome(str, Enum):
    """The outcome status of the planning phase."""

    KNOWN = "known"
    CHAT = "chat"
    UNSUPPORTED = "unsupported"


@dataclass(slots=True)
class Plan:
    """Represents a structured action produced by the Planner."""

    intent: str
    tool: str
    parameters: dict = field(default_factory=dict)
    outcome: PlanOutcome = PlanOutcome.KNOWN