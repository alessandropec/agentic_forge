# `item_dataset` Material

This document describes the general YAML contract for `item_dataset` materials.

## Top-Level YAML Pattern

```yaml
forge: item_dataset
path: ./items.json
format: list
key_field: id
```

## Common YAML Rules

- Add `forge: item_dataset` when this file is forged directly.
- Use `ref` when you want to reuse another dataset material.
- Do not set `base_dir` manually. Agentic Forge injects it internally.

## Fields

| Field | Required | Type | Description | How to set it |
| --- | --- | --- | --- | --- |
| `forge` | yes at top level | string | Selects the dataset forge. | Set it to `item_dataset`. |
| `ref` | no | string | Loads another dataset material before local overrides. | Use it for reuse when datasets share most settings. |
| `path` | yes | string | Filesystem path to the JSON dataset. | Use a path relative to the YAML file or an absolute path. |
| `format` | no | `list` \| `dict` | Declares the JSON root shape. | Use `list` for arrays of items or `dict` for mappings of key to item. |
| `key_field` | yes for `format: list` | string | Field used as the item identifier. | For `list`, set it to the key already present in each record. For `dict`, set it to the field name that should receive the mapping key at runtime. |

## Notes

- `key_field` is mandatory when `format` is `list`.
- For `dict` datasets, the runtime loader injects the top-level dictionary key into each item using `key_field`.
