"""Capability provider for the application tool."""

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


class ApplicationCapabilityProvider(CapabilityProvider):
    """Exposes capability metadata for launching desktop applications."""

    def build(self) -> ToolCapability:
        open_app_intent = IntentCapability(
            id="application.launch",
            name="open_application",
            description="Launches desktop applications by name",
            tool_name="application",
            category=CapabilityCategory.APPLICATION,
            version="1.0.0",
            priority=100,
            preferred=True,
            tags=("application", "launch", "desktop", "process"),
            parameters=(
                ParameterDefinition(
                    name="name",
                    type=ParameterType.STRING,
                    description="display name of the application to open (e.g. 'Calculator', 'Notepad', 'Google Chrome')",
                    required=True,
                ),
            ),
            examples=ExampleDataset(
                examples=(
                    ExampleCommand(
                        user_input="Open the calculator",
                        expected_intent="open_application",
                        expected_tool="application",
                        expected_parameters={"name": "Calculator"},
                    ),
                    ExampleCommand(
                        user_input="Open notepad",
                        expected_intent="open_application",
                        expected_tool="application",
                        expected_parameters={"name": "Notepad"},
                    ),
                )
            ),
            preconditions=("Approved application record in ApplicationRegistry",),
            postconditions=("Process launched",),
            constraints={"approved_only": True},
            consumes_artifacts=(),
            produces_artifacts=(ArtifactType.APPLICATION,),
            estimated_latency_ms=150,
            requires_confirmation=False,
            side_effects=True,
            risk_level="normal",
        )

        return ToolCapability(
            tool_name="application",
            description="Launches desktop applications",
            category=CapabilityCategory.APPLICATION,
            version="1.0.0",
            intents=(open_app_intent,),
            supported_operations=("open_application",),
        )
