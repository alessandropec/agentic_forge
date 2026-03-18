"""Forged schema utilities for structured outputs."""

from __future__ import annotations

import json
from typing import Any, List, Optional, Type

from pydantic import BaseModel

from agentic_forge.core.forged import Forged
from agentic_forge.structured_output.material import (
    EnumSchemaField,
    ListSchemaField,
    ObjectSchemaField,
    PrimitiveSchemaField,
    SchemaField,
)


class ForgedResponseSchema(Forged):
    """Carry the generated Pydantic model plus format instruction rendering."""

    def __init__(
        self,
        schema: Type[BaseModel],
        fields: List[SchemaField],
        default_template: str = "{format_instruction}",
    ) -> None:
        """Initialize a forged response schema.

        Args:
            schema: Generated Pydantic model.
            fields: Declarative field definitions.
            default_template: Template used when rendering format instructions.
        """
        self.schema = schema
        self._fields = fields
        self._template = default_template
        self._cache: dict[tuple[bool, str], str] = {}

    def get_format_instruction(
        self, include_description: bool = False, template: Optional[str] = None
    ) -> str:
        """Render the format instruction (cached).

        Args:
            include_description: Whether to include inline descriptions.
            template: Optional template overriding the default.

        Returns:
            Rendered format instruction string.

        Example:
            >>> from pydantic import BaseModel
            >>> from agentic_forge.structured_output.material import PrimitiveSchemaField
            >>> class Doc(BaseModel):
            ...     text: str
            >>> field = PrimitiveSchemaField(name="text", description="body", type="str")
            >>> forged = ForgedResponseSchema(schema=Doc, fields=[field])
            >>> isinstance(forged.get_format_instruction(), str)
            True
        """
        active_template = template or self._template
        cache_key = (include_description, active_template)
        if cache_key in self._cache:
            return self._cache[cache_key]

        payload = self._build_format_instruction(include_description=include_description)
        rendered = active_template.format(format_instruction=payload)
        self._cache[cache_key] = rendered
        return rendered

    def _build_format_instruction(self, include_description: bool) -> str:
        if include_description:
            # Render with inline comments on object/list openings so parent descriptions are visible.
            lines = self._render_fields_with_comments(self._fields, indent_level=0, include_description=True)
            return "\n".join(lines)

        example_obj = self._example_object(self._fields, include_description=include_description)
        return json.dumps(example_obj, indent=2, ensure_ascii=False)

    def _example_object(
        self, fields: List[SchemaField], include_description: bool
    ) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for field in fields:
            result[field.name] = self._example_value(field, include_description=include_description)
        return result

    def _placeholder(
        self,
        type_hint: str,
        required: bool,
        description: str,
        include_description: bool,
        extra: str = "",
    ) -> str:
        optional_suffix = " (optional)" if not required else ""
        extra_suffix = f" {extra}".strip()
        extra_suffix = f" {extra_suffix}" if extra_suffix else ""
        desc_suffix = ""
        if include_description and description:
            desc_suffix = f" // {description}"
        return f"<{type_hint}{optional_suffix}{extra_suffix}>{desc_suffix}"

    def _example_value(self, field: SchemaField, include_description: bool) -> Any:

        required = getattr(field, "required", True)
        description = getattr(field, "description", "")

        if isinstance(field, PrimitiveSchemaField):
            hint_map = {
                "str": "string",
                "int": "integer",
                "float": "float",
                "bool": "boolean",
            }
            return self._placeholder(
                hint_map[field.type],
                required,
                description,
                include_description,
                extra="value",
            )

        if isinstance(field, EnumSchemaField):
            extra = f"one of {', '.join(field.choices)}"
            return self._placeholder("enum", required, description, include_description, extra=extra)

        if isinstance(field, ObjectSchemaField):
            return self._example_object(field.fields, include_description=include_description)

        if isinstance(field, ListSchemaField):
            # Represent a list with a single exemplar element (which can itself be list/object)
            return [
                self._example_value(field.items, include_description=include_description)
            ]

        raise ValueError(f"Unsupported field type: {getattr(field, 'type', 'unknown')}")

    def _render_fields_with_comments(
        self, fields: List[SchemaField], indent_level: int, include_description: bool
    ) -> List[str]:
        indent = "  " * indent_level
        lines = [f"{indent}{{"]
        for idx, field in enumerate(fields):
            field_lines = self._render_field_with_comments(
                field, indent_level + 1, include_description=include_description
            )
            if idx < len(fields) - 1:
                field_lines[-1] += ","
            lines.extend(field_lines)
        lines.append(f"{indent}}}")
        return lines

    def _render_field_with_comments(
        self, field: SchemaField, indent_level: int, include_description: bool
    ) -> List[str]:
        indent = "  " * indent_level
        required = getattr(field, "required", True)
        description = getattr(field, "description", "")
        comment = self._comment_suffix(description, required, include_description)

        if isinstance(field, (PrimitiveSchemaField, EnumSchemaField)):
            value = json.dumps(self._example_value(field, include_description=True), ensure_ascii=False)
            return [f'{indent}"{field.name}": {value}']

        if isinstance(field, ObjectSchemaField):
            lines = [f'{indent}"{field.name}": {{' + comment]
            for idx, child in enumerate(field.fields):
                child_lines = self._render_field_with_comments(
                    child, indent_level + 1, include_description=include_description
                )
                if idx < len(field.fields) - 1:
                    child_lines[-1] += ","
                lines.extend(child_lines)
            lines.append(f"{indent}}}")
            return lines

        if isinstance(field, ListSchemaField):
            lines = [f'{indent}"{field.name}": [' + comment]
            item_lines = self._render_list_item_with_comments(
                field.items, indent_level + 1, include_description=include_description
            )
            lines.extend(item_lines)
            lines.append(f"{indent}]")
            return lines

        raise ValueError(f"Unsupported field type: {getattr(field, 'type', 'unknown')}")

    def _render_list_item_with_comments(
        self, item_field: SchemaField, indent_level: int, include_description: bool
    ) -> List[str]:
        indent = "  " * indent_level
        if isinstance(item_field, (PrimitiveSchemaField, EnumSchemaField)):
            value = json.dumps(
                self._example_value(item_field, include_description=True),
                ensure_ascii=False,
            )
            return [f"{indent}{value}"]

        if isinstance(item_field, ObjectSchemaField):
            required = getattr(item_field, "required", True)
            description = getattr(item_field, "description", "")
            comment = self._comment_suffix(description, required, include_description)
            lines = [f"{indent}{{" + comment]
            for idx, child in enumerate(item_field.fields):
                child_lines = self._render_field_with_comments(
                    child, indent_level + 1, include_description=include_description
                )
                if idx < len(item_field.fields) - 1:
                    child_lines[-1] += ","
                lines.extend(child_lines)
            lines.append(f"{indent}}}")
            return lines

        if isinstance(item_field, ListSchemaField):
            required = getattr(item_field, "required", True)
            description = getattr(item_field, "description", "")
            comment = self._comment_suffix(description, required, include_description)
            lines = [f"{indent}[" + comment]
            lines.extend(
                self._render_list_item_with_comments(
                    item_field.items, indent_level + 1, include_description=include_description
                )
            )
            lines.append(f"{indent}]")
            return lines

        raise ValueError(f"Unsupported list item type: {getattr(item_field, 'type', 'unknown')}")

    def _comment_suffix(self, description: str, required: bool, include_description: bool) -> str:
        if not include_description:
            return ""
        parts: List[str] = []
        if description:
            parts.append(description)
        if not required:
            parts.append("(optional)")
        if not parts:
            return ""
        return " // " + " ".join(parts)
