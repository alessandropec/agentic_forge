"""Public entrypoint to run a forge pipeline from a YAML config."""

from pathlib import Path
from typing import Union

from agentic_forge.core.codex import get_forge
from agentic_forge.core.forged import Forged
from agentic_forge.core.refiner import Refiner


def forge(path: Union[str, Path]) -> Forged:
    """Instantiate and execute a forge from a YAML material file.

    Args:
        path: Path to the YAML config containing the ``forge`` name and material fields.

    Returns:
        The forged object produced by the registered forge (e.g., dataset, prompt chain).

    Example:
        >>> forged = forge("dataset.yaml")
        >>> isinstance(forged, Forged)
        True
    """
    data = Refiner.from_yaml(path)

    forge_name = data["forge"]
    ForgeClass = get_forge(forge_name)

    material = ForgeClass.material_cls(**data)

    forge_instance = ForgeClass()
    return forge_instance.forge_from_material(material)
