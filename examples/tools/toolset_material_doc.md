# `toolset` Material

This document describes the general YAML contract for `toolset` materials.

## Top-Level YAML Pattern

```yaml
forge: toolset
resources:
  shared_db:
    factory: handlers.py:build_connector
tools:
  search_documents:
    ref: ./tools/search.yaml
  answer_with_memory:
    description: Answer using stored state.
    implementation: handlers.py:answer_with_memory
    runtime:
      inject_state: true
```

## Common YAML Rules

- Add `forge: toolset` when this file is forged directly.
- Do not set `base_dir` manually. Agentic Forge injects it internally.
- Each `tools` entry follows the `tool` material shape, inline or through `ref`.

## Fields

| Field | Required | Type | Description | How to set it |
| --- | --- | --- | --- | --- |
| `forge` | yes at top level | string | Selects the toolset forge. | Set it to `toolset`. |
| `ref` | no | string | Loads another toolset file before local overrides. | Use it only when reusing a whole tool collection. |
| `resources` | no | mapping | Shared runtime dependencies built once at forge time. | Use it for connectors, clients, caches, or local services. |
| `resources.<name>.factory` | yes for each resource | string | Callable used to build the resource. | Point it to a Python function such as `handlers.py:build_demo_db_connector`. |
| `resources.<name>.kwargs` | no | mapping | Keyword arguments passed to the resource factory. | Use it to parameterize the shared resource. |
| `tools` | yes | mapping | Mapping of tool names to tool definitions. | Add inline tool bodies or `ref` blocks. |

## Related Material

- [tool_material_doc.md](./tool_material_doc.md)
