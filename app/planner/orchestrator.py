"""Planner orchestration and selection.

This module owns **all** planner selection and fallback logic.
Individual planners (``RulePlanner``, ``LLMPlanner``) know nothing
about each other or about fallback — they simply produce plans.

The ``PlannerOrchestrator`` tries each registered strategy in
priority order.  If a strategy raises an exception, it logs the
failure and moves to the next.  If all strategies fail, the
guaranteed fallback strategy is used.

The orchestrator returns a ``PlanningResult`` that includes
diagnostic metadata (which planner was used, latency, whether
fallback was triggered, and any error message) for developer
debugging and future analytics.
"""

import logging
import time
from dataclasses import dataclass, field

from app.models.plan import Plan
from app.planner.strategy import PlannerStrategy

logger = logging.getLogger("SentinelAI.PlannerOrchestrator")


# ── Planning Result ───────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class PlanningResult:
    """Result of the planning orchestration process.

    Contains the produced ``Plan`` alongside diagnostic metadata
    for logging, debugging, and future analytics.

    Attributes:
        plan: The validated ``Plan`` to be executed.
        planner_name: The class name of the planner that produced
                      the plan (e.g. ``"LLMPlanner"``).
        latency_ms: Time in milliseconds taken by the winning
                    planner (not including failed attempts).
        fallback_used: ``True`` if the fallback planner was used
                       because all primary strategies failed.
        error: The error message from the last failed strategy,
               or ``None`` if the primary strategy succeeded.
    """

    plan: Plan
    planner_name: str
    latency_ms: float
    fallback_used: bool
    error: str | None = None


# ── Orchestrator ──────────────────────────────────────────────────

class PlannerOrchestrator:
    """Selects a planner and handles fallback.

    Strategies are tried in the order they are provided.
    The fallback strategy is guaranteed to be called if all
    primary strategies fail.  The fallback should never raise
    (``RulePlanner`` always returns a ``chat`` plan).

    Args:
        strategies: An ordered list of primary ``PlannerStrategy``
                    instances to try.  May be empty.
        fallback: The guaranteed fallback ``PlannerStrategy``.
    """

    def __init__(
        self,
        strategies: list[PlannerStrategy],
        fallback: PlannerStrategy,
    ) -> None:
        self._strategies = list(strategies)
        self._fallback = fallback

    def create_plan(self, user_input: str) -> PlanningResult:
        """Attempt to produce a plan using registered strategies.

        Tries each strategy in order.  On the first success,
        returns the result immediately.  On failure, logs the
        error and tries the next strategy.  If all strategies
        fail, uses the fallback.

        Args:
            user_input: The raw text entered by the user.

        Returns:
            A ``PlanningResult`` containing the plan and metadata.
        """
        last_error: str | None = None

        logger.info(
            "Planning request: '%s'.",
            user_input[:100],
        )

        # ── Try primary strategies ────────────────────────────────
        for strategy in self._strategies:
            strategy_name = type(strategy).__name__

            try:
                start = time.perf_counter()
                plan = strategy.create_plan(user_input)
                elapsed_ms = (time.perf_counter() - start) * 1000

                logger.info(
                    "Planner selected: %s (%.1f ms) → "
                    "intent='%s', tool='%s'.",
                    strategy_name,
                    elapsed_ms,
                    plan.intent,
                    plan.tool,
                )

                return PlanningResult(
                    plan=plan,
                    planner_name=strategy_name,
                    latency_ms=round(elapsed_ms, 1),
                    fallback_used=False,
                )

            except Exception as exc:
                last_error = f"{strategy_name}: {exc}"

                logger.warning(
                    "Planner %s failed: %s. Trying next.",
                    strategy_name,
                    exc,
                )

        # ── Fallback ──────────────────────────────────────────────
        fallback_name = type(self._fallback).__name__

        logger.info(
            "All primary planners failed. "
            "Falling back to %s. Reason: %s",
            fallback_name,
            last_error,
        )

        start = time.perf_counter()
        plan = self._fallback.create_plan(user_input)
        elapsed_ms = (time.perf_counter() - start) * 1000

        logger.info(
            "Fallback planner: %s (%.1f ms) → "
            "intent='%s', tool='%s'.",
            fallback_name,
            elapsed_ms,
            plan.intent,
            plan.tool,
        )

        return PlanningResult(
            plan=plan,
            planner_name=fallback_name,
            latency_ms=round(elapsed_ms, 1),
            fallback_used=True,
            error=last_error,
        )
