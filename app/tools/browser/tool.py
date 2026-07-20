"""Browser tool — safe URL opener and web search.

This is the **only** module in SentinelAI that interacts with the
user's web browser.  All other layers remain browser-free.

Security invariants:
- Every URL is validated by the ``URLValidator`` before any browser
  access occurs.
- Only ``http`` and ``https`` schemes are permitted.
- URLs with embedded credentials are rejected.
- Every operation (success or failure) is logged.

The tool dispatches based on ``plan.intent``:
- ``"open_url"``   → opens a validated URL in the default browser.
- ``"search_web"`` → constructs a search URL and opens it.

Future handlers (download, automation) can be added to the dispatch
table without modifying existing logic.
"""

import logging
import webbrowser
from urllib.parse import quote_plus

from app.models.plan import Plan
from app.tools.base import Tool
from app.tools.browser.config import (
    SearchEngine,
    create_default_search_engine,
)
from app.tools.browser.validator import URLValidationError, URLValidator
from app.tools.result import ExecutionResult

logger = logging.getLogger("SentinelAI.BrowserTool")

# ── Intent dispatch table ─────────────────────────────────────────
# Maps plan.intent strings to handler method names.
# New capabilities are added here without touching execute().
_INTENT_HANDLERS: dict[str, str] = {
    "open_url": "_open_url",
    "search_web": "_search_web",
    "open_browser": "_open_url",
}


class BrowserTool(Tool):
    """Opens URLs and performs web searches safely.

    The tool validates requested URLs against the security
    configuration, rejects unsafe schemes, and opens the user's
    default browser.

    Args:
        validator: An optional ``URLValidator`` instance.  When
                   ``None``, a default validator is constructed.
        search_engine: An optional ``SearchEngine`` instance.  When
                       ``None``, the default search engine is used.
    """

    def __init__(
        self,
        validator: URLValidator | None = None,
        search_engine: SearchEngine | None = None,
    ) -> None:
        self._validator = validator or URLValidator()
        self._search_engine = search_engine or create_default_search_engine()

    def execute(self, plan: Plan) -> ExecutionResult:
        """Execute a browser request.

        Dispatches to the appropriate internal handler based on
        ``plan.intent``.  Unknown intents return a failure result.

        Args:
            plan: A ``Plan`` containing intent and parameters.

        Returns:
            An ``ExecutionResult``.
        """
        handler_name = _INTENT_HANDLERS.get(plan.intent)

        if handler_name is None:
            logger.warning(
                "BrowserTool received unknown intent: '%s'.",
                plan.intent,
            )
            return ExecutionResult(
                success=False,
                message=f"Unknown browser intent: '{plan.intent}'.",
            )

        handler = getattr(self, handler_name)
        return handler(plan.parameters)

    # ── Handlers ──────────────────────────────────────────────────

    def _open_url(self, parameters: dict) -> ExecutionResult:
        """Open a URL in the user's default browser."""
        raw_url: str = (
            parameters.get("url")
            or parameters.get("name")
            or ""
        )

        # ── Validate ──────────────────────────────────────────────
        try:
            validated_url = self._validator.validate(raw_url)
        except URLValidationError as exc:
            logger.warning(
                "Browser open rejected: '%s' — %s",
                raw_url,
                exc.reason,
            )
            return ExecutionResult(
                success=False,
                message=exc.reason,
            )

        # ── Open browser ──────────────────────────────────────────
        try:
            opened = webbrowser.open(validated_url)
        except OSError as exc:
            logger.error(
                "Browser open failed (OS error): '%s' — %s",
                validated_url,
                exc,
            )
            return ExecutionResult(
                success=False,
                message=f"Failed to open browser: {exc}",
            )

        if not opened:
            logger.error(
                "Browser open failed: webbrowser.open returned False "
                "for '%s'.",
                validated_url,
            )
            return ExecutionResult(
                success=False,
                message="Failed to open browser. No suitable browser found.",
            )

        logger.info("Browser opened: '%s'.", validated_url)

        return ExecutionResult(
            success=True,
            message=f"Opened '{validated_url}' in the default browser.",
            data={"url": validated_url},
        )

    def _search_web(self, parameters: dict) -> ExecutionResult:
        """Construct a search URL and open it."""
        query: str = parameters.get("query", "")

        if not query or not query.strip():
            logger.warning("Search rejected: empty query.")
            return ExecutionResult(
                success=False,
                message="No search query provided.",
            )

        query = query.strip()
        encoded_query = quote_plus(query)
        search_url = self._search_engine.search_url_template.format(
            query=encoded_query,
        )

        logger.info(
            "Search via %s: '%s'.",
            self._search_engine.name,
            query,
        )

        # Delegate to _open_url for actual browser opening
        return self._open_url({"url": search_url})
