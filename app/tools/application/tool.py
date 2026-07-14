"""Real Windows application launcher.

This is the **only** module in SentinelAI that contains
Windows-specific knowledge (executable names, ``subprocess`` calls).
All other layers remain platform-independent.

Security invariants:
- Only applications present in the allowlist may be launched.
- ``subprocess.Popen`` is **always** called with ``shell=False``.
- Every launch attempt (success or failure) is logged.
"""

import logging
import subprocess

from app.models.plan import Plan
from app.tools.application import allowlist
from app.tools.base import Tool
from app.tools.result import ExecutionResult

logger = logging.getLogger("SentinelAI.ApplicationTool")


class ApplicationTool(Tool):
    """Launches a Windows application via ``subprocess.Popen``.

    The tool validates the requested application name against the
    application allowlist before invoking any operating-system process.
    If the application is not in the allowlist, execution is refused
    and a failure ``ExecutionResult`` is returned.
    """

    def execute(self, plan: Plan) -> ExecutionResult:
        """Execute an application launch request.

        Args:
            plan: A ``Plan`` whose ``parameters`` dict must contain
                  a ``"name"`` key with the user-facing application
                  name (e.g. ``"Calculator"``).

        Returns:
            An ``ExecutionResult`` indicating whether the application
            was launched successfully.  On success, ``data`` contains
            ``{"pid": <int>}``.
        """
        app_name: str = plan.parameters.get("name", "")

        if not app_name:
            logger.warning("ApplicationTool received a plan with no 'name' parameter.")
            return ExecutionResult(
                success=False,
                message="No application name provided.",
            )

        # ── Allowlist validation ──────────────────────────────────
        allowed = allowlist.lookup(app_name)

        if allowed is None:
            logger.warning(
                "Blocked: '%s' is not in the application allowlist.",
                app_name,
            )
            return ExecutionResult(
                success=False,
                message=f"Application '{app_name}' is not in the allowlist.",
            )

        # ── Subprocess launch ─────────────────────────────────────
        executable = allowed.executable

        try:
            process = subprocess.Popen(
                [executable],
                shell=False,
            )
        except FileNotFoundError:
            logger.error(
                "Executable not found: '%s' for application '%s'.",
                executable,
                allowed.name,
            )
            return ExecutionResult(
                success=False,
                message=(
                    f"Executable '{executable}' not found. "
                    f"'{allowed.name}' may not be installed."
                ),
            )
        except PermissionError:
            logger.error(
                "Permission denied launching '%s' (%s).",
                allowed.name,
                executable,
            )
            return ExecutionResult(
                success=False,
                message=(
                    f"Permission denied when launching '{allowed.name}'. "
                    f"Check your system permissions."
                ),
            )
        except OSError as exc:
            logger.error(
                "OS error launching '%s' (%s): %s",
                allowed.name,
                executable,
                exc,
            )
            return ExecutionResult(
                success=False,
                message=f"OS error launching '{allowed.name}': {exc}",
            )

        logger.info(
            "Launched '%s' (%s) — PID %d.",
            allowed.name,
            executable,
            process.pid,
        )

        return ExecutionResult(
            success=True,
            message=f"Application '{allowed.name}' launched successfully.",
            data={"pid": process.pid},
        )
