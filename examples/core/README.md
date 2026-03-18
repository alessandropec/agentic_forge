# Core Example

This example is the smallest possible introduction to Agentic Forge. It shows the full `material -> forge -> forged` flow before moving to the built-in components.

## What This Example Shows

The notebook keeps the whole lifecycle in one place:

- define a custom `Material`
- define a custom `Forged` runtime object
- define and register a custom `Forge`
- load a YAML file through the public `forge(...)` entrypoint

## Files In This Example

- `quickstart.ipynb`
  Primary walkthrough. The custom forge is defined directly in the notebook.
- `custom_forge.py`
  Standalone Python version of the same forge.
- `materials/uppercase_material.yaml`
  Concrete YAML instance used by the notebook.

## Material Docs

- [example_uppercase_material_doc.md](./example_uppercase_material_doc.md)

Use the material doc to understand the general YAML shape. Then use `materials/uppercase_material.yaml` as the concrete example instance.
