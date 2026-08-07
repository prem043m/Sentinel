"""Application controller — coordinates the SentinelAI pipeline with observability.

Every user request flows through this single, unified pipeline:

    ContextManager → Planner → PolicyEngine → ToolExecutor → Response

No intent receives special treatment.  Chat, filesystem, browser, and application
requests all follow the same path. In addition, latency metrics and correlation request
IDs are tracked across all execution layers.
"""

from __future__ import annotations

import time

from app.context.manager import ContextManager
from app.core.history import ExecutionHistory, ExecutionRecord
from app.core.logger import RequestLogger
from app.core.request_context import generate_request_id, request_id_scope
from app.core.timing import clear_timings, get_timings, record_timing, timer_scope, get_metadata
from app.models.plan import PlanOutcome
from app.planner.planner import Planner
from app.policy.engine import PolicyEngine
from app.tools.executor import ToolExecutor
from app.tools.registry import create_default_registry

logger = RequestLogger("SentinelAI.AssistantController")


class AssistantController:
    """Coordinates the application's workflow.

    The controller is a pure pipeline coordinator.  It does not contain business
    logic, LLM calls, or tool-specific code. Every executable action flows through
    :class:`ToolExecutor`.

    Args:
        planner: Planning facade (defaults to :class:`Planner`
            backed by :class:`PlannerOrchestrator`).
        policy: Policy evaluation engine.
        executor: Tool dispatch engine.
        context_manager: Session-scoped conversation context.
        history: Session-scoped execution history registry.
    """

    def __init__(
        self,
        planner: Planner | None = None,
        policy: PolicyEngine | None = None,
        executor: ToolExecutor | None = None,
        context_manager: ContextManager | None = None,
        history: ExecutionHistory | None = None,
    ) -> None:
        self.context_manager = context_manager or ContextManager()
        self.planner = planner or Planner()
        self.policy = policy or PolicyEngine()
        self.executor = executor or ToolExecutor(
            create_default_registry(
                context_manager=self.context_manager,
            )
        )
        self.history = history or ExecutionHistory()

    def process_message(self, message: str) -> str:
        """Process a user message through the full pipeline.

        Pipeline stages:
        1. Start request timing and generate request correlation ID.
        2. Record user input in context.
        3. Create a plan via the planner.
        4. Evaluate the plan against security policies.
        5. Execute the plan via the appropriate tool.
        6. Record tool results and assistant response in context.
        7. Save execution record to history database and log timing metrics.

        Args:
            message: The raw text entered by the user.

        Returns:
            The response string to display to the user.
        """
        clear_timings()
        request_id = generate_request_id()

        with request_id_scope(request_id):
            logger.info("Request received: '%s'", message[:100])
            start_time = time.perf_counter()

            plan = None
            decision = None
            result = None
            success = True
            response = ""

            try:
                # 2. Add user message
                with timer_scope("context_entry"):
                    self.context_manager.add_user_message(message)

                # 3. Planning
                with timer_scope("planning"):
                    plan = self.planner.create_plan(message)

                if plan.outcome == PlanOutcome.UNSUPPORTED:
                    response = (
                        f"Unsupported operation.\n"
                        f"Reason: {plan.parameters.get('reason', 'This operation is not supported.')}"
                    )
                    with timer_scope("context_entry"):
                        self.context_manager.add_assistant_message(response)
                    return response

                # 4. Policy Evaluation
                with timer_scope("policy_evaluation"):
                    decision = self.policy.evaluate(plan)

                if not decision.allowed:
                    response = (
                        f"Blocked by Policy Engine.\n"
                        f"Reason: {decision.reason}"
                    )
                    with timer_scope("context_entry"):
                        self.context_manager.add_assistant_message(response)
                    return response

                if decision.confirmation_required:
                    response = (
                        f"Confirmation required.\n"
                        f"Risk: {decision.risk.value}"
                    )
                    with timer_scope("context_entry"):
                        self.context_manager.add_assistant_message(response)
                    return response

                # 5. Tool Execution
                with timer_scope("tool_execution"):
                    result = self.executor.execute(plan)

                # 6. Capture Tool Results
                with timer_scope("context_entry"):
                    self.context_manager.add_tool_result(result, plan)

                response = result.message

                with timer_scope("context_entry"):
                    self.context_manager.add_assistant_message(response)

                return response

            except Exception as exc:
                success = False
                logger.error("Error processing request: %s", exc, exc_info=True)
                response = f"An internal error occurred: {exc}"
                return response

            finally:
                # 7. Record total request latency
                total_latency_ms = (time.perf_counter() - start_time) * 1000.0
                record_timing("total", total_latency_ms)

                # Fetch and format timing and metrics summary
                timings = get_timings()
                meta = get_metadata()

                summary_lines = [
                    "",
                    "================ REQUEST SUMMARY ================",
                    f"Request ID             : {request_id}",
                    f"Prompt Hash            : {meta.get('prompt_hash', 'N/A')}",
                    f"Planner                : {timings.get('planning', 0.0):.1f} ms",
                    f"Policy                 : {timings.get('policy_evaluation', 0.0):.1f} ms",
                    f"Executor               : {timings.get('tool_execution', 0.0):.1f} ms",
                    f"ContextResolver        : {timings.get('ContextResolver', 0.0):.1f} ms",
                    f"PromptBuilder          : {timings.get('PromptBuilder', 0.0):.1f} ms",
                    f"Prompt Size            : {meta.get('prompt_chars', 0):,} chars (≈{meta.get('prompt_tokens', 0):,} tokens)",
                    f"  System Prompt        : {meta.get('system_chars', 0):,} chars",
                    f"  Conversation History : {meta.get('conversation_chars', 0):,} chars ({meta.get('prompt_history', 0)} messages)",
                    f"  Artifacts Injected   : {meta.get('artifact_chars', 0):,} chars ({meta.get('prompt_artifacts', 0)} artifacts)",
                    f"LLM Request            : {timings.get('LLMRequest', 0.0):.1f} ms",
                    f"Response Length        : {meta.get('response_length', 0):,} chars",
                    f"Artifacts Used         : {meta.get('artifacts_used', 'None')}",
                    f"Total                  : {timings.get('total', 0.0):.1f} ms",
                    "================================================="
                ]
                logger.info("\n".join(summary_lines))

                # Save execution record trace to history
                record = ExecutionRecord(
                    request_id=request_id,
                    raw_message=message,
                    plan=plan,
                    policy_decision=decision,
                    tool_result=result,
                    timings=timings,
                    success=success,
                )
                self.history.add_record(record)

    def warm_up(self) -> dict[str, Any]:
        """Verify LLM connection status and warm/load the model.

        Returns:
            A dictionary containing status metadata.
        """
        chat_tool = self.executor._registry.get("llm")
        if chat_tool and hasattr(chat_tool, "_llm") and hasattr(chat_tool._llm, "warm_up"):
            return chat_tool._llm.warm_up()
        return {}
