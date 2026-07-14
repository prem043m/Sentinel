from app.models.plan import Plan
from app.tools.base import Tool
from app.tools.executor import ToolExecutor
from app.tools.result import ExecutionResult


class FakeApplicationTool(Tool):
    """Fake tool that simulates a successful application launch."""

    def execute(self, plan: Plan) -> ExecutionResult:
        return ExecutionResult(
            success=True,
            message=f"Application '{plan.parameters['name']}' would be launched.",
        )


class FakeFilesystemTool(Tool):
    """Fake tool that simulates a successful file read."""

    def execute(self, plan: Plan) -> ExecutionResult:
        return ExecutionResult(
            success=True,
            message=f"Would read file '{plan.parameters['path']}'.",
        )


def _create_test_registry() -> dict[str, Tool]:
    return {
        "application": FakeApplicationTool(),
        "filesystem": FakeFilesystemTool(),
    }


def test_application_tool():
    executor = ToolExecutor(_create_test_registry())

    plan = Plan(
        intent="open_application",
        tool="application",
        parameters={"name": "Calculator"},
    )

    result = executor.execute(plan)

    assert result.success
    assert "Calculator" in result.message


def test_filesystem_tool():
    executor = ToolExecutor(_create_test_registry())

    plan = Plan(
        intent="read_file",
        tool="filesystem",
        parameters={"path": "README.md"},
    )

    result = executor.execute(plan)

    assert result.success
    assert "README.md" in result.message


def test_unknown_tool_returns_failure():
    executor = ToolExecutor(_create_test_registry())

    plan = Plan(
        intent="unknown",
        tool="nonexistent",
        parameters={},
    )

    result = executor.execute(plan)

    assert not result.success
    assert "nonexistent" in result.message
