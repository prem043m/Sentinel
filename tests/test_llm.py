"""Tests for the LLMClient (Ollama provider)."""

import pytest
from unittest.mock import patch, MagicMock

from app.llm.client import LLMClient
from app.llm.service import LLMService


def test_llm_client_implements_llm_service():
    """LLMClient must implement the LLMService interface."""
    assert issubclass(LLMClient, LLMService)


def test_generate_returns_string_on_success():
    """Mocked Ollama returns a valid response."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"response": "Hello!"}
    mock_response.raise_for_status = MagicMock()

    with patch("app.llm.client.requests.post", return_value=mock_response):
        client = LLMClient()
        result = client.generate("Hi")

    assert result == "Hello!"
    assert isinstance(result, str)


def test_generate_raises_on_connection_error():
    """Connection errors propagate instead of being silenced."""
    import requests

    with patch(
        "app.llm.client.requests.post",
        side_effect=requests.exceptions.ConnectionError("no server"),
    ):
        client = LLMClient()
        with pytest.raises(requests.exceptions.ConnectionError):
            client.generate("Hi")


def test_generate_raises_on_timeout():
    """Timeouts propagate instead of being silenced."""
    import requests

    with patch(
        "app.llm.client.requests.post",
        side_effect=requests.exceptions.Timeout("timed out"),
    ):
        client = LLMClient()
        with pytest.raises(requests.exceptions.Timeout):
            client.generate("Hi")