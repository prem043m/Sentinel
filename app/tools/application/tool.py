"""Real Windows application launcher."""

from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path

from app.models.plan import Plan
from app.tools.application.database import ApplicationDatabase, bootstrap_applications
from app.tools.application.registry import ApplicationRegistry
from app.tools.base import Tool
from app.tools.result import ExecutionResult

logger = logging.getLogger("SentinelAI.ApplicationTool")


class ApplicationTool(Tool):
    """Launches a trusted application via ``subprocess.Popen``."""

    def __init__(self, registry: ApplicationRegistry | None = None) -> None:
        self._registry = registry or ApplicationRegistry(
            database=ApplicationDatabase(seed=bootstrap_applications()),
        )

    def execute(self, plan: Plan) -> ExecutionResult:
        app_name: str = plan.parameters.get("name", "")

        if not app_name:
            logger.warning("ApplicationTool received a plan with no 'name' parameter.")
            return ExecutionResult(success=False, message="No application name provided.")

        application = self._registry.lookup(app_name)
        if application is None:
            logger.warning(
                "Blocked: '%s' is not in the application registry or is not approved.",
                app_name,
            )
            return ExecutionResult(success=False, message=f"Application '{app_name}' is not in the allowlist.")

        executable_candidates = [application.path]
        executable_candidates.extend(
            str(value) for value in application.metadata.get("fallback_paths", []) if value
        )

        for executable in executable_candidates:
            resolved_executable = os.path.expandvars(str(Path(executable).expanduser()))

            try:
                process = subprocess.Popen([resolved_executable], shell=False)
            except FileNotFoundError:
                logger.warning(
                    "Executable not found: '%s' for application '%s'.",
                    resolved_executable,
                    application.name,
                )
                continue
            except PermissionError:
                logger.error(
                    "Permission denied launching '%s' (%s).",
                    application.name,
                    resolved_executable,
                )
                return ExecutionResult(
                    success=False,
                    message=(
                        f"Permission denied when launching '{application.name}'. "
                        f"Check your system permissions."
                    ),
                )
            except OSError as exc:
                logger.error(
                    "OS error launching '%s' (%s): %s",
                    application.name,
                    resolved_executable,
                    exc,
                )
                return ExecutionResult(success=False, message=f"OS error launching '{application.name}': {exc}")

            logger.info(
                "Launched '%s' (%s) — PID %d.",
                application.name,
                resolved_executable,
                process.pid,
            )
            return ExecutionResult(
                success=True,
                message=f"Application '{application.name}' launched successfully.",
                data={"pid": process.pid},
            )

        logger.error(
            "Executable not found: '%s' for application '%s'.",
            application.path,
            application.name,
        )
        return ExecutionResult(
            success=False,
            message=(
                f"Executable '{application.path}' not found. "
                f"'{application.name}' may not be installed."
            ),
        )
