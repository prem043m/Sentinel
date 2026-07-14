from app.models.plan import Plan
from app.tools.base import Tool
from app.tools.result import ExecutionResult


class FilesystemTool(Tool):
    def execute(self, plan: Plan) -> ExecutionResult:
        path = plan.parameters["path"]

        return ExecutionResult(
            success=True,
            message=f"Would read file '{path}'."
        )
