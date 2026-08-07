"""Comprehensive tests for the ChatTool."""

import requests
import pytest

from app.context.manager import ContextManager
from app.llm.service import LLMService
from app.models.plan import Plan
from app.tools.chat.tool import ChatTool
from app.tools.result import ExecutionResult


# ═════════════════════════════════════════════════════════════════
# Mock helpers
# ═════════════════════════════════════════════════════════════════


class MockLLM(LLMService):
    """LLMService that returns a canned response and records the prompt."""

    def __init__(self, response: str = "mock response") -> None:
        self.response = response
        self.received_prompt: str | None = None

    def generate(self, prompt: str) -> str:
        self.received_prompt = prompt
        return self.response


class FailingLLM(LLMService):
    """LLMService that always raises a configured exception."""

    def __init__(self, error: Exception) -> None:
        self.error = error

    def generate(self, prompt: str) -> str:
        raise self.error


def _chat_plan(prompt: str = "hello") -> Plan:
    """Build a minimal chat Plan for testing."""
    return Plan(intent="chat", tool="llm", parameters={"prompt": prompt})


# ═════════════════════════════════════════════════════════════════
# TestChatToolSuccess
# ═════════════════════════════════════════════════════════════════


class TestChatToolSuccess:
    """Happy-path tests for ChatTool.execute()."""

    def test_chat_returns_successful_result(self) -> None:
        llm = MockLLM(response="hello")
        ctx = ContextManager()
        tool = ChatTool(llm=llm, context_manager=ctx)

        result = tool.execute(_chat_plan("hi"))

        assert result.success is True
        assert result.message == "hello"

    def test_chat_passes_prompt_to_context_manager(self) -> None:
        llm = MockLLM()
        ctx = ContextManager()
        tool = ChatTool(llm=llm, context_manager=ctx)

        plan = _chat_plan("What is Python?")
        tool.execute(plan)

        # build_chat_prompt is called with the plan's prompt parameter;
        # the resulting string is forwarded to generate().
        assert llm.received_prompt is not None
        assert "What is Python?" in llm.received_prompt

    def test_chat_result_data_contains_type(self) -> None:
        llm = MockLLM(response="ok")
        ctx = ContextManager()
        tool = ChatTool(llm=llm, context_manager=ctx)

        result = tool.execute(_chat_plan())

        assert result.data is not None
        assert result.data["type"] == "chat"

    def test_chat_with_empty_prompt(self) -> None:
        llm = MockLLM(response="I can still respond")
        ctx = ContextManager()
        tool = ChatTool(llm=llm, context_manager=ctx)

        result = tool.execute(_chat_plan(""))

        assert result.success is True
        assert result.message == "I can still respond"


# ═════════════════════════════════════════════════════════════════
# TestChatToolErrors
# ═════════════════════════════════════════════════════════════════


class TestChatToolErrors:
    """Verify that LLM failures are caught and mapped to safe results."""

    def test_connection_error_returns_failure(self) -> None:
        llm = FailingLLM(ConnectionError("server down"))
        ctx = ContextManager()
        tool = ChatTool(llm=llm, context_manager=ctx)

        result = tool.execute(_chat_plan())

        assert result.success is False

    def test_timeout_error_returns_failure(self) -> None:
        llm = FailingLLM(TimeoutError("timed out"))
        ctx = ContextManager()
        tool = ChatTool(llm=llm, context_manager=ctx)

        result = tool.execute(_chat_plan())

        assert result.success is False

    def test_request_exception_returns_failure(self) -> None:
        llm = FailingLLM(requests.exceptions.RequestException("bad request"))
        ctx = ContextManager()
        tool = ChatTool(llm=llm, context_manager=ctx)

        result = tool.execute(_chat_plan())

        assert result.success is False

    def test_key_error_returns_failure(self) -> None:
        llm = FailingLLM(KeyError("missing key"))
        ctx = ContextManager()
        tool = ChatTool(llm=llm, context_manager=ctx)

        result = tool.execute(_chat_plan())

        assert result.success is False

    def test_error_message_is_user_friendly(self) -> None:
        llm = FailingLLM(ConnectionError("socket closed"))
        ctx = ContextManager()
        tool = ChatTool(llm=llm, context_manager=ctx)

        result = tool.execute(_chat_plan())

        assert "Unable to get a response" in result.message

    def test_error_does_not_raise(self) -> None:
        llm = FailingLLM(ConnectionError("boom"))
        ctx = ContextManager()
        tool = ChatTool(llm=llm, context_manager=ctx)

        # Must not propagate — the tool should always return an ExecutionResult.
        result = tool.execute(_chat_plan())
        assert isinstance(result, ExecutionResult)


# ═════════════════════════════════════════════════════════════════
# TestChatToolDependencyInjection
# ═════════════════════════════════════════════════════════════════


class TestChatToolDependencyInjection:
    """Verify that ChatTool honours dependency injection contracts."""

    def test_accepts_any_llm_service(self) -> None:
        class CustomLLM(LLMService):
            def generate(self, prompt: str) -> str:
                return "custom"

        tool = ChatTool(llm=CustomLLM(), context_manager=ContextManager())
        result = tool.execute(_chat_plan())

        assert result.success is True
        assert result.message == "custom"

    def test_accepts_any_context_manager(self) -> None:
        llm = MockLLM(response="ok")
        ctx = ContextManager()
        tool = ChatTool(llm=llm, context_manager=ctx)

        # Merely constructing and executing with a real ContextManager
        # proves DI wiring works without coupling to a concrete subclass.
        result = tool.execute(_chat_plan("test DI"))
        assert result.success is True
