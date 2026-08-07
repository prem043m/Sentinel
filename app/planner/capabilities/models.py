"""Immutable data models for the capability framework."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from app.artifacts.types import ArtifactType


class ParameterType(str, Enum):
    """Supported parameter types for capability definitions."""

    STRING = "string"
    BOOLEAN = "boolean"
    PATH = "path"
    URL = "url"
    INTEGER = "integer"
    FLOAT = "float"
    LIST = "list"
    ENUM = "enum"


class CapabilityCategory(str, Enum):
    """Functional categories for grouping tools and capabilities."""

    SYSTEM = "system"
    FILESYSTEM = "filesystem"
    BROWSER = "browser"
    APPLICATION = "application"
    NETWORK = "network"
    AI = "ai"
    UTILITY = "utility"
    MEDIA = "media"


@dataclass(frozen=True, slots=True)
class ParameterDefinition:
    """Definition of a single parameter required or accepted by an intent."""

    name: str
    type: ParameterType
    description: str
    required: bool = True
    default: Any | None = None
    allowed_values: tuple[Any, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("ParameterDefinition name must not be empty.")
        object.__setattr__(self, "allowed_values", tuple(self.allowed_values))


@dataclass(frozen=True, slots=True)
class ExampleCommand:
    """An example natural language command and its expected intent plan."""

    user_input: str
    expected_intent: str
    expected_tool: str
    expected_parameters: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.user_input.strip():
            raise ValueError("ExampleCommand user_input must not be empty.")
        object.__setattr__(self, "expected_parameters", MappingProxyType(dict(self.expected_parameters)))


@dataclass(frozen=True, slots=True)
class ExampleDataset:
    """Independent collection of example commands for a capability."""

    examples: tuple[ExampleCommand, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(self, "examples", tuple(self.examples))


@dataclass(frozen=True, slots=True)
class IntentCapability:
    """Capability specification for a specific intent/action."""

    id: str
    name: str
    description: str
    tool_name: str
    category: CapabilityCategory
    version: str = "1.0.0"
    priority: int = 100
    preferred: bool = False
    tags: tuple[str, ...] = field(default_factory=tuple)
    parameters: tuple[ParameterDefinition, ...] = field(default_factory=tuple)
    examples: ExampleDataset = field(default_factory=ExampleDataset)
    preconditions: tuple[str, ...] = field(default_factory=tuple)
    postconditions: tuple[str, ...] = field(default_factory=tuple)
    constraints: Mapping[str, Any] = field(default_factory=dict)
    consumes_artifacts: tuple[ArtifactType, ...] = field(default_factory=tuple)
    produces_artifacts: tuple[ArtifactType, ...] = field(default_factory=tuple)
    estimated_latency_ms: int = 100
    requires_confirmation: bool = False
    side_effects: bool = False
    risk_level: str = "normal"

    def __post_init__(self) -> None:
        if not self.id.strip():
            raise ValueError("IntentCapability id must not be empty.")
        if not self.name.strip():
            raise ValueError("IntentCapability name must not be empty.")
        if not self.tool_name.strip():
            raise ValueError("IntentCapability tool_name must not be empty.")

        object.__setattr__(self, "tags", tuple(dict.fromkeys(tag.strip().lower() for tag in self.tags if tag.strip())))
        object.__setattr__(self, "parameters", tuple(self.parameters))
        object.__setattr__(self, "preconditions", tuple(self.preconditions))
        object.__setattr__(self, "postconditions", tuple(self.postconditions))
        object.__setattr__(self, "constraints", MappingProxyType(dict(self.constraints)))
        object.__setattr__(self, "consumes_artifacts", tuple(self.consumes_artifacts))
        object.__setattr__(self, "produces_artifacts", tuple(self.produces_artifacts))


@dataclass(frozen=True, slots=True)
class ToolCapability:
    """Capability specification for an entire tool."""

    tool_name: str
    description: str
    category: CapabilityCategory
    version: str = "1.0.0"
    intents: tuple[IntentCapability, ...] = field(default_factory=tuple)
    supported_operations: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.tool_name.strip():
            raise ValueError("ToolCapability tool_name must not be empty.")
        object.__setattr__(self, "intents", tuple(self.intents))
        object.__setattr__(self, "supported_operations", tuple(self.supported_operations))
