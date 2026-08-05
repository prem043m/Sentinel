# SentinelAI

SentinelAI is a local-first, security-oriented Windows desktop assistant.
It converts a natural-language request into a structured plan, checks that
plan against policy, and dispatches approved work to narrowly scoped tools.
The project is an early-stage prototype focused on making the execution
boundary explicit and testable.

## How it works

```text
User input
  -> AssistantController
  -> Planner
  -> Plan
  -> PolicyEngine
  -> ToolExecutor
  -> Tool
  -> Result
```

`AssistantController` coordinates the flow but does not perform operating
system actions itself. The active `RulePlanner` recognizes supported commands;
all other input becomes a chat request for the local Ollama model. The policy
engine evaluates the requested intent before the executor routes it to a tool.
Tools independently validate their inputs, providing a second security
boundary.

## Current runtime behavior

The command-line entry point is `app/launcher/main.py` and is started with:

```powershell
python -m app.launcher.main
```

The active application supports these request paths:

| Request type | Example | Current behavior |
| --- | --- | --- |
| Launch an allowed app | `open calculator` | Launches Calculator, Notepad, Google Chrome, or Visual Studio Code using `subprocess.Popen(..., shell=False)`. |
| Chat | `What is a vector database?` | Sends the message to a locally running Ollama server. |
| Open URL / search | `open https://example.com`, `search for Python` | Plans a browser action; the current browser tool is a simulation and returns a message without opening a browser. |
| Read file / list directory | `read C:\Users\me\Documents\notes.txt` | Plans a filesystem action; the tool includes path validation and file/listing code, but this path needs fixes before it is reliable in the CLI. |

### Security controls

- Application launches are restricted to a small, case-insensitive allowlist.
- Process creation always uses `shell=False`.
- Unknown intents are denied by the policy engine.
- Filesystem paths are canonicalized and restricted to configured user roots:
  `Documents`, `Desktop`, and `Downloads`.
- Filesystem validation blocks traversal, configured protected directory names,
  and operations not granted by a root's permissions.
- Text-file reads are limited to 10 MB and reject non-UTF-8 files.

## Project structure

```text
app/
  launcher/       CLI entry point
  controller/     Request orchestration
  planner/        Rule-based and in-progress LLM planning
  policy/         Intent/risk rules and policy decisions
  tools/          Application, browser, and filesystem tools
  llm/            Ollama client abstraction
  evaluation/     Planner comparison and JSONL observation utilities
  models/         Plan, policy, and result data models
tests/            pytest suite
docs/             Design notes and roadmap
```

## Setup

Requirements: Windows, Python 3.11 or newer, and Ollama for chat support.

```powershell
git clone <repository-url>
cd SentinelAi
python -m venv .Senv
.\.Senv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install requests
```

`requests` is used by `app.llm.client` but is not currently declared in
`requirements.txt`, so it is installed separately above. For chat, install and
run Ollama, then pull the configured model:

```powershell
ollama pull llama3.2:1b
ollama serve
python -m app.launcher.main
```

The default endpoint, model, and timeout are configured in
`app/config/settings.py` (`http://localhost:11434`, `llama3.2:1b`, and 15
seconds).

Type `exit` to leave the CLI.

## Development and tests

```powershell
.\.Senv\Scripts\python.exe -m pytest tests -q
```

The checkout currently has 219 passing tests, 21 failing tests, and 76 setup
errors when run in the supplied environment. The first failure is a mismatch
between browser tests (which expect `webbrowser` integration) and the current
simulated `BrowserTool`. Many filesystem test setup errors are caused by
permission-denied temporary-directory creation in the environment. These
results mean the suite is not currently green; they are not a release-quality
test result.

## Work in progress and limitations

- The production controller currently constructs `Planner()` with
  `RulePlanner`; the LLM planner and `PlannerOrchestrator` exist but are not
  connected to the CLI workflow.
- `app/evaluation` contains asynchronous, JSONL-backed comparisons between
  rule and LLM plans, but is not invoked by the runtime controller.
- Browser actions are simulated, not executed.
- The filesystem tool has a defect in its file-read path: `_read_file` refers
  to an undefined `plan` variable when the requested path is a directory.
- A policy decision that requires confirmation is returned to the user as a
  message; the CLI does not yet collect a confirmation and resume execution.
- PySide6 is declared as a dependency, but no graphical interface is wired up.

## Documentation

The `docs/` directory describes the architecture, planner, policy engine,
tool framework, filesystem security model, testing approach, and roadmap.
Some documents describe planned milestones, so prefer this README and the
source code for the current runtime state.
