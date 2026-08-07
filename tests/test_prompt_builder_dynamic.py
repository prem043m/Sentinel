from app.planner.capabilities.models import (
    CapabilityCategory,
    ExampleCommand,
    ExampleDataset,
    IntentCapability,
    ParameterDefinition,
    ParameterType,
    ToolCapability,
)
from app.planner.capabilities.provider import CapabilityProvider
from app.planner.capabilities.registry import CapabilityRegistry
from app.planner.prompt_builder import DefaultPromptBuilder


class TerminalCapabilityProvider(CapabilityProvider):
    def build(self) -> ToolCapability:
        intent = IntentCapability(
            id="terminal.run",
            name="run_command",
            description="Runs shell command",
            tool_name="terminal",
            category=CapabilityCategory.SYSTEM,
            parameters=(
                ParameterDefinition("command", ParameterType.STRING, "command line string"),
            ),
            examples=ExampleDataset((
                ExampleCommand("run dir", "run_command", "terminal", {"command": "dir"}),
            )),
        )
        return ToolCapability(
            tool_name="terminal",
            description="Executes shell commands",
            category=CapabilityCategory.SYSTEM,
            intents=(intent,),
        )


def test_adding_new_capability_updates_prompt_without_prompt_builder_changes():
    registry = CapabilityRegistry()
    registry.register(TerminalCapabilityProvider().build())

    builder = DefaultPromptBuilder(registry=registry)
    prompt = builder.build("run dir")

    assert "| terminal |" in prompt
    assert "| run_command |" in prompt
    assert "For 'run_command'" in prompt
    assert "run dir" in prompt
