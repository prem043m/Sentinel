"""Tool execution dispatcher.

Routes approved Plans to their respective concrete Tool implementations.
"""

from __future__ import annotations

from app.core.logger import RequestLogger
from app.models.plan import Plan
from app.tools.base import Tool
from app.tools.result import ExecutionResult

logger = RequestLogger("SentinelAI.ToolExecutor")


class ToolExecutor:
    """Dispatches a Plan to the appropriate registered Tool.

    The registry is injected via the constructor to support dependency injection,
    testability, and the Open/Closed principle.
    """

    def __init__(self, registry: dict[str, Tool]) -> None:
        self._registry = dict(registry)

    def execute(self, plan: Plan) -> ExecutionResult:
        """Execute the tool identified by ``plan.tool``.

        Returns an ``ExecutionResult`` indicating success or failure.
        If no tool is registered for the requested name, a failure result is
        returned without raising an exception.
        """
        tool = self._registry.get(plan.tool)

        if tool is None:
            logger.error("Execution failed: No tool registered for '%s'", plan.tool)
            return ExecutionResult(
                success=False,
                message=f"No tool registered for '{plan.tool}'.",
            )

        logger.info("Executing tool: tool='%s', intent='%s'", plan.tool, plan.intent)
        result = tool.execute(plan)

        if result.success:
            logger.info("Tool execution succeeded: tool='%s'", plan.tool)
        else:
            logger.warning("Tool execution failed: tool='%s', message='%s'", plan.tool, result.message)

        return result
