from app.models.policy_decision import PolicyDecision
from app.policy.rules import POLICY_RULES
from app.policy.risk import RiskLevel


class PolicyEngine:

    def evaluate(self, plan):

        rule = POLICY_RULES.get(plan.intent)

        if rule is None:

            return PolicyDecision(
                allowed=False,
                risk=RiskLevel.CRITICAL,
                confirmation_required=False,
                reason=f"No policy found for intent '{plan.intent}'",
            )

        return PolicyDecision(
            allowed=rule["allowed"],
            risk=rule["risk"],
            confirmation_required=rule["confirmation"],
        )