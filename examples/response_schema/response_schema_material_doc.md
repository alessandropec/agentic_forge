# `response_schema` Material

This document describes the general YAML contract for `response_schema` materials.

## Top-Level YAML Pattern

```yaml
forge: response_schema
name: simple_profile
fields:
  - name: username
    type: str
    description: User handle
```

## Common YAML Rules

- Add `forge: response_schema` when this file is forged directly.
- Use `ref` to reuse another schema file.
- Do not set `base_dir` manually. Agentic Forge injects it internally.

## Top-Level Fields

| Field | Required | Type | Description | How to set it |
| --- | --- | --- | --- | --- |
| `forge` | yes at top level | string | Selects the schema forge. | Set it to `response_schema`. |
| `ref` | no | string | Loads another response-schema file before applying local overrides. | Use it for schema reuse. |
| `name` | yes | string | Name of the generated Pydantic model. | Use a valid model name such as `CatalogItem` or `scene_bounding_boxes`. |
| `fields` | yes | list | Ordered list of schema field definitions. | Add one entry per output field expected from the model. |

## Schema Field Variants

Every entry in `fields` must include:

- `name`
- `description`
- `required` (optional, defaults to `true`)
- `type`

### Primitive Field

```yaml
- name: price
  type: float
  description: Price in USD
  required: true
```

Allowed primitive `type` values:

- `str`
- `int`
- `float`
- `bool`

### Enum Field

```yaml
- name: role
  type: enum
  description: User role
  choices: ["admin", "editor", "viewer"]
```

Extra field:

- `choices`: required list of allowed string values

### Object Field

```yaml
- name: metadata
  type: obj
  description: Additional metadata
  fields:
    - name: source
      type: str
      description: Origin
```

Extra field:

- `fields`: nested schema fields inside the object

### List Field

```yaml
- name: tags
  type: list
  description: Search tags
  items:
    name: tag
    type: str
    description: One tag
```

Extra field:

- `items`: schema of one list item

## Notes

- Nested `fields` and `items` use the same schema-field rules recursively.
- Keep `description` short and precise because it is used to generate formatting instructions.
