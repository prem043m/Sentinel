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


def test_parameter_definition_creation():
    param = ParameterDefinition(
        name="path",
        type=ParameterType.PATH,
        description="target path",
        required=True,
    )
    assert param.name == "path"
    assert param.type is ParameterType.PATH
    assert param.required is True


def test_example_command_creation():
    example = ExampleCommand(
        user_input="Read README.md",
        expected_intent="read_file",
        expected_tool="filesystem",
        expected_parameters={"path": "README.md"},
    )
    assert example.user_input == "Read README.md"
    assert example.expected_parameters["path"] == "README.md"


def test_intent_capability_immutable_fields_and_defaults():
    intent = IntentCapability(
        id="filesystem.read",
        name="read_file",
        description="Reads UTF-8 text file",
        tool_name="filesystem",
        category=CapabilityCategory.FILESYSTEM,
        tags=("file", "read"),
        produces_artifacts=(ArtifactType.FILE,),
    )
    assert intent.id == "filesystem.read"
    assert intent.category is CapabilityCategory.FILESYSTEM
    assert "file" in intent.tags
    assert intent.produces_artifacts == (ArtifactType.FILE,)


def test_tool_capability_creation():
    intent = IntentCapability(
        id="filesystem.read",
        name="read_file",
        description="Reads UTF-8 text file",
        tool_name="filesystem",
        category=CapabilityCategory.FILESYSTEM,
    )
    tool_cap = ToolCapability(
        tool_name="filesystem",
        description="Reads files",
        category=CapabilityCategory.FILESYSTEM,
        intents=(intent,),
    )
    assert tool_cap.tool_name == "filesystem"
    assert len(tool_cap.intents) == 1
