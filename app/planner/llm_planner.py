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

import hashlib
from app.core.logger import RequestLogger
from app.core.timing import timer_scope, record_metadata
from app.llm.service import LLMService
from app.models.plan import Plan
from app.planner.prompt_builder import PromptBuilder
from app.planner.response_parser import PlanResponseParser
from app.planner.strategy import PlannerStrategy

logger = RequestLogger("SentinelAI.LLMPlanner")


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

        with timer_scope("PromptBuilder"):
            prompt = self._prompt_builder.build(user_input)

        # Record prompt metrics
        char_count = len(prompt)
        est_tokens = char_count // 4
        prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:12]
        
        record_metadata("prompt_chars", char_count)
        record_metadata("prompt_tokens", est_tokens)
        record_metadata("prompt_artifacts", 0)
        record_metadata("prompt_history", 0)
        record_metadata("artifacts_used", "None")
        record_metadata("conversation_chars", 0)
        record_metadata("artifact_chars", 0)
        record_metadata("system_chars", char_count - len(user_input))
        record_metadata("prompt_hash", prompt_hash)

        logger.info(
            "Planner Prompt Metrics: characters=%d, est_tokens=%d, hash=%s",
            char_count,
            est_tokens,
            prompt_hash,
        )

        logger.info("Sending planning prompt to LLM...")
        with timer_scope("LLMRequest"):
            raw_response = self._llm.generate(prompt)

        record_metadata("response_length", len(raw_response))

        logger.info("Parsing LLM planner response...")
        with timer_scope("LLM_Parsing"):
            plan = self._response_parser.parse(raw_response)

        logger.info(
            "LLMPlanner produced plan: intent='%s', tool='%s'.",
            plan.intent,
            plan.tool,
        )

        return plan