"""Dynamic capability discovery and loading."""

from __future__ import annotations

import importlib
import inspect
import logging
import pkgutil
from typing import Iterable

from app.planner.capabilities.provider import CapabilityProvider
from app.planner.capabilities.registry import CapabilityRegistry

logger = logging.getLogger("SentinelAI.CapabilityLoader")


class CapabilityLoader:
    """Discovers and populates a CapabilityRegistry from tool capability modules."""

    def load_providers(self, providers: Iterable[CapabilityProvider]) -> CapabilityRegistry:
        """Construct a CapabilityRegistry from an explicit list of providers."""
        registry = CapabilityRegistry()
        for provider in providers:
            registry.register(provider.build())
        return registry

    def discover_and_load(self, package_name: str = "app.tools") -> CapabilityRegistry:
        """Scan a Python package for capability modules and populate a CapabilityRegistry.

        Looks for subpackages in `app.tools` containing a `capability` module
        and instantiates any `CapabilityProvider` classes found within them.
        """
        registry = CapabilityRegistry()
        providers = self.discover_providers(package_name)
        for provider in providers:
            registry.register(provider.build())
        return registry

    def discover_providers(self, package_name: str = "app.tools") -> tuple[CapabilityProvider, ...]:
        """Discover capability providers by dynamically inspecting tool packages."""
        providers: list[CapabilityProvider] = []

        try:
            package = importlib.import_module(package_name)
        except ImportError as exc:
            logger.warning("Could not import package '%s' for discovery: %s", package_name, exc)
            return ()

        if not hasattr(package, "__path__"):
            return ()

        for _, subname, ispkg in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
            if not ispkg:
                continue

            capability_module_name = f"{subname}.capability"
            try:
                module = importlib.import_module(capability_module_name)
            except ImportError:
                continue

            for _, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, CapabilityProvider) and obj is not CapabilityProvider:
                    try:
                        instance = obj()
                        providers.append(instance)
                        logger.debug("Discovered CapabilityProvider: %s", obj.__name__)
                    except Exception as exc:
                        logger.warning("Failed to instantiate CapabilityProvider %s: %s", obj.__name__, exc)

        return tuple(providers)
