# SentinelAI — System Overview

SentinelAI is a local-first, secure AI operating assistant for Windows. It translates natural language into structured plans, validates them against security policies, and executes them through a sandboxed tool framework.

## Design Philosophy

| Principle | Implementation |
|---|---|
| **Local-first** | LLM runs on-device via Ollama. No cloud dependencies for core functionality. |
| **Security-first** | Every OS action passes through a PolicyEngine and tool-level validation before execution. |
| **Zero Trust** | No component trusts another component's output without independent validation. |
| **Incremental** | Features are implemented milestone-by-milestone. Abstractions are introduced only when needed. |

## Core Pipeline

Every user request flows through a fixed execution pipeline:

```
User → AssistantController → Planner → Plan → PolicyEngine → PolicyDecision → ToolExecutor → Tool → ExecutionResult
```

The Controller never executes OS commands. The Planner never executes anything. The PolicyEngine never executes anything. Only Tools perform OS-level operations, and only after passing through policy evaluation and tool-level security validation.

## Current Capabilities

### Implemented

- **Application launching** — Calculator, Notepad, Google Chrome, Visual Studio Code via `subprocess.Popen` with `shell=False` and allowlist validation
- **Chat** — Natural language conversation routed to a local Ollama LLM (llama3.2:1b)
- **Filesystem security foundation** — Path validator with allowed roots, blocked directories, traversal protection, and per-root permissions (read/write/delete). File read operation is not yet connected.

### Simulation Only

- **FilesystemTool** — Returns mock strings. Real implementation in progress (path validation is complete, read operation is next).
- **BrowserTool** — Returns mock strings. No real browser integration.

## Technology Stack

| Component | Technology |
|---|---|
| Language | Python 3.11+ |
| LLM | Ollama (llama3.2:1b) running locally |
| HTTP Client | `requests` library for Ollama API |
| Process Execution | `subprocess.Popen` with `shell=False` |
| Future GUI | PySide6 (dependency declared, not implemented) |
| Testing | pytest |
| Configuration | Python modules (`settings.py`, `allowlist.py`, `config.py`) |

## Getting Started

```bash
# Clone the repository
git clone <repository-url>
cd SentinelAi

# Create virtual environment
python -m venv .Senv

# Activate (Windows)
.Senv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run SentinelAI
python -m app.launcher.main

# Run tests
python -m pytest tests/ -v --ignore=tests/test_llm.py
```

> **Note:** `test_llm.py` requires a running Ollama server and is excluded from the standard test suite.

## Test Status

**115 tests, 115 passing** across 11 test files.

## Further Reading

| Document | Topic |
|---|---|
| [02-architecture.md](02-architecture.md) | Design patterns, layers, DI model |
| [03-project-structure.md](03-project-structure.md) | Directory tree and file conventions |
| [04-execution-pipeline.md](04-execution-pipeline.md) | Step-by-step request walkthrough |
| [05-planner.md](05-planner.md) | Strategy pattern, RulePlanner, commands |
| [06-policy-engine.md](06-policy-engine.md) | Risk levels, policy rules, decisions |
| [07-tool-framework.md](07-tool-framework.md) | Tool ABC, ToolExecutor, registry, ApplicationTool |
| [08-filesystem-security.md](08-filesystem-security.md) | PathValidator, allowed roots, blocked patterns |
| [09-development-roadmap.md](09-development-roadmap.md) | Completed milestones |
| [10-coding-standards.md](10-coding-standards.md) | Conventions and rules |
| [11-testing.md](11-testing.md) | Test framework, patterns, inventory |
| [12-future-roadmap.md](12-future-roadmap.md) | Planned directions |
