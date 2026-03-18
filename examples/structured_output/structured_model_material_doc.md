# `structured_model` Material

This document describes the general YAML contract for `structured_model` materials.

## Top-Level YAML Pattern

```yaml
forge: structured_model
llm_manager:
  ref: ./manager_multi_provider.yaml
model_selector: default_openrouter:vision_chat
prompt_schema_pairs:
  - name: detect
    prompt:
      ref: ./chat_prompt.yaml
    schema:
      ref: ./response_schema.yaml
```

## Common YAML Rules

- Add `forge: structured_model` when this file is forged directly.
- Use `ref` inside nested materials when you want to reuse prompt, schema, or manager files.
- Do not set `base_dir` manually. Agentic Forge injects it internally.

## Fields

| Field | Required | Type | Description | How to set it |
| --- | --- | --- | --- | --- |
| `forge` | yes at top level | string | Selects the structured-model forge. | Set it to `structured_model`. |
| `ref` | no | string | Loads another structured-model file before local overrides. | Use it for reuse only when the whole structured model should be shared. |
| `llm_manager` | yes | object | Manager material used to resolve providers and models. | Provide an inline `llm_manager` material or a `ref` to one. |
| `model_selector` | yes | string | Chooses the runtime model from the manager. | Use the `provider:model` format, such as `default_openai:default_chat`. |
| `prompt_schema_pairs` | yes | list | List of named chains exposed by the forged object. | Add one entry per chain you want to register. |
| `prompt_schema_pairs[].name` | no | string | Optional chain identifier. | Use a short stable name such as `detect`, `refine`, or `classify`. |
| `prompt_schema_pairs[].prompt` | yes | object | Prompt material used by the chain. | Provide a `chat_prompt` material inline or via `ref`. |
| `prompt_schema_pairs[].schema` | yes | object | Response schema used by the chain. | Provide a `response_schema` material inline or via `ref`. |

## Related Materials

- [chat_prompt_material_doc.md](../chat_prompt/chat_prompt_material_doc.md)
- [response_schema_material_doc.md](../response_schema/response_schema_material_doc.md)
- [llm_manager_material_doc.md](../llm/llm_manager_material_doc.md)
