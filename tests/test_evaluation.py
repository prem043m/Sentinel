"""Tests for planner evaluation components."""

from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import requests

from app.evaluation.comparator import PlanComparator
from app.evaluation.models import Observation
from app.evaluation.observer import PlannerObserver
from app.evaluation.reporter import ObservationReporter
from app.evaluation.storage import JSONLObservationStorage
from app.models.plan import Plan


def test_plan_comparator_identifies_mismatches():
    comparator = PlanComparator()
    rule_plan = Plan(intent="open_url", tool="browser", parameters={"url": "https://x.com"})
    llm_plan = Plan(intent="chat", tool="llm", parameters={"prompt": "hello"})

    comparison = comparator.compare(rule_plan, llm_plan)

    assert comparison.overall_match is False
    assert comparison.intent_match is False
    assert comparison.tool_match is False
    assert comparison.parameters_match is False
    assert comparison.agreement_score == 0


def test_plan_comparator_scores_partial_match():
    comparator = PlanComparator()
    rule_plan = Plan(intent="open_application", tool="application", parameters={"name": "calculator"})
    llm_plan = Plan(intent="open_application", tool="application", parameters={"name": "calc"})

    comparison = comparator.compare(rule_plan, llm_plan)

    assert comparison.intent_match is True
    assert comparison.tool_match is True
    assert comparison.parameters_match is False
    assert comparison.overall_match is False
    assert comparison.agreement_score == 67


def test_observation_serializes_version_and_plans(tmp_path: Path):
    rule_plan = Plan(intent="chat", tool="llm", parameters={"prompt": "hi"})
    llm_plan = Plan(intent="chat", tool="llm", parameters={"prompt": "hi"})
    production_plan = Plan(intent="chat", tool="llm", parameters={"prompt": "hi"})
    storage = JSONLObservationStorage(tmp_path / "evaluations.jsonl")
    comparison = PlanComparator().compare(rule_plan, llm_plan)
    observation = Observation.now(
        user_input="hi sentinel",
        rule_plan=rule_plan,
        llm_plan=llm_plan,
        production_plan=production_plan,
        comparison_result=comparison,
        latency_ms=1.0,
        planner_used="RulePlanner",
        rule_latency_ms=0.2,
        llm_latency_ms=6000.0,
    )

    assert observation.planner_used == "RulePlanner"
    assert observation.planner_version
    assert observation.prompt_builder_version
    assert observation.comparison_result.overall_match is True

    storage.append(observation)
    records = storage.read_all()

    assert len(records) == 1
    assert records[0]["planner_used"] == "RulePlanner"
    assert records[0]["comparison_result"]["agreement_score"] == 100


def test_observer_skips_chat_requests(tmp_path: Path):
    rule_planner = MagicMock()
    llm_planner = MagicMock()
    storage = JSONLObservationStorage(tmp_path / "evaluations.jsonl")
    observer = PlannerObserver(
        rule_planner=rule_planner,
        llm_planner=llm_planner,
        comparator=PlanComparator(),
        storage=storage,
    )

    with patch("app.evaluation.observer.threading.Thread") as mock_thread:
        observer.observe(
            "hi sentinel",
            production_plan=Plan(intent="chat", tool="llm", parameters={"prompt": "hi sentinel"}),
            planner_used="RulePlanner",
            latency_ms=1.0,
        )

    mock_thread.assert_not_called()
    assert storage.read_all() == []


def test_observer_triggers_tool_request_evaluation_asynchronously(tmp_path: Path):
    rule_plan = Plan(intent="open_application", tool="application", parameters={"name": "calculator"})
    llm_plan = Plan(intent="open_application", tool="application", parameters={"name": "calculator"})
    production_plan = rule_plan

    rule_planner = MagicMock()
    rule_planner.create_plan.return_value = rule_plan

    llm_planner = MagicMock()
    llm_planner.create_plan.return_value = llm_plan

    storage = JSONLObservationStorage(tmp_path / "evaluations.jsonl")
    observer = PlannerObserver(
        rule_planner=rule_planner,
        llm_planner=llm_planner,
        comparator=PlanComparator(),
        storage=storage,
    )

    with patch("app.evaluation.observer.threading.Thread") as mock_thread:
        observer.observe(
            "open calculator",
            production_plan=production_plan,
            planner_used="RulePlanner",
            latency_ms=2.5,
        )

    mock_thread.assert_called_once()
    mock_thread.return_value.start.assert_called_once()


def test_reporter_summarizes_observations(tmp_path: Path):
    storage = JSONLObservationStorage(tmp_path / "evaluations.jsonl")
    reporter = ObservationReporter(storage)

    assert reporter.build_report().total_observations == 0

    rule_plan = Plan(
        intent="open_application",
        tool="application",
        parameters={"name": "calculator"},
    )
    matching_llm_plan = Plan(
        intent="open_application",
        tool="application",
        parameters={"name": "calculator"},
    )
    llm_better_plan = Plan(
        intent="open_application",
        tool="application",
        parameters={"name": "calc"},
    )
    production_plan = rule_plan
    storage.append(
        Observation.now(
            user_input="open calculator",
            rule_plan=rule_plan,
            llm_plan=matching_llm_plan,
            production_plan=production_plan,
            comparison_result=PlanComparator().compare(rule_plan, matching_llm_plan),
            latency_ms=0.2,
            planner_used="RulePlanner",
            rule_latency_ms=0.2,
            llm_latency_ms=6000.0,
        )
    )

    storage.append(
        Observation.now(
            user_input="open calculator",
            rule_plan=rule_plan,
            llm_plan=llm_better_plan,
            production_plan=rule_plan,
            comparison_result=PlanComparator().compare(rule_plan, llm_better_plan),
            latency_ms=0.8,
            planner_used="RulePlanner",
            rule_latency_ms=0.2,
            llm_latency_ms=1.0,
        )
    )

    storage.append(
        Observation.now(
            user_input="open calculator",
            rule_plan=rule_plan,
            llm_plan=llm_better_plan,
            production_plan=llm_better_plan,
            comparison_result=PlanComparator().compare(rule_plan, llm_better_plan),
            latency_ms=1.0,
            planner_used="LLMPlanner",
            rule_latency_ms=0.2,
            llm_latency_ms=1.0,
        )
    )

    assert reporter.format_report().startswith("Planner evaluation report")

    report = reporter.build_report()

    assert report.total_observations == 3
    assert report.agreement_rate == 0.333
    assert report.intent_agreement_rate == 1.0
    assert report.tool_agreement_rate == 1.0
    assert report.parameter_agreement_rate == 0.333
    assert report.rule_better_count == 1
    assert report.llm_better_count == 1
    assert report.unknown_count == 1


def test_observer_skips_shadow_llm_timeout(tmp_path: Path):
    rule_plan = Plan(intent="chat", tool="llm", parameters={"prompt": "hi"})
    rule_planner = MagicMock()
    rule_planner.create_plan.return_value = rule_plan

    llm_planner = MagicMock()
    llm_planner.create_plan.side_effect = requests.exceptions.ReadTimeout("timed out")

    storage = JSONLObservationStorage(tmp_path / "evaluations.jsonl")
    observer = PlannerObserver(
        rule_planner=rule_planner,
        llm_planner=llm_planner,
        comparator=PlanComparator(),
        storage=storage,
    )

    observer._observe(
        "open calculator",
        production_plan=Plan(intent="open_application", tool="application", parameters={"name": "calculator"}),
        planner_used="RulePlanner",
        latency_ms=1.0,
    )

    assert storage.read_all() == []


def test_observer_handles_malformed_llm_response(tmp_path: Path):
    rule_plan = Plan(intent="open_application", tool="application", parameters={"name": "calculator"})

    rule_planner = MagicMock()
    rule_planner.create_plan.return_value = rule_plan

    llm_planner = MagicMock()
    llm_planner.create_plan.side_effect = ValueError("bad json")

    storage = JSONLObservationStorage(tmp_path / "evaluations.jsonl")
    observer = PlannerObserver(
        rule_planner=rule_planner,
        llm_planner=llm_planner,
        comparator=PlanComparator(),
        storage=storage,
    )

    observer._observe(
        "open calculator",
        production_plan=rule_plan,
        planner_used="RulePlanner",
        latency_ms=1.0,
    )

    assert storage.read_all() == []