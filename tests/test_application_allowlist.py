from app.tools.application.allowlist import AllowedApplication, lookup


class TestAllowedApplicationDataclass:
    """Tests for the AllowedApplication frozen dataclass."""

    def test_fields_are_accessible(self):
        app = AllowedApplication(name="Calculator", executable="calc.exe")

        assert app.name == "Calculator"
        assert app.executable == "calc.exe"

    def test_is_frozen(self):
        app = AllowedApplication(name="Notepad", executable="notepad.exe")

        try:
            app.name = "Modified"
            assert False, "AllowedApplication should be frozen"
        except AttributeError:
            pass


class TestLookup:
    """Tests for the case-insensitive allowlist lookup function."""

    def test_exact_case_match(self):
        result = lookup("Calculator")

        assert result is not None
        assert result.name == "Calculator"
        assert result.executable == "calc.exe"

    def test_lowercase_match(self):
        result = lookup("calculator")

        assert result is not None
        assert result.name == "Calculator"

    def test_uppercase_match(self):
        result = lookup("CALCULATOR")

        assert result is not None
        assert result.name == "Calculator"

    def test_mixed_case_match(self):
        result = lookup("CaLcUlAtOr")

        assert result is not None
        assert result.name == "Calculator"

    def test_notepad_lookup(self):
        result = lookup("Notepad")

        assert result is not None
        assert result.executable == "notepad.exe"

    def test_chrome_lookup(self):
        result = lookup("Google Chrome")

        assert result is not None
        assert result.executable == "chrome.exe"

    def test_chrome_case_insensitive(self):
        result = lookup("google chrome")

        assert result is not None
        assert result.name == "Google Chrome"

    def test_vscode_lookup(self):
        result = lookup("Visual Studio Code")

        assert result is not None
        assert result.executable == "code.cmd"

    def test_unlisted_application_returns_none(self):
        result = lookup("Malware.exe")

        assert result is None

    def test_empty_string_returns_none(self):
        result = lookup("")

        assert result is None

    def test_whitespace_is_stripped(self):
        result = lookup("  Calculator  ")

        assert result is not None
        assert result.name == "Calculator"

    def test_unknown_application_returns_none(self):
        result = lookup("Unknown App")

        assert result is None
