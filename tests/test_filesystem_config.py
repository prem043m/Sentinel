"""Tests for filesystem security configuration."""

from pathlib import Path

from app.tools.filesystem.config import (
    BLOCKED_PATTERNS,
    MAX_READ_SIZE_BYTES,
    MAX_WRITE_SIZE_BYTES,
    AllowedRoot,
    FileOperation,
    create_default_roots,
)


class TestAllowedRoot:
    """Tests for the AllowedRoot dataclass."""

    def test_default_permissions(self):
        root = AllowedRoot(path=Path("/some/dir"))

        assert root.readable is True
        assert root.writable is False
        assert root.deletable is False

    def test_explicit_permissions(self):
        root = AllowedRoot(
            path=Path("/data"),
            readable=True,
            writable=True,
            deletable=True,
        )

        assert root.readable is True
        assert root.writable is True
        assert root.deletable is True

    def test_is_frozen(self):
        root = AllowedRoot(path=Path("/some/dir"))

        try:
            root.readable = False
            assert False, "AllowedRoot should be frozen"
        except AttributeError:
            pass

    def test_path_is_stored(self):
        path = Path("/specific/path")
        root = AllowedRoot(path=path)

        assert root.path == path


class TestFileOperation:
    """Tests for the FileOperation enum."""

    def test_read_value(self):
        assert FileOperation.READ == "read"

    def test_write_value(self):
        assert FileOperation.WRITE == "write"

    def test_delete_value(self):
        assert FileOperation.DELETE == "delete"

    def test_enum_members(self):
        members = set(FileOperation)
        assert members == {
            FileOperation.READ,
            FileOperation.WRITE,
            FileOperation.DELETE,
        }


class TestCreateDefaultRoots:
    """Tests for the default root factory function."""

    def test_returns_three_roots(self):
        roots = create_default_roots()

        assert len(roots) == 3

    def test_all_roots_are_allowed_root_instances(self):
        roots = create_default_roots()

        for root in roots:
            assert isinstance(root, AllowedRoot)

    def test_documents_root(self):
        roots = create_default_roots()
        documents = roots[0]

        assert documents.path == Path.home() / "Documents"
        assert documents.readable is True
        assert documents.writable is True
        assert documents.deletable is False

    def test_desktop_root(self):
        roots = create_default_roots()
        desktop = roots[1]

        assert desktop.path == Path.home() / "Desktop"
        assert desktop.readable is True
        assert desktop.writable is True
        assert desktop.deletable is False

    def test_downloads_root(self):
        roots = create_default_roots()
        downloads = roots[2]

        assert downloads.path == Path.home() / "Downloads"
        assert downloads.readable is True
        assert downloads.writable is False
        assert downloads.deletable is False

    def test_no_root_is_deletable_by_default(self):
        roots = create_default_roots()

        for root in roots:
            assert root.deletable is False

    def test_all_roots_are_under_home(self):
        roots = create_default_roots()
        home = Path.home()

        for root in roots:
            assert str(root.path).startswith(str(home))

    def test_returns_new_list_each_call(self):
        roots_a = create_default_roots()
        roots_b = create_default_roots()

        assert roots_a is not roots_b


class TestBlockedPatterns:
    """Tests for the blocked directory patterns."""

    def test_windows_is_blocked(self):
        assert "windows" in BLOCKED_PATTERNS

    def test_program_files_is_blocked(self):
        assert "program files" in BLOCKED_PATTERNS

    def test_program_files_x86_is_blocked(self):
        assert "program files (x86)" in BLOCKED_PATTERNS

    def test_recycle_bin_is_blocked(self):
        assert "$recycle.bin" in BLOCKED_PATTERNS

    def test_system_volume_information_is_blocked(self):
        assert "system volume information" in BLOCKED_PATTERNS

    def test_appdata_is_blocked(self):
        assert "appdata" in BLOCKED_PATTERNS

    def test_all_patterns_are_lowercase(self):
        for pattern in BLOCKED_PATTERNS:
            assert pattern == pattern.lower()


class TestSizeLimits:
    """Tests for the size limit constants."""

    def test_read_limit_is_ten_megabytes(self):
        assert MAX_READ_SIZE_BYTES == 10 * 1024 * 1024

    def test_write_limit_is_ten_megabytes(self):
        assert MAX_WRITE_SIZE_BYTES == 10 * 1024 * 1024

    def test_limits_are_positive(self):
        assert MAX_READ_SIZE_BYTES > 0
        assert MAX_WRITE_SIZE_BYTES > 0
