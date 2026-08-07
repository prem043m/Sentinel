"""Integration tests verifying timing, logging, and execution history database."""

from __future__ import annotations

import pytest
from app.controller.assistant_controller import AssistantController
from app.core.history import ExecutionHistory
from app.models.plan import Plan
from app.tools.result import ExecutionResult


class FakePlanner:
    def create_plan(self, message: str) -> Plan:
        return Plan(intent="chat", tool="llm", parameters={"prompt": message})


class FakeExecutor:
    def execute(self, plan: Plan) -> ExecutionResult:
        return ExecutionResult(success=True, message="mock response")


def test_controller_records_timing_and_execution_history():
    history = ExecutionHistory()
    controller = AssistantController(
        planner=FakePlanner(),
        executor=FakeExecutor(),
        history=history,
    )

    response = controller.process_message("hello")
    assert response == "mock response"

    # Verify execution record is recorded in history
    records = history.list_records()
    assert len(records) == 1
    record = records[0]

    assert record.raw_message == "hello"
    assert record.success is True
    assert record.plan.intent == "chat"
    assert record.tool_result.message == "mock response"
    
    # Verify timing metrics are recorded
    assert "total" in record.timings
    assert "planning" in record.timings
    assert "policy_evaluation" in record.timings
    assert "tool_execution" in record.timings
    assert "context_entry" in record.timings

    # All timings should be numeric and positive
    assert record.timings["total"] > 0.0
    assert record.timings["planning"] >= 0.0
