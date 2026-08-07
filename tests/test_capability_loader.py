from app.planner.capabilities.loader import CapabilityLoader


def test_capability_loader_discovers_all_default_tool_capabilities():
    loader = CapabilityLoader()
    registry = loader.discover_and_load("app.tools")

    tools = {t.tool_name for t in registry.all_tools()}
    assert "application" in tools
    assert "filesystem" in tools
    assert "browser" in tools
    assert "llm" in tools
