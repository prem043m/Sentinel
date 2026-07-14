from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class ExecutionResult:
    """Result returned by every Tool."""

    success: bool
    message: str
    data: dict | None = None
