"""Base Forge class handling common material loading and instantiation."""

from pathlib import Path
from typing import Type, Union

from agentic_forge.core.forged import Forged
from agentic_forge.core.material import Material
from agentic_forge.core.refiner import Refiner

MaterialOrPath = Union[Material, str, Path]


class Forge:
    """Abstract forge that creates ``Forged`` objects from ``Material`` data."""

    material_cls: Type[Material] = Material

    def forge(self, material_or_path: MaterialOrPath) -> Forged:
        """Load/refine a material (if needed) and forge it.

        Args:
            material_or_path: Material instance or path to a YAML material file.

        Returns:
            A ``Forged`` runtime object produced by ``forge_from_material``.
        """
        if isinstance(material_or_path, Material):
            material = material_or_path
        else:
            raw = Refiner.from_yaml(material_or_path)
            material = self.material_cls(**raw)

        return self.forge_from_material(material)

    def forge_from_material(self, material: Material) -> Forged:
        """Implement the concrete forging logic."""
        raise NotImplementedError
