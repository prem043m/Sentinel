# SentinelAI — Project Structure

The project is structured by feature/component to promote modularity and clean boundaries.

## Directory Tree

```
SentinelAi/
├── app/                        # Application Source Code
│   ├── config/                 # Global configuration
│   │   └── settings.py         # Env vars, constants, risk levels
│   │
│   ├── controller/             # Orchestration
│   │   └── assistant_controller.py
│   │
│   ├── launcher/               # Entry points and composition root
│   │   └── main.py             # Wires DI and starts the CLI loop
│   │
│   ├── llm/                    # Local LLM integration
│   │   └── client.py           # HTTP client for Ollama
│   │
│   ├── models/                 # Data transfer objects
│   │   └── plan.py             # Plan dataclass
│   │
│   ├── planner/                # Translates input to Plans
│   │   ├── commands.py         # Regex patterns for RulePlanner
│   │   ├── llm_planner.py      # LLM strategy (placeholder)
│   │   ├── matcher.py          # Regex matching utility
│   │   ├── parser.py           # Validates Plan dictionaries
│   │   ├── registry.py         # Maps regex patterns to Plan templates
│   │   ├── rule_planner.py     # Concrete regex strategy
│   │   └── strategy.py         # Planner interface
│   │
│   ├── policy/                 # Security authorization
│   │   ├── decision.py         # PolicyDecision dataclass
│   │   ├── engine.py           # Evaluates plans against rules
│   │   └── rules.py            # Intent-to-risk mappings
│   │
│   ├── tools/                  # Execution framework
│   │   ├── application/        # Application launching tool
│   │   │   ├── allowlist.py    # Allowed applications config
│   │   │   └── tool.py         # ApplicationTool implementation
│   │   ├── browser/            # Browser tool (mock)
│   │   │   └── tool.py         
│   │   ├── filesystem/         # Filesystem tool (mock logic, real validator)
│   │   │   ├── config.py       # Allowed roots, limits, blocked patterns
│   │   │   ├── tool.py         # FilesystemTool (currently returns mock string)
│   │   │   └── validator.py    # Security PathValidator
│   │   ├── base.py             # Tool ABC
│   │   ├── executor.py         # Routes plans to registered tools
│   │   ├── registry.py         # Default tool registry factory
│   │   └── result.py           # ExecutionResult dataclass
│   │
│   └── utils/                  # Shared utilities
│       └── logger.py           # Application logging setup
│
├── docs/                       # Documentation (you are here)
│
├── tests/                      # Pytest suite
│   ├── test_application_allowlist.py
│   ├── test_application_tool.py
│   ├── test_controller.py
│   ├── test_executor.py
│   ├── test_filesystem_config.py
│   ├── test_llm.py             # Excluded from default suite
│   ├── test_parser.py
│   ├── test_path_validator.py
│   ├── test_plan.py
│   ├── test_planner.py
│   ├── test_policy.py
│   └── test_registry.py
│
├── pyproject.toml              # Project metadata and pytest config
├── requirements.txt            # Python dependencies
└── .env                        # Environment variables (not committed)
```

## Module Responsibilities

- **`app/`**: Contains all business logic and execution code. Imports should generally flow downwards (e.g., `launcher` imports `controller`, `controller` imports `planner`).
- **`app/models/`**: Domain objects shared across the application. These should have minimal dependencies.
- **`tests/`**: Unit and integration tests. Mirror the `app/` structure where practical, but named by feature (e.g., `test_filesystem_config.py`).
