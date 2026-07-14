from abc import ABC, abstractmethod

from app.models.plan import Plan


class PlannerStrategy(ABC):
    """Base interface for all planning strategies."""

    @abstractmethod
    def create_plan(self, user_input: str) -> Plan:
        raise NotImplementedError