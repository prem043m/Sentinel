import logging
import webbrowser
from urllib.parse import quote_plus

from app.models.plan import Plan
from app.tools.browser.config import SearchEngine, create_default_search_engine
from app.tools.browser.validator import URLValidationError, URLValidator
from app.tools.base import Tool
from app.tools.result import ExecutionResult

logger = logging.getLogger("SentinelAI.BrowserTool")


class BrowserTool(Tool):
    def __init__(
        self,
        validator: URLValidator | None = None,
        search_engine: SearchEngine | None = None,
    ) -> None:
        self._validator = validator or URLValidator()
        self._search_engine = search_engine or create_default_search_engine()

    def execute(self, plan: Plan) -> ExecutionResult:
        if plan.intent == "open_url":
            return self._open_url(plan)

        if plan.intent == "search_web":
            return self._search_web(plan)

        logger.warning("BrowserTool received unknown intent: '%s'.", plan.intent)
        return ExecutionResult(
            success=False,
            message=f"Unknown browser intent: '{plan.intent}'.",
        )

    def _open_url(self, plan: Plan) -> ExecutionResult:
        raw_url = plan.parameters.get("url", "")

        try:
            url = self._validator.validate(raw_url)
        except URLValidationError as exc:
            logger.warning("Browser open rejected: %s", exc.reason)
            return ExecutionResult(success=False, message=f"Browser open rejected: {exc.reason}")

        try:
            opened = webbrowser.open(url)
        except OSError as exc:
            logger.error("Failed to open browser for '%s': %s", url, exc)
            return ExecutionResult(success=False, message=f"Failed to open browser: {exc}")

        if not opened:
            logger.error("No suitable browser could open '%s'.", url)
            return ExecutionResult(success=False, message=f"No suitable browser could open '{url}'.")

        logger.info("Browser opened '%s'.", url)
        return ExecutionResult(success=True, message=f"Opened '{url}' in the default browser.", data={"url": url})

    def _search_web(self, plan: Plan) -> ExecutionResult:
        query = plan.parameters.get("query", "")
        if not query or not str(query).strip():
            logger.warning("Browser search rejected: empty query.")
            return ExecutionResult(success=False, message="No search query provided.")

        encoded_query = quote_plus(str(query).strip())
        search_url = self._search_engine.search_url_template.format(query=encoded_query)

        try:
            opened = webbrowser.open(search_url)
        except OSError as exc:
            logger.error("Failed to open browser for search '%s': %s", query, exc)
            return ExecutionResult(success=False, message=f"Failed to open browser: {exc}")

        if not opened:
            logger.error("No suitable browser could open search URL '%s'.", search_url)
            return ExecutionResult(success=False, message=f"No suitable browser could open '{search_url}'.")

        logger.info("Search via %s: '%s'.", self._search_engine.name, query)
        return ExecutionResult(success=True, message=f"Opened search results for '{query}' in {self._search_engine.name}.", data={"url": search_url, "query": query})
