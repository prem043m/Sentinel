from abc import ABC, abstractmethod

from app.models.plan import Plan
from app.tools.result import ExecutionResult


class Tool(ABC):
    """Base interface for every executable tool."""

    @abstractmethod
    def execute(self, plan: Plan) -> ExecutionResult:
        raise NotImplementedError
