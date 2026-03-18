"""Runtime wrapper for a single declarative tool."""

from __future__ import annotations

from inspect import Signature, isawaitable, signature
import re
from typing import Any

from pydantic import ConfigDict, Field, ValidationError, create_model

from agentic_forge.core.forged import Forged
from agentic_forge.tools.loaders import load_callable
from agentic_forge.tools.materials import JsonArgumentType, ToolArgumentMaterial, ToolMaterial
_CLASS_NAME_CLEANER = re.compile(r"[^0-9a-zA-Z]+")
_PYTHON_ANNOTATION_MAP: dict[JsonArgumentType, Any] = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "array": list[Any],
    "object": dict[str, Any],
}
_PYTHON_RUNTIME_TYPE_MAP: dict[JsonArgumentType, Any] = {
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "array": list,
    "object": dict,
}


class ForgedTool(Forged):
    """Runtime tool object with schema export and callable invocation."""

    def __init__(self, material: ToolMaterial, resources: dict[str, Any] | None = None) -> None:
        if not material.name:
            raise ValueError("ToolMaterial.name is required to forge a runtime tool.")

        self.material = material
        self.name = material.name
        self.description = material.description
        self.arguments = material.arguments
        self.defaults = dict(material.defaults)
        self.resources = dict(resources or {})
        self.allow_additional_args = material.allow_additional_args
        self.runtime = material.runtime

        self._callable = load_callable(material.implementation, base_dir=material.base_dir)
        self._signature = signature(self._callable)
        self._input_model = self._build_input_model()
        self._validate_available_resources()
        self._validate_runtime_signature()

    def parameters_schema(self) -> dict[str, Any]:
        """Return the JSON schema used by OpenAI-style tool calling."""
        required_fields = [
            field_name
            for field_name, field_material in self.arguments.items()
            if field_material.required
        ]
        properties = {
            field_name: field_material.to_json_schema()
            for field_name, field_material in self.arguments.items()
        }

        schema: dict[str, Any] = {
            "type": "object",
            "properties": properties,
            "additionalProperties": self.allow_additional_args,
        }

        if required_fields:
            schema["required"] = required_fields

        return schema

    def to_openai_tool(self) -> dict[str, Any]:
        """Render this runtime tool as an OpenAI-compatible function tool."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema(),
            },
        }

    def describe(self) -> dict[str, Any]:
        """Return the declarative metadata useful for registries or debugging."""
        return {
            "name": self.name,
            "description": self.description,
            "implementation": self.material.implementation,
            "defaults": dict(self.defaults),
            "runtime": {
                "inject_state": self.runtime.inject_state,
                "resources": dict(self.runtime.resources),
            },
            "parameters": self.parameters_schema(),
        }

    def validate_arguments(
        self, arguments: dict[str, Any] | None = None, /, **kwargs: Any
    ) -> dict[str, Any]:
        """Validate a tool-call payload against the YAML-defined argument schema."""
        payload = dict(arguments or {})
        payload.update(kwargs)

        try:
            validated = self._input_model.model_validate(payload)
        except ValidationError as exc:
            raise ValueError(f"Invalid arguments for tool '{self.name}': {exc}") from exc

        result: dict[str, Any] = {}
        for argument_name, argument_material in self.arguments.items():
            if argument_name in payload or argument_material.has_default:
                result[argument_name] = getattr(validated, argument_name)

        if self.allow_additional_args and validated.model_extra:
            result.update(validated.model_extra)

        self._validate_declared_constraints(result)
        return result

    def invoke(
        self,
        arguments: dict[str, Any] | None = None,
        /,
        *,
        state: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Invoke the underlying callable with validated inputs and base defaults."""
        validated = self.validate_arguments(arguments, **kwargs)
        call_args = self._build_call_args(validated, state=state)
        result = self._callable(**call_args)

        if isawaitable(result):
            raise TypeError(
                f"Tool '{self.name}' returned an awaitable. Use 'ainvoke' for async tools."
            )

        return result

    async def ainvoke(
        self,
        arguments: dict[str, Any] | None = None,
        /,
        *,
        state: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Async invocation helper that supports both sync and async callables."""
        validated = self.validate_arguments(arguments, **kwargs)
        call_args = self._build_call_args(validated, state=state)
        result = self._callable(**call_args)

        if isawaitable(result):
            return await result

        return result

    def _build_input_model(self) -> type[Any]:
        """Construct a Pydantic model from the declarative tool-argument definitions."""
        model_name = _build_model_name(self.name)
        field_definitions: dict[str, tuple[Any, Any]] = {}

        for argument_name, argument_material in self.arguments.items():
            annotation = _annotation_for_argument(argument_material)
            field_default = _field_default_for_argument(argument_material)
            json_schema_extra = {"enum": argument_material.enum} if argument_material.enum else None

            field_definitions[argument_name] = (
                annotation,
                Field(
                    field_default,
                    description=argument_material.description,
                    json_schema_extra=json_schema_extra,
                ),
            )

        return create_model(
            model_name,
            __config__=ConfigDict(
                extra="allow" if self.allow_additional_args else "forbid"
            ),
            **field_definitions,
        )

    def _build_call_args(
        self,
        validated: dict[str, Any],
        *,
        state: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Merge declarative args, defaults, and runtime injections."""
        call_args = {**self.defaults, **validated}

        if self.runtime.inject_state:
            call_args["state"] = dict(state or {})

        for argument_name, resource_name in self.runtime.resources.items():
            call_args[argument_name] = self.resources[resource_name]

        return call_args

    def _validate_available_resources(self) -> None:
        """Ensure every declared runtime resource is available at forge time."""
        missing = [
            resource_name
            for resource_name in self.runtime.resources.values()
            if resource_name not in self.resources
        ]
        if missing:
            raise ValueError(
                f"Tool '{self.name}' requires unknown resources: {sorted(set(missing))}"
            )

    def _validate_runtime_signature(self) -> None:
        """Check that the implementation signature matches the declared runtime contract."""
        if self.runtime.inject_state and not _accepts_keyword(self._signature, "state"):
            raise ValueError(
                f"Tool '{self.name}' declares runtime.inject_state=true but its implementation "
                "does not accept a 'state' keyword argument."
            )

        missing_parameters = [
            argument_name
            for argument_name in self.runtime.resources.keys()
            if not _accepts_keyword(self._signature, argument_name)
        ]
        if missing_parameters:
            raise ValueError(
                f"Tool '{self.name}' declares runtime resources for parameters "
                f"{sorted(missing_parameters)} but its implementation does not accept them."
            )

    def _validate_declared_constraints(self, values: dict[str, Any]) -> None:
        """Enforce enum and array-item constraints not covered by the dynamic model."""
        for argument_name, argument_material in self.arguments.items():
            if argument_name not in values:
                continue

            value = values[argument_name]
            if value is None:
                continue

            if argument_material.enum and value not in argument_material.enum:
                raise ValueError(
                    f"Argument '{argument_name}' for tool '{self.name}' must be one of "
                    f"{argument_material.enum!r}."
                )

            if (
                argument_material.type == "array"
                and argument_material.items_type is not None
                and isinstance(value, list)
            ):
                _validate_array_item_types(
                    tool_name=self.name,
                    argument_name=argument_name,
                    items=value,
                    expected_type=argument_material.items_type,
                )


def _build_model_name(tool_name: str) -> str:
    """Generate a safe dynamic model name from the tool name."""
    cleaned = _CLASS_NAME_CLEANER.sub("_", tool_name).strip("_") or "Tool"
    if cleaned[0].isdigit():
        cleaned = f"Tool_{cleaned}"
    return f"{cleaned}Input"


def _annotation_for_argument(argument: ToolArgumentMaterial) -> Any:
    """Map a declarative argument spec into a Python type annotation."""
    if argument.type == "array" and argument.items_type is not None:
        annotation: Any = list[_PYTHON_ANNOTATION_MAP[argument.items_type]]
    else:
        annotation = _PYTHON_ANNOTATION_MAP[argument.type]

    if not argument.required or (argument.has_default and argument.default is None):
        return annotation | None

    return annotation


def _field_default_for_argument(argument: ToolArgumentMaterial) -> Any:
    """Compute the default marker used when building the dynamic input model."""
    if argument.required:
        return ...
    if argument.has_default:
        return argument.default
    return None


def _validate_array_item_types(
    *,
    tool_name: str,
    argument_name: str,
    items: list[Any],
    expected_type: JsonArgumentType,
) -> None:
    """Validate array item types declared in YAML."""
    python_type = _PYTHON_RUNTIME_TYPE_MAP[expected_type]

    for index, item in enumerate(items):
        if item is None:
            continue
        if not isinstance(item, python_type):
            raise ValueError(
                f"Argument '{argument_name}' for tool '{tool_name}' expects '{expected_type}' "
                f"items, but item {index} is {type(item).__name__}."
            )


def _accepts_keyword(call_signature: Signature, argument_name: str) -> bool:
    """Whether a callable can receive a given argument as keyword."""
    for parameter in call_signature.parameters.values():
        if parameter.kind == parameter.VAR_KEYWORD:
            return True
        if parameter.name == argument_name and parameter.kind in {
            parameter.POSITIONAL_OR_KEYWORD,
            parameter.KEYWORD_ONLY,
        }:
            return True
    return False
