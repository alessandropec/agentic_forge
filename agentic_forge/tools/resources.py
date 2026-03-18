"""Runtime resource builders for tool dependencies."""

from __future__ import annotations

from inspect import isawaitable
from typing import Any, Dict

from agentic_forge.tools.loaders import load_callable
from agentic_forge.tools.materials import ToolResourceMaterial


def build_resources(
    resources: Dict[str, ToolResourceMaterial],
    *,
    base_dir: str | None = None,
) -> Dict[str, Any]:
    """Instantiate a set of named resources from declarative factory definitions."""
    built: Dict[str, Any] = {}

    for name, material in resources.items():
        factory = load_callable(material.factory, base_dir=material.base_dir or base_dir)
        instance = factory(**material.kwargs)

        if isawaitable(instance):
            raise TypeError(
                f"Resource factory '{material.factory}' for resource '{name}' returned an "
                "awaitable. Async resource factories are not supported yet."
            )

        built[name] = instance

    return built
