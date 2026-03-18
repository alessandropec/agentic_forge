# `data_runner` Material

This document describes the general YAML contract for `data_runner` materials.

## Top-Level YAML Pattern

```yaml
forge: data_runner
dataset:
  ref: ./dict_dataset.yaml
batch_size: 1
num_workers: 0
save_path: ./outputs.json
save_every: 1
save_format: json
skip_keys:
  - item_001
```

## Common YAML Rules

- Add `forge: data_runner` when this file is forged directly.
- Do not set `base_dir` manually. Agentic Forge injects it internally.
- The nested `dataset` entry must contain an `item_dataset` material, inline or via `ref`.

## Fields

| Field | Required | Type | Description | How to set it |
| --- | --- | --- | --- | --- |
| `forge` | yes at top level | string | Selects the data-runner forge. | Set it to `data_runner`. |
| `ref` | no | string | Loads another runner material before local overrides. | Use it only when reusing a whole runner config. |
| `dataset` | yes | object | Dataset material consumed by the runner. | Provide an `item_dataset` material inline or via `ref`. |
| `batch_size` | no | integer | Default batch size. | Use a positive integer. Keep it small in notebooks. |
| `num_workers` | no | integer | Default worker count. | Use `0` for simple local runs or increase it for throughput. |
| `save_path` | no | string | Output location used during persistence. | Set it when the runner should write results to disk. |
| `save_every` | no | integer | Number of processed items between saves. | Use a positive integer. If set, `save_path` must also be set. |
| `save_format` | no | `json` \| `csv` | Output file format. | Choose the format that matches `save_path`. |
| `skip_keys` | no | list of strings | Dataset keys to skip. | Use it for resumable or partial runs. |

## Related Material

- [item_dataset_material_doc.md](../dataset/item_dataset_material_doc.md)
