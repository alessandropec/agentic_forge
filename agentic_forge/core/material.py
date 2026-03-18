"""Base class for declarative materials."""

from typing import Optional

from pydantic import BaseModel


class Material(BaseModel):
    """Base class for materials (inputs) consumed by forges.

    Attributes:
        ref: Optional relative path used for YAML ref expansion.
        base_dir: Optional base directory of the originating YAML (used for resolving relative assets).
    """

    ref: Optional[str] = None  # Used to inline a referenced sub-configuration from YAML.
    base_dir: Optional[str] = None  # Source YAML directory, used to resolve relative assets.
