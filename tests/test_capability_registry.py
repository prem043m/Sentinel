from app.artifacts.types import ArtifactType
from app.planner.capabilities.loader import CapabilityLoader
from app.planner.capabilities.models import CapabilityCategory, ParameterType


def test_registry_lookup_and_grouping():
    registry = CapabilityLoader().discover_and_load("app.tools")

    assert registry.lookup_tool("filesystem") is not None
    assert registry.lookup_intent("read_file") is not None
    assert "filesystem" in registry.group_by_tool()
    assert "read_file" in registry.group_by_intent()


def test_registry_find_by_category():
    registry = CapabilityLoader().discover_and_load("app.tools")

    fs_intents = registry.find_by_category(CapabilityCategory.FILESYSTEM)
    assert any(intent.name == "read_file" for intent in fs_intents)
    assert any(intent.name == "list_directory" for intent in fs_intents)


def test_registry_find_by_artifact():
    registry = CapabilityLoader().discover_and_load("app.tools")

    file_producers = registry.find_by_artifact(ArtifactType.FILE, mode="produces")
    assert any(intent.name == "read_file" for intent in file_producers)


def test_registry_find_by_parameter_type():
    registry = CapabilityLoader().discover_and_load("app.tools")

    path_intents = registry.find_by_parameter_type(ParameterType.PATH)
    assert any(intent.name == "read_file" for intent in path_intents)


def test_registry_search():
    registry = CapabilityLoader().discover_and_load("app.tools")

    results = registry.search("browser")
    assert any(intent.name == "open_url" for intent in results)
    assert any(intent.name == "search_web" for intent in results)


def test_registry_unregister():
    registry = CapabilityLoader().discover_and_load("app.tools")
    assert registry.lookup_tool("browser") is not None

    assert registry.unregister("browser") is True
    assert registry.lookup_tool("browser") is None
    assert registry.lookup_intent("open_url") is None
