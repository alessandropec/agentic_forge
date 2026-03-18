"""Declarative configuration for dataset forging."""

from __future__ import annotations

from typing import Literal, Optional

FormatType = Literal["dict", "list"]

from pydantic import model_validator

from agentic_forge.core.material import Material


class ItemDatasetMaterial(Material):
    """
    Declarative dataset config used by the dataset forge.

    Args:
        path: Filesystem path to the dataset JSON file.
        format: Serialization format, either ``"list"`` (list of objects) or ``"dict"`` (mapping id->object).
        key_field: Field name that uniquely identifies each item when ``format`` is ``"list"``.

    Example:
        >>> material = ItemDatasetMaterial(path="data/items.json", format="list", key_field="id")
        >>> material.format
        'list'
    """

    path: str
    format: FormatType = "list"
    key_field: Optional[str] = None

    @model_validator(mode="after")
    def _validate_key_field(self) -> "ItemDatasetMaterial":
        """Ensure ``key_field`` is provided when the dataset is stored as a list."""
        if self.format == "list" and not self.key_field:
            raise ValueError("key_field is required when format='list'")
        return self
