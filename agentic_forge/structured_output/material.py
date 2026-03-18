"""Schema materials for structured outputs."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Union

PrimitiveKind = Literal["str", "int", "float", "bool"]
EnumKind = Literal["enum"]
ObjectKind = Literal["obj"]
ListKind = Literal["list"]

from pydantic import BaseModel, ConfigDict, Field, model_validator

from agentic_forge.core.material import Material


class BaseSchemaField(BaseModel):
    """Common attributes for any field in the response schema."""

    name: str
    description: str
    required: bool = True


class PrimitiveSchemaField(BaseSchemaField):
    """Primitive field description."""

    type: PrimitiveKind


class EnumSchemaField(BaseSchemaField):
    """Enumeration field description."""

    type: EnumKind
    choices: List[str] = Field(..., min_items=1)


class ObjectSchemaField(BaseSchemaField):
    """Nested object field description."""

    type: ObjectKind
    fields: List["SchemaField"] = Field(default_factory=list)


class ListSchemaField(BaseSchemaField):
    """List field description."""

    type: ListKind
    items: "SchemaField"

    @model_validator(mode="after")
    def _validate_items(cls, model: "ListSchemaField") -> "ListSchemaField":
        """Ensure list fields declare their item schema."""
        if model.items is None:
            raise ValueError("List fields require an 'items' definition")
        return model


SchemaField = Union[
    PrimitiveSchemaField,
    EnumSchemaField,
    ObjectSchemaField,
    ListSchemaField,
]


class ResponseSchemaMaterial(Material):
    """
    Declarative description of a structured output schema to be forged into a Pydantic model.

    Args:
        name: Name of the generated Pydantic model.
        fields: List of schema field definitions.

    Example:
        >>> field = PrimitiveSchemaField(name="text", description="content", type="str")
        >>> material = ResponseSchemaMaterial(name="MySchema", fields=[field])
        >>> material.name
        'MySchema'
    """

    name: str
    fields: List[SchemaField]


# Forward refs for pydantic
ObjectSchemaField.model_rebuild()
ListSchemaField.model_rebuild()


class PromptSchemaPair(BaseModel):
    """
    Pairing between a prompt config and its exact response schema.

    Args:
        name: Optional identifier for the chain.
        prompt: Serialized prompt configuration.
        response_schema: Serialized schema configuration, loaded from the YAML key `schema`.
    """

    model_config = ConfigDict(populate_by_name=True)

    name: Optional[str] = None
    prompt: Dict[str, Any]
    response_schema: Dict[str, Any] = Field(alias="schema")


class StructuredModelMaterial(Material):
    """
    Declarative config to forge a model + prompt/schema chains.

    Args:
        llm_manager: Serialized manager configuration (may include forge key to strip).
        model_selector: Identifier used to pick a model from the manager.
        prompt_schema_pairs: Pairings of prompts and schemas to compose chains.

    Example:
        >>> material = StructuredModelMaterial(
        ...     llm_manager={"forge": "llm_manager", "provider": "test"},
        ...     model_selector="default",
        ...     prompt_schema_pairs=[],
        ... )
        >>> material.model_selector
        'default'
    """

    llm_manager: Dict[str, Any]
    model_selector: str
    prompt_schema_pairs: List[PromptSchemaPair]
