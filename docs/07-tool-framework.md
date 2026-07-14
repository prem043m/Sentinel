# SentinelAI — Tool Framework

The Tool Framework executes authorized `Plans`. It consists of an Executor, a Registry, and the individual Tools.

## Tool Interface

All tools must inherit from the `Tool` Abstract Base Class (`app/tools/base.py`):

```python
class Tool(ABC):
    @abstractmethod
    def execute(self, plan: Plan) -> ExecutionResult:
        pass
```

Tools receive the `Plan` (for access to `parameters`), perform their operation, and return an `ExecutionResult`.

## ExecutionResult

Defined in `app/tools/result.py`.

```python
@dataclass
class ExecutionResult:
    success: bool
    message: str
    data: dict | None = None
```

The controller uses this object to inform the user (or the LLM) of the outcome. Exceptions should *never* propagate out of a Tool; they must be caught and returned as a failed `ExecutionResult`.

## Tool Executor & Registry

The `ToolExecutor` (`app/tools/executor.py`) is injected with a dictionary registry:

```python
def create_default_registry() -> dict[str, Tool]:
    return {
        "application": ApplicationTool(),
        "browser": BrowserTool(),
        "filesystem": FilesystemTool(),
        "llm": LLMTool(LLMClient())
    }
```

When `executor.execute(plan)` is called, it looks up `plan.tool` in this registry. If found, it calls `tool.execute(plan)`. If not, it returns a failed `ExecutionResult`.

## ApplicationTool: The Reference Implementation

The `ApplicationTool` (`app/tools/application/tool.py`) is the reference pattern for implementing a real, secure tool.

### Security: Application Allowlist

Before executing anything, `ApplicationTool` validates the `name` parameter against the `ApplicationAllowlist` (`app/tools/application/allowlist.py`).

```python
ALLOWED_APPLICATIONS: dict[str, AllowedApplication] = {
    "notepad": AllowedApplication(
        name="Notepad",
        executable_path="notepad.exe",
        description="Windows Notepad text editor"
    ),
    # ... calculator, chrome, code
}
```
Validation is case-insensitive and strips whitespace. If the requested app is not in the allowlist, the tool refuses execution and logs the attempt.

### Execution: Subprocess

If validation passes, the tool launches the application using Python's `subprocess.Popen`.

**CRITICAL SECURITY GUARANTEE:** The tool always sets `shell=False`. This prevents shell injection attacks entirely.

### Error Handling

The tool explicitly catches `FileNotFoundError`, `PermissionError`, and generic `OSError`, returning a structured `ExecutionResult` for each, rather than throwing exceptions.

## Future Extension Points

To add a new tool (e.g., a DatabaseTool):
1. Create `app/tools/database/tool.py` implementing `Tool`.
2. Add security logic (e.g., a connection config validator).
3. Update `app/tools/registry.py` to map `"database": DatabaseTool()`.
4. Update `app/planner/commands.py` (and the `POLICY_RULES`) to route to it.
