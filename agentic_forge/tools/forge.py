"""Forge implementations for declarative tools and tool collections."""

from __future__ import annotations

from typing import Dict

from agentic_forge.core.codex import register_forge
from agentic_forge.core.forge import Forge
from agentic_forge.tools.forged import ForgedTool, ForgedToolset
from agentic_forge.tools.materials import ToolMaterial, ToolsetMaterial
from agentic_forge.tools.resources import build_resources


@register_forge("tool")
class ToolForge(Forge):
    """Forge that builds one runtime tool from a YAML interface."""

    material_cls = ToolMaterial

    def __init__(self, base_resources: Dict[str, object] | None = None) -> None:
        self.base_resources = dict(base_resources or {})

    def forge_from_material(self, material: ToolMaterial) -> ForgedTool:
        """Instantiate a single tool wrapper around a Python callable."""
        if not material.name:
            raise ValueError("Single-tool configs must declare a tool name.")

        local_resources = build_resources(material.resources, base_dir=material.base_dir)
        duplicate_resources = self.base_resources.keys() & local_resources.keys()
        if duplicate_resources:
            raise ValueError(
                f"Tool '{material.name}' defines local resources that collide with shared "
                f"resources: {sorted(duplicate_resources)}"
            )

        all_resources = {**self.base_resources, **local_resources}
        return ForgedTool(material, resources=all_resources)


@register_forge("toolset")
class ToolsetForge(Forge):
    """Forge that aggregates multiple tools into one runtime registry."""

    material_cls = ToolsetMaterial

    def forge_from_material(self, material: ToolsetMaterial) -> ForgedToolset:
        """Instantiate a toolset and all nested tools."""
        tools: Dict[str, ForgedTool] = {}
        shared_resources = build_resources(material.resources, base_dir=material.base_dir)
        tool_forge = ToolForge(base_resources=shared_resources)

        for fallback_name, tool_dict in material.tools.items():
            tool_data = dict(tool_dict)
            tool_data.setdefault("name", fallback_name)
            tool_data.setdefault("base_dir", material.base_dir)

            tool_material = ToolMaterial(**tool_data)
            forged_tool = tool_forge.forge_from_material(tool_material)

            if forged_tool.name in tools:
                raise ValueError(f"Duplicate tool name detected: '{forged_tool.name}'")

            tools[forged_tool.name] = forged_tool

        return ForgedToolset(tools)
