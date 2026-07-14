# SentinelAI — Planner

The Planner layer is responsible for translating natural language input into a structured `Plan` object.

## The Strategy Pattern

The planner uses the Strategy Pattern defined in `app/planner/strategy.py`:

```python
class PlannerStrategy(ABC):
    @abstractmethod
    def create_plan(self, user_input: str) -> Plan:
        pass
```

This allows the `AssistantController` to remain completely ignorant of *how* a plan is created.

## Current Implementations

### RulePlanner

The current active implementation is `RulePlanner` (`app/planner/rule_planner.py`). It uses regular expressions to parse commands quickly and deterministically without requiring an LLM.

**Workflow:**
1. Hardcoded regex patterns (like `read file notes.txt`) are checked first.
2. If those fail, it delegates to the `CommandRegistry` (`app/planner/registry.py`).
3. The registry checks `COMMANDS` (`app/planner/commands.py`), which maps regex patterns to pre-defined `Plan` dictionaries.
4. `PlanParser` (`app/planner/parser.py`) validates the dictionary and converts it into a `Plan` object.
5. If no pattern matches, the `RulePlanner` defaults to a `chat` plan targeting the `llm` tool.

**Example Command Pattern (`commands.py`):**
```python
    {
        "patterns": [
            r"^open\s+(.*)$",
            r"^launch\s+(.*)$",
            r"^run\s+(.*)$"
        ],
        "plan": {
            "intent": "open_application",
            "tool": "application",
            "parameters": {"name": "{0}"} # Not actually replaced yet, RulePlanner handles this logic separately for now.
        }
    }
```
*Note: The `RulePlanner` currently implements specific logic to handle the regex grouping for app names (e.g., `match.group(1)`) rather than relying entirely on the registry for parameter extraction.*

### LLMPlanner

A placeholder implementation `LLMPlanner` exists (`app/planner/llm_planner.py`). Currently, it raises `NotImplementedError`. In the future, this will use the `LLMClient` to parse complex user requests that regex cannot handle.

## The Plan Object

Defined in `app/models/plan.py`.

```python
@dataclass
class Plan:
    intent: str
    tool: str
    parameters: dict
```

- **intent**: A string mapped to a risk level in the Policy Engine (e.g., `open_application`, `read_file`, `chat`).
- **tool**: The registry key of the tool to execute (e.g., `"application"`, `"filesystem"`, `"llm"`).
- **parameters**: A dictionary of arguments passed to the tool (e.g., `{"name": "calculator"}`, `{"path": "notes.txt"}`).
