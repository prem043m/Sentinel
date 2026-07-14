# SentinelAI — Testing Guide

SentinelAI uses `pytest` for all unit and integration testing.

## Test Philosophy

1. **High Coverage on Security Boundaries:** Components like `ApplicationAllowlist`, `PolicyEngine`, and `PathValidator` must have exhaustive test coverage, including edge cases, case-insensitivity checks, and malicious inputs (e.g., directory traversal).
2. **Real Objects, Fake Data:** We prefer passing fake data (like `tmp_path` for filesystem tests) into real objects over using `unittest.mock` to mock out the objects themselves. This ensures the actual logic is tested.
3. **No Side Effects:** Tests must not launch real apps on the developer's machine (unless explicitly testing process launching in a controlled way) and must not modify files outside of temporary directories.

## Current Test Inventory (115 passing tests)

### Configuration & Data (`tests/test_filesystem_config.py`, `tests/test_application_allowlist.py`)
- Tests ensure default roots are created correctly.
- Tests verify dataclasses are frozen and permissions are set correctly.
- Tests verify blocked patterns and allowlists are matched case-insensitively and ignore whitespace.

### Planning (`tests/test_parser.py`, `tests/test_plan.py`, `tests/test_planner.py`, `tests/test_registry.py`)
- Tests verify `Plan` object instantiation.
- Tests verify that `RulePlanner` correctly parses regex and delegates to the `CommandRegistry`.
- Tests confirm that invalid dictionaries raise errors in the `PlanParser`.

### Security (`tests/test_policy.py`, `tests/test_path_validator.py`)
- Tests verify the `PolicyEngine` maps known intents to the correct `RiskLevel`.
- Tests verify unknown intents are blocked (CRITICAL).
- Tests verify the `PathValidator` blocks directory traversal, empty paths, paths outside allowed roots, and paths containing blocked patterns.

### Execution (`tests/test_executor.py`, `tests/test_application_tool.py`)
- Tests verify the `ToolExecutor` routes to the correct tool or returns a failure.
- Tests verify `ApplicationTool` catches `FileNotFoundError` and `PermissionError` cleanly.

## Running Tests

```bash
# Run all standard tests
python -m pytest tests/ -v --ignore=tests/test_llm.py

# Run a specific file
python -m pytest tests/test_path_validator.py -v
```

> **Note:** `tests/test_llm.py` is excluded by default because it requires a live Ollama server running locally.
