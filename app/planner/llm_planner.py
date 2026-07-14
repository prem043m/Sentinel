from app.models.plan import Plan 
from app.planner.strategy import PlannerStrategy

class LLMPlanner(PlannerStrategy):
    
    def __init__(self, llm):
        self.llm = llm
    
    def create_plan(self, user_input: str) -> Plan:
        raise NotImplementedError