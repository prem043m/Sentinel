"""Unit tests for the real ApplicationTool.

All tests mock ``subprocess.Popen`` so that no real processes are
launched during testing.  Tests verify:
- Allowlisted applications trigger Popen with correct args
- Unlisted applications are refused without calling Popen
- subprocess exceptions are caught and returned as failure results
- shell=True is never used
- PID is returned in ExecutionResult.data on success
- Structured logging output
"""

import subprocess
from unittest.mock import MagicMock, patch

from app.models.plan import Plan
from app.tools.application.database import ApplicationDatabase
from app.tools.application.models import Application, ApplicationSource, build_application_id
from app.tools.application.registry import ApplicationRegistry
from app.tools.application.tool import ApplicationTool


def _make_plan(name: str) -> Plan:
    """Create a Plan for opening an application by name."""
    return Plan(
        intent="open_application",
        tool="application",
        parameters={"name": name},
    )


def _custom_registry(application: Application | None = None) -> ApplicationRegistry:
    seed = (application,) if application is not None else ()
    return ApplicationRegistry(database=ApplicationDatabase(file_path=None, seed=seed))


class TestAllowedApplicationLaunch:
    """Tests for successfully launching allowed applications."""

    @patch("app.tools.application.tool.subprocess.Popen")
    def test_calculator_launches_successfully(self, mock_popen: MagicMock):
        mock_process = MagicMock()
        mock_process.pid = 1234
        mock_popen.return_value = mock_process

        tool = ApplicationTool()
        result = tool.execute(_make_plan("Calculator"))

        assert result.success
        assert "Calculator" in result.message
        assert result.data == {"pid": 1234}
        mock_popen.assert_called_once_with(["calc.exe"], shell=False)

    @patch("app.tools.application.tool.subprocess.Popen")
    def test_notepad_launches_successfully(self, mock_popen: MagicMock):
        mock_process = MagicMock()
        mock_process.pid = 5678
        mock_popen.return_value = mock_process

        tool = ApplicationTool()
        result = tool.execute(_make_plan("Notepad"))

        assert result.success
        assert "Notepad" in result.message
        assert result.data == {"pid": 5678}
        mock_popen.assert_called_once_with(["notepad.exe"], shell=False)

    @patch("app.tools.application.tool.subprocess.Popen")
    def test_chrome_launches_successfully(self, mock_popen: MagicMock):
        mock_process = MagicMock()
        mock_process.pid = 9999
        mock_popen.return_value = mock_process

        tool = ApplicationTool()
        result = tool.execute(_make_plan("Google Chrome"))

        assert result.success
        mock_popen.assert_called_once_with(["chrome.exe"], shell=False)

    @patch("app.tools.application.tool.subprocess.Popen")
    def test_vscode_launches_successfully(self, mock_popen: MagicMock):
        mock_process = MagicMock()
        mock_process.pid = 4242
        mock_popen.return_value = mock_process

        tool = ApplicationTool()
        result = tool.execute(_make_plan("Visual Studio Code"))

        assert result.success
        mock_popen.assert_called_once_with(["code.cmd"], shell=False)

    @patch("app.tools.application.tool.subprocess.Popen")
    def test_case_insensitive_lookup(self, mock_popen: MagicMock):
        mock_process = MagicMock()
        mock_process.pid = 1111
        mock_popen.return_value = mock_process

        tool = ApplicationTool()
        result = tool.execute(_make_plan("calculator"))

        assert result.success
        mock_popen.assert_called_once_with(["calc.exe"], shell=False)

    @patch("app.tools.application.tool.subprocess.Popen")
    def test_pid_is_returned_in_data(self, mock_popen: MagicMock):
        mock_process = MagicMock()
        mock_process.pid = 7777
        mock_popen.return_value = mock_process

        tool = ApplicationTool()
        result = tool.execute(_make_plan("Notepad"))

        assert result.data is not None
        assert "pid" in result.data
        assert result.data["pid"] == 7777


class TestBlockedApplications:
    """Tests for applications not in the allowlist."""

    @patch("app.tools.application.tool.subprocess.Popen")
    def test_unlisted_app_is_refused(self, mock_popen: MagicMock):
        tool = ApplicationTool()
        result = tool.execute(_make_plan("Malware.exe"))

        assert not result.success
        assert "not in the allowlist" in result.message
        mock_popen.assert_not_called()

    @patch("app.tools.application.tool.subprocess.Popen")
    def test_unknown_app_is_refused(self, mock_popen: MagicMock):
        tool = ApplicationTool()
        result = tool.execute(_make_plan("RandomApp"))

        assert not result.success
        mock_popen.assert_not_called()

    @patch("app.tools.application.tool.subprocess.Popen")
    def test_empty_name_is_refused(self, mock_popen: MagicMock):
        plan = Plan(
            intent="open_application",
            tool="application",
            parameters={"name": ""},
        )

        tool = ApplicationTool()
        result = tool.execute(plan)

        assert not result.success
        assert "No application name" in result.message
        mock_popen.assert_not_called()

    @patch("app.tools.application.tool.subprocess.Popen")
    def test_missing_name_parameter(self, mock_popen: MagicMock):
        plan = Plan(
            intent="open_application",
            tool="application",
            parameters={},
        )

        tool = ApplicationTool()
        result = tool.execute(plan)

        assert not result.success
        mock_popen.assert_not_called()

    @patch("app.tools.application.tool.subprocess.Popen")
    def test_unapproved_application_is_refused(self, mock_popen: MagicMock):
        application = Application(
            id=build_application_id("Steam", r"C:\\Steam\\steam.exe", ApplicationSource.REGISTRY),
            name="Steam",
            path=r"C:\\Steam\\steam.exe",
            aliases=("steam",),
            approved=False,
            source=ApplicationSource.REGISTRY,
        )
        tool = ApplicationTool(registry=_custom_registry(application))
        result = tool.execute(_make_plan("Steam"))

        assert not result.success
        mock_popen.assert_not_called()


class TestSubprocessErrors:
    """Tests for subprocess failure scenarios."""

    @patch("app.tools.application.tool.subprocess.Popen")
    def test_file_not_found_error(self, mock_popen: MagicMock):
        mock_popen.side_effect = FileNotFoundError("calc.exe not found")

        tool = ApplicationTool()
        result = tool.execute(_make_plan("Calculator"))

        assert not result.success
        assert "not found" in result.message
        assert result.data is None

    @patch("app.tools.application.tool.subprocess.Popen")
    def test_fallback_executable_is_tried_after_missing_primary(self, mock_popen: MagicMock):
        mock_process = MagicMock()
        mock_process.pid = 2468
        mock_popen.side_effect = [FileNotFoundError("missing"), mock_process]

        tool = ApplicationTool()
        result = tool.execute(_make_plan("Microsoft Edge"))

        assert result.success
        assert result.data == {"pid": 2468}
        assert mock_popen.call_args_list[0].args[0] == ["msedge.exe"]
        assert mock_popen.call_args_list[1].args[0][0].endswith("msedge.exe")

    @patch("app.tools.application.tool.subprocess.Popen")
    def test_permission_error(self, mock_popen: MagicMock):
        mock_popen.side_effect = PermissionError("Access denied")

        tool = ApplicationTool()
        result = tool.execute(_make_plan("Calculator"))

        assert not result.success
        assert "Permission denied" in result.message

    @patch("app.tools.application.tool.subprocess.Popen")
    def test_os_error(self, mock_popen: MagicMock):
        mock_popen.side_effect = OSError("Generic OS failure")

        tool = ApplicationTool()
        result = tool.execute(_make_plan("Calculator"))

        assert not result.success
        assert "OS error" in result.message


class TestShellSafety:
    """Verify that shell=True is never used."""

    @patch("app.tools.application.tool.subprocess.Popen")
    def test_shell_is_always_false(self, mock_popen: MagicMock):
        mock_process = MagicMock()
        mock_process.pid = 1
        mock_popen.return_value = mock_process

        tool = ApplicationTool()
        tool.execute(_make_plan("Calculator"))

        _, kwargs = mock_popen.call_args
        assert kwargs.get("shell") is False


class TestLogging:
    """Verify structured logging output."""

    @patch("app.tools.application.tool.subprocess.Popen")
    def test_successful_launch_is_logged(self, mock_popen: MagicMock, caplog):
        mock_process = MagicMock()
        mock_process.pid = 100
        mock_popen.return_value = mock_process

        tool = ApplicationTool()

        with caplog.at_level("INFO", logger="SentinelAI.ApplicationTool"):
            tool.execute(_make_plan("Calculator"))

        assert any("Launched" in record.message for record in caplog.records)
        assert any("calc.exe" in record.message for record in caplog.records)

    @patch("app.tools.application.tool.subprocess.Popen")
    def test_blocked_app_is_logged(self, mock_popen: MagicMock, caplog):
        tool = ApplicationTool()

        with caplog.at_level("WARNING", logger="SentinelAI.ApplicationTool"):
            tool.execute(_make_plan("Malware.exe"))

        assert any("Blocked" in record.message for record in caplog.records)
        assert any("Malware.exe" in record.message for record in caplog.records)

    @patch("app.tools.application.tool.subprocess.Popen")
    def test_file_not_found_is_logged(self, mock_popen: MagicMock, caplog):
        mock_popen.side_effect = FileNotFoundError()

        tool = ApplicationTool()

        with caplog.at_level("ERROR", logger="SentinelAI.ApplicationTool"):
            tool.execute(_make_plan("Calculator"))

        assert any("not found" in record.message for record in caplog.records)
