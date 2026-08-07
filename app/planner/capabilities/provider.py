"""Abstract base class for capability providers."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.planner.capabilities.models import ToolCapability


class CapabilityProvider(ABC):
    """Provides a ToolCapability instance describing a tool's capabilities."""

    @abstractmethod
    def build(self) -> ToolCapability:
        """Construct and return the immutable ToolCapability metadata."""
        raise NotImplementedError
