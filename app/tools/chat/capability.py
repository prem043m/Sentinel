"""Capability provider for conversational chat handling."""

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


class ChatCapabilityProvider(CapabilityProvider):
    """Exposes capability metadata for conversational LLM chat."""

    def build(self) -> ToolCapability:
        chat_intent = IntentCapability(
            id="ai.chat",
            name="chat",
            description="Handles general chat and conversation",
            tool_name="llm",
            category=CapabilityCategory.AI,
            version="1.0.0",
            priority=50,
            preferred=True,
            tags=("chat", "llm", "conversation", "qa"),
            parameters=(
                ParameterDefinition(
                    name="prompt",
                    type=ParameterType.STRING,
                    description="entire user message to send to the chat model",
                    required=True,
                ),
            ),
            examples=ExampleDataset(
                examples=(
                    ExampleCommand(
                        user_input="What is the capital of France?",
                        expected_intent="chat",
                        expected_tool="llm",
                        expected_parameters={"prompt": "What is the capital of France?"},
                    ),
                    ExampleCommand(
                        user_input="Hello, how are you?",
                        expected_intent="chat",
                        expected_tool="llm",
                        expected_parameters={"prompt": "Hello, how are you?"},
                    ),
                )
            ),
            preconditions=("Active LLM API connection",),
            postconditions=("Conversational answer generated",),
            constraints={},
            consumes_artifacts=(),
            produces_artifacts=(ArtifactType.CHAT,),
            estimated_latency_ms=1000,
            requires_confirmation=False,
            side_effects=False,
            risk_level="normal",
        )

        return ToolCapability(
            tool_name="llm",
            description="Handles general chat and conversation",
            category=CapabilityCategory.AI,
            version="1.0.0",
            intents=(chat_intent,),
            supported_operations=("chat",),
        )
