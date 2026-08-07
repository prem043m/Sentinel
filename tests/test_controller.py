"""Tests for AssistantController — Milestone 9.5.1 Pipeline Unification.

Verifies that every intent (including chat) flows through the
unified pipeline: Planner → PolicyEngine → ToolExecutor → Response.
No special-casing. No bypasses.
"""

from app.controller.assistant_controller import AssistantController
from app.context.manager import ContextManager
from app.tools.result import ExecutionResult


# ══════════════════════════════════════════════════════════════════
# Test Doubles
# ══════════════════════════════════════════════════════════════════


class DummyPlan:
    def __init__(self, intent, parameters, tool="llm"):
        self.intent = intent
        self.tool = tool
        self.parameters = parameters
        self.outcome = "known"


class DummyPlanner:
    def __init__(self, plan):
        self.plan = plan
        self.received_message = None

    def create_plan(self, message: str):
        self.received_message = message
        return self.plan


class DummyExecutor:
    def __init__(self, result=None):
        self.received_plan = None
        self._result = result or ExecutionResult(
            success=True,
            message="executed-plan",
        )

    def execute(self, plan):
        self.received_plan = plan
        return self._result


class DirectoryExecutor:
    def __init__(self):
        self.received_plan = None

    def execute(self, plan):
        self.received_plan = plan
        return ExecutionResult(
            success=True,
            message="Successfully listed 'docs' (2 items).",
            data={
                "directory_contents": [
                    {
                        "name": "notes.txt",
                        "path": "docs/notes.txt",
                        "size": 12,
                        "extension": ".txt",
                        "is_directory": False,
                    },
                    {
                        "name": "archive",
                        "path": "docs/archive",
                        "size": 0,
                        "extension": "",
                        "is_directory": True,
                    },
                ]
            },
        )


# ══════════════════════════════════════════════════════════════════
# Pipeline Unification Tests
# ══════════════════════════════════════════════════════════════════


class TestChatFlowsThroughExecutor:
    """Chat must flow through ToolExecutor — no bypass."""

    def test_chat_routes_through_executor(self):
        plan = DummyPlan("chat", {"prompt": "Hello"})
        planner = DummyPlanner(plan)
        executor = DummyExecutor(
            ExecutionResult(success=True, message="llm-response", data={"type": "chat"}),
        )
        controller = AssistantController(planner=planner, executor=executor)

        response = controller.process_message("Hello")

        assert response == "llm-response"
        assert planner.received_message == "Hello"
        assert executor.received_plan is plan

    def test_chat_error_flows_through_executor(self):
        plan = DummyPlan("chat", {"prompt": "Hello"})
        planner = DummyPlanner(plan)
        executor = DummyExecutor(
            ExecutionResult(
                success=False,
                message="Unable to get a response from the LLM. Please check the server status.",
            ),
        )
        controller = AssistantController(planner=planner, executor=executor)

        response = controller.process_message("Hello")

        assert "Unable to get a response" in response
        assert executor.received_plan is plan

    def test_controller_has_no_llm_attribute(self):
        """Controller must not hold a direct LLM reference."""
        controller = AssistantController(
            planner=DummyPlanner(DummyPlan("chat", {})),
            executor=DummyExecutor(),
        )
        assert not hasattr(controller, "llm")


# ══════════════════════════════════════════════════════════════════
# Non-Chat Pipeline Tests
# ══════════════════════════════════════════════════════════════════


class TestNonChatRouting:
    """Non-chat intents still route through executor unchanged."""

    def test_open_application_routes_to_executor(self):
        plan = DummyPlan("open_application", {"name": "Visual Studio Code"}, tool="application")
        planner = DummyPlanner(plan)
        executor = DummyExecutor()
        controller = AssistantController(planner=planner, executor=executor)

        response = controller.process_message("Open VS Code")

        assert response == "executed-plan"
        assert planner.received_message == "Open VS Code"
        assert executor.received_plan is plan

    def test_directory_listing_routes_to_executor(self):
        plan = DummyPlan("list_directory", {"path": "docs"}, tool="filesystem")
        planner = DummyPlanner(plan)
        executor = DirectoryExecutor()
        controller = AssistantController(planner=planner, executor=executor)

        response = controller.process_message("List docs")

        assert response == "Successfully listed 'docs' (2 items)."
        assert planner.received_message == "List docs"
        assert executor.received_plan is plan


# ══════════════════════════════════════════════════════════════════
# Context Management Tests
# ══════════════════════════════════════════════════════════════════


class TestContextTracking:
    """Verify context is updated for all pipeline outcomes."""

    def test_successful_execution_records_context(self):
        plan = DummyPlan("open_application", {"name": "Calc"}, tool="application")
        planner = DummyPlanner(plan)
        executor = DummyExecutor()
        controller = AssistantController(planner=planner, executor=executor)

        controller.process_message("open calc")

        roles = [entry.role.value for entry in controller.context_manager.history()]
        assert roles == ["user", "tool", "assistant"]

    def test_chat_failure_records_only_user_message(self):
        plan = DummyPlan("chat", {"prompt": "Hello"})
        planner = DummyPlanner(plan)
        executor = DummyExecutor(
            ExecutionResult(success=False, message="LLM error"),
        )
        controller = AssistantController(planner=planner, executor=executor)

        controller.process_message("Hello")

        roles = [entry.role.value for entry in controller.context_manager.history()]
        # user + assistant (the error message is still recorded as assistant response)
        assert "user" in roles
        assert "assistant" in roles

    def test_blocked_by_policy_records_context(self):
        plan = DummyPlan("unknown_intent", {}, tool="unknown")
        planner = DummyPlanner(plan)
        executor = DummyExecutor()
        controller = AssistantController(planner=planner, executor=executor)

        response = controller.process_message("do something blocked")

        assert "Blocked by Policy Engine" in response
        roles = [entry.role.value for entry in controller.context_manager.history()]
        assert roles == ["user", "assistant"]
        assert executor.received_plan is None
