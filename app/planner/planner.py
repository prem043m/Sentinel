"""Planner facade for AssistantController.

Provides a stable ``create_plan(user_input) -> Plan`` interface while
delegating internally to :class:`PlannerOrchestrator` for strategy
selection, latency tracking, and fallback handling.
"""

from __future__ import annotations

from app.models.plan import Plan
from app.planner.orchestrator import PlannerOrchestrator
from app.planner.strategy import PlannerStrategy


class Planner:
    """Stable planning facade for the controller layer.

    By default, uses :class:`PlannerOrchestrator` with
    :class:`RulePlanner` as both primary strategy and fallback.
    When an ``LLMPlanner`` is available, pass a custom
    orchestrator via the constructor.

    Args:
        orchestrator: An optional pre-configured
            :class:`PlannerOrchestrator`.  When omitted, a default
            orchestrator backed by :class:`RulePlanner` is created.
    """

    def __init__(self, orchestrator: PlannerOrchestrator | None = None) -> None:
        if orchestrator is None:
            from app.planner.rule_planner import RulePlanner

            rule = RulePlanner()
            orchestrator = PlannerOrchestrator(
                strategies=[rule],
                fallback=rule,
            )
        self._orchestrator = orchestrator

    def create_plan(self, user_input: str) -> Plan:
        """Create an execution plan for the given user input.

        Delegates to the :class:`PlannerOrchestrator` and extracts
        the :class:`Plan` from the :class:`PlanningResult`.

        Args:
            user_input: The raw text entered by the user.

        Returns:
            A :class:`Plan` ready for policy evaluation and execution.
        """
        result = self._orchestrator.create_plan(user_input)
        return result.plan