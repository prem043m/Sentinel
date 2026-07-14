from dataclasses import dataclass

from app.policy.risk import RiskLevel


@dataclass(slots=True, frozen=True)
class PolicyDecision:

    allowed: bool

    risk: RiskLevel

    confirmation_required: bool

    reason: str | None = None