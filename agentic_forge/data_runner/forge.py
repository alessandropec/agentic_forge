"""Forge that builds a ``ForgedDataRunner`` from its material."""

from typing import Any, Dict

from agentic_forge.core.codex import register_forge
from agentic_forge.core.forge import Forge
from agentic_forge.data_runner.forged import ForgedDataRunner
from agentic_forge.data_runner.material import DataRunnerMaterial
from agentic_forge.dataset.forge import ItemDatasetForge
from agentic_forge.dataset.material import ItemDatasetMaterial


@register_forge("data_runner")
class DataRunnerForge(Forge):
    """Instantiate a runner that iterates over an item dataset."""

    material_cls = DataRunnerMaterial

    def forge_from_material(self, material: DataRunnerMaterial) -> ForgedDataRunner:
        """Build the runner from dataset and runtime defaults.

        Args:
            material: Declarative configuration including dataset, dataloader defaults, save policy, and skip list.

        Returns:
            ForgedDataRunner ready to process items.
        """
        dataset_dict = self._ensure_dataset_forge(dict(material.dataset))
        dataset_material = ItemDatasetMaterial(**{k: v for k, v in dataset_dict.items() if k != "forge"})
        dataset = ItemDatasetForge().forge_from_material(dataset_material)

        return ForgedDataRunner(
            dataset=dataset,
            default_batch_size=material.batch_size,
            default_num_workers=material.num_workers,
            default_save_path=material.save_path,
            default_save_every=material.save_every,
            default_save_format=material.save_format,
            default_skip_keys=material.skip_keys,
        )

    def _ensure_dataset_forge(self, dataset_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Guarantee the nested dataset uses the item_dataset forge."""
        if "forge" not in dataset_dict:
            dataset_dict["forge"] = "item_dataset"
        if dataset_dict["forge"] != "item_dataset":
            raise ValueError("DataRunner supports only 'item_dataset' forge for 'dataset'.")
        return dataset_dict
