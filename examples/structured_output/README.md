# Structured Output Example

This example shows how Agentic Forge combines prompts, schemas, and model managers into named structured-output chains.

## What This Component Does

The structured output component wires together:

- a prompt material
- a response schema material
- an LLM manager plus a model selector

The forged runtime object exposes named chains that can be invoked with a payload and return structured responses.

## Files In This Example

- `quickstart.ipynb`
  Walkthrough for schema inspection, prompt formatting, and chain wiring.
- `materials/`
  Concrete materials used to build the structured model.
- `assets/`
  Local images used by the notebook.

## Material Docs

- [structured_model_material_doc.md](./structured_model_material_doc.md)

This example also reuses other built-in materials:

- [chat_prompt_material_doc.md](../chat_prompt/chat_prompt_material_doc.md)
- [response_schema_material_doc.md](../response_schema/response_schema_material_doc.md)
- [llm_manager_material_doc.md](../llm/llm_manager_material_doc.md)
- [llm_provider_material_doc.md](../llm/llm_provider_material_doc.md)
