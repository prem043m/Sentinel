# Context Engine

## Purpose

The Context Engine supplies short-lived conversational context to SentinelAI's
LLM requests. It is an observer of the existing execution pipeline: it records
accepted user messages, assistant responses, and safe summaries of successful
tool results. It never executes an action, changes a `Plan`, or participates in
policy decisions.

Context exists only in the `ContextManager` instance owned by an
`AssistantController`. Exiting the application discards that instance and all
of its entries. There is no file, database, cache, or automatic learning.

## Architecture

```text
User -> AssistantController -> Planner -> PolicyEngine -> ToolExecutor -> Tool
          |                                      |              |
          |                                      |              +-- ExecutionResult
          +-- ContextManager <-------------------+-------------------+
                    |                                           observe
                    +-- ContextPolicy -> ContextWindow -> ContextFormatter
                                                              |
                                                              +-- LLM prompt
```

The controller adds the user message before planning. It stores every response
that it returns. For successful tool execution it also supplies the result and
plan to `ContextManager.add_tool_result()`. On a chat request the controller
asks the manager for formatted context; the current user message is labelled
separately rather than repeated in conversation history, and the returned text
is sent to the LLM.

## Components

| Component | Responsibility |
| --- | --- |
| `ContextEntry` | Immutable, timestamped record with a role, source, content, and immutable metadata snapshot. |
| `ContextManager` | Session owner and public API: add entries, build prompt context, return history, trim, and clear. |
| `ContextPolicy` | Rejects unsuitable prompt content: binary data, secrets, stack traces, debug logs, and oversized content. |
| `ContextWindow` | Enforces per-role and aggregate character limits, removing the oldest entries first. |
| `ContextFormatter` | Turns accepted entries into stable sections for conversation, tool output, and the current request. |

The default window retains at most 10 user messages, 10 assistant messages, 5
tool results, and 30,000 total characters. The policy separately limits an
individual entry to 10,000 characters. Both dependencies can be injected for
tests or product-specific configuration.

## Execution example

```text
User: Read requirements.txt
  -> user entry is stored
  -> filesystem result is stored when it succeeds
  -> assistant response is stored

User: Explain it.
  -> current user entry is stored
  -> formatter builds prior conversation + file result + current request
  -> local LLM receives that prompt
  -> its response is stored as an assistant entry
```

Only successful tool results are considered. When a filesystem result contains
small text content, the manager stores it with its summary and path. Browser
URLs/search data and application summaries are retained when provided by tool
results. Exceptions and failed tool results are not recorded.

## Context is not memory

Context is a bounded prompt assembly mechanism for the active process. It does
not persist information across runs, infer user preferences, retrieve semantic
knowledge, or modify future behavior without an explicit request. Phase 9
memory can later provide durable, permissioned retrieval through a separate
source such as `ContextSource.MEMORY`; it must still pass through the context
policy and window before reaching a prompt.

## Future integrations

- **Memory:** a retrieval service may contribute explicitly selected entries
  with `ContextSource.MEMORY`; it must not make `ContextManager` persistent.
- **Code Intelligence:** a code-analysis tool can submit bounded file/symbol
  summaries with `ContextSource.CODE`.
- **Terminal Tool:** a terminal integration can submit sanitized command
  summaries with `ContextSource.TERMINAL`; raw logs, secrets, and stack traces
  remain excluded by policy.

These integrations preserve the observer model: they contribute safe context,
not execution authority.
