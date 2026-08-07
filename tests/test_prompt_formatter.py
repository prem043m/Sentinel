from app.planner.capabilities.formatter import MarkdownPromptFormatter
from app.planner.capabilities.loader import CapabilityLoader


def test_markdown_prompt_formatter_generates_sections():
    registry = CapabilityLoader().discover_and_load("app.tools")
    formatter = MarkdownPromptFormatter()

    tools_text = formatter.format_tools(registry)
    intents_text = formatter.format_intents(registry)
    rules_text = formatter.format_parameter_rules(registry)
    examples_text = formatter.format_positive_examples(registry)

    assert "| filesystem |" in tools_text
    assert "| read_file |" in intents_text
    assert "For 'read_file'" in rules_text
    assert "Read the README file" in examples_text
