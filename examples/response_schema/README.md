# Response Schema Example

This example shows how Agentic Forge turns declarative schema YAML into runtime Pydantic models and prompt-ready formatting instructions.

## What This Component Does

The response schema component lets you describe structured outputs in YAML and forge:

- a runtime Pydantic model
- a formatting instruction string that can be injected into prompts

## Files In This Example

- `quickstart.ipynb`
  Forges the schemas and prints the generated format instructions.
- `materials/`
  Concrete schema YAML instances, including nested and `ref`-based variants.

## Material Docs

- [response_schema_material_doc.md](./response_schema_material_doc.md)

The material doc explains the general shape of `response_schema` YAML files. The files under `materials/` are example instantiations of that schema.
