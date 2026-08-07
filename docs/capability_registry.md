# Capability Registry

## Purpose

The **Capability Registry** satisfies the Open/Closed Principle for SentinelAI's LLM planning prompt construction.

Tool execution logic (`Tool.execute()`) is completely separated from capability metadata (`ToolCapability`). Tool metadata lives in dedicated capability providers (`capability.py` files per tool package), allowing tools to be added or modified without modifying `PromptBuilder`.

---

## Architectural Dependency Chain & Graph

```text
               User
                │
                ▼
       Planner Orchestrator
                │
      ┌─────────┴─────────┐
      ▼                   ▼
 Rule Planner       LLM Planner
      │                   │
      └─────────┬─────────┘
                ▼
        Capability Registry
                │
      ┌─────────┴─────────┐
      ▼                   ▼
 Capability Graph   Prompt Formatter (Markdown / Extensible)
      │                   │
      └─────────┬─────────┘
                ▼
          Policy Engine
                ▼
          Tool Executor
                ▼
               Tools
                ▼
           Artifacts
                ▼
        Artifact Store
                ▼
        Context Resolver
```

---

## Key Components (`app/planner/capabilities/`)

| File / Component | Responsibility |
|---|---|
| [`models.py`](file:///d:/Users/043mk/projects/SentinelAi/app/planner/capabilities/models.py) | Immutable dataclasses (`ParameterDefinition`, `ExampleCommand`, `ExampleDataset`, `IntentCapability`, `ToolCapability`) and Enums (`ParameterType`, `CapabilityCategory`). |
| [`provider.py`](file:///d:/Users/043mk/projects/SentinelAi/app/planner/capabilities/provider.py) | `CapabilityProvider` abstract base class defining `build() -> ToolCapability`. |
| [`registry.py`](file:///d:/Users/043mk/projects/SentinelAi/app/planner/capabilities/registry.py) | In-memory queryable repository (`find_by_category`, `find_by_artifact`, `find_by_parameter_type`, `find_by_risk`, `search`). |
| [`loader.py`](file:///d:/Users/043mk/projects/SentinelAi/app/planner/capabilities/loader.py) | `CapabilityLoader` dynamically inspects `app.tools.*` for `capability.py` modules and registers discovered providers automatically. |
| [`formatter.py`](file:///d:/Users/043mk/projects/SentinelAi/app/planner/capabilities/formatter.py) | `PromptFormatter` ABC and `MarkdownPromptFormatter` strategy rendering tools, intents, parameter rules, and examples. |
| [`graph.py`](file:///d:/Users/043mk/projects/SentinelAi/app/planner/capabilities/graph.py) | `CapabilityGraph` mapping artifact inputs and outputs across intent capabilities. |

---

## Data Model Taxonomy

Each `IntentCapability` includes rich metadata for planning:
- `id`: Unique capability string (e.g. `filesystem.read`, `browser.search`).
- `name`: Intent name string (e.g. `read_file`, `search_web`).
- `version`: Version string (e.g. `"1.0.0"`).
- `category`: `CapabilityCategory` enum (`FILESYSTEM`, `BROWSER`, `APPLICATION`, `AI`, etc.).
- `priority`: Integer priority (e.g. `100`).
- `preferred`: Boolean flag indicating primary capability preference.
- `tags`: Tuple of search/grouping tags.
- `parameters`: Tuple of `ParameterDefinition` objects.
- `examples`: `ExampleDataset` object.
- `preconditions` & `postconditions`: String tuples detailing prerequisites and results.
- `constraints`: Mapping of runtime constraints (e.g. `{"max_file_size_bytes": 10485760}`).
- `consumes_artifacts` & `produces_artifacts`: Tuples of `ArtifactType` values.
- `estimated_latency_ms`, `requires_confirmation`, `side_effects`, `risk_level`.

---

## Dynamic Discovery Workflow

1. A tool package defines its capability provider in `capability.py` (e.g. `FilesystemCapabilityProvider` in `app/tools/filesystem/capability.py`).
2. `CapabilityLoader` scans `app/tools/*` via module inspection and imports all capability providers.
3. `CapabilityRegistry` receives all built `ToolCapability` instances.
4. `DefaultPromptBuilder` invokes `MarkdownPromptFormatter` against the `CapabilityRegistry` to construct prompt sections dynamically.
5. Adding a new tool requires **zero** changes to `PromptBuilder`, `PlannerOrchestrator`, or `PolicyEngine`.
