"""Tests for the filesystem path validator.

All tests use pytest's ``tmp_path`` fixture to create isolated
temporary directories as allowed roots.  No real user files are
ever accessed.
"""

from pathlib import Path

import pytest

from app.tools.filesystem.config import AllowedRoot, FileOperation
from app.tools.filesystem.validator import (
    PathValidationError,
    PathValidator,
    ValidatedPath,
)


# ── Fixtures ──────────────────────────────────────────────────────


@pytest.fixture()
def sandbox(tmp_path: Path) -> Path:
    """Create a sandbox directory with test files."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "readme.txt").write_text("hello", encoding="utf-8")
    (docs / "sub").mkdir()
    (docs / "sub" / "nested.txt").write_text("nested", encoding="utf-8")
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
def writable_root(sandbox: Path) -> AllowedRoot:
    return AllowedRoot(
        path=sandbox / "docs",
        readable=True,
        writable=True,
        deletable=False,
    )


@pytest.fixture()
def deletable_root(sandbox: Path) -> AllowedRoot:
    return AllowedRoot(
        path=sandbox / "docs",
        readable=True,
        writable=True,
        deletable=True,
    )


@pytest.fixture()
def validator(readable_root: AllowedRoot) -> PathValidator:
    """A validator with a single readable root."""
    return PathValidator(roots=[readable_root])


# ── ValidatedPath dataclass ───────────────────────────────────────


class TestValidatedPath:
    """Tests for the ValidatedPath output type."""

    def test_fields_are_accessible(self, sandbox: Path, readable_root: AllowedRoot):
        vp = ValidatedPath(
            canonical=sandbox / "docs" / "readme.txt",
            root=readable_root,
            original="readme.txt",
        )

        assert vp.canonical == sandbox / "docs" / "readme.txt"
        assert vp.root is readable_root
        assert vp.original == "readme.txt"

    def test_is_frozen(self, sandbox: Path, readable_root: AllowedRoot):
        vp = ValidatedPath(
            canonical=sandbox / "docs" / "readme.txt",
            root=readable_root,
            original="readme.txt",
        )

        with pytest.raises(AttributeError):
            vp.original = "modified"


# ── Valid paths ───────────────────────────────────────────────────


class TestValidPaths:
    """Tests for paths that should pass validation."""

    def test_absolute_path_under_root(self, sandbox: Path, validator: PathValidator):
        absolute = str(sandbox / "docs" / "readme.txt")

        result = validator.validate(absolute, FileOperation.READ)

        assert isinstance(result, ValidatedPath)
        assert result.canonical == (sandbox / "docs" / "readme.txt").resolve()
        assert result.original == absolute

    def test_nested_path_under_root(self, sandbox: Path, validator: PathValidator):
        nested = str(sandbox / "docs" / "sub" / "nested.txt")

        result = validator.validate(nested, FileOperation.READ)

        assert result.canonical == (sandbox / "docs" / "sub" / "nested.txt").resolve()

    def test_root_directory_itself(self, sandbox: Path, validator: PathValidator):
        root_path = str(sandbox / "docs")

        result = validator.validate(root_path, FileOperation.READ)

        assert result.canonical == (sandbox / "docs").resolve()

    def test_returns_matching_root(
        self, sandbox: Path, readable_root: AllowedRoot, validator: PathValidator
    ):
        path = str(sandbox / "docs" / "readme.txt")

        result = validator.validate(path, FileOperation.READ)

        assert result.root is readable_root

    def test_preserves_original_path(self, sandbox: Path, validator: PathValidator):
        original = str(sandbox / "docs" / "readme.txt")

        result = validator.validate(original, FileOperation.READ)

        assert result.original == original

    def test_dot_in_path_resolves(self, sandbox: Path, validator: PathValidator):
        path_with_dot = str(sandbox / "docs" / "." / "readme.txt")

        result = validator.validate(path_with_dot, FileOperation.READ)

        assert result.canonical == (sandbox / "docs" / "readme.txt").resolve()

    def test_nonexistent_file_under_root_is_accepted(
        self, sandbox: Path, validator: PathValidator
    ):
        """The validator doesn't check file existence — that's the tool's job."""
        nonexistent = str(sandbox / "docs" / "does_not_exist.txt")

        result = validator.validate(nonexistent, FileOperation.READ)

        assert result.canonical == (sandbox / "docs" / "does_not_exist.txt").resolve()


# ── Empty and whitespace paths ────────────────────────────────────


class TestEmptyPaths:
    """Tests for empty or whitespace-only paths."""

    def test_empty_string_is_rejected(self, validator: PathValidator):
        with pytest.raises(PathValidationError, match="No file path provided"):
            validator.validate("", FileOperation.READ)

    def test_whitespace_only_is_rejected(self, validator: PathValidator):
        with pytest.raises(PathValidationError, match="No file path provided"):
            validator.validate("   ", FileOperation.READ)

    def test_none_coerced_to_empty(self, validator: PathValidator):
        """Passing an empty-ish value is caught."""
        with pytest.raises(PathValidationError, match="No file path provided"):
            validator.validate("", FileOperation.READ)


# ── Paths outside allowed roots ───────────────────────────────────


class TestPathsOutsideRoots:
    """Tests for paths that are not under any allowed root."""

    def test_sibling_directory_is_rejected(self, sandbox: Path, validator: PathValidator):
        outside = sandbox / "other" / "file.txt"

        with pytest.raises(PathValidationError, match="not under any allowed"):
            validator.validate(str(outside), FileOperation.READ)

    def test_parent_directory_is_rejected(self, sandbox: Path, validator: PathValidator):
        parent = sandbox.parent / "file.txt"

        with pytest.raises(PathValidationError, match="not under any allowed"):
            validator.validate(str(parent), FileOperation.READ)

    def test_root_of_filesystem_is_rejected(self, validator: PathValidator):
        with pytest.raises(PathValidationError, match="not under any allowed"):
            validator.validate("C:\\file.txt", FileOperation.READ)


# ── Directory traversal ───────────────────────────────────────────


class TestDirectoryTraversal:
    """Tests for path traversal attacks using '..' components."""

    def test_dotdot_escaping_root_is_rejected(
        self, sandbox: Path, validator: PathValidator
    ):
        traversal = str(sandbox / "docs" / ".." / ".." / "etc" / "passwd")

        with pytest.raises(PathValidationError, match="not under any allowed"):
            validator.validate(traversal, FileOperation.READ)

    def test_dotdot_staying_within_root_is_accepted(
        self, sandbox: Path, validator: PathValidator
    ):
        """../sub from docs/sub/.. resolves back into docs/."""
        path = str(sandbox / "docs" / "sub" / ".." / "readme.txt")

        result = validator.validate(path, FileOperation.READ)

        assert result.canonical == (sandbox / "docs" / "readme.txt").resolve()

    def test_deep_traversal_is_rejected(self, sandbox: Path, validator: PathValidator):
        deep = str(
            sandbox / "docs" / ".." / ".." / ".." / ".." / "Windows" / "System32"
        )

        with pytest.raises(PathValidationError):
            validator.validate(deep, FileOperation.READ)


# ── Blocked patterns ─────────────────────────────────────────────


class TestBlockedPatterns:
    """Tests for paths containing blocked directory names within the root."""

    def test_appdata_in_relative_path_is_blocked(self, sandbox: Path):
        root = AllowedRoot(path=sandbox / "docs", readable=True)
        (sandbox / "docs" / "AppData").mkdir(exist_ok=True)
        validator = PathValidator(roots=[root])

        with pytest.raises(PathValidationError, match="restricted system directory"):
            validator.validate(
                str(sandbox / "docs" / "AppData" / "file.txt"),
                FileOperation.READ,
            )

    def test_windows_in_relative_path_is_blocked(self, sandbox: Path):
        root = AllowedRoot(path=sandbox / "docs", readable=True)
        (sandbox / "docs" / "Windows").mkdir(exist_ok=True)
        validator = PathValidator(roots=[root])

        with pytest.raises(PathValidationError, match="restricted system directory"):
            validator.validate(
                str(sandbox / "docs" / "Windows" / "System32" / "cmd.exe"),
                FileOperation.READ,
            )

    def test_blocked_pattern_is_case_insensitive(self, sandbox: Path):
        root = AllowedRoot(path=sandbox / "docs", readable=True)
        (sandbox / "docs" / "APPDATA").mkdir(exist_ok=True)
        validator = PathValidator(roots=[root])

        with pytest.raises(PathValidationError, match="restricted system directory"):
            validator.validate(
                str(sandbox / "docs" / "APPDATA" / "secrets.txt"),
                FileOperation.READ,
            )

    def test_custom_blocked_patterns(self, sandbox: Path):
        root = AllowedRoot(path=sandbox / "docs", readable=True)
        (sandbox / "docs" / "secret").mkdir(exist_ok=True)
        validator = PathValidator(
            roots=[root],
            blocked_patterns=("secret",),
        )

        with pytest.raises(PathValidationError, match="restricted system directory"):
            validator.validate(
                str(sandbox / "docs" / "secret" / "file.txt"),
                FileOperation.READ,
            )

    def test_no_blocked_patterns_allows_all(self, sandbox: Path):
        root = AllowedRoot(path=sandbox / "docs", readable=True)
        (sandbox / "docs" / "AppData").mkdir(exist_ok=True)
        (sandbox / "docs" / "AppData" / "file.txt").write_text("ok", encoding="utf-8")
        validator = PathValidator(roots=[root], blocked_patterns=())

        result = validator.validate(
            str(sandbox / "docs" / "AppData" / "file.txt"),
            FileOperation.READ,
        )

        assert result.canonical == (sandbox / "docs" / "AppData" / "file.txt").resolve()


# ── Root permission checks ────────────────────────────────────────


class TestRootPermissions:
    """Tests for per-root operation permissions."""

    def test_read_from_readable_root(self, sandbox: Path):
        root = AllowedRoot(path=sandbox / "docs", readable=True)
        validator = PathValidator(roots=[root])

        result = validator.validate(
            str(sandbox / "docs" / "readme.txt"),
            FileOperation.READ,
        )

        assert result.canonical == (sandbox / "docs" / "readme.txt").resolve()

    def test_read_from_non_readable_root_is_rejected(self, sandbox: Path):
        root = AllowedRoot(
            path=sandbox / "docs",
            readable=False,
            writable=True,
        )
        validator = PathValidator(roots=[root])

        with pytest.raises(PathValidationError, match="Read access is not permitted"):
            validator.validate(
                str(sandbox / "docs" / "readme.txt"),
                FileOperation.READ,
            )

    def test_write_to_writable_root(self, sandbox: Path, writable_root: AllowedRoot):
        validator = PathValidator(roots=[writable_root])

        result = validator.validate(
            str(sandbox / "docs" / "new_file.txt"),
            FileOperation.WRITE,
        )

        assert isinstance(result, ValidatedPath)

    def test_write_to_readonly_root_is_rejected(
        self, sandbox: Path, readable_root: AllowedRoot
    ):
        validator = PathValidator(roots=[readable_root])

        with pytest.raises(PathValidationError, match="Write access is not permitted"):
            validator.validate(
                str(sandbox / "docs" / "file.txt"),
                FileOperation.WRITE,
            )

    def test_delete_from_deletable_root(
        self, sandbox: Path, deletable_root: AllowedRoot
    ):
        validator = PathValidator(roots=[deletable_root])

        result = validator.validate(
            str(sandbox / "docs" / "readme.txt"),
            FileOperation.DELETE,
        )

        assert isinstance(result, ValidatedPath)

    def test_delete_from_non_deletable_root_is_rejected(
        self, sandbox: Path, writable_root: AllowedRoot
    ):
        validator = PathValidator(roots=[writable_root])

        with pytest.raises(
            PathValidationError, match="Delete access is not permitted"
        ):
            validator.validate(
                str(sandbox / "docs" / "readme.txt"),
                FileOperation.DELETE,
            )

    def test_all_defaults_deny_delete(self):
        """Default AllowedRoot has deletable=False."""
        root = AllowedRoot(path=Path("/any/dir"))

        assert root.deletable is False


# ── Multiple roots ────────────────────────────────────────────────


class TestMultipleRoots:
    """Tests for validators with multiple allowed roots."""

    def test_matches_first_applicable_root(self, sandbox: Path):
        dir_a = sandbox / "alpha"
        dir_b = sandbox / "beta"
        dir_a.mkdir()
        dir_b.mkdir()
        (dir_a / "file.txt").write_text("a", encoding="utf-8")

        root_a = AllowedRoot(path=dir_a, readable=True)
        root_b = AllowedRoot(path=dir_b, readable=True, writable=True)
        validator = PathValidator(roots=[root_a, root_b])

        result = validator.validate(str(dir_a / "file.txt"), FileOperation.READ)

        assert result.root is root_a

    def test_path_in_second_root(self, sandbox: Path):
        dir_a = sandbox / "alpha"
        dir_b = sandbox / "beta"
        dir_a.mkdir()
        dir_b.mkdir()
        (dir_b / "file.txt").write_text("b", encoding="utf-8")

        root_a = AllowedRoot(path=dir_a, readable=True)
        root_b = AllowedRoot(path=dir_b, readable=True, writable=True)
        validator = PathValidator(roots=[root_a, root_b])

        result = validator.validate(str(dir_b / "file.txt"), FileOperation.READ)

        assert result.root is root_b

    def test_path_outside_all_roots(self, sandbox: Path):
        dir_a = sandbox / "alpha"
        dir_b = sandbox / "beta"
        dir_a.mkdir()
        dir_b.mkdir()

        root_a = AllowedRoot(path=dir_a, readable=True)
        root_b = AllowedRoot(path=dir_b, readable=True)
        validator = PathValidator(roots=[root_a, root_b])

        with pytest.raises(PathValidationError, match="not under any allowed"):
            validator.validate(
                str(sandbox / "gamma" / "file.txt"),
                FileOperation.READ,
            )


# ── PathValidationError ──────────────────────────────────────────


class TestPathValidationError:
    """Tests for the PathValidationError exception."""

    def test_reason_attribute(self):
        error = PathValidationError("test reason")

        assert error.reason == "test reason"
        assert str(error) == "test reason"

    def test_is_exception(self):
        assert issubclass(PathValidationError, Exception)


# ── Logging ───────────────────────────────────────────────────────


class TestLogging:
    """Tests for structured logging output."""

    def test_rejected_path_is_logged(self, validator: PathValidator, caplog):
        with caplog.at_level("WARNING", logger="SentinelAI.PathValidator"):
            with pytest.raises(PathValidationError):
                validator.validate("", FileOperation.READ)

        assert any("empty path" in r.message for r in caplog.records)

    def test_blocked_pattern_is_logged(self, sandbox: Path, caplog):
        root = AllowedRoot(path=sandbox, readable=True)
        (sandbox / "AppData").mkdir(exist_ok=True)
        validator = PathValidator(roots=[root])

        with caplog.at_level("WARNING", logger="SentinelAI.PathValidator"):
            with pytest.raises(PathValidationError):
                validator.validate(
                    str(sandbox / "AppData" / "file.txt"),
                    FileOperation.READ,
                )

        assert any("blocked directory" in r.message for r in caplog.records)

    def test_outside_root_is_logged(self, sandbox: Path, validator: PathValidator, caplog):
        with caplog.at_level("WARNING", logger="SentinelAI.PathValidator"):
            with pytest.raises(PathValidationError):
                validator.validate(
                    str(sandbox / "outside" / "file.txt"),
                    FileOperation.READ,
                )

        assert any("not under any allowed root" in r.message for r in caplog.records)
