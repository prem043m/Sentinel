"""Integration tests for context resolution with ChatTool and the controller."""

from __future__ import annotations

import pytest
from app.context.manager import ContextManager
from app.controller.assistant_controller import AssistantController
from app.models.plan import Plan
from app.tools.result import ExecutionResult
from tests.test_chat_tool import MockLLM


class FakeFilesystemTool:
    def execute(self, plan: Plan) -> ExecutionResult:
        if plan.intent == "read_file":
            return ExecutionResult(
                success=True,
                message="Read file README.md successfully",
                data={"content": "SentinelAI architecture details...", "path": "README.md"},
            )
        return ExecutionResult(success=False, message="unsupported")


class FakeExecutor:
    def __init__(self, chat_tool, filesystem_tool):
        self.chat_tool = chat_tool
        self.filesystem_tool = filesystem_tool

    def execute(self, plan: Plan) -> ExecutionResult:
        if plan.tool == "llm":
            return self.chat_tool.execute(plan)
        if plan.tool == "filesystem":
            return self.filesystem_tool.execute(plan)
        return ExecutionResult(success=False, message="unknown tool")


class DirectPlanner:
    def __init__(self, plan):
        self.plan = plan

    def create_plan(self, _msg):
        return self.plan


def test_integration_artifact_is_resolved_and_summarized():
    # 1. Initialize context manager and controller
    manager = ContextManager()
    llm = MockLLM("mocked LLM summary")
    
    from app.tools.chat.tool import ChatTool
    chat_tool = ChatTool(llm=llm, context_manager=manager)
    executor = FakeExecutor(chat_tool, FakeFilesystemTool())

    # 2. Run filesystem read request
    plan_read = Plan("read_file", "filesystem", {"path": "README.md"})
    planner_read = DirectPlanner(plan_read)
    controller = AssistantController(planner=planner_read, executor=executor, context_manager=manager)

    response = controller.process_message("read README.md")
    assert "Read file README.md successfully" in response

    # 3. Verify artifact is stored
    stored = manager.artifact_store.list_all()
    assert len(stored) == 1
    assert stored[0].name == "README.md"

    # 4. Run chat request referencing the file
    plan_chat = Plan("chat", "llm", {"prompt": "summarize it"})
    planner_chat = DirectPlanner(plan_chat)
    controller.planner = planner_chat

    # Reset LLM received prompt
    llm.received_prompt = None

    response_chat = controller.process_message("summarize it")
    assert response_chat == "mocked LLM summary"

    # Verify that the prompt sent to the LLM contains the resolved artifact details
    assert llm.received_prompt is not None
    assert "[RELEVANT ARTIFACTS]" in llm.received_prompt
    assert "Name: README.md" in llm.received_prompt
    assert "SentinelAI architecture details..." in llm.received_prompt
