# LLM Example

This example shows how Agentic Forge declares LLM providers and managers in YAML.

## What This Component Does

The LLM component provides:

- provider-level materials for OpenAI, OpenRouter, and Ollama
- model catalogs for each provider
- a manager that exposes `provider:model` selectors

## Files In This Example

- `quickstart.ipynb`
  Walkthrough for forging providers, managers, and model selectors.
- `materials/`
  Concrete provider, manager, and local credential placeholder files.

## Material Docs

- [llm_provider_material_doc.md](./llm_provider_material_doc.md)
- [llm_manager_material_doc.md](./llm_manager_material_doc.md)
