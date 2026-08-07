from app.context.formatter import ContextFormatter
from app.context.models import ContextEntry, ContextRole, ContextSource


def test_formatter_groups_conversation_tool_output_and_current_request():
    entries = [
        ContextEntry(ContextRole.USER, ContextSource.USER, "Search Python decorators"),
        ContextEntry(ContextRole.ASSISTANT, ContextSource.ASSISTANT, "Search completed."),
        ContextEntry(ContextRole.TOOL, ContextSource.TOOL, "Python decorators", {"label": "Search query"}),
    ]

    formatted = ContextFormatter().build_context(entries, "Summarize what I searched.")

    assert "Conversation" in formatted
    assert "User:\nSearch Python decorators" in formatted
    assert "Assistant:\nSearch completed." in formatted
    assert "Tool Output" in formatted
    assert "Search query:\nPython decorators" in formatted
    assert formatted.endswith("Current User Request\nSummarize what I searched.")


def test_formatter_is_deterministic_for_empty_context():
    assert ContextFormatter().build_context([], "Hello") == "[SESSION CONTEXT]\n\nCurrent User Request\nHello"
