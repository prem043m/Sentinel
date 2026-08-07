"""Capability provider for the filesystem tool."""

from __future__ import annotations

from app.artifacts.types import ArtifactType
from app.planner.capabilities.models import (
    CapabilityCategory,
    ExampleCommand,
    ExampleDataset,
    IntentCapability,
    ParameterDefinition,
    ParameterType,
    ToolCapability,
)
from app.planner.capabilities.provider import CapabilityProvider


class FilesystemCapabilityProvider(CapabilityProvider):
    """Exposes capability metadata for filesystem operations."""

    def build(self) -> ToolCapability:
        read_file_intent = IntentCapability(
            id="filesystem.read",
            name="read_file",
            description="Reads UTF-8 text files safely",
            tool_name="filesystem",
            category=CapabilityCategory.FILESYSTEM,
            version="1.0.0",
            priority=100,
            preferred=True,
            tags=("file", "read", "filesystem", "text"),
            parameters=(
                ParameterDefinition(
                    name="path",
                    type=ParameterType.PATH,
                    description="exact file path or filename to read",
                    required=True,
                ),
            ),
            examples=ExampleDataset(
                examples=(
                    ExampleCommand(
                        user_input="Read the README file",
                        expected_intent="read_file",
                        expected_tool="filesystem",
                        expected_parameters={"path": "README.md"},
                    ),
                )
            ),
            preconditions=("Readable path within allowed roots",),
            postconditions=("File content loaded",),
            constraints={"max_file_size_bytes": 10_485_760},
            consumes_artifacts=(),
            produces_artifacts=(ArtifactType.FILE,),
            estimated_latency_ms=50,
            requires_confirmation=False,
            side_effects=False,
            risk_level="normal",
        )

        list_directory_intent = IntentCapability(
            id="filesystem.list",
            name="list_directory",
            description="Lists contents of a directory",
            tool_name="filesystem",
            category=CapabilityCategory.FILESYSTEM,
            version="1.0.0",
            priority=90,
            preferred=True,
            tags=("directory", "folder", "list", "filesystem"),
            parameters=(
                ParameterDefinition(
                    name="path",
                    type=ParameterType.PATH,
                    description="exact directory path or folder name to list",
                    required=True,
                ),
            ),
            examples=ExampleDataset(
                examples=(
                    ExampleCommand(
                        user_input="List files in the docs folder",
                        expected_intent="list_directory",
                        expected_tool="filesystem",
                        expected_parameters={"path": "docs"},
                    ),
                )
            ),
            preconditions=("Directory path within allowed roots",),
            postconditions=("Directory entries listed",),
            constraints={},
            consumes_artifacts=(),
            produces_artifacts=(ArtifactType.DIRECTORY,),
            estimated_latency_ms=50,
            requires_confirmation=False,
            side_effects=False,
            risk_level="normal",
        )

        return ToolCapability(
            tool_name="filesystem",
            description="Reads files and lists directories",
            category=CapabilityCategory.FILESYSTEM,
            version="1.0.0",
            intents=(read_file_intent, list_directory_intent),
            supported_operations=("read_file", "list_directory"),
        )
