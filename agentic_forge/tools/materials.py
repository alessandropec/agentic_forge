"""Declarative materials for tool interfaces and tool collections."""

from __future__ import annotations

from typing import Any, Dict, Literal

from pydantic import Field, model_validator

from agentic_forge.core.material import Material

JsonArgumentType = Literal["string", "integer", "number", "boolean", "array", "object"]


class ToolArgumentMaterial(Material):
    """Declarative schema for one tool argument."""

    type: JsonArgumentType = "string"
    description: str
    required: bool | None = None
    default: Any = None
    enum: list[Any] | None = None
    items_type: JsonArgumentType | None = None

    @model_validator(mode="after")
    def normalize_required(self) -> "ToolArgumentMaterial":
        """Infer required-ness from default presence and validate array settings."""
        has_default = "default" in self.model_fields_set

        if self.required is None:
            self.required = not has_default

        if self.required and has_default:
            raise ValueError("A required argument cannot declare a default value.")

        if self.type != "array" and self.items_type is not None:
            raise ValueError("items_type can only be used for array arguments.")

        return self

    @property
    def has_default(self) -> bool:
        """Whether the argument default was explicitly provided in YAML."""
        return "default" in self.model_fields_set

    def to_json_schema(self) -> Dict[str, Any]:
        """Render the argument as a JSON-schema fragment."""
        schema: Dict[str, Any] = {
            "type": self.type,
            "description": self.description,
        }

        if self.enum:
            schema["enum"] = self.enum

        if self.type == "array" and self.items_type is not None:
            schema["items"] = {"type": self.items_type}

        if self.has_default:
            schema["default"] = self.default

        return schema


class ToolRuntimeMaterial(Material):
    """Runtime-only execution settings for a tool."""

    inject_state: bool = False
    resources: Dict[str, str] = Field(default_factory=dict)


class ToolResourceMaterial(Material):
    """Declarative definition of a runtime dependency built once at forge time."""

    factory: str
    kwargs: Dict[str, Any] = Field(default_factory=dict)


class ToolMaterial(Material):
    """Declarative definition of a tool backed by Python code."""

    name: str | None = None
    description: str
    implementation: str
    arguments: Dict[str, ToolArgumentMaterial] = Field(default_factory=dict)
    resources: Dict[str, ToolResourceMaterial] = Field(default_factory=dict)
    defaults: Dict[str, Any] = Field(default_factory=dict)
    allow_additional_args: bool = False
    runtime: ToolRuntimeMaterial = Field(default_factory=ToolRuntimeMaterial)

    @model_validator(mode="after")
    def validate_runtime_bindings(self) -> "ToolMaterial":
        """Ensure runtime-injected kwargs do not collide with user-facing arguments."""
        reserved = set(self.runtime.resources.keys())
        if self.runtime.inject_state:
            reserved.add("state")

        collisions = reserved.intersection(self.arguments.keys())
        if collisions:
            raise ValueError(
                "Runtime-injected argument names cannot overlap user arguments: "
                f"{sorted(collisions)}"
            )

        return self


class ToolsetMaterial(Material):
    """Collection of tool configs assembled into a runtime registry."""

    resources: Dict[str, ToolResourceMaterial] = Field(default_factory=dict)
    tools: Dict[str, dict]
