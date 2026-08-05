from app.models.plan import Plan
from app.tools.base import Tool
from app.tools.result import ExecutionResult


class BrowserTool(Tool):
    def execute(self, plan: Plan) -> ExecutionResult:
        target = plan.parameters.get("url") or plan.parameters.get("name") or "browser"

        return ExecutionResult(
            success=True,
            message=f"Browser action would target '{target}'."
        )
