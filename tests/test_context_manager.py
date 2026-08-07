from datetime import timezone

from app.context.manager import ContextManager
from app.context.models import ContextRole, ContextSource
from app.context.policy import ContextPolicy
from app.context.window import ContextWindow
from app.tools.result import ExecutionResult


def test_adds_entries_in_order_with_utc_timestamp():
    manager = ContextManager()
    user = manager.add_user_message("Read requirements.txt")
    assistant = manager.add_assistant_message("Reading it.")

    assert [entry.role for entry in manager.history()] == [ContextRole.USER, ContextRole.ASSISTANT]
    assert user.source is ContextSource.USER
    assert assistant.timestamp.tzinfo is timezone.utc


def test_tool_result_keeps_successful_file_content():
    manager = ContextManager()
    result = ExecutionResult(True, "Successfully read requirements.txt.", {"path": "requirements.txt", "content": "requests\npytest"})

    entry = manager.add_tool_result(result)

    assert entry is not None
    assert entry.role is ContextRole.TOOL
    assert "requests" in entry.content
    assert entry.metadata["path"] == "requirements.txt"


def test_failed_tool_result_is_not_retained():
    manager = ContextManager()
    assert manager.add_tool_result(ExecutionResult(False, "Traceback: failure")) is None
    assert manager.history() == ()


def test_clear_discards_only_this_manager_session():
    first = ContextManager()
    second = ContextManager()
    first.add_user_message("one")
    second.add_user_message("two")

    first.clear()

    assert first.history() == ()
    assert [entry.content for entry in second.history()] == ["two"]


def test_trim_applies_configured_window():
    manager = ContextManager(window=ContextWindow(max_user_messages=1, max_assistant_messages=1, max_tool_outputs=1, max_total_characters=100))
    manager.add_user_message("first")
    manager.add_user_message("second")

    assert [entry.content for entry in manager.history()] == ["second"]


def test_build_context_excludes_current_request_from_history():
    manager = ContextManager()
    manager.add_user_message("Read requirements.txt")
    manager.add_assistant_message("Successfully read requirements.txt.")
    manager.add_user_message("Explain it.")

    prompt = manager.build_context("Explain it.")

    assert "Read requirements.txt" in prompt
    assert "Assistant:\nSuccessfully read requirements.txt." in prompt
    assert prompt.count("Explain it.") == 1
    assert "Current User Request\nExplain it." in prompt


def test_build_chat_prompt_includes_session_tool_content():
    manager = ContextManager()
    manager.add_tool_result(
        ExecutionResult(
            True,
            "Successfully read README.md.",
            {
                "path": "README.md",
                "content": "# SentinelAI\n\nSentinelAI is a local-first, security-oriented Windows desktop assistant.\n\n## How it works\n\n- User input -> AssistantController -> Planner -> Plan\n- PolicyEngine evaluates the requested intent before execution",
            },
        )
    )

    prompt = manager.build_chat_prompt("Explain it.")

    assert "[SESSION CONTEXT]" in prompt
    assert "Tool Output" in prompt
    assert "README.md:" in prompt
    assert "SentinelAI is a local-first, security-oriented Windows desktop assistant." in prompt
    assert prompt.endswith("Current User Request\nExplain it.")


def test_entry_metadata_is_immutable():
    entry = ContextManager().add_user_message("hello", {"topic": "greeting"})
    try:
        entry.metadata["topic"] = "other"
        assert False, "metadata must be immutable"
    except TypeError:
        pass
