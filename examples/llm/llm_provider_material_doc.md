# `llm_provider` Material

This document describes the general YAML contract for `llm_provider` materials.

## Top-Level YAML Pattern

```yaml
forge: llm_provider
type: openai
api_key_file: ./api_keys.yaml
models:
  default_chat:
    type: chat
    name: gpt-4.1-mini
```

## Common YAML Rules

- Add `forge: llm_provider` when this file is forged directly.
- Use `ref` when you want to reuse another provider file.
- Do not set `base_dir` manually. Agentic Forge injects it internally.

## Fields

| Field | Required | Type | Description | How to set it |
| --- | --- | --- | --- | --- |
| `forge` | yes at top level | string | Selects the provider forge. | Set it to `llm_provider`. |
| `ref` | no | string | Loads another provider material before local overrides. | Use it for provider-level reuse. |
| `type` | yes | `openai` \| `ollama` \| `openrouter` | Chooses the backend implementation. | Set it to the provider backend you want to target. |
| `base_url` | no | string | Overrides the backend base URL. | Useful for Ollama and OpenRouter, or for custom OpenAI-compatible endpoints. |
| `api_key_file` | no | string | Path to a local YAML file containing API keys. | Point it to a local untracked credentials file. |
| `keep_alive` | no | string | Ollama keep-alive duration. | Use values such as `2m` when you want the local model kept warm. |
| `models` | yes | mapping | Local model catalog exposed by this provider. | Add one entry per chat or embedding model alias. |

## `models` Entry

Each model entry supports:

| Field | Required | Type | Description |
| --- | --- | --- | --- |
| `type` | yes | `chat` \| `embedding` | Model modality. |
| `name` | yes | string | Real provider-specific model name. |
| `max_tokens` | no | integer | Optional maximum token count for chat responses. |
| `temperature` | no | number | Optional sampling temperature. |
| `top_p` | no | number | Optional nucleus sampling parameter. |
| `supports_vision` | no | boolean | Informational image-input capability, default `false`; exposed in the manager catalog, not enforced. |
| `extra_options` | no | mapping | Additional chat or embedding constructor options, such as Ollama `num_gpu` or `reasoning`. |

## Runtime behavior

Chat and embedding options are merged in this order: declared model fields, `extra_options`, then keyword arguments to `get_model()`. For example, `get_model("chat", temperature=0.2)` overrides the YAML temperature. Use backend constructor names in `extra_options`; for Ollama, the declared `max_tokens` field maps to `num_predict`.

API key files are read when a model is constructed, not when the provider or catalog is loaded. A missing key file therefore does not prevent inspecting the catalog or using another provider. Relative key paths resolve from the provider YAML, or from the enclosing manager YAML for inline providers.

Credentials loaded from files stay local to each provider instance. Without a key file, the provider uses its existing `OPENAI_API_KEY` or `OPENROUTER_API_KEY` environment variable. Constructing providers never changes those variables or `OLLAMA_KEEP_ALIVE`; `keep_alive` is passed directly to Ollama models. Embeddings also honor `base_url`, `extra_options`, and explicit `get_model()` overrides.
