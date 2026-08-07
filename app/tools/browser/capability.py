"""Capability provider for the browser tool."""

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


class BrowserCapabilityProvider(CapabilityProvider):
    """Exposes capability metadata for browser operations."""

    def build(self) -> ToolCapability:
        open_url_intent = IntentCapability(
            id="browser.open",
            name="open_url",
            description="Opens a full URL in the default browser",
            tool_name="browser",
            category=CapabilityCategory.BROWSER,
            version="1.0.0",
            priority=100,
            preferred=True,
            tags=("browser", "url", "web", "open"),
            parameters=(
                ParameterDefinition(
                    name="url",
                    type=ParameterType.URL,
                    description="full target web URL",
                    required=True,
                ),
            ),
            examples=ExampleDataset(
                examples=(
                    ExampleCommand(
                        user_input="Open github.com",
                        expected_intent="open_url",
                        expected_tool="browser",
                        expected_parameters={"url": "https://github.com"},
                    ),
                )
            ),
            preconditions=("Valid URL schema",),
            postconditions=("Browser opened to URL",),
            constraints={"https_preferred": True},
            consumes_artifacts=(),
            produces_artifacts=(ArtifactType.WEB_PAGE,),
            estimated_latency_ms=300,
            requires_confirmation=False,
            side_effects=True,
            risk_level="normal",
        )

        search_web_intent = IntentCapability(
            id="browser.search",
            name="search_web",
            description="Performs a web search in the default browser",
            tool_name="browser",
            category=CapabilityCategory.BROWSER,
            version="1.0.0",
            priority=90,
            preferred=True,
            tags=("browser", "search", "web", "query"),
            parameters=(
                ParameterDefinition(
                    name="query",
                    type=ParameterType.STRING,
                    description="search query string as provided by the user",
                    required=True,
                ),
            ),
            examples=ExampleDataset(
                examples=(
                    ExampleCommand(
                        user_input="Search for Python tutorials",
                        expected_intent="search_web",
                        expected_tool="browser",
                        expected_parameters={"query": "Python tutorials"},
                    ),
                )
            ),
            preconditions=("Non-empty search query",),
            postconditions=("Search results page opened",),
            constraints={},
            consumes_artifacts=(),
            produces_artifacts=(ArtifactType.SEARCH_RESULTS,),
            estimated_latency_ms=300,
            requires_confirmation=False,
            side_effects=True,
            risk_level="normal",
        )

        return ToolCapability(
            tool_name="browser",
            description="Opens URLs and performs web searches",
            category=CapabilityCategory.BROWSER,
            version="1.0.0",
            intents=(open_url_intent, search_web_intent),
            supported_operations=("open_url", "search_web"),
        )
