"""Tests for the PlanResponseParser."""

import json

import pytest

from app.planner.response_parser import JSONPlanResponseParser


class TestValidJSON:
    """Tests for valid JSON responses."""

    def test_valid_json_returns_plan(self):
        parser = JSONPlanResponseParser()
        raw = json.dumps({
            "intent": "open_application",
            "tool": "application",
            "parameters": {"name": "Calculator"},
        })

        plan = parser.parse(raw)

        assert plan.intent == "open_application"
        assert plan.tool == "application"
        assert plan.parameters["name"] == "Calculator"

    def test_chat_intent_returns_plan(self):
        parser = JSONPlanResponseParser()
        raw = json.dumps({
            "intent": "chat",
            "tool": "llm",
            "parameters": {"prompt": "hello world"},
        })

        plan = parser.parse(raw)

        assert plan.intent == "chat"
        assert plan.parameters["prompt"] == "hello world"

    def test_empty_parameters_allowed(self):
        parser = JSONPlanResponseParser()
        raw = json.dumps({
            "intent": "chat",
            "tool": "llm",
            "parameters": {},
        })

        plan = parser.parse(raw)

        assert plan.parameters == {}


class TestCodeFenceStripping:
    """Tests for markdown code fence handling."""

    def test_json_in_code_fence(self):
        parser = JSONPlanResponseParser()
        raw = '```json\n{"intent":"chat","tool":"llm","parameters":{}}\n```'

        plan = parser.parse(raw)

        assert plan.intent == "chat"

    def test_plain_code_fence(self):
        parser = JSONPlanResponseParser()
        raw = '```\n{"intent":"chat","tool":"llm","parameters":{}}\n```'

        plan = parser.parse(raw)

        assert plan.intent == "chat"

    def test_code_fence_with_extra_whitespace(self):
        parser = JSONPlanResponseParser()
        raw = (
            '  ```json  \n'
            '  {"intent":"chat","tool":"llm","parameters":{}}  \n'
            '  ```  '
        )

        plan = parser.parse(raw)

        assert plan.intent == "chat"


class TestInvalidResponses:
    """Tests for responses that should fail parsing."""

    def test_empty_string_raises(self):
        parser = JSONPlanResponseParser()

        with pytest.raises(ValueError, match="Empty"):
            parser.parse("")

    def test_whitespace_only_raises(self):
        parser = JSONPlanResponseParser()

        with pytest.raises(ValueError, match="Empty"):
            parser.parse("   ")

    def test_malformed_json_raises(self):
        parser = JSONPlanResponseParser()

        with pytest.raises(ValueError, match="Invalid JSON"):
            parser.parse("{not valid json}")

    def test_missing_intent_raises(self):
        parser = JSONPlanResponseParser()
        raw = json.dumps({
            "tool": "llm",
            "parameters": {},
        })

        with pytest.raises(ValueError, match="Missing field"):
            parser.parse(raw)

    def test_missing_tool_raises(self):
        parser = JSONPlanResponseParser()
        raw = json.dumps({
            "intent": "chat",
            "parameters": {},
        })

        with pytest.raises(ValueError, match="Missing field"):
            parser.parse(raw)

    def test_missing_parameters_raises(self):
        parser = JSONPlanResponseParser()
        raw = json.dumps({
            "intent": "chat",
            "tool": "llm",
        })

        with pytest.raises(ValueError, match="Missing field"):
            parser.parse(raw)

    def test_json_array_raises(self):
        parser = JSONPlanResponseParser()

        with pytest.raises(ValueError, match="JSON object"):
            parser.parse('[{"intent":"chat","tool":"llm","parameters":{}}]')

    def test_plain_text_raises(self):
        parser = JSONPlanResponseParser()

        with pytest.raises(ValueError):
            parser.parse("I would suggest opening the calculator.")


class TestLogging:
    """Tests that parsing events are logged."""

    def test_successful_parse_logged(self, caplog):
        parser = JSONPlanResponseParser()
        raw = json.dumps({
            "intent": "chat",
            "tool": "llm",
            "parameters": {},
        })

        with caplog.at_level("INFO", logger="SentinelAI.ResponseParser"):
            parser.parse(raw)

        assert any(
            "produced plan" in r.message for r in caplog.records
        )

    def test_malformed_json_logged(self, caplog):
        parser = JSONPlanResponseParser()

        with caplog.at_level("WARNING", logger="SentinelAI.ResponseParser"):
            with pytest.raises(ValueError):
                parser.parse("{broken}")

        assert any(
            "failed to decode" in r.message for r in caplog.records
        )
