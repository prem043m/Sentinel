"""URL validation for the Browser tool.

This module is the **only** place in SentinelAI that decides whether
a URL is safe to open.  It enforces scheme restrictions, length limits,
and structural checks without performing any I/O.

Designed to be modular and grow independently of BrowserTool as
new validation rules are needed (e.g. domain blocklists, IP filtering).
"""

import logging
from urllib.parse import urlparse

from app.tools.browser.config import ALLOWED_SCHEMES, MAX_URL_LENGTH

logger = logging.getLogger("SentinelAI.URLValidator")


class URLValidationError(Exception):
    """Raised when a URL fails validation.

    Attributes:
        reason: A human-readable explanation of why validation failed.
    """

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


class URLValidator:
    """Validates URLs against SentinelAI's security policy.

    This validator is stateless and can be shared across tool
    instances.  It is injected into ``BrowserTool`` via the
    constructor to support testing and Dependency Injection.

    Args:
        allowed_schemes: Tuple of permitted URL schemes.
                         Defaults to ``ALLOWED_SCHEMES`` from config.
        max_length: Maximum URL length in characters.
                    Defaults to ``MAX_URL_LENGTH`` from config.
    """

    def __init__(
        self,
        allowed_schemes: tuple[str, ...] | None = None,
        max_length: int | None = None,
    ) -> None:
        self._allowed_schemes = allowed_schemes or ALLOWED_SCHEMES
        self._max_length = max_length or MAX_URL_LENGTH

    def validate(self, url: str) -> str:
        """Validate and normalise a URL.

        If the URL has no scheme, ``https://`` is prepended
        automatically.

        Args:
            url: The raw URL string to validate.

        Returns:
            The validated (and possibly normalised) URL string.

        Raises:
            URLValidationError: If the URL fails any security check.
        """
        if not url or not url.strip():
            logger.warning("URL validation failed: empty URL provided.")
            raise URLValidationError("No URL provided.")

        url = url.strip()

        # ── Strip surrounding quotes ──────────────────────────────
        if (url.startswith('"') and url.endswith('"')) or \
           (url.startswith("'") and url.endswith("'")):
            url = url[1:-1]

        # ── Auto-prepend scheme ───────────────────────────────────
        parsed = urlparse(url)
        if not parsed.scheme:
            url = f"https://{url}"
            parsed = urlparse(url)

        # ── Length check ──────────────────────────────────────────
        if len(url) > self._max_length:
            logger.warning(
                "URL validation failed: URL exceeds %d characters.",
                self._max_length,
            )
            raise URLValidationError(
                f"URL exceeds the maximum length of "
                f"{self._max_length:,} characters."
            )

        # ── Scheme check ─────────────────────────────────────────
        if parsed.scheme.lower() not in self._allowed_schemes:
            logger.warning(
                "URL validation failed: scheme '%s' is not allowed.",
                parsed.scheme,
            )
            raise URLValidationError(
                f"URL scheme '{parsed.scheme}' is not allowed. "
                f"Only {', '.join(self._allowed_schemes)} are permitted."
            )

        # ── Hostname check ───────────────────────────────────────
        if not parsed.hostname:
            logger.warning(
                "URL validation failed: no hostname in '%s'.",
                url,
            )
            raise URLValidationError(
                "URL has no hostname."
            )

        # ── Credentials check ────────────────────────────────────
        if parsed.username or parsed.password:
            logger.warning(
                "URL validation failed: embedded credentials in '%s'.",
                url,
            )
            raise URLValidationError(
                "URLs with embedded credentials are not allowed."
            )

        return url
