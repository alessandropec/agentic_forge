"""Registry utilities for declaring and retrieving forges."""

from typing import TYPE_CHECKING, Callable, Dict, Type

if TYPE_CHECKING:
    from agentic_forge.core.forge import Forge

ForgeRegistry = Dict[str, Type["Forge"]]

FORGES: ForgeRegistry = {}


def register_forge(name: str) -> Callable[[Type["Forge"]], Type["Forge"]]:
    """Register a concrete Forge under a name.

    Args:
        name: Unique identifier used to retrieve the forge.

    Returns:
        A class decorator that registers the forge.

    Example:
        >>> @register_forge("example")
        ... class ExampleForge(Forge):
        ...     ...
    """

    def wrapper(cls: Type["Forge"]) -> Type["Forge"]:
        FORGES[name] = cls
        return cls

    return wrapper


def get_forge(name: str) -> Type["Forge"]:
    """Retrieve a registered forge by name.

    Args:
        name: Name used during registration.

    Returns:
        The forge class associated with the name.

    Raises:
        KeyError: If no forge is registered with that name.
    """
    if name not in FORGES:
        raise KeyError(f"Forge '{name}' is not registered. Available forges: {list(FORGES.keys())}")
    return FORGES[name]
