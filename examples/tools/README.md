# Tools Example

This example shows how Agentic Forge declares tools and toolsets in YAML and binds them to Python callables.

## What This Component Does

The tools component supports:

- declarative argument schemas
- default values and validation
- runtime resource injection
- agent-state injection for stateful tools

## Files In This Example

- `quickstart.ipynb`
  Walkthrough for forging, schema generation, and runtime invocation.
- `materials/`
  Concrete YAML instances plus the Python handlers used by the example.

## Material Docs

- [tool_material_doc.md](./tool_material_doc.md)
- [toolset_material_doc.md](./toolset_material_doc.md)

Use the material docs for the general contract of `tool` and `toolset` YAML files. The files in `materials/` show concrete instances and composition patterns.
