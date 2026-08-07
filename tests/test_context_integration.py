"""Integration test — verify context flows through the unified pipeline.

After Milestone 9.5.1, chat routes through ``ChatTool`` via ``ToolExecutor``.
This test verifies that tool results from a previous request appear in the
chat prompt when the user asks a follow-up question.
"""

from app.context.manager import ContextManager
from app.controller.assistant_controller import AssistantController
from app.models.plan import Plan
from app.tools.base import Tool
from app.tools.result import ExecutionResult


class SequentialPlanner:
    """Returns a sequence of pre-defined plans."""

    def __init__(self, plans):
        self._plans = iter(plans)

    def create_plan(self, _message):
        return next(self._plans)


class FakeFilesystemTool(Tool):
    """Returns a canned file-read result."""

    def execute(self, _plan):
        return ExecutionResult(
            True,
            "Successfully read README.md.",
            {
                "path": "README.md",
                "content": (
                    "# SentinelAI\n\n"
                    "SentinelAI is a local-first, security-oriented "
                    "Windows desktop assistant.\n\n"
                    "## How it works\n\n"
                    "- User input -> AssistantController -> Planner -> Plan\n"
                    "- PolicyEngine evaluates the requested intent before execution"
                ),
            },
        )


class FakeChatTool(Tool):
    """Captures the prompt and returns a canned response."""

    def __init__(self, context_manager):
        self._context_manager = context_manager
        self.prompts = []

    def execute(self, plan):
        prompt = plan.parameters.get("prompt", "")
        chat_prompt = self._context_manager.build_chat_prompt(prompt)
        self.prompts.append(chat_prompt)
        return ExecutionResult(
            True,
            "The README describes SentinelAI's architecture, "
            "runtime behavior, and safety controls.",
            {"type": "chat"},
        )


class FakeExecutor:
    """Routes plans to the appropriate fake tool."""

    def __init__(self, tools):
        self._tools = tools

    def execute(self, plan):
        tool = self._tools.get(plan.tool)
        if tool is None:
            return ExecutionResult(False, f"No tool for '{plan.tool}'.")
        return tool.execute(plan)


def test_controller_observes_tool_results_and_sends_prior_context_to_chat_llm():
    """After reading a file, the next chat prompt must include the file content."""
    manager = ContextManager()
    chat_tool = FakeChatTool(manager)

    planner = SequentialPlanner([
        Plan("read_file", "filesystem", {"path": "requirements.txt"}),
        Plan("chat", "llm", {"prompt": "Explain it."}),
    ])

    executor = FakeExecutor({
        "filesystem": FakeFilesystemTool(),
        "llm": chat_tool,
    })

    controller = AssistantController(
        planner=planner,
        executor=executor,
        context_manager=manager,
    )

    # First request: read file
    assert controller.process_message("Read requirements.txt") == "Successfully read README.md."

    # Second request: chat follow-up
    assert controller.process_message("Explain it.") == (
        "The README describes SentinelAI's architecture, "
        "runtime behavior, and safety controls."
    )

    # Verify the chat prompt included the file content from the previous tool result
    assert len(chat_tool.prompts) == 1
    prompt = chat_tool.prompts[0]
    assert "Successfully read README.md." in prompt
    assert "SentinelAI is a local-first, security-oriented Windows desktop assistant." in prompt
    assert prompt.endswith("Current User Request\nExplain it.")

    # Verify context history: user, tool, assistant, user, tool (chat), assistant
    roles = [entry.role.value for entry in manager.history()]
    assert roles == ["user", "tool", "assistant", "user", "tool", "assistant"]
