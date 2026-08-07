"""Tests for context manager capture of artifacts from tool outputs."""

from __future__ import annotations

import pytest
from app.artifacts.models import ExecutionArtifactType
from app.context.manager import ContextManager
from app.models.plan import Plan
from app.tools.result import ExecutionResult


def test_context_manager_capture_filesystem_read():
    manager = ContextManager()
    plan = Plan(intent="read_file", tool="filesystem", parameters={"path": "sub/dir/notes.py"})
    result = ExecutionResult(
        success=True,
        message="Read successfully",
        data={
            "content": "print('hello')",
            "path": "sub/dir/notes.py",
        },
    )

    artifact = manager.capture(result, plan)
    assert artifact is not None
    assert artifact.id == "ART-001"
    assert artifact.type == ExecutionArtifactType.CODE
    assert artifact.name == "notes.py"
    assert artifact.content == "print('hello')"
    assert artifact.metadata["path"] == "sub/dir/notes.py"


def test_context_manager_capture_filesystem_list():
    manager = ContextManager()
    plan = Plan(intent="list_directory", tool="filesystem", parameters={"path": "docs"})
    result = ExecutionResult(
        success=True,
        message="Listed docs directory",
        data={
            "path": "docs",
            "directory_contents": [
                {"name": "file.txt", "is_directory": False, "size": 100},
                {"name": "subfolder", "is_directory": True, "size": 0},
            ],
        },
    )

    artifact = manager.capture(result, plan)
    assert artifact is not None
    assert artifact.type == ExecutionArtifactType.DIRECTORY
    assert "file.txt (100 bytes)" in artifact.content
    assert "subfolder (Directory)" in artifact.content


def test_context_manager_capture_browser_search():
    manager = ContextManager()
    plan = Plan(intent="search_web", tool="browser", parameters={"query": "python contextvars"})
    result = ExecutionResult(
        success=True,
        message="Search results opened",
        data={
            "query": "python contextvars",
            "url": "https://google.com/search?q=python+contextvars",
        },
    )

    artifact = manager.capture(result, plan)
    assert artifact is not None
    assert artifact.type == ExecutionArtifactType.SEARCH_RESULTS
    assert "python contextvars" in artifact.name
    assert "https://google.com/search" in artifact.content


def test_context_manager_add_tool_result_triggers_capture():
    manager = ContextManager()
    plan = Plan(intent="read_file", tool="filesystem", parameters={"path": "README.md"})
    result = ExecutionResult(
        success=True,
        message="Read README.md",
        data={
            "content": "# SentinelAI",
            "path": "README.md",
        },
    )

    manager.add_tool_result(result, plan)

    stored = manager.artifact_store.list_all()
    assert len(stored) == 1
    assert stored[0].name == "README.md"
    assert stored[0].type == ExecutionArtifactType.TEXT
