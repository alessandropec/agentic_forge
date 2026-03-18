# `chat_prompt` Material

This document describes the general YAML contract for `chat_prompt` materials.

## Top-Level YAML Pattern

```yaml
forge: chat_prompt
name: vision_prompt
messages:
  - role: system
    content: "You are a helpful assistant."
  - role: placeholder
    content: history
  - role: human
    content: "{user_input}"
    images:
      - "{image_path}"
```

## Common YAML Rules

- Add `forge: chat_prompt` when this file is forged directly.
- Use `ref` to reuse another prompt file or another message file.
- Do not set `base_dir` manually. Agentic Forge injects it internally.
- Each `messages` entry follows the `chat_message` shape, either inline or through `ref`.

## Fields

| Field | Required | Type | Description | How to set it |
| --- | --- | --- | --- | --- |
| `forge` | yes at top level | string | Selects the prompt forge. | Set it to `chat_prompt`. |
| `ref` | no | string | Loads another chat-prompt material before applying local overrides. | Use it when you want prompt-level reuse. |
| `name` | yes | string | Human-readable prompt identifier. | Use a stable descriptive name such as `vision_prompt`. |
| `messages` | yes | list | Ordered list of prompt messages. | Add the messages in the exact order they should be sent to the model. |
| `messages[].ref` | no | string | Loads a reusable message file for one entry. | Use it when one message should come from another YAML file. |
| `messages[].role` | yes for inline entries | string | Role of the inline message. | Use the same allowed roles as `chat_message`. |
| `messages[].content` | no | string | Body of the inline message. | Use template placeholders such as `{user_input}` or `history` for placeholder entries. |
| `messages[].images` | no | list of strings | Images attached to an inline human message. | Use it only for multimodal prompts. |

## Related Material

- [chat_message_material_doc.md](./chat_message_material_doc.md)
