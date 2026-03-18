"""Forge implementations for LLM providers and managers (canonical module)."""

from typing import Dict

from agentic_forge.core.codex import register_forge
from agentic_forge.core.forge import Forge
from agentic_forge.llm.forged.manager import ForgedLlmManager
from agentic_forge.llm.forged.provider import ForgedLlmProvider
from agentic_forge.llm.materials import LlmManagerMaterial, LlmProviderMaterial


@register_forge("llm_provider")
class LlmProviderForge(Forge):
    """Forge that builds a single ``ForgedLlmProvider``."""

    material_cls = LlmProviderMaterial

    def forge_from_material(self, material: LlmProviderMaterial) -> ForgedLlmProvider:
        """Instantiate a provider from its material."""
        return ForgedLlmProvider(material)


@register_forge("llm_manager")
class LlmManagerForge(Forge):
    """Forge that aggregates multiple providers into a manager."""

    material_cls = LlmManagerMaterial

    def forge_from_material(self, material: LlmManagerMaterial) -> ForgedLlmManager:
        """Instantiate a manager and all nested providers."""
        providers: Dict[str, ForgedLlmProvider] = {}
        provider_forge = LlmProviderForge()

        for key, provider_dict in material.providers.items():
            pm = LlmProviderMaterial(**provider_dict)
            providers[key] = provider_forge.forge_from_material(pm)

        return ForgedLlmManager(providers)
