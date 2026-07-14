from app.llm.client import LLMClient
from app.planner.planner import Planner
from app.policy.engine import PolicyEngine
from app.tools.executor import ToolExecutor
from app.tools.registry import create_default_registry


class AssistantController:
    """Coordinates the application's workflow."""

    def __init__(self, planner=None, policy=None, executor=None, llm=None):
        self.planner = planner or Planner()
        self.policy = policy or PolicyEngine()
        self.executor = executor or ToolExecutor(create_default_registry())
        self.llm = llm or LLMClient()

    def process_message(self, message: str):
        plan = self.planner.create_plan(message)

        decision = self.policy.evaluate(plan)

        if not decision.allowed:
            return (
                f"Blocked by Policy Engine.\n"
                f"Reason: {decision.reason}"
            )

        if decision.confirmation_required:
            return (
                f"Confirmation required.\n"
                f"Risk: {decision.risk.value}"
            )
        if plan.intent == "chat":
            return self.llm.generate(
                plan.parameters["prompt"]
            )

        result = self.executor.execute(plan)
        return result.message