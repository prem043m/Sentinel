from app.context.models import ContextRole, ContextSource
from app.context.policy import ContextPolicy


def _allows(content, metadata=None):
    return ContextPolicy(max_content_characters=30).allows(content, role=ContextRole.TOOL, source=ContextSource.TOOL, metadata=metadata)


def test_policy_allows_small_conversation_and_file_content():
    assert _allows("requests\npytest")


def test_policy_rejects_binary_secrets_stack_traces_debug_logs_and_large_content():
    assert not _allows("text\x00binary")
    assert not _allows("password=not-for-context")
    assert not _allows('Traceback (most recent call last):\n  File "x.py", line 1')
    assert not _allows("DEBUG: temporary details")
    assert not _allows("x" * 31)


def test_policy_rejects_sensitive_metadata():
    assert not _allows("ordinary text", {"api_key": "hidden"})
