# `chat_message` Material

This document describes the general YAML contract for `chat_message` materials.

## Top-Level YAML Pattern

```yaml
forge: chat_message
role: human
content: "Describe the image"
images:
  - "{image_path}"
```

## Common YAML Rules

- Add `forge: chat_message` when this file is forged directly.
- Inside another material, the same shape can appear inline without its own `forge` key.
- Use `ref` to reuse another message file and override only the fields that change.
- Do not set `base_dir` manually. Agentic Forge injects it internally.

## Fields

| Field | Required | Type | Description | How to set it |
| --- | --- | --- | --- | --- |
| `forge` | yes at top level | string | Selects the message forge. | Set it to `chat_message`. |
| `ref` | no | string | Loads another chat-message material before applying local overrides. | Use it when you want reusable message fragments. |
| `role` | yes | `system` \| `human` \| `ai` \| `placeholder` | Declares the message role. | Use `system` for instructions, `human` for user input, `ai` for assistant examples, and `placeholder` for injected history or variables. |
| `content` | no | string | Text body of the message. | Use normal text or template placeholders such as `{user_input}`. For `placeholder`, use only the placeholder name such as `history`. |
| `images` | no | list of strings | Image inputs for multimodal human messages. | Use local paths, remote URLs, data URLs, or placeholders such as `{image_path}`. |

## Notes

- `images` is primarily useful with `role: human`.
- A `placeholder` message usually does not need `images`.
