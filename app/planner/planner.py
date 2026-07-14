from app.models.plan import Plan
from app.planner.strategy import PlannerStrategy


class Planner:
    def __init__(self, strategy: PlannerStrategy | None = None):
        if strategy is None:
            from app.planner.rule_planner import RulePlanner

            strategy = RulePlanner()

        self.strategy = strategy

    def create_plan(self, user_input: str) -> Plan:
        return self.strategy.create_plan(user_input)