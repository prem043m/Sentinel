# SentinelAI — Future Roadmap

This document outlines planned features and architectural evolutions. None of these features are currently implemented.

## 1. Real Filesystem Operations
**Goal:** Connect the existing `PathValidator` to real file I/O.
- Implement `read_file` (with UTF-8 decoding and size limits).
- Implement `list_directory`.
- Implement `write_file` and `rename_file` (with PolicyEngine confirmation).

## 2. PySide6 GUI Integration
**Goal:** Move away from the CLI to a rich desktop interface.
- Implement a chat window.
- Implement visual confirmation dialogs for HIGH risk policy decisions.
- Display structured tool outputs (e.g., rendering file contents).

## 3. LLM Planner Integration
**Goal:** Allow the LLM to generate `Plan` objects instead of relying solely on `RulePlanner` regex.
- Implement `LLMPlanner` to inherit from `PlannerStrategy`.
- Force the LLM to output structured JSON matching the `Plan` schema.
- Route complex queries to the `LLMPlanner` while keeping simple commands on `RulePlanner`.

## 4. Audit Logger
**Goal:** Persistently record all actions.
- Log every `Plan`, `PolicyDecision`, and `ExecutionResult` to a local SQLite database.
- *Prerequisite for enabling `delete_file` operations in the FilesystemTool.*

## 5. RAG & System Context
**Goal:** Give the assistant memory.
- Allow the LLM to read local documentation or user notes via the `FilesystemTool` before answering.
- Implement a vector store for semantic search of local files.

## 6. Advanced Tools
**Goal:** Expand capabilities.
- **BrowserTool:** Integrate with Playwright or Selenium for local web automation.
- **PowerShellTool:** A highly restricted, CRITICAL-risk tool for executing scripts.
