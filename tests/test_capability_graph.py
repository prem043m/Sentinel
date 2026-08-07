from app.artifacts.types import ArtifactType
from app.planner.capabilities.graph import CapabilityGraph
from app.planner.capabilities.loader import CapabilityLoader


def test_capability_graph_producers_and_consumers():
    registry = CapabilityLoader().discover_and_load("app.tools")
    graph = CapabilityGraph(registry)

    file_producers = graph.producers_for(ArtifactType.FILE)
    assert any(intent.name == "read_file" for intent in file_producers)

    dir_producers = graph.producers_for(ArtifactType.DIRECTORY)
    assert any(intent.name == "list_directory" for intent in dir_producers)
