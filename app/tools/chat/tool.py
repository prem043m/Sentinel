"""Chat tool — routes conversational prompts through the standard tool pipeline."""

from __future__ import annotations

import hashlib
import logging

import requests

from app.context.manager import ContextManager
from app.llm.service import LLMService
from app.models.plan import Plan
from app.tools.base import Tool
from app.core.logger import RequestLogger
from app.core.timing import timer_scope, record_metadata
from app.tools.result import ExecutionResult

logger = RequestLogger("SentinelAI.ChatTool")


class ChatTool(Tool):
    """Handles the ``chat`` intent via the standard :class:`Tool` pipeline.

    Instead of bypassing :class:`ToolExecutor`, conversational requests are
    routed here so they benefit from the same error handling, context
    recording, and lifecycle hooks as every other tool.

    Args:
        llm: The LLM provider used to generate responses.
        context_manager: Session context manager that builds the chat prompt
            from conversation history and the current user request.
    """

    def __init__(self, llm: LLMService, context_manager: ContextManager) -> None:
        self._llm = llm
        self._context_manager = context_manager

    def execute(self, plan: Plan) -> ExecutionResult:
        """Build a contextual chat prompt and return the LLM's response.

        The method extracts the user's raw prompt from ``plan.parameters``,
        enriches it with conversation history via
        :meth:`ContextManager.build_chat_prompt`, and forwards the result to
        the configured :class:`LLMService`.

        Args:
            plan: The execution plan produced by the planner.  Expected to
                carry a ``prompt`` key inside ``plan.parameters``.

        Returns:
            An :class:`ExecutionResult` with the LLM's reply on success, or a
            user-friendly error message on failure.
        """
        prompt: str = plan.parameters.get("prompt", "")

        try:
            with timer_scope("ContextResolver"):
                logger.info("Resolving context and artifacts for prompt...")
                resolved = self._context_manager.resolve_context(prompt)

            with timer_scope("PromptBuilder"):
                logger.info("Building chat prompt from resolved context...")
                chat_prompt: str = self._context_manager.build_chat_prompt_resolved(resolved, prompt)

            # Record prompt metrics
            char_count = len(chat_prompt)
            est_tokens = char_count // 4
            artifact_count = len(resolved.artifacts)
            history_count = len(resolved.conversation_history)

            # Character breakdowns
            conversation_chars = sum(len(entry.content) for entry in resolved.conversation_history)
            artifact_chars = sum(len(art.content) for art in resolved.artifacts)
            system_chars = len(self._context_manager._formatter._CHAT_INSTRUCTIONS)
            prompt_hash = hashlib.sha256(chat_prompt.encode("utf-8")).hexdigest()[:12]
            
            record_metadata("prompt_chars", char_count)
            record_metadata("prompt_tokens", est_tokens)
            record_metadata("prompt_artifacts", artifact_count)
            record_metadata("prompt_history", history_count)
            record_metadata("artifacts_used", ", ".join(a.name for a in resolved.artifacts) or "None")
            record_metadata("conversation_chars", conversation_chars)
            record_metadata("artifact_chars", artifact_chars)
            record_metadata("system_chars", system_chars)
            record_metadata("prompt_hash", prompt_hash)

            logger.info(
                "Prompt Metrics: characters=%d, est_tokens=%d, artifacts=%d, history_entries=%d, hash=%s",
                char_count,
                est_tokens,
                artifact_count,
                history_count,
                prompt_hash,
            )

            # Save prompt to debug file logs/last_prompt.txt
            try:
                import os
                os.makedirs("logs", exist_ok=True)
                with open("logs/last_prompt.txt", "w", encoding="utf-8") as f:
                    f.write(chat_prompt)
                logger.info("Saved debug prompt copy to 'logs/last_prompt.txt'")
            except Exception as e:
                logger.warning("Failed to save debug prompt file: %s", e)

            logger.info("Sending chat prompt to LLM...")
            with timer_scope("LLMRequest"):
                response: str = self._llm.generate(chat_prompt)

            record_metadata("response_length", len(response))

        except (
            requests.exceptions.RequestException,
            KeyError,
            ConnectionError,
            TimeoutError,
        ) as exc:
            logger.error("Chat generation failed: %s", exc)
            return ExecutionResult(
                success=False,
                message=(
                    "Unable to get a response from the LLM. "
                    "Please check the server status."
                ),
                data={"error": str(exc)},
            )

        logger.info("Chat response generated successfully.")
        return ExecutionResult(
            success=True,
            message=response,
            data={"type": "chat"},
        )
