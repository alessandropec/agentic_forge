"""Tools domain for YAML-declared tool interfaces backed by Python code."""

try:
    from langgraph.types import Command
except ImportError:  # pragma: no cover - optional dependency for some tool patterns
    class Command:  # type: ignore[override]
        """Fallback placeholder when langgraph is not installed."""

        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

from agentic_forge.tools.forge import ToolForge, ToolsetForge
from agentic_forge.tools.forged import ForgedTool, ForgedToolset
from agentic_forge.tools.materials import (
    ToolArgumentMaterial,
    ToolMaterial,
    ToolResourceMaterial,
    ToolRuntimeMaterial,
    ToolsetMaterial,
)

__all__ = [
    "ToolArgumentMaterial",
    "ToolMaterial",
    "ToolResourceMaterial",
    "ToolRuntimeMaterial",
    "ToolsetMaterial",
    "ForgedTool",
    "ForgedToolset",
    "Command",
    "ToolForge",
    "ToolsetForge",
]
