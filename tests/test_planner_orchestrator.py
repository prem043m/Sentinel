"""Tests for the PlannerOrchestrator."""

from unittest.mock import MagicMock

import pytest

from app.models.plan import Plan
from app.planner.orchestrator import PlannerOrchestrator, PlanningResult
from app.planner.strategy import PlannerStrategy


# ── Helpers ───────────────────────────────────────────────────────

def _mock_strategy(
    name: str = "MockPlanner",
    plan: Plan | None = None,
    error: Exception | None = None,
) -> PlannerStrategy:
    """Create a mock PlannerStrategy.

    Args:
        name: The class name to report.
        plan: The plan to return on success.
        error: The exception to raise on failure.
    """
    mock = MagicMock(spec=PlannerStrategy)
    type(mock).__name__ = name

    if error:
        mock.create_plan.side_effect = error
    else:
        mock.create_plan.return_value = plan or Plan(
            intent="chat", tool="llm", parameters={"prompt": "hi"},
        )

    return mock


_DEFAULT_PLAN = Plan(
    intent="chat", tool="llm", parameters={"prompt": "hello"},
)

_LLM_PLAN = Plan(
    intent="open_url", tool="browser", parameters={"url": "https://x.com"},
)

_RULE_PLAN = Plan(
    intent="chat", tool="llm", parameters={"prompt": "fallback"},
)


# ── Tests ─────────────────────────────────────────────────────────


class TestPrimarySuccess:
    """Tests when the primary strategy succeeds."""

    def test_returns_primary_plan(self):
        primary = _mock_strategy("LLMPlanner", plan=_LLM_PLAN)
        fallback = _mock_strategy("RulePlanner", plan=_RULE_PLAN)

        orch = PlannerOrchestrator(
            strategies=[primary], fallback=fallback,
        )
        result = orch.create_plan("open x.com")

        assert result.plan is _LLM_PLAN

    def test_fallback_not_called(self):
        primary = _mock_strategy("LLMPlanner", plan=_LLM_PLAN)
        fallback = _mock_strategy("RulePlanner", plan=_RULE_PLAN)

        orch = PlannerOrchestrator(
            strategies=[primary], fallback=fallback,
        )
        orch.create_plan("test")

        fallback.create_plan.assert_not_called()

    def test_fallback_used_is_false(self):
        primary = _mock_strategy("LLMPlanner", plan=_LLM_PLAN)
        fallback = _mock_strategy("RulePlanner", plan=_RULE_PLAN)

        orch = PlannerOrchestrator(
            strategies=[primary], fallback=fallback,
        )
        result = orch.create_plan("test")

        assert result.fallback_used is False

    def test_error_is_none(self):
        primary = _mock_strategy("LLMPlanner", plan=_LLM_PLAN)
        fallback = _mock_strategy("RulePlanner", plan=_RULE_PLAN)

        orch = PlannerOrchestrator(
            strategies=[primary], fallback=fallback,
        )
        result = orch.create_plan("test")

        assert result.error is None

    def test_planner_name_is_primary(self):
        primary = _mock_strategy("LLMPlanner", plan=_LLM_PLAN)
        fallback = _mock_strategy("RulePlanner", plan=_RULE_PLAN)

        orch = PlannerOrchestrator(
            strategies=[primary], fallback=fallback,
        )
        result = orch.create_plan("test")

        assert result.planner_name == "LLMPlanner"

    def test_latency_is_positive(self):
        primary = _mock_strategy("LLMPlanner", plan=_LLM_PLAN)
        fallback = _mock_strategy("RulePlanner", plan=_RULE_PLAN)

        orch = PlannerOrchestrator(
            strategies=[primary], fallback=fallback,
        )
        result = orch.create_plan("test")

        assert result.latency_ms >= 0


class TestFallback:
    """Tests when primary strategies fail."""

    def test_fallback_used_on_primary_failure(self):
        primary = _mock_strategy(
            "LLMPlanner", error=ValueError("bad json"),
        )
        fallback = _mock_strategy("RulePlanner", plan=_RULE_PLAN)

        orch = PlannerOrchestrator(
            strategies=[primary], fallback=fallback,
        )
        result = orch.create_plan("test")

        assert result.plan is _RULE_PLAN
        assert result.fallback_used is True

    def test_error_contains_failure_reason(self):
        primary = _mock_strategy(
            "LLMPlanner", error=ValueError("bad json"),
        )
        fallback = _mock_strategy("RulePlanner", plan=_RULE_PLAN)

        orch = PlannerOrchestrator(
            strategies=[primary], fallback=fallback,
        )
        result = orch.create_plan("test")

        assert "bad json" in result.error

    def test_planner_name_is_fallback(self):
        primary = _mock_strategy(
            "LLMPlanner", error=ConnectionError("no server"),
        )
        fallback = _mock_strategy("RulePlanner", plan=_RULE_PLAN)

        orch = PlannerOrchestrator(
            strategies=[primary], fallback=fallback,
        )
        result = orch.create_plan("test")

        assert result.planner_name == "RulePlanner"


class TestMultipleStrategies:
    """Tests with multiple primary strategies."""

    def test_first_succeeds_second_not_called(self):
        first = _mock_strategy("FirstPlanner", plan=_LLM_PLAN)
        second = _mock_strategy("SecondPlanner", plan=_RULE_PLAN)
        fallback = _mock_strategy("Fallback", plan=_DEFAULT_PLAN)

        orch = PlannerOrchestrator(
            strategies=[first, second], fallback=fallback,
        )
        result = orch.create_plan("test")

        assert result.plan is _LLM_PLAN
        second.create_plan.assert_not_called()

    def test_first_fails_second_succeeds(self):
        first = _mock_strategy(
            "FirstPlanner", error=ValueError("nope"),
        )
        second = _mock_strategy("SecondPlanner", plan=_LLM_PLAN)
        fallback = _mock_strategy("Fallback", plan=_DEFAULT_PLAN)

        orch = PlannerOrchestrator(
            strategies=[first, second], fallback=fallback,
        )
        result = orch.create_plan("test")

        assert result.plan is _LLM_PLAN
        assert result.planner_name == "SecondPlanner"
        assert result.fallback_used is False

    def test_all_fail_uses_fallback(self):
        first = _mock_strategy(
            "FirstPlanner", error=ValueError("fail 1"),
        )
        second = _mock_strategy(
            "SecondPlanner", error=ConnectionError("fail 2"),
        )
        fallback = _mock_strategy("Fallback", plan=_DEFAULT_PLAN)

        orch = PlannerOrchestrator(
            strategies=[first, second], fallback=fallback,
        )
        result = orch.create_plan("test")

        assert result.plan is _DEFAULT_PLAN
        assert result.fallback_used is True
        assert "fail 2" in result.error


class TestEmptyStrategies:
    """Tests with no primary strategies."""

    def test_no_strategies_uses_fallback_immediately(self):
        fallback = _mock_strategy("RulePlanner", plan=_RULE_PLAN)

        orch = PlannerOrchestrator(
            strategies=[], fallback=fallback,
        )
        result = orch.create_plan("test")

        assert result.plan is _RULE_PLAN
        assert result.fallback_used is True


class TestPlanningResult:
    """Tests for the PlanningResult dataclass."""

    def test_is_frozen(self):
        result = PlanningResult(
            plan=_DEFAULT_PLAN,
            planner_name="Test",
            latency_ms=1.0,
            fallback_used=False,
        )

        with pytest.raises(AttributeError):
            result.plan = _LLM_PLAN

    def test_error_defaults_to_none(self):
        result = PlanningResult(
            plan=_DEFAULT_PLAN,
            planner_name="Test",
            latency_ms=1.0,
            fallback_used=False,
        )

        assert result.error is None

    def test_all_fields_accessible(self):
        result = PlanningResult(
            plan=_DEFAULT_PLAN,
            planner_name="LLMPlanner",
            latency_ms=42.5,
            fallback_used=True,
            error="timeout",
        )

        assert result.plan is _DEFAULT_PLAN
        assert result.planner_name == "LLMPlanner"
        assert result.latency_ms == 42.5
        assert result.fallback_used is True
        assert result.error == "timeout"


class TestOrchestratorLogging:
    """Tests that the orchestrator logs appropriately."""

    def test_primary_success_logged(self, caplog):
        primary = _mock_strategy("LLMPlanner", plan=_LLM_PLAN)
        fallback = _mock_strategy("RulePlanner", plan=_RULE_PLAN)
        orch = PlannerOrchestrator(
            strategies=[primary], fallback=fallback,
        )

        with caplog.at_level("INFO", logger="SentinelAI.PlannerOrchestrator"):
            orch.create_plan("test")

        assert any(
            "Planner selected: LLMPlanner" in r.message
            for r in caplog.records
        )

    def test_failure_logged_as_warning(self, caplog):
        primary = _mock_strategy(
            "LLMPlanner", error=ValueError("bad"),
        )
        fallback = _mock_strategy("RulePlanner", plan=_RULE_PLAN)
        orch = PlannerOrchestrator(
            strategies=[primary], fallback=fallback,
        )

        with caplog.at_level("WARNING", logger="SentinelAI.PlannerOrchestrator"):
            orch.create_plan("test")

        assert any(
            "LLMPlanner failed" in r.message
            for r in caplog.records
        )

    def test_fallback_logged(self, caplog):
        primary = _mock_strategy(
            "LLMPlanner", error=ValueError("bad"),
        )
        fallback = _mock_strategy("RulePlanner", plan=_RULE_PLAN)
        orch = PlannerOrchestrator(
            strategies=[primary], fallback=fallback,
        )

        with caplog.at_level("INFO", logger="SentinelAI.PlannerOrchestrator"):
            orch.create_plan("test")

        assert any(
            "Falling back" in r.message
            for r in caplog.records
        )
