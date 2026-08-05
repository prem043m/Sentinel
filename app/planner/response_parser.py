"""LLM response parsing for plan extraction.

This module is the **only** place where raw LLM output is
converted into validated ``Plan`` objects.  No other component
inspects or parses LLM response text.

The abstract ``PlanResponseParser`` interface allows the parsing
strategy to change (JSON today, function calling or XML tomorrow)
without affecting the ``LLMPlanner`` or any other component.
"""

import json
import logging
import re
from abc import ABC, abstractmethod

from app.models.plan import Plan
from app.planner.parser import PlanParser

logger = logging.getLogger("SentinelAI.ResponseParser")


class PlanResponseParser(ABC):
    """Base interface for LLM response parsers.

    Implementations convert a raw LLM response string into a
    validated ``Plan`` object.  They should raise ``ValueError``
    on any parsing failure so that the ``PlannerOrchestrator``
    can trigger fallback.

    Future implementations might support:
    - Function / tool calling formats
    - XML-based responses
    - Multi-plan outputs (returning ``list[Plan]``)
    """

    @abstractmethod
    def parse(self, raw_response: str) -> Plan:
        """Parse raw LLM output into a ``Plan``.

        Args:
            raw_response: The raw text returned by the LLM.

        Returns:
            A validated ``Plan`` instance.

        Raises:
            ValueError: If the response cannot be parsed or
                        fails validation.
        """
        raise NotImplementedError


class JSONPlanResponseParser(PlanResponseParser):
    """Parses JSON-formatted LLM responses into ``Plan`` objects.

    Handles common LLM quirks:
    - Strips markdown code fences (`` ```json ... ``` ``).
    - Strips leading/trailing whitespace.

    Delegates field validation to ``PlanParser.parse()`` so that
    schema rules are defined in exactly one place.
    """

    # Pattern to match markdown code fences wrapping JSON
    _CODE_FENCE_PATTERN = re.compile(
        r"```(?:json)?\s*(.*?)\s*```",
        re.DOTALL,
    )

    def parse(self, raw_response: str) -> Plan:
        """Extract JSON from the LLM response and create a ``Plan``.

        Args:
            raw_response: The raw text returned by the LLM.

        Returns:
            A validated ``Plan`` instance.

        Raises:
            ValueError: If JSON extraction or Plan validation fails.
        """
        if not raw_response or not raw_response.strip():
            logger.warning("Response parser received empty response.")
            raise ValueError("Empty LLM response.")

        cleaned = self._extract_json(raw_response)

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.warning(
                "Response parser failed to decode JSON: %s", exc,
            )
            raise ValueError(f"Invalid JSON in LLM response: {exc}") from exc

        if not isinstance(data, dict):
            logger.warning(
                "Response parser expected a JSON object, got %s.",
                type(data).__name__,
            )
            raise ValueError(
                f"Expected a JSON object, got {type(data).__name__}."
            )

        try:
            plan = PlanParser.parse(data)
        except ValueError as exc:
            logger.warning(
                "Response parser plan validation failed: %s", exc,
            )
            raise

        logger.info(
            "Response parser produced plan: intent='%s', tool='%s'.",
            plan.intent,
            plan.tool,
        )

        return plan

    @classmethod
    def _extract_json(cls, text: str) -> str:
        """Strip markdown code fences if present.

        Args:
            text: Raw LLM output that may contain code fences.

        Returns:
            The cleaned text with fences removed.
        """
        match = cls._CODE_FENCE_PATTERN.search(text)
        if match:
            return match.group(1).strip()
        return text.strip()
