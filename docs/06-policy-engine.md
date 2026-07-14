# SentinelAI — Policy Engine

The Policy Engine is the security authorization layer. It sits between the `Planner` and the `ToolExecutor`.

Every `Plan` must be evaluated by the `PolicyEngine` before it is executed.

## Core Concepts

### 1. Risk Levels

Defined in `app/config/settings.py`, risk levels categorize the potential danger of an intent:

- **LOW**: Safe, read-only operations that don't access sensitive data (e.g., `chat`).
- **MEDIUM**: Operations that might access local data or open local apps, but are generally safe (e.g., `open_application`, `read_file`, `create_folder`).
- **HIGH**: Destructive or highly sensitive operations (e.g., `delete_file`, `shutdown_system`).
- **CRITICAL**: Operations that are explicitly denied.

### 2. Policy Rules

Defined in `app/policy/rules.py`, `POLICY_RULES` is a dictionary mapping an `intent` string to its `RiskLevel`.

```python
POLICY_RULES = {
    "chat": RiskLevel.LOW,
    "open_application": RiskLevel.MEDIUM,
    "read_file": RiskLevel.MEDIUM,
    "create_folder": RiskLevel.MEDIUM,
    "delete_file": RiskLevel.HIGH,
    "delete_folder": RiskLevel.HIGH,
    "shutdown_system": RiskLevel.HIGH,
    "unknown": RiskLevel.CRITICAL
}
```
*Note: Some of these intents (like delete, create, shutdown) do not have corresponding tool capabilities implemented yet.*

### 3. Policy Decision

The `PolicyEngine.evaluate(plan)` method returns a `PolicyDecision` (`app/policy/decision.py`):

```python
@dataclass
class PolicyDecision:
    is_allowed: bool
    reason: str
    requires_confirmation: bool = False
```

## Evaluation Logic

1. The Engine looks up the `plan.intent` in `POLICY_RULES`.
2. If the intent is missing, it defaults to `RiskLevel.CRITICAL`.
3. Based on the `RiskLevel`:
   - **LOW** or **MEDIUM**: `is_allowed=True`, `requires_confirmation=False`
   - **HIGH**: `is_allowed=True`, `requires_confirmation=True`
   - **CRITICAL**: `is_allowed=False`, `requires_confirmation=False`

The `AssistantController` uses this decision to either proceed, prompt the user for confirmation (Y/n), or reject the request entirely.

## Zero Trust Integration

The Policy Engine evaluates *intent authorization*. It does *not* validate the parameters of the plan.

For example, the Policy Engine might authorize `open_application` (a MEDIUM risk action), but the `ApplicationTool` might still reject the specific application requested because it's not in the allowlist. This separation of concerns ensures that the Policy Engine remains simple and the Tools handle domain-specific security rules.
