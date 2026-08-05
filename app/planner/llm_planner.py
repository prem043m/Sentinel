"""LLM-based planner.

Coordinates prompt construction, LLM invocation, and response
parsing to produce a ``Plan`` from natural-language user input.

This planner has exactly one responsibility: **coordinate**.
It does NOT:
- Build prompts  (``PromptBuilder`` does that)
- Call the LLM   (``LLMService`` does that)
- Parse JSON     (``PlanResponseParser`` does that)
- Handle fallback (``PlannerOrchestrator`` does that)

If any step fails, the exception propagates to the orchestrator.
"""

import logging

from app.llm.service import LLMService
from app.models.plan import Plan
from app.planner.prompt_builder import PromptBuilder
from app.planner.response_parser import PlanResponseParser
from app.planner.strategy import PlannerStrategy

logger = logging.getLogger("SentinelAI.LLMPlanner")


class LLMPlanner(PlannerStrategy):
    """Produces a ``Plan`` by consulting an LLM.

    All three dependencies are injected via the constructor,
    making this class trivially testable and provider-agnostic.

    Args:
        llm: The LLM service to call.
        prompt_builder: Constructs the prompt string.
        response_parser: Parses the LLM response into a ``Plan``.
    """

    def __init__(
        self,
        llm: LLMService,
        prompt_builder: PromptBuilder,
        response_parser: PlanResponseParser,
    ) -> None:
        self._llm = llm
        self._prompt_builder = prompt_builder
        self._response_parser = response_parser

    def create_plan(self, user_input: str) -> Plan:
        """Convert user input into a ``Plan`` via the LLM.

        Steps:
        1. Build the prompt (``PromptBuilder``).
        2. Send to the LLM (``LLMService``).
        3. Parse the response (``PlanResponseParser``).

        Any exception is allowed to propagate so that the
        ``PlannerOrchestrator`` can trigger fallback.

        Args:
            user_input: The raw text entered by the user.

        Returns:
            A validated ``Plan`` instance.
        """
        logger.debug("LLMPlanner building prompt for: '%s'.", user_input)

        prompt = self._prompt_builder.build(user_input)

        logger.debug("LLMPlanner sending prompt to LLM (%d chars).", len(prompt))

        raw_response = self._llm.generate(prompt)

        logger.debug(
            "LLMPlanner received response (%d chars).",
            len(raw_response),
        )

        plan = self._response_parser.parse(raw_response)

        logger.info(
            "LLMPlanner produced plan: intent='%s', tool='%s'.",
            plan.intent,
            plan.tool,
        )

        return plan