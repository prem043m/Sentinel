# SentinelAI — Development Roadmap (Completed)

This document tracks the milestones that have been fully implemented in SentinelAI.

## Milestone 1: Initial Scaffold
**Goal:** Setup basic project structure, config, logging, and PySide6 foundation.
**Status:** ✅ Complete
- Basic CLI entry point created (`app/launcher/main.py`)
- Configuration and constants defined (`settings.py`)
- Application logging configured

## Milestone 2: Policy Engine & Planner
**Goal:** Implement the core execution pipeline (Planner -> Policy -> ToolExecutor).
**Status:** ✅ Complete
- `Plan` and `PolicyDecision` models created
- `RulePlanner` implemented with basic regex routing
- `PolicyEngine` implemented with risk-based evaluation
- `ToolExecutor` and base `Tool` interface defined

## Milestone 3: Safe LLM Integration
**Goal:** Integrate local Ollama without giving it OS control.
**Status:** ✅ Complete
- `LLMClient` implemented for HTTP POST to Ollama
- `LLMTool` created to handle `chat` intents
- *Note: The LLM acts as an isolated tool (like a chatbot) and does not currently generate Plans.*

## Milestone 4: Tool Execution & Allowlisting (The Reference Pattern)
**Goal:** Implement a real OS-level tool with strict zero-trust boundaries.
**Status:** ✅ Complete
- `ApplicationTool` implemented to launch processes via `subprocess.Popen(shell=False)`
- `ApplicationAllowlist` implemented to prevent unauthorized app launches
- Extensive unit tests created for the `ApplicationTool`
- This established the architectural reference pattern for all future tools.

## Milestone 5: Filesystem Security Foundation
**Goal:** Design and implement the security boundary for the upcoming FilesystemTool.
**Status:** ✅ Complete
- Fixed rule planner casing bug (`fileSystem` -> `filesystem`)
- Configured allowed roots (Documents, Desktop, Downloads), blocked patterns (Windows, AppData, etc.), and file size limits
- Implemented `PathValidator` to handle canonicalization, traversal protection, and per-root permission checks (Read/Write/Delete)
- *Note: The real file I/O operations are planned for a future milestone.*

## Future Roadmaps

See [12-future-roadmap.md](12-future-roadmap.md) for planned milestones.
