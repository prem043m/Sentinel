"""Tests for the BrowserTool, URLValidator, and browser configuration."""

from unittest.mock import MagicMock, patch

import pytest

from app.models.plan import Plan
from app.tools.browser.config import (
    ALLOWED_SCHEMES,
    MAX_URL_LENGTH,
    SearchEngine,
    create_default_search_engine,
)
from app.tools.browser.tool import BrowserTool
from app.tools.browser.validator import URLValidationError, URLValidator


# ═════════════════════════════════════════════════════════════════
# URL Validator Tests
# ═════════════════════════════════════════════════════════════════


class TestURLValidatorValidURLs:
    """Tests for URLs that should pass validation."""

    def test_https_url_is_valid(self):
        validator = URLValidator()
        result = validator.validate("https://www.google.com")
        assert result == "https://www.google.com"

    def test_http_url_is_valid(self):
        validator = URLValidator()
        result = validator.validate("http://example.com")
        assert result == "http://example.com"

    def test_url_with_path_is_valid(self):
        validator = URLValidator()
        result = validator.validate("https://github.com/user/repo")
        assert result == "https://github.com/user/repo"

    def test_url_with_query_params_is_valid(self):
        validator = URLValidator()
        result = validator.validate("https://google.com/search?q=test")
        assert result == "https://google.com/search?q=test"

    def test_bare_domain_gets_https_prepended(self):
        validator = URLValidator()
        result = validator.validate("google.com")
        assert result == "https://google.com"

    def test_bare_domain_with_path_gets_https(self):
        validator = URLValidator()
        result = validator.validate("github.com/user/repo")
        assert result == "https://github.com/user/repo"

    def test_strips_whitespace(self):
        validator = URLValidator()
        result = validator.validate("  https://example.com  ")
        assert result == "https://example.com"

    def test_strips_surrounding_quotes(self):
        validator = URLValidator()
        result = validator.validate('"https://example.com"')
        assert result == "https://example.com"

    def test_strips_surrounding_single_quotes(self):
        validator = URLValidator()
        result = validator.validate("'https://example.com'")
        assert result == "https://example.com"


class TestURLValidatorRejections:
    """Tests for URLs that should be rejected."""

    def test_empty_string_rejected(self):
        validator = URLValidator()
        with pytest.raises(URLValidationError, match="No URL provided"):
            validator.validate("")

    def test_whitespace_only_rejected(self):
        validator = URLValidator()
        with pytest.raises(URLValidationError, match="No URL provided"):
            validator.validate("   ")

    def test_file_scheme_rejected(self):
        validator = URLValidator()
        with pytest.raises(URLValidationError, match="not allowed"):
            validator.validate("file:///etc/passwd")

    def test_ftp_scheme_rejected(self):
        validator = URLValidator()
        with pytest.raises(URLValidationError, match="not allowed"):
            validator.validate("ftp://files.example.com/data")

    def test_javascript_scheme_rejected(self):
        validator = URLValidator()
        with pytest.raises(URLValidationError, match="not allowed"):
            validator.validate("javascript:alert(1)")

    def test_no_hostname_rejected(self):
        validator = URLValidator()
        with pytest.raises(URLValidationError, match="no hostname"):
            validator.validate("https://")

    def test_embedded_credentials_rejected(self):
        validator = URLValidator()
        with pytest.raises(URLValidationError, match="credentials"):
            validator.validate("https://user:pass@evil.com")

    def test_url_exceeding_max_length_rejected(self):
        validator = URLValidator()
        long_url = "https://example.com/" + "a" * MAX_URL_LENGTH
        with pytest.raises(URLValidationError, match="maximum length"):
            validator.validate(long_url)

    def test_url_at_exact_max_length_is_accepted(self):
        validator = URLValidator()
        # Build a URL that is exactly MAX_URL_LENGTH characters
        prefix = "https://example.com/"
        padding = "a" * (MAX_URL_LENGTH - len(prefix))
        exact_url = prefix + padding
        assert len(exact_url) == MAX_URL_LENGTH
        result = validator.validate(exact_url)
        assert result == exact_url


class TestURLValidatorDI:
    """Tests for URLValidator dependency injection."""

    def test_custom_allowed_schemes(self):
        validator = URLValidator(allowed_schemes=("ftp",))
        result = validator.validate("ftp://files.example.com")
        assert result == "ftp://files.example.com"

    def test_custom_max_length(self):
        validator = URLValidator(max_length=30)
        with pytest.raises(URLValidationError, match="maximum length"):
            validator.validate("https://example.com/very/long/path")


class TestURLValidatorLogging:
    """Tests that validation failures are logged."""

    def test_empty_url_is_logged(self, caplog):
        validator = URLValidator()
        with caplog.at_level("WARNING", logger="SentinelAI.URLValidator"):
            with pytest.raises(URLValidationError):
                validator.validate("")
        assert any("empty URL" in r.message for r in caplog.records)

    def test_bad_scheme_is_logged(self, caplog):
        validator = URLValidator()
        with caplog.at_level("WARNING", logger="SentinelAI.URLValidator"):
            with pytest.raises(URLValidationError):
                validator.validate("ftp://example.com")
        assert any("not allowed" in r.message for r in caplog.records)

    def test_credentials_logged(self, caplog):
        validator = URLValidator()
        with caplog.at_level("WARNING", logger="SentinelAI.URLValidator"):
            with pytest.raises(URLValidationError):
                validator.validate("https://user:pass@evil.com")
        assert any("credentials" in r.message for r in caplog.records)


# ═════════════════════════════════════════════════════════════════
# Browser Config Tests
# ═════════════════════════════════════════════════════════════════


class TestBrowserConfig:
    """Tests for browser configuration."""

    def test_allowed_schemes_contains_http(self):
        assert "http" in ALLOWED_SCHEMES

    def test_allowed_schemes_contains_https(self):
        assert "https" in ALLOWED_SCHEMES

    def test_allowed_schemes_excludes_ftp(self):
        assert "ftp" not in ALLOWED_SCHEMES

    def test_max_url_length_is_positive(self):
        assert MAX_URL_LENGTH > 0

    def test_max_url_length_is_2048(self):
        assert MAX_URL_LENGTH == 2048


class TestSearchEngine:
    """Tests for the SearchEngine dataclass."""

    def test_default_search_engine_is_google(self):
        engine = create_default_search_engine()
        assert engine.name == "Google"

    def test_default_engine_has_query_placeholder(self):
        engine = create_default_search_engine()
        assert "{query}" in engine.search_url_template

    def test_search_engine_is_frozen(self):
        engine = create_default_search_engine()
        with pytest.raises(AttributeError):
            engine.name = "Bing"

    def test_custom_search_engine(self):
        engine = SearchEngine(
            name="DuckDuckGo",
            search_url_template="https://duckduckgo.com/?q={query}",
        )
        assert engine.name == "DuckDuckGo"
        url = engine.search_url_template.format(query="test")
        assert url == "https://duckduckgo.com/?q=test"


# ═════════════════════════════════════════════════════════════════
# BrowserTool Tests
# ═════════════════════════════════════════════════════════════════


def _open_plan(url: str) -> Plan:
    return Plan(intent="open_url", tool="browser", parameters={"url": url})


def _search_plan(query: str) -> Plan:
    return Plan(intent="search_web", tool="browser", parameters={"query": query})


class TestBrowserToolOpenURL:
    """Tests for the open_url handler."""

    @patch("app.tools.browser.tool.webbrowser.open", return_value=True)
    def test_valid_url_opens_successfully(self, mock_open):
        tool = BrowserTool()
        result = tool.execute(_open_plan("https://github.com"))

        assert result.success is True
        assert "github.com" in result.message
        mock_open.assert_called_once_with("https://github.com")

    @patch("app.tools.browser.tool.webbrowser.open", return_value=True)
    def test_bare_domain_auto_prepends_https(self, mock_open):
        tool = BrowserTool()
        result = tool.execute(_open_plan("google.com"))

        assert result.success is True
        mock_open.assert_called_once_with("https://google.com")

    @patch("app.tools.browser.tool.webbrowser.open", return_value=True)
    def test_success_data_contains_url(self, mock_open):
        tool = BrowserTool()
        result = tool.execute(_open_plan("https://example.com"))

        assert result.data is not None
        assert result.data["url"] == "https://example.com"

    def test_invalid_scheme_returns_failure(self):
        tool = BrowserTool()
        result = tool.execute(_open_plan("ftp://files.example.com"))

        assert result.success is False
        assert "not allowed" in result.message

    def test_empty_url_returns_failure(self):
        tool = BrowserTool()
        result = tool.execute(_open_plan(""))

        assert result.success is False
        assert result.data is None

    @patch("app.tools.browser.tool.webbrowser.open", return_value=False)
    def test_browser_not_found_returns_failure(self, mock_open):
        tool = BrowserTool()
        result = tool.execute(_open_plan("https://example.com"))

        assert result.success is False
        assert "No suitable browser" in result.message

    @patch(
        "app.tools.browser.tool.webbrowser.open",
        side_effect=OSError("No browser"),
    )
    def test_os_error_returns_failure(self, mock_open):
        tool = BrowserTool()
        result = tool.execute(_open_plan("https://example.com"))

        assert result.success is False
        assert "Failed to open browser" in result.message

    def test_javascript_scheme_rejected(self):
        tool = BrowserTool()
        result = tool.execute(_open_plan("javascript:alert(1)"))
        assert result.success is False

    def test_credentials_in_url_rejected(self):
        tool = BrowserTool()
        result = tool.execute(_open_plan("https://user:pass@evil.com"))
        assert result.success is False


class TestBrowserToolSearchWeb:
    """Tests for the search_web handler."""

    @patch("app.tools.browser.tool.webbrowser.open", return_value=True)
    def test_search_opens_google(self, mock_open):
        tool = BrowserTool()
        result = tool.execute(_search_plan("Python tutorials"))

        assert result.success is True
        call_url = mock_open.call_args[0][0]
        assert "google.com/search" in call_url
        assert "Python+tutorials" in call_url

    @patch("app.tools.browser.tool.webbrowser.open", return_value=True)
    def test_search_encodes_special_characters(self, mock_open):
        tool = BrowserTool()
        result = tool.execute(_search_plan("C++ hello world"))

        assert result.success is True
        call_url = mock_open.call_args[0][0]
        assert "C%2B%2B" in call_url

    def test_empty_query_returns_failure(self):
        tool = BrowserTool()
        result = tool.execute(_search_plan(""))

        assert result.success is False
        assert "No search query" in result.message

    @patch("app.tools.browser.tool.webbrowser.open", return_value=True)
    def test_search_data_contains_url(self, mock_open):
        tool = BrowserTool()
        result = tool.execute(_search_plan("test"))

        assert result.data is not None
        assert "url" in result.data

    @patch("app.tools.browser.tool.webbrowser.open", return_value=True)
    def test_custom_search_engine(self, mock_open):
        engine = SearchEngine(
            name="DuckDuckGo",
            search_url_template="https://duckduckgo.com/?q={query}",
        )
        tool = BrowserTool(search_engine=engine)
        result = tool.execute(_search_plan("privacy"))

        assert result.success is True
        call_url = mock_open.call_args[0][0]
        assert "duckduckgo.com" in call_url


class TestBrowserToolUnknownIntent:
    """Tests for unrecognised intents."""

    def test_unknown_intent_returns_failure(self):
        tool = BrowserTool()
        plan = Plan(
            intent="browser_automation",
            tool="browser",
            parameters={},
        )
        result = tool.execute(plan)

        assert result.success is False
        assert "Unknown browser intent" in result.message


class TestBrowserToolDI:
    """Tests for BrowserTool dependency injection."""

    def test_custom_validator_is_used(self):
        mock_validator = MagicMock()
        mock_validator.validate.side_effect = URLValidationError("blocked")

        tool = BrowserTool(validator=mock_validator)
        result = tool.execute(_open_plan("https://example.com"))

        assert result.success is False
        mock_validator.validate.assert_called_once()

    @patch("app.tools.browser.tool.webbrowser.open", return_value=True)
    def test_custom_search_engine_is_used(self, mock_open):
        engine = SearchEngine(
            name="Bing",
            search_url_template="https://www.bing.com/search?q={query}",
        )
        tool = BrowserTool(search_engine=engine)
        result = tool.execute(_search_plan("test"))

        assert result.success is True
        call_url = mock_open.call_args[0][0]
        assert "bing.com" in call_url


class TestBrowserToolLogging:
    """Tests that browser operations are logged."""

    @patch("app.tools.browser.tool.webbrowser.open", return_value=True)
    def test_successful_open_is_logged(self, mock_open, caplog):
        tool = BrowserTool()
        with caplog.at_level("INFO", logger="SentinelAI.BrowserTool"):
            tool.execute(_open_plan("https://example.com"))

        assert any(
            "Browser opened" in r.message for r in caplog.records
        )

    def test_rejected_url_is_logged(self, caplog):
        tool = BrowserTool()
        with caplog.at_level("WARNING", logger="SentinelAI.BrowserTool"):
            tool.execute(_open_plan("ftp://bad.com"))

        assert any(
            "Browser open rejected" in r.message for r in caplog.records
        )

    @patch("app.tools.browser.tool.webbrowser.open", return_value=True)
    def test_search_is_logged(self, mock_open, caplog):
        tool = BrowserTool()
        with caplog.at_level("INFO", logger="SentinelAI.BrowserTool"):
            tool.execute(_search_plan("Python"))

        assert any(
            "Search via Google" in r.message for r in caplog.records
        )

    def test_unknown_intent_is_logged(self, caplog):
        tool = BrowserTool()
        plan = Plan(intent="browser_hack", tool="browser", parameters={})
        with caplog.at_level("WARNING", logger="SentinelAI.BrowserTool"):
            tool.execute(plan)

        assert any(
            "unknown intent" in r.message for r in caplog.records
        )
