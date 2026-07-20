"""Tests for directory operations in FilesystemTool."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.models.plan import Plan
from app.tools.filesystem.config import AllowedRoot, FileOperation
from app.tools.filesystem.tool import FilesystemTool
from app.tools.filesystem.validator import PathValidator

@pytest.fixture()
def sandbox(tmp_path: Path) -> Path:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "a.txt").write_text("A", encoding="utf-8")
    (docs / "b.txt").write_text("B"*10, encoding="utf-8")
    (docs / "c.md").write_text("C", encoding="utf-8")
    (docs / ".hidden").write_text("secret", encoding="utf-8")
    (docs / "sub").mkdir()
    return tmp_path

@pytest.fixture()
def validator(sandbox: Path) -> PathValidator:
    root = AllowedRoot(path=sandbox / "docs", readable=True)
    return PathValidator(roots=[root])

@pytest.fixture()
def tool(validator: PathValidator) -> FilesystemTool:
    return FilesystemTool(validator=validator)

def _list_plan(path: str, parameters: dict = None) -> Plan:
    params = {"path": path}
    if parameters:
        params.update(parameters)
    return Plan(
        intent="list_directory",
        tool="filesystem",
        parameters=params,
    )

def test_list_valid_directory(sandbox: Path, tool: FilesystemTool):
    plan = _list_plan(str(sandbox / "docs"))
    result = tool.execute(plan)
    assert result.success is True
    contents = result.data["directory_contents"]
    assert len(contents) == 4 # a.txt, b.txt, c.md, sub (.hidden excluded by default)

def test_list_not_a_directory(sandbox: Path, tool: FilesystemTool):
    plan = _list_plan(str(sandbox / "docs" / "a.txt"))
    result = tool.execute(plan)
    assert result.success is False
    assert "not a directory" in result.message

def test_list_hidden_files(sandbox: Path, tool: FilesystemTool):
    plan = _list_plan(str(sandbox / "docs"), parameters={"show_hidden": True})
    result = tool.execute(plan)
    assert result.success is True
    contents = result.data["directory_contents"]
    assert len(contents) == 5
    names = [c["name"] for c in contents]
    assert ".hidden" in names

def test_filter_extension(sandbox: Path, tool: FilesystemTool):
    plan = _list_plan(str(sandbox / "docs"), parameters={"filter_ext": ".txt"})
    result = tool.execute(plan)
    assert result.success is True
    contents = result.data["directory_contents"]
    names = [c["name"] for c in contents]
    assert "a.txt" in names
    assert "b.txt" in names
    assert "c.md" not in names
    assert "sub" in names # directories are kept unless filtered

def test_sort_by_size(sandbox: Path, tool: FilesystemTool):
    plan = _list_plan(str(sandbox / "docs"), parameters={"sort_by": "size", "sort_desc": True})
    result = tool.execute(plan)
    contents = result.data["directory_contents"]
    assert contents[0]["name"] == "b.txt" # size 10
    assert contents[1]["name"] == "a.txt" # size 1 (or sub which is size 0)

def test_file_metadata(sandbox: Path, tool: FilesystemTool):
    plan = _list_plan(str(sandbox / "docs"))
    result = tool.execute(plan)
    contents = result.data["directory_contents"]
    b_file = next(c for c in contents if c["name"] == "b.txt")
    assert b_file["size"] == 10
    assert b_file["extension"] == ".txt"
    assert b_file["is_directory"] is False
    assert b_file["modified_at"] > 0
