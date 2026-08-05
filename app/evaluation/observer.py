"""Planner observation coordinator."""

from __future__ import annotations

import logging
import threading
import time

import requests

from app.planner.llm_planner import LLMPlanner
from app.planner.rule_planner import RulePlanner

from .comparator import PlanComparator
from .models import Observation
from .storage import JSONLObservationStorage

logger = logging.getLogger("SentinelAI.PlannerObserver")


class PlannerObserver:
    """Runs evaluation in the background without affecting execution."""

    def __init__(
        self,
        rule_planner: RulePlanner,
        llm_planner: LLMPlanner,
        comparator: PlanComparator,
        storage: JSONLObservationStorage,
    ) -> None:
        self._rule_planner = rule_planner
        self._llm_planner = llm_planner
        self._comparator = comparator
        self._storage = storage

    def observe(
        self,
        user_input: str,
        production_plan,
        planner_used: str,
        latency_ms: float,
    ) -> None:
        """Start a background observation task."""
        if production_plan.intent == "chat":
            logger.debug(
                "Planner observation skipped for chat request: '%s'.",
                user_input[:100],
            )
            return

        thread = threading.Thread(
            target=self._observe,
            kwargs={
                "user_input": user_input,
                "production_plan": production_plan,
                "planner_used": planner_used,
                "latency_ms": latency_ms,
            },
            daemon=True,
        )
        thread.start()

    def _observe(self, user_input: str, production_plan, planner_used: str, latency_ms: float) -> None:
        try:
            observation = self.capture(
                user_input,
                production_plan,
                planner_used,
                latency_ms,
            )
            self._storage.append(observation)
            logger.info(
                "Planner Shadow Evaluation stored: request='%s', planner='%s', agreement=%s%%.",
                user_input[:100],
                planner_used,
                observation.comparison_result.agreement_score,
            )
        except requests.exceptions.RequestException as exc:
            logger.warning(
                "Planner observation skipped: shadow LLM request failed (%s).",
                exc,
            )
        except Exception:
            logger.exception("Planner observation failed.")

    def capture(self, user_input: str, production_plan, planner_used: str, latency_ms: float) -> Observation:
        """Synchronously build one observation record."""
        rule_start = time.perf_counter()
        rule_plan = self._rule_planner.create_plan(user_input)
        rule_latency_ms = (time.perf_counter() - rule_start) * 1000

        llm_start = time.perf_counter()
        llm_plan = self._llm_planner.create_plan(user_input)
        llm_latency_ms = (time.perf_counter() - llm_start) * 1000

        comparison = self._comparator.compare(rule_plan, llm_plan)

        return Observation.now(
            user_input=user_input,
            rule_plan=rule_plan,
            llm_plan=llm_plan,
            production_plan=production_plan,
            comparison_result=comparison,
            latency_ms=latency_ms,
            planner_used=planner_used,
            rule_latency_ms=round(rule_latency_ms, 1),
            llm_latency_ms=round(llm_latency_ms, 1),
        )