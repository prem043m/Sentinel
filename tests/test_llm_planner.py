"""Tests for the LLMPlanner coordinator."""

import json
from unittest.mock import MagicMock

import pytest

from app.planner.llm_planner import LLMPlanner


def _make_llm_planner(llm_response: str) -> tuple[LLMPlanner, MagicMock, MagicMock, MagicMock]:
    """Create an LLMPlanner with mocked dependencies.

    Returns:
        A tuple of (planner, mock_llm, mock_builder, mock_parser).
    """
    mock_llm = MagicMock()
    mock_llm.generate.return_value = llm_response

    mock_builder = MagicMock()
    mock_builder.build.return_value = "the built prompt"

    mock_parser = MagicMock()

    planner = LLMPlanner(
        llm=mock_llm,
        prompt_builder=mock_builder,
        response_parser=mock_parser,
    )

    return planner, mock_llm, mock_builder, mock_parser


class TestLLMPlannerCoordination:
    """Tests that LLMPlanner correctly coordinates its dependencies."""

    def test_prompt_builder_called_with_user_input(self):
        planner, _, mock_builder, _ = _make_llm_planner("response")

        planner.create_plan("open calculator")

        mock_builder.build.assert_called_once_with("open calculator")

    def test_llm_called_with_built_prompt(self):
        planner, mock_llm, _, _ = _make_llm_planner("response")

        planner.create_plan("test")

        mock_llm.generate.assert_called_once_with("the built prompt")

    def test_parser_called_with_llm_response(self):
        planner, _, _, mock_parser = _make_llm_planner("the llm output")

        planner.create_plan("test")

        mock_parser.parse.assert_called_once_with("the llm output")

    def test_returns_parser_result(self):
        planner, _, _, mock_parser = _make_llm_planner("response")
        expected_plan = MagicMock()
        mock_parser.parse.return_value = expected_plan

        result = planner.create_plan("test")

        assert result is expected_plan


class TestLLMPlannerExceptionPropagation:
    """Tests that exceptions propagate (for orchestrator fallback)."""

    def test_llm_connection_error_propagates(self):
        planner, mock_llm, _, _ = _make_llm_planner("")
        mock_llm.generate.side_effect = ConnectionError("no server")

        with pytest.raises(ConnectionError):
            planner.create_plan("test")

    def test_llm_timeout_propagates(self):
        planner, mock_llm, _, _ = _make_llm_planner("")
        mock_llm.generate.side_effect = TimeoutError("timed out")

        with pytest.raises(TimeoutError):
            planner.create_plan("test")

    def test_parser_error_propagates(self):
        planner, _, _, mock_parser = _make_llm_planner("bad json")
        mock_parser.parse.side_effect = ValueError("Invalid JSON")

        with pytest.raises(ValueError):
            planner.create_plan("test")

    def test_prompt_builder_error_propagates(self):
        planner, _, mock_builder, _ = _make_llm_planner("")
        mock_builder.build.side_effect = RuntimeError("builder broke")

        with pytest.raises(RuntimeError):
            planner.create_plan("test")
