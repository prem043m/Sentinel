"""Execution history tracking for SentinelAI.

Maintains a session-scoped database of all request executions, recording the
full pipeline trace (request -> plan -> policy -> tool -> result -> latency).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Sequence

logger = logging.getLogger("SentinelAI.ExecutionHistory")


@dataclass(frozen=True, slots=True)
class ExecutionRecord:
    """A trace recording the execution pipeline of a single request.

    Attributes:
        request_id: Unique correlation ID.
        timestamp: Time when the request was processed.
        raw_message: The raw input message from the user.
        plan: The generated Plan, if planning succeeded.
        policy_decision: The policy evaluation result, if evaluated.
        tool_result: The executed tool's result, if executed.
        timings: Latency metrics recorded across different layers (in ms).
        success: True if the request was processed without exceptions.
    """

    request_id: str
    raw_message: str
    plan: Any | None = None
    policy_decision: Any | None = None
    tool_result: Any | None = None
    timings: dict[str, float] = field(default_factory=dict)
    success: bool = True
    timestamp: float = field(default_factory=lambda: datetime.now(timezone.utc).timestamp())


class ExecutionHistory:
    """In-memory session history database for request execution traces.

    Allows diagnostics, shadow evaluation statistics, and performance analysis.
    """

    def __init__(self) -> None:
        self._records: dict[str, ExecutionRecord] = {}

    def add_record(self, record: ExecutionRecord) -> None:
        """Add an execution record to the history trace.

        Args:
            record: The execution record to register.
        """
        self._records[record.request_id] = record
        logger.info(
            "Execution history trace recorded: request_id=%s, success=%s, total_latency=%.1f ms",
            record.request_id,
            record.success,
            record.timings.get("total", 0.0),
        )

    def get_record(self, request_id: str) -> ExecutionRecord | None:
        """Retrieve an execution record by request ID.

        Args:
            request_id: The request correlation ID.

        Returns:
            The ExecutionRecord if found, else None.
        """
        return self._records.get(request_id)

    def list_records(self) -> Sequence[ExecutionRecord]:
        """List all execution records in chronological order.

        Returns:
            A sequence of all recorded traces.
        """
        return sorted(self._records.values(), key=lambda r: r.timestamp)

    def clear(self) -> None:
        """Clear all session history records."""
        self._records.clear()
        logger.debug("Execution history cleared.")
