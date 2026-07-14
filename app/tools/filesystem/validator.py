"""Filesystem path validation.

Provides the security gate between raw path strings (from Plans)
and filesystem operations.  Every path must pass through the
``PathValidator`` before any OS-level file access occurs.

This module is **completely independent** of the PolicyEngine.
It validates paths and their accessibility for specific operation
types — it does not make intent-level policy decisions.

Security guarantees:

- Only paths under an explicitly allowed root are accepted.
- Directory traversal via ``..`` is neutralised by canonical
  path resolution.
- Blocked directory patterns are denied regardless of root
  configuration.
- Root-level permissions (readable / writable / deletable) are
  checked against the requested operation type.
"""

import logging
from dataclasses import dataclass
from pathlib import Path

from app.tools.filesystem.config import (
    BLOCKED_PATTERNS,
    AllowedRoot,
    FileOperation,
)

logger = logging.getLogger("SentinelAI.PathValidator")


class PathValidationError(Exception):
    """Raised when a path fails security validation.

    The ``reason`` attribute contains a human-readable explanation
    suitable for inclusion in an ``ExecutionResult.message``.
    """

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason: str = reason


@dataclass(frozen=True, slots=True)
class ValidatedPath:
    """A path that has passed all security validation checks.

    Attributes:
        canonical: The resolved, absolute canonical path.
        root: The ``AllowedRoot`` this path falls under.
        original: The raw path string before validation,
                  preserved for logging and error messages.
    """

    canonical: Path
    root: AllowedRoot
    original: str


class PathValidator:
    """Validates filesystem paths against the security configuration.

    The validator performs the following checks in order:

    1. The raw path is non-empty.
    2. ``~`` is expanded to the user's home directory.
    3. The path is resolved to its canonical absolute form
       (eliminates ``..``, ``.``, and symlinks).
    4. No component of the canonical path matches a blocked
       directory pattern.
    5. The canonical path falls under an allowed root.
    6. The allowed root grants permission for the requested
       operation type (read / write / delete).

    If any check fails, ``PathValidationError`` is raised with a
    descriptive reason.  The validator never performs OS operations
    (no file reads, no writes, no deletes).
    """

    def __init__(
        self,
        roots: list[AllowedRoot],
        blocked_patterns: tuple[str, ...] = BLOCKED_PATTERNS,
    ) -> None:
        self._roots = list(roots)
        self._blocked_patterns = blocked_patterns

    def validate(
        self,
        raw_path: str,
        operation: FileOperation,
    ) -> ValidatedPath:
        """Validate a raw path string for a specific operation.

        Args:
            raw_path: The untrusted path string from the Plan.
            operation: The type of filesystem operation requested.

        Returns:
            A ``ValidatedPath`` containing the canonical path and
            the matching allowed root.

        Raises:
            PathValidationError: If the path fails any security
                check.  The ``reason`` attribute describes why.
        """
        # 1. Non-empty check
        stripped = raw_path.strip() if raw_path else ""
        if not stripped:
            logger.warning("Path validation failed: empty path provided.")
            raise PathValidationError("No file path provided.")

        # 2. Expand ~ and resolve to canonical absolute path
        try:
            expanded = Path(stripped).expanduser()
        except RuntimeError as exc:
            logger.warning(
                "Path validation failed: cannot expand '%s': %s",
                stripped,
                exc,
            )
            raise PathValidationError(
                f"Cannot expand path '{stripped}': {exc}"
            ) from exc

        canonical = expanded.resolve(strict=False)

        # 3. Find matching allowed root
        root = self._find_matching_root(canonical)
        if root is None:
            logger.warning(
                "Path validation failed: '%s' is not under any allowed root.",
                canonical,
            )
            raise PathValidationError(
                f"Path '{stripped}' is not under any allowed directory."
            )

        # 4. Blocked pattern check (on relative path within root)
        root_resolved = root.path.resolve(strict=False)
        relative = canonical.relative_to(root_resolved)
        if self._contains_blocked_pattern(relative):
            logger.warning(
                "Path validation failed: '%s' contains a blocked directory.",
                canonical,
            )
            raise PathValidationError(
                f"Path '{stripped}' targets a restricted system directory."
            )

        # 5. Root permission check for the requested operation
        self._check_root_permission(root, operation, stripped)

        logger.debug(
            "Path validated: '%s' → '%s' (root: %s, operation: %s).",
            stripped,
            canonical,
            root.path,
            operation.value,
        )

        return ValidatedPath(
            canonical=canonical,
            root=root,
            original=stripped,
        )

    def _contains_blocked_pattern(self, path: Path) -> bool:
        """Check if any path component matches a blocked pattern."""
        parts_lower = [part.lower() for part in path.parts]
        return any(pattern in parts_lower for pattern in self._blocked_patterns)

    def _find_matching_root(self, canonical: Path) -> AllowedRoot | None:
        """Find the allowed root that contains the canonical path."""
        for root in self._roots:
            root_resolved = root.path.resolve(strict=False)
            try:
                canonical.relative_to(root_resolved)
                return root
            except ValueError:
                continue
        return None

    def _check_root_permission(
        self,
        root: AllowedRoot,
        operation: FileOperation,
        original_path: str,
    ) -> None:
        """Verify the root grants permission for the operation.

        Raises:
            PathValidationError: If the root does not permit the
                requested operation.
        """
        if operation is FileOperation.READ and not root.readable:
            logger.warning(
                "Path validation failed: root '%s' is not readable.",
                root.path,
            )
            raise PathValidationError(
                f"Read access is not permitted under '{root.path}'."
            )

        if operation is FileOperation.WRITE and not root.writable:
            logger.warning(
                "Path validation failed: root '%s' is not writable.",
                root.path,
            )
            raise PathValidationError(
                f"Write access is not permitted under '{root.path}'."
            )

        if operation is FileOperation.DELETE and not root.deletable:
            logger.warning(
                "Path validation failed: root '%s' is not deletable.",
                root.path,
            )
            raise PathValidationError(
                f"Delete access is not permitted under '{root.path}'."
            )
