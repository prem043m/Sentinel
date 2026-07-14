import re
from copy import deepcopy

from app.models.plan import Plan
from app.planner.commands import COMMANDS
from app.planner.strategy import PlannerStrategy


class RulePlanner(PlannerStrategy):
    def create_plan(self, user_input: str) -> Plan:
        for command in COMMANDS:
            if self._matches(command["patterns"], user_input):
                return deepcopy(command["plan"])

        file_match = re.search(
            r"read(?:\s+file)?\s+(.+)",
            user_input,
            re.IGNORECASE,
        )

        if file_match:
            return Plan(
                intent="read_file",
                tool="filesystem",
                parameters={"path": file_match.group(1)},
            )

        return Plan(
            intent="chat",
            tool="llm",
            parameters={"prompt": user_input},
        )

    @staticmethod
    def _matches(patterns: list[str], text: str) -> bool:
        normalized_text = text.lower().strip()

        for pattern in patterns:
            if re.search(pattern, normalized_text):
                return True

        return False
