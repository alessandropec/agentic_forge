"""Forged data runner that iterates datasets and processes items.

The runner enriches every item with its key (using the dataset ``key_field``)
so ``process_item`` can rely on ``item[key_field]`` without extra arguments,
regardless of whether the source dataset was stored as a list (key already inside
the item) or a dict (key injected under ``key_field``).
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set

try:  # pragma: no cover - optional dependency
    import pandas as pd
except ImportError:  # pragma: no cover
    pd = None

try:  # pragma: no cover - optional dependency
    from tqdm.auto import tqdm
except ImportError:  # pragma: no cover
    class _NullTqdm:  # type: ignore
        def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401 - minimal stub
            pass

        def update(self, *_: Any, **__: Any) -> None:
            return

        def set_postfix(self, *_: Any, **__: Any) -> None:
            return

        def close(self) -> None:
            return

    def tqdm(*args: Any, **kwargs: Any) -> _NullTqdm:  # type: ignore
        return _NullTqdm()

from agentic_forge.core.forged import Forged
from agentic_forge.dataset.forged import ForgedItemDataset


class ForgedDataRunner(Forged):
    """Runtime runner that processes dataset items with a user callable."""

    def __init__(
        self,
        dataset: ForgedItemDataset,
        default_batch_size: int = 1,
        default_num_workers: int = 0,
        default_save_path: Optional[str] = None,
        default_save_every: Optional[int] = None,
        default_save_format: str = "json",
        default_skip_keys: Optional[List[str]] = None,
    ) -> None:
        """Initialize the runner with dataset and default runtime settings."""
        self.dataset = dataset
        self.default_batch_size = default_batch_size
        self.default_num_workers = default_num_workers
        self.default_save_path = default_save_path
        self.default_save_every = default_save_every
        self.default_save_format = default_save_format
        self.default_skip_keys: Set[str] = {str(key) for key in default_skip_keys or []}

    def run(
        self,
        process_item: Callable[..., Optional[Dict[str, Any]]],
        *,
        batch_size: Optional[int] = None,
        num_workers: Optional[int] = None,
        save_every: Optional[int] = None,
        save_path: Optional[str] = None,
        save_format: Optional[str] = None,
        skip_keys: Optional[List[str]] = None,
        **process_kwargs: Any,
    ) -> List[Dict[str, Any]]:
        """
        Iterate over the dataset and apply ``process_item`` to each element.

        Args:
            process_item: Callable receiving ``item`` (named arg) and returning a dict or ``None``.
            batch_size: Override default batch size for the DataLoader.
            num_workers: Override default worker count.
            save_every: Items between saves; ``None`` disables saving.
            save_path: Path for persisted outputs; required if ``save_every`` is set.
            save_format: ``json`` (append to a JSON list) or ``csv``; defaults to material value.
            skip_keys: Keys to skip during this run (merged with material-level skips).
            **process_kwargs: Extra keyword args forwarded to ``process_item``.

        Returns:
            List of dict of processed item outputs (each guaranteed to include the key field).

        Raises:
            TypeError: If the dataloader batch is not a dict or ``process_item`` returns non-dict/non-None.
            ValueError: If CSV batches introduce new columns after the first write.

        Example:
            >>> runner.run(
            ...     process_item=lambda *, item: {"key": item["key"], "value": item["INPUT_text"]},
            ...     save_every=10,
            ...     save_path="out.json",
            ...     save_format="json",
            ...     skip_keys=["item_002"],
            ... )
        """
        bs = self.default_batch_size if batch_size is None else batch_size
        workers = self.default_num_workers if num_workers is None else num_workers
        cadence = self.default_save_every if save_every is None else save_every
        target_path = save_path or self.default_save_path
        output_format = save_format or self.default_save_format
        skip_set: Set[str] = set(self.default_skip_keys)
        if skip_keys:
            skip_set.update(str(key) for key in skip_keys)

        self._validate_runtime_config(bs, workers, cadence, target_path, output_format)

        loader = self.dataset.get_dataloader(batch_size=bs, num_workers=workers)

        results: List[Dict[str, Any]] = []
        pending_chunk: List[Dict[str, Any]] = []
        processed = 0
        skipped = 0
        visited = 0
        key_field = self.dataset.key_field or "id"

        progress = tqdm(
            total=len(self.dataset),
            desc=f"Processing dataset (save_every={cadence or 'off'})",
            unit="item",
        )
        progress.set_postfix(saved=len(results))

        for batch in loader:
            if not isinstance(batch, dict):
                raise TypeError("DataLoader must yield dict batches; provide a compatible collate_fn.")

            values_iter = iter(batch.values())
            try:
                first_val = next(values_iter)
            except StopIteration:
                continue
            batch_len = len(first_val)
            for value in values_iter:
                if len(value) != batch_len:
                    raise ValueError("Inconsistent batch lengths detected.")

            for i in range(batch_len):
                item = {k: v[i] for k, v in batch.items()}
                key_value = item.get(key_field, self.dataset.get_key(visited))
                # Torch's default collation turns numeric IDs into scalar tensors.
                if hasattr(key_value, "item"):
                    key_value = key_value.item()
                item[key_field] = key_value
                visited += 1

                if str(key_value) in skip_set:
                    skipped += 1
                    progress.update(1)
                    progress.set_postfix(saved=len(results), skipped=skipped)
                    continue

                output = process_item(item=item, **process_kwargs)
                progress.update(1)

                if output is None:
                    continue

                if not isinstance(output, dict):
                    raise TypeError("process_item must return a dict.")

                result_with_key = dict(output)
                if key_field not in result_with_key:
                    result_with_key[key_field] = key_value
                results.append(result_with_key)
                pending_chunk.append(result_with_key)
                processed += 1

                if cadence is not None and processed % cadence == 0:
                    if pending_chunk:
                        self._append_results(pending_chunk, target_path, output_format)
                        progress.set_postfix(saved=len(results), skipped=skipped)
                        pending_chunk = []

        progress.close()

        if cadence is not None and target_path and pending_chunk:
            self._append_results(pending_chunk, target_path, output_format)

        return results

    def _validate_runtime_config(
        self,
        batch_size: int,
        num_workers: int,
        save_every: Optional[int],
        save_path: Optional[str],
        save_format: str,
    ) -> None:
        """Validate runtime overrides for the runner."""
        if batch_size <= 0:
            raise ValueError("batch_size must be > 0")
        if num_workers < 0:
            raise ValueError("num_workers must be >= 0")
        if save_every is not None:
            if save_every <= 0:
                raise ValueError("save_every must be > 0 or None")
            if not save_path:
                raise ValueError("save_path is required when save_every is set")
        if save_format not in {"json", "csv"}:
            raise ValueError("save_format must be 'json' or 'csv'")

    def _append_results(self, rows: List[Dict[str, Any]], path: str, fmt: str) -> None:
        """Persist results to disk in append mode."""
        dest = Path(path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        if fmt == "json":
            if not rows:
                return
            if not dest.exists() or dest.stat().st_size == 0:
                existing_rows: List[Dict[str, Any]] = []
            else:
                with dest.open("r", encoding="utf-8") as fp:
                    existing_data = json.load(fp)
                if not isinstance(existing_data, list):
                    raise ValueError("JSON output must be a JSON array to append results.")
                existing_rows = existing_data

            existing_rows.extend(rows)
            with dest.open("w", encoding="utf-8") as fp:
                json.dump(existing_rows, fp, ensure_ascii=False, indent=2)
                fp.write("\n")
            return

        if fmt == "csv":
            self._append_csv_rows(rows, dest)
            return

        raise ValueError(f"Unsupported format: {fmt}")

    def _append_csv_rows(self, rows: List[Dict[str, Any]], dest: Path) -> None:
        """Persist CSV rows using pandas when available, else stdlib csv."""
        if not rows:
            return

        if pd is not None:
            df = pd.DataFrame(rows)
            header_needed = not dest.exists() or dest.stat().st_size == 0

            if header_needed:
                df.to_csv(dest, mode="a", index=False, header=True)
                return

            existing_header = pd.read_csv(dest, nrows=0).columns.tolist()
            extra_cols = set(df.columns) - set(existing_header)
            if extra_cols:
                raise ValueError(
                    f"CSV output fields must match existing columns. Unexpected columns: {sorted(extra_cols)}"
                )
            df = df.reindex(columns=existing_header)
            df.to_csv(dest, mode="a", index=False, header=False)
            return

        header_needed = not dest.exists() or dest.stat().st_size == 0
        if header_needed:
            header = list(rows[0].keys())
        else:
            with dest.open("r", encoding="utf-8", newline="") as fp:
                reader = csv.reader(fp)
                header = next(reader)

            extra_cols = set(rows[0].keys()) - set(header)
            if extra_cols:
                raise ValueError(
                    f"CSV output fields must match existing columns. Unexpected columns: {sorted(extra_cols)}"
                )

        with dest.open("a", encoding="utf-8", newline="") as fp:
            writer = csv.DictWriter(fp, fieldnames=header, extrasaction="ignore")
            if header_needed:
                writer.writeheader()
            for row in rows:
                writer.writerow({column: row.get(column) for column in header})
