"""Filesystem tool — safe UTF-8 file reader.

This is the **only** module in SentinelAI that performs filesystem
I/O (open, read, stat).  All other layers remain I/O-free.

Security invariants:
- Every path is validated by the ``PathValidator`` before any OS
  access occurs.
- Binary files are rejected (``UnicodeDecodeError``).
- Files exceeding ``MAX_READ_SIZE_BYTES`` are rejected before
  reading.
- Every operation (success or failure) is logged.
"""

import logging
from pathlib import Path

from app.models.plan import Plan
from app.tools.base import Tool
from app.tools.filesystem.config import (
    MAX_READ_SIZE_BYTES,
    FileOperation,
    create_default_roots,
)
from app.tools.filesystem.validator import (
    PathValidationError,
    PathValidator,
)
from app.tools.result import ExecutionResult

logger = logging.getLogger("SentinelAI.FilesystemTool")


class FilesystemTool(Tool):
    """Reads UTF-8 text files safely.

    The tool validates the requested path against the security
    configuration, enforces size limits, rejects binary files,
    and returns the file content in ``ExecutionResult.data``.

    Args:
        validator: An optional ``PathValidator`` instance.  When
                   ``None``, a default validator is constructed from
                   ``create_default_roots()``.
    """

    def __init__(self, validator: PathValidator | None = None) -> None:
        if validator is None:
            validator = PathValidator(roots=create_default_roots())
        self._validator = validator

    def execute(self, plan: Plan) -> ExecutionResult:
        """Execute a filesystem request.

        Args:
            plan: A ``Plan`` containing intent and parameters.

        Returns:
            An ``ExecutionResult``.
        """
        raw_path: str = plan.parameters.get("path", "")

        # ── 1. Path validation ────────────────────────────────────
        try:
            validated = self._validator.validate(
                raw_path, FileOperation.READ,
            )
        except PathValidationError as exc:
            logger.warning(
                "Rejected (validation): '%s' — %s",
                raw_path,
                exc.reason,
            )
            return ExecutionResult(
                success=False,
                message=exc.reason,
            )

        if plan.intent == "list_directory":
            return self._list_directory(validated.canonical, plan.parameters, validated.original)
        else:
            return self._read_file(validated.canonical, validated.original)

    def _list_directory(self, directory: Path, parameters: dict, original_path: str) -> ExecutionResult:
        if not directory.is_dir():
            return ExecutionResult(
                success=False,
                message=f"Path '{original_path}' is not a directory."
            )

        filter_ext = parameters.get("filter_ext")
        sort_by = parameters.get("sort_by", "name")
        sort_desc = parameters.get("sort_desc", False)
        show_hidden = parameters.get("show_hidden", False)

        from app.models.file_info import FileInfo
        from pathlib import Path

        results: list[FileInfo] = []
        try:
            for item in directory.iterdir():
                if not show_hidden and item.name.startswith("."):
                    continue

                if filter_ext and not item.is_dir() and item.suffix != filter_ext:
                    continue

                try:
                    stat = item.stat()
                    size = stat.st_size if not item.is_dir() else 0
                    modified_at = stat.st_mtime
                except OSError:
                    size = 0
                    modified_at = 0.0

                info = FileInfo(
                    name=item.name,
                    path=str(item),
                    size=size,
                    extension=item.suffix,
                    is_directory=item.is_dir(),
                    modified_at=modified_at,
                )
                results.append(info)
        except OSError as exc:
            logger.error("List failed (OS error): '%s' — %s", directory, exc)
            return ExecutionResult(
                success=False,
                message=f"Cannot list '{original_path}': {exc}"
            )

        if sort_by == "size":
            results.sort(key=lambda x: x.size, reverse=sort_desc)
        elif sort_by == "modified_at":
            results.sort(key=lambda x: x.modified_at, reverse=sort_desc)
        else:
            results.sort(key=lambda x: x.name.lower(), reverse=sort_desc)

        logger.info("List successful: '%s' (%d items).", directory, len(results))

        import dataclasses
        return ExecutionResult(
            success=True,
            message=f"Successfully listed '{original_path}' ({len(results)} items).",
            data={
                "directory_contents": [dataclasses.asdict(i) for i in results]
            }
        )

    def _read_file(self, canonical: Path, original_path: str) -> ExecutionResult:
        from pathlib import Path
        # ── 2. Size check (before opening) ────────────────────────
        try:
            size = canonical.stat().st_size
        except FileNotFoundError:
            logger.warning("Read failed (not found): '%s'.", canonical)
            return ExecutionResult(success=False, message=f"File not found: '{original_path}'.")
        except PermissionError:
            logger.error("Read failed (permission denied): '%s'.", canonical)
            return ExecutionResult(success=False, message=f"Permission denied: cannot access '{original_path}'.")
        except OSError as exc:
            logger.error("Read failed (OS error during stat): '%s' — %s", canonical, exc)
            return ExecutionResult(success=False, message=f"Cannot access '{original_path}': {exc}")

        if size > MAX_READ_SIZE_BYTES:
            limit_mb = MAX_READ_SIZE_BYTES / (1024 * 1024)
            logger.warning("Read rejected (too large): '%s' is %d bytes (limit: %d bytes).", canonical, size, MAX_READ_SIZE_BYTES)
            return ExecutionResult(success=False, message=f"Cannot read '{original_path}': file size ({size:,} bytes) exceeds the {limit_mb:.0f} MB limit.")

        if canonical.is_dir():
            return self._list_directory(canonical, plan.parameters, original_path)

        # ── 3. Read UTF-8 content ─────────────────────────────────
        try:
            content = canonical.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            logger.warning("Read rejected (binary): '%s' is not valid UTF-8.", canonical)
            return ExecutionResult(success=False, message=f"Cannot read '{original_path}': file appears to be binary, not UTF-8 text.")
        except FileNotFoundError:
            logger.warning("Read failed (not found after stat): '%s'.", canonical)
            return ExecutionResult(success=False, message=f"File not found: '{original_path}'.")
        except PermissionError:
            logger.error("Read failed (permission denied): '%s'.", canonical)
            return ExecutionResult(success=False, message=f"Permission denied: cannot read '{original_path}'.")
        except OSError as exc:
            logger.error("Read failed (OS error): '%s' — %s", canonical, exc)
            return ExecutionResult(success=False, message=f"Cannot read '{original_path}': {exc}")

        # ── 4. Success ────────────────────────────────────────────
        logger.info("Read successful: '%s' (%d bytes).", canonical, size)

        return ExecutionResult(
            success=True,
            message=f"Successfully read '{original_path}' ({size:,} bytes).",
            data={
                "content": content,
                "path": str(canonical),
                "size_bytes": size,
                "mime_type": "text/plain; charset=utf-8",
            }
        )
