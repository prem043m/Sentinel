"""Format capability metadata into structured prompt text."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.planner.capabilities.models import ParameterType
from app.planner.capabilities.registry import CapabilityRegistry


class PromptFormatter(ABC):
    """Abstract interface for formatting capability metadata into prompt text."""

    @abstractmethod
    def format_tools(self, registry: CapabilityRegistry) -> str:
        """Format available tools into prompt section text."""
        raise NotImplementedError

    @abstractmethod
    def format_intents(self, registry: CapabilityRegistry) -> str:
        """Format available intents into prompt section text."""
        raise NotImplementedError

    @abstractmethod
    def format_parameter_rules(self, registry: CapabilityRegistry) -> str:
        """Format parameter rules into prompt section text."""
        raise NotImplementedError

    @abstractmethod
    def format_positive_examples(self, registry: CapabilityRegistry) -> str:
        """Format positive examples into prompt section text."""
        raise NotImplementedError


class MarkdownPromptFormatter(PromptFormatter):
    """Formats capability metadata into Markdown tables and structured text."""

    def format_tools(self, registry: CapabilityRegistry) -> str:
        tools = registry.all_tools()
        if not tools:
            return "No registered tools available."

        lines: list[str] = [
            "The following tools are registered in SentinelAI. You MUST use exactly one of these tool names in your output.",
            "",
            "| Tool Name | Description | Category |",
            "|-----------|-------------|----------|",
        ]
        for tool in tools:
            lines.append(f"| {tool.tool_name} | {tool.description} | {tool.category.value} |")
        return "\n".join(lines)

    def format_intents(self, registry: CapabilityRegistry) -> str:
        intents = registry.all_intents()
        if not intents:
            return "No registered intents available."

        lines: list[str] = [
            "The following intents are supported. Each intent is bound to exactly one tool. You MUST use one of these intent names.",
            "",
            "| Intent | Tool | Required Parameters | Description |",
            "|--------|------|---------------------|-------------|",
        ]
        for intent in intents:
            req_params = [f"{p.name} ({p.type.value})" for p in intent.parameters if p.required]
            param_str = ", ".join(req_params) if req_params else "none"
            lines.append(f"| {intent.name} | {intent.tool_name} | {param_str} | {intent.description} |")
        return "\n".join(lines)

    def format_parameter_rules(self, registry: CapabilityRegistry) -> str:
        intents = registry.all_intents()
        rules: list[str] = [
            "1. Every intent requires specific parameters as listed above.",
            "2. Parameter values must be strings unless specified otherwise.",
        ]
        rule_num = 3
        for intent in intents:
            for param in intent.parameters:
                rule_text = f"For '{intent.name}': '{param.name}' ({param.description})"
                if param.allowed_values:
                    allowed = ", ".join(repr(v) for v in param.allowed_values)
                    rule_text += f". Allowed values: {allowed}"
                rules.append(f"{rule_num}. {rule_text}.")
                rule_num += 1
        return "\n".join(rules)

    def format_positive_examples(self, registry: CapabilityRegistry) -> str:
        intents = registry.all_intents()
        examples_text: list[str] = []
        import json

        for intent in intents:
            for example in intent.examples.examples:
                payload = {
                    "intent": example.expected_intent,
                    "tool": example.expected_tool,
                    "parameters": dict(example.expected_parameters),
                }
                examples_text.append(f'User: "{example.user_input}"\n{json.dumps(payload, separators=(",", ":"))}')

        return "\n\n".join(examples_text)
