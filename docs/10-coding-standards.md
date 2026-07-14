# SentinelAI — Coding Standards

## 1. Zero Trust and Security
- **No Implicit Trust:** No component trusts input from another component unless it is a strongly typed, validated domain object.
- **Tools Validate Themselves:** A `Tool` must independently validate `Plan.parameters` against its own security boundaries (e.g., `PathValidator`, `ApplicationAllowlist`) before executing OS operations.
- **No Shell Execution:** Never use `shell=True` in `subprocess.Popen`. Always pass command arguments as a list.
- **Fail Closed:** If a rule, pattern, or policy is missing or ambiguous, default to CRITICAL risk or denied execution.
- **Exceptions as Results:** Tools must catch OS exceptions (e.g., `FileNotFoundError`, `PermissionError`) and return them as failed `ExecutionResult` objects. Exceptions must not propagate up the execution pipeline.

## 2. Architecture and Design
- **Strict Pipeline:** Maintain the `Controller -> Planner -> Policy -> Executor -> Tool` flow. Do not bypass layers.
- **Dependency Injection:** Inject dependencies via constructors. Avoid global state, singletons, and hardcoded instantiations outside of factories or the composition root.
- **Interface-based Design:** Depend on abstractions (like `PlannerStrategy` and `Tool`), not concrete classes.
- **Data Transfer Objects:** Use dataclasses (`Plan`, `PolicyDecision`, `ExecutionResult`) to pass data between pipeline stages. Keep them immutable (`frozen=True`) where practical.

## 3. Python Style
- **Type Hinting:** All function signatures and class attributes must have explicit type hints. Use modern Python 3.10+ syntax (`|` instead of `Union`, `list[str]` instead of `List[str]`).
- **Docstrings:** Use Google-style docstrings for all classes and public methods. Module-level docstrings should explain the file's purpose.
- **Formatting:** Code should be formatted with Black/Ruff (implied standard, keep lines under 88 chars where possible).

## 4. Testing
- **Test-First:** Write tests alongside or before implementation.
- **Isolation:** Tests must not modify the developer's real filesystem or execute real applications outside of controlled sandboxes. Use `pytest` fixtures (like `tmp_path`) for isolation.
- **Mocking:** Avoid deep mocking of internal objects. Prefer instantiating real objects with fake dependencies (e.g., passing a temporary directory to the `PathValidator` instead of mocking the validator itself).
