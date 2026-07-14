"""Filesystem security configuration.

Defines the security boundaries for all filesystem operations:

- **AllowedRoot**: directories SentinelAI may access, with per-root
  read/write/delete permissions.
- **FileOperation**: the operation types that roots can authorise.
- **BLOCKED_PATTERNS**: directory names that are always denied,
  regardless of allowed-root configuration.
- **Size limits**: maximum byte counts for read and write operations.

This module contains data definitions and a factory function only.
No execution logic, no OS operations, no policy decisions.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class FileOperation(str, Enum):
    """The type of filesystem operation being requested.

    Used by the PathValidator to check whether an allowed root
    grants the necessary permission for a given operation.
    """

    READ = "read"
    WRITE = "write"
    DELETE = "delete"


@dataclass(frozen=True, slots=True)
class AllowedRoot:
    """A directory that SentinelAI is permitted to access.

    Attributes:
        path: Absolute path to the root directory.
        readable: Whether files under this root can be read.
        writable: Whether files under this root can be written
                  or created.
        deletable: Whether files under this root can be deleted.
                   Disabled by default — delete operations require
                   explicit opt-in and are deferred until the
                   Audit Logger milestone.
    """

    path: Path
    readable: bool = True
    writable: bool = False
    deletable: bool = False


# ── Size limits ───────────────────────────────────────────────────

MAX_READ_SIZE_BYTES: int = 10 * 1024 * 1024   # 10 MB
"""Maximum file size (in bytes) that a read operation will accept."""

MAX_WRITE_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB
"""Maximum content size (in bytes) that a write operation will accept."""


# ── Blocked directory patterns ────────────────────────────────────
# Matching is case-insensitive against each component of the
# resolved canonical path.  If *any* component matches, the
# path is denied — even if it falls under an allowed root.

BLOCKED_PATTERNS: tuple[str, ...] = (
    "windows",
    "program files",
    "program files (x86)",
    "$recycle.bin",
    "system volume information",
    "appdata",
)


def create_default_roots() -> list[AllowedRoot]:
    """Create the default set of allowed root directories.

    The roots are scoped to the current user's home directory.
    Delete permission is **disabled** on all roots by default.

    Returns:
        A list of ``AllowedRoot`` instances:

        - ``~/Documents`` — read + write
        - ``~/Desktop``   — read + write
        - ``~/Downloads``  — read only
    """
    home = Path.home()

    return [
        AllowedRoot(
            path=home / "Documents",
            readable=True,
            writable=True,
            deletable=False,
        ),
        AllowedRoot(
            path=home / "Desktop",
            readable=True,
            writable=True,
            deletable=False,
        ),
        AllowedRoot(
            path=home / "Downloads",
            readable=True,
            writable=False,
            deletable=False,
        ),
    ]
