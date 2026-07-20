"""Default tool registry factory.

Provides a factory function that constructs the standard tool registry.
This keeps concrete tool imports isolated to a single location and allows
the composition root (main.py) to build the registry once and inject it.
"""

from app.tools.application.tool import ApplicationTool
from app.tools.base import Tool
from app.tools.browser.tool import BrowserTool
from app.tools.filesystem.config import create_default_roots
from app.tools.filesystem.tool import FilesystemTool
from app.tools.filesystem.validator import PathValidator


def create_default_registry() -> dict[str, Tool]:
    """Create and return the default tool registry.

    Each key is the tool name referenced by ``Plan.tool``.
    Each value is a concrete ``Tool`` instance.
    """
    return {
        "application": ApplicationTool(),
        "filesystem": FilesystemTool(
            validator=PathValidator(roots=create_default_roots()),
        ),
        "browser": BrowserTool(),
    }
