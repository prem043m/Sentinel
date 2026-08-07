"""Tests for unsupported operation domain recognition and defense-in-depth policy rules."""

from __future__ import annotations

import pytest
from app.context.manager import ContextManager
from app.controller.assistant_controller import AssistantController
from app.models.plan import Plan, PlanOutcome
from app.planner.rule_planner import RulePlanner
from app.policy.engine import PolicyEngine
from app.models.policy_decision import PolicyDecision


def test_rule_planner_unsupported_operations():
    planner = RulePlanner()

    # Test file deletion
    plan = planner.create_plan("delete README.md")
    assert plan.outcome == PlanOutcome.UNSUPPORTED
    assert plan.intent == "unsupported_operation"
    assert "deletion" in plan.parameters["reason"]

    # Test file copy
    plan = planner.create_plan("copy file notes.txt")
    assert plan.outcome == PlanOutcome.UNSUPPORTED
    assert "copying" in plan.parameters["reason"]

    # Test file move/rename
    plan = planner.create_plan("move notes.txt to archive")
    assert plan.outcome == PlanOutcome.UNSUPPORTED
    assert "moving" in plan.parameters["reason"]

    # Test write/edit file
    plan = planner.create_plan("create file todo.txt")
    assert plan.outcome == PlanOutcome.UNSUPPORTED
    assert "Creating/modifying" in plan.parameters["reason"]

    # Test system power actions
    plan = planner.create_plan("shutdown pc")
    assert plan.outcome == PlanOutcome.UNSUPPORTED
    assert "power" in plan.parameters["reason"]

    # Test refresh applications
    plan = planner.create_plan("refresh applications")
    assert plan.outcome == PlanOutcome.UNSUPPORTED
    assert "registry" in plan.parameters["reason"]


def test_rule_planner_chat_fallback():
    planner = RulePlanner()
    plan = planner.create_plan("what is recursion?")
    assert plan.outcome == PlanOutcome.CHAT
    assert plan.intent == "chat"
    assert plan.tool == "llm"


def test_rule_planner_known_intents():
    planner = RulePlanner()
    
    # Standard command
    plan = planner.create_plan("read file README.md")
    assert plan.outcome == PlanOutcome.KNOWN
    assert plan.intent == "read_file"
    assert plan.tool == "filesystem"
    assert plan.parameters["path"] == "README.md"

    # With leading "the" and trailing "file"
    plan = planner.create_plan("read the README.md file")
    assert plan.parameters["path"] == "README.md"

    # With trailing "file" only
    plan = planner.create_plan("read README.md file")
    assert plan.parameters["path"] == "README.md"

    # With leading "the" only
    plan = planner.create_plan("read the README.md")
    assert plan.parameters["path"] == "README.md"

    # With trailing punctuation
    plan = planner.create_plan("read the README.md.")
    assert plan.parameters["path"] == "README.md"


def test_controller_intercepts_unsupported_operation():
    planner = RulePlanner()
    controller = AssistantController(planner=planner)

    response = controller.process_message("delete README.md")
    assert "Unsupported operation" in response
    assert "deletion" in response


def test_policy_engine_defense_in_depth_unsupported_operation():
    policy = PolicyEngine()
    
    # Create an unsupported operation plan explicitly
    plan = Plan(
        intent="unsupported_operation",
        tool="unknown",
        parameters={"reason": "Explicit check"},
        outcome=PlanOutcome.UNSUPPORTED,
    )

    decision = policy.evaluate(plan)
    assert decision.allowed is False
