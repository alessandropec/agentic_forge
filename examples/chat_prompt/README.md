# Chat Prompt Example

This example shows how Agentic Forge turns declarative chat YAML into reusable prompt runtime objects.

## What This Component Does

The chat prompt component supports:

- reusable single-message materials
- full ordered chat prompts
- multimodal human messages with image inputs
- composition through `ref`

## Files In This Example

- `quickstart.ipynb`
  Walkthrough for forging and formatting prompts.
- `materials/`
  Concrete YAML instances used by the notebook.
- `assets/`
  Local images used by the multimodal examples.

## Material Docs

- [chat_prompt_material_doc.md](./chat_prompt_material_doc.md)
- [chat_message_material_doc.md](./chat_message_material_doc.md)

Use the material docs to understand the general YAML contract. Then inspect the files in `materials/` to see concrete examples of those materials.
