"""Forge that builds Pydantic schemas from declarative materials."""

from __future__ import annotations

from typing import Annotated, Any, List, Tuple

from pydantic import BaseModel, Field, create_model

from agentic_forge.core.codex import register_forge
from agentic_forge.core.forge import Forge
from agentic_forge.structured_output.forged.response_schema import ForgedResponseSchema
from agentic_forge.structured_output.material import (
    EnumSchemaField,
    ListSchemaField,
    ObjectSchemaField,
    PrimitiveKind,
    PrimitiveSchemaField,
    ResponseSchemaMaterial,
    SchemaField,
)


@register_forge("response_schema")
class ResponseSchemaForge(Forge):
    """Turn declarative schema materials into dynamic Pydantic models."""

    material_cls = ResponseSchemaMaterial

    def forge_from_material(self, material: ResponseSchemaMaterial) -> ForgedResponseSchema:
        """Create a forged response schema from the provided material.

        Args:
            material: Declarative schema material.

        Returns:
            ``ForgedResponseSchema`` holding the generated Pydantic model and helper methods.

        Example:
            >>> field = PrimitiveSchemaField(name="text", description="body", type="str")
            >>> material = ResponseSchemaMaterial(name="Doc", fields=[field])
            >>> forged = ResponseSchemaForge().forge_from_material(material)
            >>> forged.schema.__name__
            'Doc'
        """
        model = self._build_model(material.name, material.fields)
        return ForgedResponseSchema(schema=model, fields=material.fields)

    def _build_model(self, name: str, fields: List[SchemaField]) -> type[BaseModel]:
        """Create a Pydantic model from schema fields."""
        annotations: dict[str, Tuple[type, Any]] = {}
        for field in fields:
            ann, default = self._field_to_annotation(field, parent_name=name)
            annotations[field.name] = (ann, Field(default=default, description=field.description))

        return create_model(name, **annotations)  # type: ignore[arg-type]

    def _field_to_annotation(
        self, field: SchemaField, parent_name: str
    ) -> Tuple[type, Any]:
        """Map a schema field to (annotation, default) pair for create_model."""
        required = getattr(field, "required", True)
        optional_default = None if not required else ...

        if isinstance(field, PrimitiveSchemaField):
            mapping: dict[PrimitiveKind, type] = {
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
            }
            ann = mapping[field.type]
            if not required:
                from typing import Optional as TypingOptional

                ann = TypingOptional[ann]  # type: ignore
            return ann, optional_default

        if isinstance(field, EnumSchemaField):
            from typing import Literal as TypingLiteral
            from typing import Optional as TypingOptional

            literal_type = TypingLiteral.__getitem__(tuple(field.choices))
            if not required:
                literal_type = TypingOptional[literal_type]  # type: ignore
            return literal_type, optional_default

        if isinstance(field, ObjectSchemaField):
            nested_name = f"{parent_name}_{field.name}".title().replace(" ", "")
            nested_model = self._build_model(nested_name, field.fields)
            ann = nested_model
            if not required:
                from typing import Optional as TypingOptional

                ann = TypingOptional[ann]  # type: ignore
            return ann, optional_default

        if isinstance(field, ListSchemaField):
            from typing import List as TypingList

            item_ann, _ = self._field_to_annotation(field.items, parent_name=parent_name)
            ann = TypingList[Annotated[item_ann, Field(description=field.items.description)]]
            if not required:
                from typing import Optional as TypingOptional

                ann = TypingOptional[ann]  # type: ignore
            return ann, optional_default

        raise ValueError(f"Unsupported field type: {getattr(field, 'type', 'unknown')}")
