"""Forge that composes LLM manager, prompt(s) and schema(s) into chains."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from agentic_forge.chat_prompt.forge import ChatPromptForge
from agentic_forge.chat_prompt.material import ChatPromptMaterial
from agentic_forge.core.codex import register_forge
from agentic_forge.core.forge import Forge
from agentic_forge.llm.forge import LlmManagerForge
from agentic_forge.llm.materials import LlmManagerMaterial
from agentic_forge.structured_output.forge.response_schema import ResponseSchemaForge
from agentic_forge.structured_output.material import (
    ResponseSchemaMaterial,
    StructuredModelMaterial,
)

if TYPE_CHECKING:
    from agentic_forge.structured_output.forged.structured_model import ForgedStructuredModel


@register_forge("structured_model")
class StructuredModelForge(Forge):
    """Compose LLM manager, prompts, and schemas into ready-to-use chains.

    Each prompt must have its aligned schema (1:1).
    """

    material_cls = StructuredModelMaterial

    def forge_from_material(self, material: StructuredModelMaterial) -> "ForgedStructuredModel":
        """Compose LLM manager, prompts, and schemas into a structured model.

        Args:
            material: Declarative config containing manager, model selector, and prompt/schema pairs.

        Returns:
            ForgedStructuredModel ready to invoke chains with structured outputs.

        Example:
            >>> material = StructuredModelMaterial(
            ...     llm_manager={"forge": "llm_manager", "provider": "test"},
            ...     model_selector="default",
            ...     prompt_schema_pairs=[],
            ... )
            >>> forge = StructuredModelForge()
            >>> result = forge.forge_from_material(material)
            >>> hasattr(result, "chains")
            True
        """
        manager_dict = self._strip_forge_key(material.llm_manager)
        manager_material = LlmManagerMaterial(**manager_dict)
        manager = LlmManagerForge().forge_from_material(manager_material)

        model = manager.get_model(material.model_selector)

        prompt_forge = ChatPromptForge()
        schema_forge = ResponseSchemaForge()

        chains: dict[str, object] = {}
        format_instructions: dict[str, str] = {}
        for idx, pair in enumerate(material.prompt_schema_pairs):
            prompt_dict = pair.prompt
            schema_dict = pair.response_schema

            prompt_material = ChatPromptMaterial(**prompt_dict)
            schema_material = ResponseSchemaMaterial(**schema_dict)

            prompt_obj = prompt_forge.forge_from_material(prompt_material)
            schema_obj = schema_forge.forge_from_material(schema_material)

            chain_name = pair.name or prompt_material.name or f"chain_{idx}"
            fmt = schema_obj.get_format_instruction(include_description=True)
            format_instructions[chain_name] = fmt

            # Auto-inject format instructions when the prompt expects them.
            if hasattr(prompt_obj, "input_variables") and "format_instruction" in prompt_obj.input_variables:
                prompt_obj = prompt_obj.partial(format_instruction=fmt)

            chains[chain_name] = prompt_obj | model.with_structured_output(schema_obj.schema)

        from agentic_forge.structured_output.forged.structured_model import ForgedStructuredModel

        return ForgedStructuredModel(model=model, chains=chains, format_instructions=format_instructions)

    def _strip_forge_key(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove 'forge' key if present."""
        if not isinstance(data, dict):
            return data
        return {k: v for k, v in data.items() if k != "forge"}
