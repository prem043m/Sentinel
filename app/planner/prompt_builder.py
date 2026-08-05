"""Prompt construction for LLM-based planning.

This module is the **only** place where LLM prompts are assembled.
No other component in SentinelAI builds prompt strings.

The prompt is constructed from discrete, named sections so that
individual sections can be modified, replaced, or dynamically
generated without affecting the overall structure or any other
component.

Sections are defined as module-level constants for readability.
The ``DefaultPromptBuilder`` assembles them into a final prompt
string with the user's request appended as the last section.

Future enhancements (not yet implemented):
- ``ContextualPromptBuilder`` that injects conversation history.
- Dynamic tool/intent sections from a CapabilityRegistry.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


# ── Prompt Sections ───────────────────────────────────────────────

@dataclass(frozen=True, slots=True)
class PromptSection:
    """A named section of a prompt.

    Attributes:
        name: Section identifier (e.g. ``"SYSTEM ROLE"``).
        content: The text content of this section.
    """

    name: str
    content: str


# ── Abstract Interface ────────────────────────────────────────────

class PromptBuilder(ABC):
    """Base interface for prompt construction.

    Implementations assemble a prompt string from the user's input
    and any contextual information needed by the LLM.
    """

    @abstractmethod
    def build(self, user_input: str) -> str:
        """Construct a complete prompt string for the LLM.

        Args:
            user_input: The raw text entered by the user.

        Returns:
            A fully-formed prompt string ready to send to the LLM.
        """
        raise NotImplementedError


# ══════════════════════════════════════════════════════════════════
# Section Definitions — Production-Quality Prompt
# ══════════════════════════════════════════════════════════════════
#
# Each section is an independent, self-contained component.
# Sections are ordered to give the LLM maximum context before
# it encounters the user's request.
#
# Section order:
#   1. System Role
#   2. SentinelAI Architecture
#   3. Available Tools
#   4. Available Intents
#   5. Parameter Rules
#   6. Security Rules
#   7. Output JSON Schema
#   8. Positive Examples
#   9. Negative Examples
# (10. User Request — appended dynamically by build())

_SECTION_SYSTEM_ROLE = PromptSection(
    name="SYSTEM ROLE",
    content=(
        "You are the planning engine for SentinelAI, a secure "
        "desktop assistant. Your sole responsibility is to convert "
        "a user's natural-language request into a single, structured "
        "action plan represented as a JSON object.\n"
        "\n"
        "You are NOT a chatbot. You do NOT answer questions directly. "
        "You do NOT explain your reasoning. You output exactly one "
        "JSON object and nothing else."
    ),
)

_SECTION_ARCHITECTURE = PromptSection(
    name="SENTINELAI ARCHITECTURE",
    content=(
        "SentinelAI processes every user request through this pipeline:\n"
        "\n"
        "  User Request → Planner (you) → Plan → PolicyEngine → "
        "ToolExecutor → Result\n"
        "\n"
        "You are the Planner. You produce a Plan. The Plan is then "
        "evaluated by the PolicyEngine (which you cannot influence) "
        "and executed by the ToolExecutor. You must produce a Plan "
        "that the downstream components can process."
    ),
)

_SECTION_AVAILABLE_TOOLS = PromptSection(
    name="AVAILABLE TOOLS",
    content=(
        "The following tools are registered in SentinelAI. You MUST "
        "use exactly one of these tool names in your output.\n"
        "\n"
        "| Tool Name     | Description                              |\n"
        "|---------------|------------------------------------------|\n"
        "| application   | Launches desktop applications            |\n"
        "| filesystem    | Reads files and lists directories         |\n"
        "| browser       | Opens URLs and performs web searches      |\n"
        "| llm           | Handles general chat and conversation     |"
    ),
)

_SECTION_AVAILABLE_INTENTS = PromptSection(
    name="AVAILABLE INTENTS",
    content=(
        "The following intents are supported. Each intent is bound "
        "to exactly one tool. You MUST use one of these intent names.\n"
        "\n"
        "| Intent            | Tool        | Required Parameters         |\n"
        "|-------------------|-------------|-----------------------------|\n"
        "| open_application  | application | name (str)                  |\n"
        "| read_file         | filesystem  | path (str)                  |\n"
        "| list_directory    | filesystem  | path (str)                  |\n"
        "| open_url          | browser     | url (str)                   |\n"
        "| search_web        | browser     | query (str)                 |\n"
        "| chat              | llm         | prompt (str)                |"
    ),
)

_SECTION_PARAMETER_RULES = PromptSection(
    name="PARAMETER RULES",
    content=(
        "1. Every intent requires specific parameters as listed above.\n"
        "2. Parameter values must be strings.\n"
        "3. For 'open_application': use the application's display "
        "name (e.g. 'Calculator', 'Notepad', 'Google Chrome', "
        "'Visual Studio Code').\n"
        "4. For 'read_file': use the exact file path or filename "
        "as provided by the user.\n"
        "5. For 'list_directory': use the exact directory path "
        "as provided by the user.\n"
        "6. For 'open_url': include the full URL. If no scheme is "
        "provided, assume 'https://'.\n"
        "7. For 'search_web': use the user's search query as-is. "
        "Do not modify or rephrase it.\n"
        "8. For 'chat': place the user's entire message in the "
        "'prompt' parameter."
    ),
)

_SECTION_SECURITY_RULES = PromptSection(
    name="SECURITY RULES",
    content=(
        "1. NEVER invent tool names. Use ONLY the tools listed above.\n"
        "2. NEVER invent intent names. Use ONLY the intents listed "
        "above.\n"
        "3. NEVER output explanations, commentary, or markdown.\n"
        "4. NEVER wrap your output in code fences.\n"
        "5. NEVER output multiple JSON objects.\n"
        "6. If the user's request does not match any specific tool "
        "capability, classify it as 'chat' with tool 'llm'.\n"
        "7. Do not attempt to execute, simulate, or describe the "
        "action. Only produce the plan."
    ),
)

_SECTION_OUTPUT_SCHEMA = PromptSection(
    name="OUTPUT JSON SCHEMA",
    content=(
        "You MUST respond with exactly one JSON object in this format:\n"
        "\n"
        "{\n"
        '  "intent": "<intent_name>",\n'
        '  "tool": "<tool_name>",\n'
        '  "parameters": {\n'
        '    "<param_name>": "<param_value>"\n'
        "  }\n"
        "}\n"
        "\n"
        "Do not add any fields beyond 'intent', 'tool', and "
        "'parameters'. Do not nest objects inside 'parameters'."
    ),
)

_SECTION_POSITIVE_EXAMPLES = PromptSection(
    name="POSITIVE EXAMPLES",
    content=(
        'User: "Open the calculator"\n'
        '{"intent":"open_application","tool":"application",'
        '"parameters":{"name":"Calculator"}}\n'
        "\n"
        'User: "Read the README file"\n'
        '{"intent":"read_file","tool":"filesystem",'
        '"parameters":{"path":"README.md"}}\n'
        "\n"
        'User: "List files in the docs folder"\n'
        '{"intent":"list_directory","tool":"filesystem",'
        '"parameters":{"path":"docs"}}\n'
        "\n"
        'User: "Open github.com"\n'
        '{"intent":"open_url","tool":"browser",'
        '"parameters":{"url":"https://github.com"}}\n'
        "\n"
        'User: "Search for Python tutorials"\n'
        '{"intent":"search_web","tool":"browser",'
        '"parameters":{"query":"Python tutorials"}}\n'
        "\n"
        'User: "What is the capital of France?"\n'
        '{"intent":"chat","tool":"llm",'
        '"parameters":{"prompt":"What is the capital of France?"}}\n'
        "\n"
        'User: "Hello, how are you?"\n'
        '{"intent":"chat","tool":"llm",'
        '"parameters":{"prompt":"Hello, how are you?"}}'
    ),
)

_SECTION_NEGATIVE_EXAMPLES = PromptSection(
    name="NEGATIVE EXAMPLES",
    content=(
        "The following are WRONG. Never produce output like this.\n"
        "\n"
        "WRONG — Invented intent:\n"
        '{"intent":"download_file","tool":"browser",'
        '"parameters":{"url":"..."}}\n'
        "Why: 'download_file' is not a registered intent.\n"
        "\n"
        "WRONG — Invented tool:\n"
        '{"intent":"chat","tool":"gpt4",'
        '"parameters":{"prompt":"..."}}\n'
        "Why: 'gpt4' is not a registered tool.\n"
        "\n"
        "WRONG — Added explanation:\n"
        "Sure! Here is the plan:\n"
        '{"intent":"chat","tool":"llm","parameters":{"prompt":"hi"}}\n'
        "Why: Output must be JSON only, no text before or after.\n"
        "\n"
        "WRONG — Code fences:\n"
        "```json\n"
        '{"intent":"chat","tool":"llm","parameters":{"prompt":"hi"}}\n'
        "```\n"
        "Why: Do not wrap output in markdown code fences.\n"
        "\n"
        "WRONG — Multiple objects:\n"
        '{"intent":"read_file",...}\n'
        '{"intent":"open_url",...}\n'
        "Why: Output exactly ONE JSON object."
    ),
)


# ── Ordered section list ──────────────────────────────────────────

DEFAULT_SECTIONS: list[PromptSection] = [
    _SECTION_SYSTEM_ROLE,
    _SECTION_ARCHITECTURE,
    _SECTION_AVAILABLE_TOOLS,
    _SECTION_AVAILABLE_INTENTS,
    _SECTION_PARAMETER_RULES,
    _SECTION_SECURITY_RULES,
    _SECTION_OUTPUT_SCHEMA,
    _SECTION_POSITIVE_EXAMPLES,
    _SECTION_NEGATIVE_EXAMPLES,
]
"""The default ordered list of prompt sections.

Exported for testing and introspection.  The list is not mutated
at runtime; ``DefaultPromptBuilder`` makes a copy on construction.
"""

# Required section names — used for validation and testing.
REQUIRED_SECTION_NAMES: frozenset[str] = frozenset(
    section.name for section in DEFAULT_SECTIONS
)


# ── Default Implementation ────────────────────────────────────────

PROMPT_BUILDER_VERSION = "default-v1"

class DefaultPromptBuilder(PromptBuilder):
    """Builds a structured prompt from predefined sections.

    The prompt is composed of named sections joined by headers.
    Sections can be overridden via constructor injection for
    testing or customisation.

    Args:
        sections: Optional list of ``PromptSection`` instances.
                  If ``None``, the default production sections
                  are used.
    """

    def __init__(
        self,
        sections: list[PromptSection] | None = None,
    ) -> None:
        self._sections = list(sections) if sections else list(DEFAULT_SECTIONS)

    @property
    def sections(self) -> list[PromptSection]:
        """Return the current prompt sections (read-only copy)."""
        return list(self._sections)

    def build(self, user_input: str) -> str:
        """Construct the full prompt string.

        Assembles all sections with bracketed headers, then
        appends the user's request as the final section.

        Args:
            user_input: The raw text entered by the user.

        Returns:
            A fully-formed prompt string.
        """
        parts: list[str] = []

        for section in self._sections:
            parts.append(f"[{section.name}]")
            parts.append(section.content)
            parts.append("")  # blank line between sections

        parts.append("[USER REQUEST]")
        parts.append(user_input)

        return "\n".join(parts)
