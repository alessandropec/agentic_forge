"""Dataset utilities for Agentic Forge."""

from __future__ import annotations

import json
import os
from pathlib import Path
import random
from typing import Any, Callable, Dict, List, Literal, Optional

DatasetFormat = Literal["dict", "list"]

import yaml
try:
    from torch.utils.data import DataLoader, Dataset
except ImportError:  # pragma: no cover - fallback for docs when torch is absent
    class Dataset:  # type: ignore[override]
        """Lightweight placeholder when torch is not installed."""

        def __len__(self) -> int:
            raise ImportError("torch is required to use ForgedItemDataset")

        def __getitem__(self, index):  # noqa: Dunder method, placeholder only
            raise ImportError("torch is required to use ForgedItemDataset")

    class DataLoader:  # type: ignore[override]
        """Very small DataLoader fallback used when torch is unavailable."""

        def __init__(
            self,
            dataset: "ForgedItemDataset",
            batch_size: int = 1,
            shuffle: bool = False,
            collate_fn: Optional[Callable[[List[Dict[str, Any]]], Any]] = None,
            **_: Any,
        ) -> None:
            self.dataset = dataset
            self.batch_size = batch_size
            self.shuffle = shuffle
            self.collate_fn = collate_fn

        def __iter__(self):
            indices = list(range(len(self.dataset)))
            if self.shuffle:
                random.shuffle(indices)

            for start in range(0, len(indices), self.batch_size):
                batch_indices = indices[start : start + self.batch_size]
                items = [self.dataset[idx] for idx in batch_indices]
                if self.collate_fn is not None:
                    yield self.collate_fn(items)
                    continue
                yield _fallback_collate(items)


def _fallback_collate(items: List[Dict[str, Any]]) -> Dict[str, List[Any]]:
    """Collate a list of dict items into dict-of-lists."""
    if not items:
        return {}

    keys = items[0].keys()
    return {key: [item[key] for item in items] for key in keys}

from agentic_forge.core.forged import Forged


def _portable_json_path_for_yaml(json_path: Path, yaml_path: Path) -> str:
    """Return a YAML-friendly path that stays portable across machines."""
    try:
        return os.path.relpath(json_path.resolve(), start=yaml_path.parent.resolve())
    except ValueError:
        return str(json_path.resolve())


class ForgedItemDataset(Forged, Dataset):
    """
    PyTorch Dataset wrapper around generic dict-based items.

    Args:
        items: List of item dictionaries.
        keys: Optional explicit keys aligned with ``items``; defaults to sequential strings.
        key_field: Name of the field containing the key when items are dicts from a list source.

    Example:
        >>> items = [{"id": 1, "text": "hi"}, {"id": 2, "text": "there"}]
        >>> ds = ForgedItemDataset(items, key_field="id")
        >>> len(ds)
        2
        >>> ds.get_key(0)
        '0'
    """

    def __init__(
        self,
        items: List[Dict[str, Any]],
        keys: Optional[List[str]] = None,
        key_field: Optional[str] = None,
    ) -> None:
        """Initialize dataset with items, optional keys and key field."""
        self._items = items
        self._keys = keys or [str(i) for i in range(len(items))]
        self._key_field = key_field or "id"
        self._key_to_index = {k: idx for idx, k in enumerate(self._keys)}

    @classmethod
    def from_json(
        cls,
        path: str | Path,
        format: DatasetFormat = "list",
        key_field: Optional[str] = None,
    ) -> "ForgedItemDataset":
        """Load a dataset from JSON file in list/dict format.

        Args:
            path: Path to the JSON file.
            format: ``"list"`` for a list of objects or ``"dict"`` for mapping key->object.
            key_field: Required when ``format`` is ``"list"``; identifies the key inside each item.

        Returns:
            A ``ForgedItemDataset`` populated with items and keys.

        Raises:
            ValueError: If the JSON structure does not match ``format`` expectations.

        Example:
            >>> ds = ForgedItemDataset.from_json("data/items.json", format="list", key_field="id")
            >>> ds.get_item_by_key("1")["id"]
            1
        """
        payload = json.loads(Path(path).read_text(encoding="utf-8"))

        if format == "dict":
            if not isinstance(payload, dict):
                raise ValueError("Expected JSON object for format='dict'")
            keys = [str(k) for k in payload.keys()]
            items = []
            for key in payload.keys():
                item = payload[key]
                if not isinstance(item, dict):
                    raise ValueError(f"Each dataset item must be an object (key: {key})")
                items.append(item)
            return cls(items=items, keys=keys, key_field=key_field)

        if format == "list":
            if not isinstance(payload, list):
                raise ValueError("Expected JSON array for format='list'")
            if not key_field:
                raise ValueError("key_field is required when format='list'")
            keys = []
            for item in payload:
                if not isinstance(item, dict):
                    raise ValueError("Each dataset item must be an object")
                if key_field not in item:
                    raise ValueError(f"Missing key_field '{key_field}' in item: {item}")
                keys.append(str(item[key_field]))
            return cls(items=payload, keys=keys, key_field=key_field)

        raise ValueError(f"Unsupported format: {format}")

    def __len__(self) -> int:
        """Return dataset size.

        Example:
            >>> len(ForgedItemDataset([{"id": 1}], key_field="id"))
            1
        """
        return len(self._items)

    def __getitem__(self, index: int) -> Dict[str, Any]:
        """Return item by positional index (required by PyTorch Dataset).

        Example:
            >>> ds = ForgedItemDataset([{"id": 1, "v": "a"}], key_field="id")
            >>> ds[0]["v"]
            'a'
            >>> ds[0]["id"]
            1
        """
        return self._item_with_key(index)

    def get_key(self, index: int) -> str:
        """Return the key associated with the item at ``index``.

        Example:
            >>> ds = ForgedItemDataset([{"id": 1}], keys=["item-1"])
            >>> ds.get_key(0)
            'item-1'
        """
        return self._keys[index]

    def get_item_by_key(self, key: str) -> Dict[str, Any]:
        """Return the item mapped to ``key``.

        Example:
            >>> ds = ForgedItemDataset([{"id": 1}], keys=["a"])
            >>> ds.get_item_by_key("a")["id"]
            1
        """
        return self._item_with_key(self._key_to_index[key])

    def _item_with_key(self, index: int) -> Dict[str, Any]:
        """Return a copy of the item enriched with ``key_field``."""
        item = self._items[index]
        if self._key_field is None:
            return item
        key_value = item.get(self._key_field, self.get_key(index))
        enriched = dict(item)
        enriched[self._key_field] = key_value
        return enriched

    def list_input_fields(self) -> List[str]:
        """
        Return sorted INPUT_* fields found across items.

        Example:
            >>> ds = ForgedItemDataset([{"INPUT_text": "hi", "id": 1}], key_field="id")
            >>> ds.list_input_fields()
            ['INPUT_text']
        """
        seen = set()
        for item in self._items:
            for field in item.keys():
                if field.startswith("INPUT_"):
                    seen.add(field)
        return sorted(seen)

    def preprocess(
        self,
        input_templates: Dict[str, str] | None = None,
        input_builders: Dict[str, Callable[[Dict[str, Any]], Any]] | None = None,
        input_prefix: str = "INPUT_",
        raw_prefix: Optional[str] = "RAW_",
        keep_original: bool = True,
    ) -> "ForgedItemDataset":
        """
        Create a standardized dataset with INPUT_* fields while preserving originals.

        Args:
            input_templates: Mapping output_field -> format string applied with item keys.
            input_builders: Mapping output_field -> callable that builds value from an item.
            input_prefix: Prefix to enforce on generated input fields.
            raw_prefix: Prefix used to copy original fields; set to ``None`` to skip copying.
            keep_original: Whether to retain original fields (with or without prefixing).

        Returns:
            New ``ForgedItemDataset`` with standardized input fields.

        Example:
            >>> items = [{"id": "a", "text": "Hello"}]
            >>> ds = ForgedItemDataset(items, key_field="id")
            >>> new_ds = ds.preprocess(input_templates={"text": "{text}"})
            >>> "INPUT_text" in new_ds[0]
            True
        """
        input_templates = input_templates or {}
        input_builders = input_builders or {}

        def normalize_input_field(field_name: str) -> str:
            if field_name.startswith(input_prefix):
                return field_name
            return f"{input_prefix}{field_name}"

        new_items: List[Dict[str, Any]] = []
        for idx, item in enumerate(self._items):
            enriched_item = self._item_with_key(idx)
            base: Dict[str, Any] = {}
            if keep_original and raw_prefix is None:
                base.update(enriched_item)

            if keep_original and self._key_field and self._key_field in enriched_item:
                base[self._key_field] = enriched_item[self._key_field]

            if keep_original and raw_prefix:
                for key, value in enriched_item.items():
                    if self._key_field and key == self._key_field:
                        continue
                    raw_key = f"{raw_prefix}{key}"
                    base[raw_key] = value

            for out_field, template in input_templates.items():
                out_field = normalize_input_field(out_field)
                try:
                    base[out_field] = template.format(**enriched_item)
                except KeyError as exc:
                    raise KeyError(
                        f"Missing field '{exc.args[0]}' while building '{out_field}' "
                        f"for item index {idx}"
                    ) from exc

            for out_field, builder in input_builders.items():
                out_field = normalize_input_field(out_field)
                base[out_field] = builder(enriched_item)

            new_items.append(base)

        return ForgedItemDataset(
            items=new_items,
            keys=list(self._keys),
            key_field=self._key_field,
        )

    def preprocess_and_save(
        self,
        json_path: str | Path,
        format: DatasetFormat = "list",
        key_field: Optional[str] = None,
        yaml_path: Optional[str | Path] = None,
        forge_name: str = "item_dataset",
        **preprocess_kwargs: Any,
    ) -> "ForgedItemDataset":
        """
        Preprocess and persist in one call.

        Args:
            json_path: Destination path for the processed JSON dataset.
            format: Serialization format for saving.
            key_field: Key field when saving as list.
            yaml_path: Optional path for the YAML config; defaults to ``json_path`` with ``.yaml``.
            forge_name: Forge name to embed in the YAML config.
            **preprocess_kwargs: Arguments forwarded to ``preprocess``.

        Returns:
            The processed dataset (also written to disk).

        Example:
            >>> ds = ForgedItemDataset([{"id": "a", "text": "Hello"}], key_field="id")
            >>> _ = ds.preprocess_and_save("out.json", key_field="id")
        """
        processed = self.preprocess(**preprocess_kwargs)
        processed.save(
            json_path=json_path,
            format=format,
            key_field=key_field,
            yaml_path=yaml_path,
            forge_name=forge_name,
        )
        return processed

    def to_serializable(
        self,
        format: DatasetFormat = "list",
        key_field: Optional[str] = None,
    ) -> Any:
        """
        Convert items to list/dict structure for JSON serialization.

        Args:
            format: Desired output structure.
            key_field: Required when producing a list representation.

        Returns:
            Serializable list or dict matching ``format``.

        Raises:
            ValueError: If ``format`` is unsupported.

        Example:
            >>> ds = ForgedItemDataset([{"id": "a"}], key_field="id")
            >>> ds.to_serializable(format="list")
            [{'id': 'a'}]
        """
        if format == "list":
            return list(self._items)

        if format == "dict":
            dataset: Dict[str, Any] = {}
            for key, item in zip(self._keys, self._items):
                dataset[str(key)] = item
            return dataset

        raise ValueError(f"Unsupported format: {format}")

    def save(
        self,
        json_path: str | Path,
        format: DatasetFormat = "list",
        key_field: Optional[str] = None,
        yaml_path: Optional[str | Path] = None,
        forge_name: str = "item_dataset",
    ) -> None:
        """
        Save dataset to JSON and write a YAML config for reloading.

        Args:
            json_path: Destination JSON path.
            format: Serialization format.
            key_field: Required for list format if not already set on the dataset.
            yaml_path: Optional YAML path; defaults to ``json_path`` with ``.yaml``.
            forge_name: Forge identifier to embed in the YAML config.

        Raises:
            ValueError: If key information is missing for list format.

        Example:
            >>> ds = ForgedItemDataset([{"id": "a"}], key_field="id")
            >>> ds.save("tmp.json", format="list", key_field="id")  # doctest: +ELLIPSIS
            ...
        """
        if format == "list" and not (key_field or self._key_field):
            raise ValueError("key_field is required when saving format='list'")
        payload = self.to_serializable(format=format, key_field=key_field)
        json_path = Path(json_path)
        json_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        if yaml_path is None:
            yaml_path = json_path.with_suffix(".yaml")
        yaml_path = Path(yaml_path)

        config = {
            "forge": forge_name,
            "path": _portable_json_path_for_yaml(json_path, yaml_path),
            "format": format,
        }
        if format == "list":
            config["key_field"] = key_field or self._key_field

        yaml_path.write_text(
            yaml.safe_dump(config, sort_keys=False),
            encoding="utf-8",
        )

    def get_dataloader(self, batch_size: int = 1, shuffle: bool = False, **kwargs: Any) -> DataLoader:
        """
        Build a PyTorch DataLoader for the dataset.

        Args:
            batch_size: Batch size for loading.
            shuffle: Whether to shuffle the dataset.
            **kwargs: Extra arguments forwarded to ``torch.utils.data.DataLoader``.

        Returns:
            Configured ``DataLoader`` instance.

        Example:
            >>> ds = ForgedItemDataset([{"id": "a"}], key_field="id")
            >>> loader = ds.get_dataloader(batch_size=1)
            >>> batch = next(iter(loader))
            >>> batch["id"][0]
            'a'
        """
        return DataLoader(self, batch_size=batch_size, shuffle=shuffle, **kwargs)

    @property
    def key_field(self) -> Optional[str]:
        """Return the field name that stores item keys."""
        return self._key_field
