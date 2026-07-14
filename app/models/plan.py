from dataclasses import dataclass, field

@dataclass(slots=True)

class Plan:
    """
    Represents a structured action produced by the Planner.
    """
    intent: str
    tool: str
    parameters: dict = field(default_factory=dict)