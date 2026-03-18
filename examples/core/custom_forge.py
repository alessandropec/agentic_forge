"""Minimal custom forge used by the core quickstart."""

from agentic_forge.core import Forge, Forged, Material, register_forge


class UppercaseMaterial(Material):
    """Declarative material for a tiny custom forge."""

    prefix: str = ""
    text: str
    uppercase: bool = True


class ForgedText(Forged):
    """Runtime object returned by the custom forge."""

    def __init__(self, text: str) -> None:
        self.text = text

    def render(self) -> str:
        """Return the forged text."""
        return self.text


@register_forge("example_uppercase")
class UppercaseForge(Forge):
    """Small example forge used to explain the core pattern."""

    material_cls = UppercaseMaterial

    def forge_from_material(self, material: UppercaseMaterial) -> ForgedText:
        text = f"{material.prefix}{material.text}"
        if material.uppercase:
            text = text.upper()
        return ForgedText(text)
