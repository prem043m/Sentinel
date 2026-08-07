"""Tests for the FilesystemTool — safe UTF-8 file reader.

All tests use pytest's ``tmp_path`` fixture to create isolated
temporary directories as allowed roots.  No real user files are
ever accessed.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.models.plan import Plan
from app.tools.filesystem.config import (
    MAX_READ_SIZE_BYTES,
    AllowedRoot,
    FileOperation,
)
from app.tools.filesystem.tool import FilesystemTool
from app.tools.filesystem.validator import (
    PathValidationError,
    PathValidator,
    ValidatedPath,
)
from app.tools.result import ExecutionResult


# ── Fixtures ──────────────────────────────────────────────────────


@pytest.fixture()
def sandbox(tmp_path: Path) -> Path:
    """Create a sandbox directory with test files."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "hello.txt").write_text(
        "Hello, World!", encoding="utf-8",
    )
    (docs / "empty.txt").write_text("", encoding="utf-8")
    (docs / "unicode.txt").write_text(
        "Héllo 🌍 wörld — «quotes»", encoding="utf-8",
    )
    return tmp_path


@pytest.fixture()
def readable_root(sandbox: Path) -> AllowedRoot:
    return AllowedRoot(
        path=sandbox / "docs",
        readable=True,
        writable=False,
        deletable=False,
    )


@pytest.fixture()
def validator(readable_root: AllowedRoot) -> PathValidator:
    return PathValidator(roots=[readable_root])


@pytest.fixture()
def tool(validator: PathValidator) -> FilesystemTool:
    return FilesystemTool(validator=validator)


def _read_plan(path: str) -> Plan:
    """Helper to build a read_file Plan."""
    return Plan(
        intent="read_file",
        tool="filesystem",
        parameters={"path": path},
    )


# ── Valid text file ───────────────────────────────────────────────


class TestValidTextFile:
    """Tests for successfully reading a valid UTF-8 text file."""

    def test_reads_content(self, sandbox: Path, tool: FilesystemTool):
        plan = _read_plan(str(sandbox / "docs" / "hello.txt"))

        result = tool.execute(plan)

        assert result.success is True
        assert result.data["content"] == "Hello, World!"

    def test_message_is_status_not_content(
        self, sandbox: Path, tool: FilesystemTool,
    ):
        plan = _read_plan(str(sandbox / "docs" / "hello.txt"))

        result = tool.execute(plan)

        assert "Successfully read" in result.message
        assert result.data["content"] not in result.message

    def test_data_contains_path(
        self, sandbox: Path, tool: FilesystemTool,
    ):
        plan = _read_plan(str(sandbox / "docs" / "hello.txt"))

        result = tool.execute(plan)

        assert "path" in result.data
        canonical = (sandbox / "docs" / "hello.txt").resolve()
        assert result.data["path"] == str(canonical)

    def test_data_contains_size_bytes(
        self, sandbox: Path, tool: FilesystemTool,
    ):
        plan = _read_plan(str(sandbox / "docs" / "hello.txt"))

        result = tool.execute(plan)

        assert "size_bytes" in result.data
        expected_size = (sandbox / "docs" / "hello.txt").stat().st_size
        assert result.data["size_bytes"] == expected_size

    def test_data_contains_mime_type(
        self, sandbox: Path, tool: FilesystemTool,
    ):
        plan = _read_plan(str(sandbox / "docs" / "hello.txt"))

        result = tool.execute(plan)

        assert result.data["mime_type"] == "text/plain; charset=utf-8"


class TestDirectoryFallback:
    """Tests for directory paths passed to the file reader."""

    def test_directory_path_lists_contents_instead_of_failing(
        self, sandbox: Path, tool: FilesystemTool,
    ):
        plan = _read_plan(str(sandbox / "docs"))

        result = tool.execute(plan)

        assert result.success is True
        assert "directory_contents" in result.data
        assert len(result.data["directory_contents"]) == 3


# ── Empty file ────────────────────────────────────────────────────


class TestEmptyFile:
    """Tests for reading a zero-byte file."""

    def test_empty_file_succeeds(
        self, sandbox: Path, tool: FilesystemTool,
    ):
        plan = _read_plan(str(sandbox / "docs" / "empty.txt"))

        result = tool.execute(plan)

        assert result.success is True
        assert result.data["content"] == ""

    def test_empty_file_size_is_zero(
        self, sandbox: Path, tool: FilesystemTool,
    ):
        plan = _read_plan(str(sandbox / "docs" / "empty.txt"))

        result = tool.execute(plan)

        assert result.data["size_bytes"] == 0


# ── UTF-8 with special characters ────────────────────────────────


class TestUTF8SpecialCharacters:
    """Tests for files containing emoji, accented chars, etc."""

    def test_unicode_content_is_preserved(
        self, sandbox: Path, tool: FilesystemTool,
    ):
        plan = _read_plan(str(sandbox / "docs" / "unicode.txt"))

        result = tool.execute(plan)

        assert result.success is True
        assert result.data["content"] == "Héllo 🌍 wörld — «quotes»"


# ── Large file rejection ──────────────────────────────────────────


class TestLargeFileRejection:
    """Tests for files exceeding the size limit."""

    def test_oversized_file_is_rejected(
        self, sandbox: Path, tool: FilesystemTool,
    ):
        big_file = sandbox / "docs" / "huge.txt"
        # Create a file that exceeds MAX_READ_SIZE_BYTES.
        # Writing a small file and patching stat is more practical
        # than creating a 10+ MB file.
        big_file.write_text("x", encoding="utf-8")

        plan = _read_plan(str(big_file))

        with patch.object(
            Path, "stat",
        ) as mock_stat:
            mock_stat.return_value = MagicMock(
                st_size=MAX_READ_SIZE_BYTES + 1,
            )
            result = tool.execute(plan)

        assert result.success is False
        assert "exceeds" in result.message
        assert "10 MB" in result.message

    def test_file_at_exact_limit_is_accepted(
        self, sandbox: Path, tool: FilesystemTool,
    ):
        limit_file = sandbox / "docs" / "at_limit.txt"
        limit_file.write_text("x", encoding="utf-8")

        plan = _read_plan(str(limit_file))

        with patch.object(
            Path, "stat",
        ) as mock_stat:
            mock_stat.return_value = MagicMock(
                st_size=MAX_READ_SIZE_BYTES,
            )
            result = tool.execute(plan)

        assert result.success is True


# ── Binary file rejection ─────────────────────────────────────────


class TestBinaryFileRejection:
    """Tests for files that are not valid UTF-8."""

    def test_binary_file_is_rejected(
        self, sandbox: Path, tool: FilesystemTool,
    ):
        binary_file = sandbox / "docs" / "image.bin"
        binary_file.write_bytes(b"\x00\x80\xff\xfe\x89PNG")

        plan = _read_plan(str(binary_file))

        result = tool.execute(plan)

        assert result.success is False
        assert "binary" in result.message.lower()

    def test_binary_rejection_mentions_utf8(
        self, sandbox: Path, tool: FilesystemTool,
    ):
        binary_file = sandbox / "docs" / "data.bin"
        binary_file.write_bytes(bytes(range(128, 256)))

        plan = _read_plan(str(binary_file))

        result = tool.execute(plan)

        assert "UTF-8" in result.message


# ── Missing file ──────────────────────────────────────────────────


class TestMissingFile:
    """Tests for files that do not exist."""

    def test_missing_file_returns_failure(
        self, sandbox: Path, tool: FilesystemTool,
    ):
        plan = _read_plan(
            str(sandbox / "docs" / "does_not_exist.txt"),
        )

        result = tool.execute(plan)

        assert result.success is False
        assert "not found" in result.message.lower()


# ── Permission denied ─────────────────────────────────────────────


class TestPermissionDenied:
    """Tests for files the OS refuses to let us read."""

    def test_permission_denied_on_stat(
        self, sandbox: Path, tool: FilesystemTool,
    ):
        locked = sandbox / "docs" / "locked.txt"
        locked.write_text("secret", encoding="utf-8")
        plan = _read_plan(str(locked))

        with patch.object(
            Path, "stat", side_effect=PermissionError("Access denied"),
        ):
            result = tool.execute(plan)

        assert result.success is False
        assert "permission" in result.message.lower()

    def test_permission_denied_on_read(
        self, sandbox: Path, tool: FilesystemTool,
    ):
        locked = sandbox / "docs" / "locked2.txt"
        locked.write_text("secret", encoding="utf-8")
        plan = _read_plan(str(locked))

        with patch.object(
            Path, "read_text",
            side_effect=PermissionError("Access denied"),
        ):
            result = tool.execute(plan)

        assert result.success is False
        assert "permission" in result.message.lower()


# ── Invalid path (empty) ─────────────────────────────────────────


class TestInvalidPath:
    """Tests for empty or missing path parameters."""

    def test_empty_path_returns_failure(self, tool: FilesystemTool):
        plan = _read_plan("")

        result = tool.execute(plan)

        assert result.success is False
        assert "No file path provided" in result.message

    def test_missing_path_key_returns_failure(
        self, tool: FilesystemTool,
    ):
        plan = Plan(
            intent="read_file",
            tool="filesystem",
            parameters={},
        )

        result = tool.execute(plan)

        assert result.success is False


# ── Outside allowed root ──────────────────────────────────────────


class TestOutsideAllowedRoot:
    """Tests for paths that are not under any allowed root."""

    def test_path_outside_root_is_rejected(
        self, sandbox: Path, tool: FilesystemTool,
    ):
        outside = sandbox / "outside" / "file.txt"
        plan = _read_plan(str(outside))

        result = tool.execute(plan)

        assert result.success is False
        assert "not under any allowed" in result.message

    def test_traversal_outside_root_is_rejected(
        self, sandbox: Path, tool: FilesystemTool,
    ):
        traversal = str(
            sandbox / "docs" / ".." / ".." / "etc" / "passwd"
        )
        plan = _read_plan(traversal)

        result = tool.execute(plan)

        assert result.success is False


# ── Logging ───────────────────────────────────────────────────────


class TestLogging:
    """Tests for structured logging output."""

    def test_successful_read_is_logged(
        self, sandbox: Path, tool: FilesystemTool, caplog,
    ):
        plan = _read_plan(str(sandbox / "docs" / "hello.txt"))

        with caplog.at_level(
            "INFO", logger="SentinelAI.FilesystemTool",
        ):
            tool.execute(plan)

        assert any(
            "Read successful" in r.message for r in caplog.records
        )

    def test_validation_failure_is_logged(
        self, tool: FilesystemTool, caplog,
    ):
        plan = _read_plan("")

        with caplog.at_level(
            "WARNING", logger="SentinelAI.FilesystemTool",
        ):
            tool.execute(plan)

        assert any(
            "Rejected (validation)" in r.message
            for r in caplog.records
        )

    def test_missing_file_is_logged(
        self, sandbox: Path, tool: FilesystemTool, caplog,
    ):
        plan = _read_plan(
            str(sandbox / "docs" / "nonexistent.txt"),
        )

        with caplog.at_level(
            "WARNING", logger="SentinelAI.FilesystemTool",
        ):
            tool.execute(plan)

        assert any(
            "not found" in r.message for r in caplog.records
        )

    def test_binary_rejection_is_logged(
        self, sandbox: Path, tool: FilesystemTool, caplog,
    ):
        binary = sandbox / "docs" / "bin.dat"
        binary.write_bytes(b"\x00\x80\xff")
        plan = _read_plan(str(binary))

        with caplog.at_level(
            "WARNING", logger="SentinelAI.FilesystemTool",
        ):
            tool.execute(plan)

        assert any(
            "binary" in r.message.lower() for r in caplog.records
        )


# ── ExecutionResult correctness ───────────────────────────────────


class TestExecutionResultCorrectness:
    """Tests that ExecutionResult fields are properly populated."""

    def test_success_result_is_frozen(
        self, sandbox: Path, tool: FilesystemTool,
    ):
        plan = _read_plan(str(sandbox / "docs" / "hello.txt"))

        result = tool.execute(plan)

        with pytest.raises(AttributeError):
            result.success = False  # type: ignore[misc]

    def test_failure_result_has_no_data(
        self, tool: FilesystemTool,
    ):
        plan = _read_plan("")

        result = tool.execute(plan)

        assert result.success is False
        assert result.data is None

    def test_success_result_data_has_all_keys(
        self, sandbox: Path, tool: FilesystemTool,
    ):
        plan = _read_plan(str(sandbox / "docs" / "hello.txt"))

        result = tool.execute(plan)

        assert set(result.data.keys()) == {
            "content", "path", "size_bytes", "mime_type",
        }


# ── PathValidator is used (not bypassed) ──────────────────────────


class TestPathValidatorIntegration:
    """Tests that FilesystemTool delegates to PathValidator."""

    def test_validator_validate_is_called(self, sandbox: Path):
        mock_validator = MagicMock(spec=PathValidator)
        mock_validator.validate.side_effect = PathValidationError(
            "mock rejection",
        )
        tool = FilesystemTool(validator=mock_validator)

        plan = _read_plan(str(sandbox / "docs" / "hello.txt"))
        tool.execute(plan)

        mock_validator.validate.assert_called_once_with(
            str(sandbox / "docs" / "hello.txt"),
            FileOperation.READ,
        )

    def test_validator_rejection_propagates(self, sandbox: Path):
        mock_validator = MagicMock(spec=PathValidator)
        mock_validator.validate.side_effect = PathValidationError(
            "custom rejection reason",
        )
        tool = FilesystemTool(validator=mock_validator)

        plan = _read_plan(str(sandbox / "docs" / "hello.txt"))
        result = tool.execute(plan)

        assert result.success is False
        assert result.message == "custom rejection reason"
