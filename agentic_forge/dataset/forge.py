"""Forge for loading JSON datasets into PyTorch-compatible datasets."""

from pathlib import Path

from agentic_forge.core.codex import register_forge
from agentic_forge.core.forge import Forge
from agentic_forge.dataset.forged import ForgedItemDataset
from agentic_forge.dataset.material import ItemDatasetMaterial


@register_forge("item_dataset")
class ItemDatasetForge(Forge):
    """Instantiate ``ForgedItemDataset`` objects from dataset materials."""

    material_cls = ItemDatasetMaterial

    def forge_from_material(self, material: ItemDatasetMaterial) -> ForgedItemDataset:
        """Load a dataset described by ``material``.

        Args:
            material: Material containing path, format, and key-field metadata.

        Returns:
            A ``ForgedItemDataset`` ready for use with PyTorch or preprocessing.

        Example:
            >>> material = ItemDatasetMaterial(path="data/items.json", format="list", key_field="id")
            >>> dataset = ItemDatasetForge().forge_from_material(material)
            >>> len(dataset)
            3
        """
        path = Path(material.path).expanduser()
        if not path.is_absolute() and material.base_dir:
            path = Path(material.base_dir) / path

        return ForgedItemDataset.from_json(
            path=path.resolve(),
            format=material.format,
            key_field=material.key_field,
        )
