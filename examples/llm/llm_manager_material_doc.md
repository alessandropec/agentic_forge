# `llm_manager` Material

This document describes the general YAML contract for `llm_manager` materials.

## Top-Level YAML Pattern

```yaml
forge: llm_manager
providers:
  default_openai:
    ref: ./provider_openai.yaml
  local_ollama:
    ref: ./provider_ollama.yaml
```

## Common YAML Rules

- Add `forge: llm_manager` when this file is forged directly.
- Do not set `base_dir` manually. Agentic Forge injects it internally.
- Each entry in `providers` must contain an `llm_provider` material, inline or via `ref`.

## Fields

| Field | Required | Type | Description | How to set it |
| --- | --- | --- | --- | --- |
| `forge` | yes at top level | string | Selects the manager forge. | Set it to `llm_manager`. |
| `ref` | no | string | Loads another manager material before local overrides. | Use it when you want to reuse a whole provider registry. |
| `providers` | yes | mapping | Named provider registry exposed by the manager. | Add one entry per provider alias you want to use in `provider:model` selectors. |
| `providers.<name>` | yes | object | Provider definition. | Use an inline `llm_provider` material or a `ref` to one. |

## Related Material

- [llm_provider_material_doc.md](./llm_provider_material_doc.md)

## Inspect and select models

```python
from agentic_forge import forge

manager = forge("manager.yaml")
catalog = manager.list_models()
info = manager.get_model_info("local_ollama:chat")
print(info["supports_vision"])
model = manager.get_model("local_ollama:chat", temperature=0.2)
```

Replace the selector with a provider/model alias from your YAML. Catalog inspection does not require the configured key files to exist. `get_model()` constructs the selected backend model and loads its credentials if configured.
