from app.context.models import ContextEntry, ContextRole, ContextSource
from app.context.window import ContextWindow


def _entry(role, content):
    return ContextEntry(role, ContextSource.TOOL if role is ContextRole.TOOL else ContextSource.USER, content)


def test_window_removes_oldest_entry_per_role():
    window = ContextWindow(max_user_messages=1, max_assistant_messages=10, max_tool_outputs=1, max_total_characters=100)
    entries = [_entry(ContextRole.USER, "old"), _entry(ContextRole.TOOL, "tool"), _entry(ContextRole.USER, "new")]

    assert [entry.content for entry in window.trim(entries)] == ["tool", "new"]


def test_window_removes_oldest_entries_until_total_character_limit_fits():
    window = ContextWindow(max_user_messages=10, max_assistant_messages=10, max_tool_outputs=10, max_total_characters=5)
    entries = [_entry(ContextRole.USER, "one"), _entry(ContextRole.USER, "two")]

    assert [entry.content for entry in window.trim(entries)] == ["two"]


def test_window_rejects_negative_limits():
    try:
        ContextWindow(max_user_messages=-1)
        assert False, "negative limits must be rejected"
    except ValueError:
        pass
