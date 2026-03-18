# `tool` Material

This document describes the general YAML contract for `tool` materials.

## Top-Level YAML Pattern

Direct definition:

```yaml
forge: tool
name: search_documents
description: Search text documents.
implementation: handlers.py:search_documents
arguments:
  query:
    type: string
    description: Search query.
```

Reference wrapper:

```yaml
forge: tool
ref: ./tools/search.yaml
```

## Common YAML Rules

- Add `forge: tool` when this file is forged directly.
- You can define the full tool inline or use `ref` to point to a reusable tool body.
- Do not set `base_dir` manually. Agentic Forge injects it internally.

## Fields

| Field | Required | Type | Description | How to set it |
| --- | --- | --- | --- | --- |
| `forge` | yes at top level | string | Selects the tool forge. | Set it to `tool`. |
| `ref` | no | string | Loads another tool definition before local overrides. | Use it to build a thin entrypoint YAML around a reusable tool file. |
| `name` | no | string | Public tool name. | Recommended when defining the tool inline. |
| `description` | yes | string | Human-readable description of the tool. | Write it as a short capability statement. |
| `implementation` | yes | string | Python callable to execute. | Use `file.py:function_name` or module-path form. |
| `arguments` | no | mapping | Declarative schema of user-facing arguments. | Add one entry per callable parameter exposed to the user or model. |
| `resources` | no | mapping | Resource factories built once at forge time. | Use it for clients, connectors, or caches local to this tool. |
| `defaults` | no | mapping | Default keyword arguments injected at runtime. | Use it to avoid repeating constant values. |
| `allow_additional_args` | no | boolean | Allows extra runtime kwargs beyond the declared schema. | Leave it `false` unless you intentionally want looser validation. |
| `runtime` | no | object | Runtime-only injection settings. | Use it when the callable needs state or shared resources. |

## `arguments` Entry

Each argument entry supports:

| Field | Required | Type | Description |
| --- | --- | --- | --- |
| `type` | no | string | JSON-like type: `string`, `integer`, `number`, `boolean`, `array`, or `object`. |
| `description` | yes | string | Human-readable explanation of the argument. |
| `required` | no | boolean | Whether the caller must provide the argument. If omitted, it is inferred from the presence of `default`. |
| `default` | no | any | Default value used when the argument is omitted. |
| `enum` | no | list | Allowed values for constrained arguments. |
| `items_type` | no | string | Item type for array arguments only. |

## `runtime` Entry

| Field | Required | Type | Description |
| --- | --- | --- | --- |
| `inject_state` | no | boolean | Injects a `state` keyword argument at runtime. |
| `resources` | no | mapping | Maps callable parameter names to resource names built at forge time. |
