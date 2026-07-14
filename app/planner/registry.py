from copy import deepcopy

from app.models.plan import Plan
from app.planner.commands import COMMANDS
from app.planner.matcher import PatternMatcher

class CommandRegistry:
    """Registry for command patterns and their corresponding plans."""

    def match(self, user_input):
        for command in COMMANDS:
            if PatternMatcher.match_pattern(command["patterns"], user_input):
                return deepcopy(command["plan"])
        return None 