"""Default tool registry factory.

Provides a factory function that constructs the standard tool registry.
This keeps concrete tool imports isolated to a single location and allows
the composition root (main.py) to build the registry once and inject it.
"""

from __future__ import annotations

from app.context.manager import ContextManager
from app.llm.client import LLMClient
from app.llm.service import LLMService
from app.tools.application.database import ApplicationDatabase, bootstrap_applications, default_database_path
from app.tools.application.registry import ApplicationRegistry
from app.tools.application.scanner import ApplicationScanner
from app.tools.application.tool import ApplicationTool
from app.tools.base import Tool
from app.tools.browser.tool import BrowserTool
from app.tools.chat.tool import ChatTool
from app.tools.filesystem.tool import FilesystemTool


def create_default_registry(
    llm: LLMService | None = None,
    context_manager: ContextManager | None = None,
) -> dict[str, Tool]:
    """Create and return the default tool registry.

    Each key is the tool name referenced by ``Plan.tool``.
    Each value is a concrete ``Tool`` instance.

    Args:
        llm: Optional :class:`LLMService` instance for ``ChatTool``.
            Defaults to :class:`LLMClient` (Ollama).
        context_manager: Optional :class:`ContextManager` for
            ``ChatTool`` to build conversation-aware prompts.
            Defaults to a new :class:`ContextManager`.
    """
    database = ApplicationDatabase(file_path=default_database_path(), seed=bootstrap_applications())
    scanner = ApplicationScanner()
    for application in scanner.discover():
        database.add(application)

    app_registry = ApplicationRegistry(database=database)

    llm_service = llm or LLMClient()
    ctx = context_manager or ContextManager()

    return {
        "application": ApplicationTool(registry=app_registry),
        "filesystem": FilesystemTool(),
        "browser": BrowserTool(),
        "llm": ChatTool(llm=llm_service, context_manager=ctx),
    }
