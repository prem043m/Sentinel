"""Browser tool security and search configuration.

Defines the security boundaries and search engine configuration
for all browser operations:

- **ALLOWED_SCHEMES**: URL schemes that BrowserTool will accept.
- **MAX_URL_LENGTH**: Maximum character length for URLs.
- **SearchEngine**: configurable search engine for web searches.
- **DEFAULT_SEARCH_ENGINE**: factory for the default search engine.

This module contains data definitions and a factory function only.
No execution logic, no OS operations, no policy decisions.
"""

from dataclasses import dataclass


# ── URL Security ──────────────────────────────────────────────────

ALLOWED_SCHEMES: tuple[str, ...] = ("http", "https")
"""URL schemes that BrowserTool is permitted to open."""

MAX_URL_LENGTH: int = 2048
"""Maximum URL length in characters.  URLs exceeding this are rejected."""


# ── Search Engine Configuration ───────────────────────────────────

@dataclass(frozen=True, slots=True)
class SearchEngine:
    """A search engine that BrowserTool can use for web searches.

    Attributes:
        name: Human-readable name (e.g. 'Google', 'DuckDuckGo').
        search_url_template: URL template with ``{query}`` placeholder.
                             The placeholder is replaced with the
                             URL-encoded search query at runtime.
    """

    name: str
    search_url_template: str


def create_default_search_engine() -> SearchEngine:
    """Create the default search engine configuration.

    Returns:
        A ``SearchEngine`` instance configured for Google Search.
    """
    return SearchEngine(
        name="Google",
        search_url_template="https://www.google.com/search?q={query}",
    )
