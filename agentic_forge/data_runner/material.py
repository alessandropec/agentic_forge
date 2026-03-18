"""Material for configuring a data runner."""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import Field, model_validator

from agentic_forge.core.material import Material


class DataRunnerMaterial(Material):
    """
    Declarative config for building a data runner.

    Args:
        dataset: Serialized ``item_dataset`` material (inline or via ref).
        batch_size: Default DataLoader batch size (default: 1).
        num_workers: Default DataLoader workers (default: 0).
        save_path: Destination for periodic saves.
        save_every: Number of processed items between saves; ``None`` disables saving.
        save_format: Output format for saved results (``json`` as a JSON list or ``csv``).
        skip_keys: Keys to skip during processing (default: none).

    Example:
        >>> material = DataRunnerMaterial(
        ...     dataset={\"forge\": \"item_dataset\", \"path\": \"data.json\", \"format\": \"dict\", \"key_field\": \"key\"},
        ...     batch_size=2,
        ...     save_every=10,
        ...     save_path=\"out.json\",
        ...     skip_keys=[\"item_001\"],
        ... )
        >>> material.batch_size
        2
    """

    dataset: Dict[str, Any]
    batch_size: int = 1
    num_workers: int = 0
    save_path: Optional[str] = None
    save_every: Optional[int] = None
    save_format: Literal["json", "csv"] = "json"
    skip_keys: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _validate(self) -> "DataRunnerMaterial":
        """Validate numeric fields and save requirements."""
        if self.batch_size <= 0:
            raise ValueError("batch_size must be > 0")
        if self.num_workers < 0:
            raise ValueError("num_workers must be >= 0")
        if self.save_every is not None:
            if self.save_every <= 0:
                raise ValueError("save_every must be > 0 or None")
            if not self.save_path:
                raise ValueError("save_path is required when save_every is set")
        return self
