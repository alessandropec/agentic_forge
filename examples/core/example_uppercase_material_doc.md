# `example_uppercase` Material

This document describes the general YAML shape used by the custom `example_uppercase` material in the core example.

## Top-Level YAML Pattern

```yaml
forge: example_uppercase
prefix: "forged: "
text: "hello agentic forge"
uppercase: true
```

## Common YAML Rules

- Add `forge: example_uppercase` when this is the file passed to `forge(...)`.
- Use `ref` only when you want to reuse another material file.
- Do not set `base_dir` manually. Agentic Forge injects it internally.

## Fields

| Field | Required | Type | Description | How to set it |
| --- | --- | --- | --- | --- |
| `forge` | yes at top level | string | Selects the forge registry entry. | Set it to `example_uppercase`. |
| `ref` | no | string | Reuses another material file before local overrides are applied. | Use a relative path such as `./shared.yaml` when you want composition. |
| `prefix` | no | string | Text prepended before the main input. | Use it for a fixed prefix or leave it empty. |
| `text` | yes | string | Main payload consumed by the forge. | Put the string you want the forge to transform. |
| `uppercase` | no | boolean | Controls whether the result is converted to uppercase. | Use `true` to uppercase the final string or `false` to preserve case. |

## Notes

- This is a teaching example, not a built-in component.
- The same material shape is implemented in the notebook and in `custom_forge.py`.
