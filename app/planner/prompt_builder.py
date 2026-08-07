"""Prompt construction for LLM-based planning.

This module is the **only** place where LLM prompts are assembled.
No other component in SentinelAI builds prompt strings.

The prompt is constructed dynamically from registered capabilities via
a CapabilityRegistry and PromptFormatter.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.planner.capabilities.formatter import MarkdownPromptFormatter, PromptFormatter
from app.planner.capabilities.loader import CapabilityLoader
from app.planner.capabilities.registry import CapabilityRegistry


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
# Section Definitions — Static Core Sections
# ══════════════════════════════════════════════════════════════════

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

_SECTION_SECURITY_RULES = PromptSection(
    name="SECURITY RULES",
    content=(
        "1. NEVER invent tool names. Use ONLY the tools listed above.\n"
        "2. NEVER invent intent names. Use ONLY the intents listed above.\n"
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


REQUIRED_SECTION_NAMES: frozenset[str] = frozenset({
    "SYSTEM ROLE",
    "SENTINELAI ARCHITECTURE",
    "AVAILABLE TOOLS",
    "AVAILABLE INTENTS",
    "PARAMETER RULES",
    "SECURITY RULES",
    "OUTPUT JSON SCHEMA",
    "POSITIVE EXAMPLES",
    "NEGATIVE EXAMPLES",
})


# ── Default Implementation ────────────────────────────────────────

PROMPT_BUILDER_VERSION = "dynamic-v2"


class DefaultPromptBuilder(PromptBuilder):
    """Builds structured prompts dynamically from CapabilityRegistry."""

    def __init__(
        self,
        sections: list[PromptSection] | None = None,
        registry: CapabilityRegistry | None = None,
        formatter: PromptFormatter | None = None,
    ) -> None:
        self._registry = registry or CapabilityLoader().discover_and_load()
        self._formatter = formatter or MarkdownPromptFormatter()

        if sections is not None:
            self._sections = list(sections)
        else:
            self._sections = self._build_dynamic_sections()

    @property
    def registry(self) -> CapabilityRegistry:
        return self._registry

    @property
    def sections(self) -> list[PromptSection]:
        """Return the current prompt sections (read-only copy)."""
        return list(self._sections)

    def _build_dynamic_sections(self) -> list[PromptSection]:
        tools_content = self._formatter.format_tools(self._registry)
        intents_content = self._formatter.format_intents(self._registry)
        params_content = self._formatter.format_parameter_rules(self._registry)
        examples_content = self._formatter.format_positive_examples(self._registry)

        return [
            _SECTION_SYSTEM_ROLE,
            _SECTION_ARCHITECTURE,
            PromptSection(name="AVAILABLE TOOLS", content=tools_content),
            PromptSection(name="AVAILABLE INTENTS", content=intents_content),
            PromptSection(name="PARAMETER RULES", content=params_content),
            _SECTION_SECURITY_RULES,
            _SECTION_OUTPUT_SCHEMA,
            PromptSection(name="POSITIVE EXAMPLES", content=examples_content),
            _SECTION_NEGATIVE_EXAMPLES,
        ]

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


DEFAULT_SECTIONS: list[PromptSection] = DefaultPromptBuilder().sections

