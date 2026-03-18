"""Helpers to resolve Python callables from declarative tool configs."""

from __future__ import annotations

from hashlib import sha1
import importlib
import importlib.util
from pathlib import Path
import sys
from types import ModuleType
from typing import Any, Callable


def load_callable(reference: str, base_dir: str | None = None) -> Callable[..., Any]:
    """Resolve ``module:attr`` or ``path.py:attr`` into a callable."""
    if ":" not in reference:
        raise ValueError(
            "Tool implementations must use 'module.path:callable' or 'relative/path.py:callable'."
        )

    module_ref, attr_path = reference.rsplit(":", 1)
    module = _load_module(module_ref, base_dir=base_dir)

    target: Any = module
    for attr_name in attr_path.split("."):
        target = getattr(target, attr_name)

    if not callable(target):
        raise TypeError(f"Implementation target '{reference}' is not callable.")

    return target


def _load_module(module_ref: str, base_dir: str | None = None) -> ModuleType:
    """Load a module reference from either import path or filesystem path."""
    if _looks_like_file_reference(module_ref):
        return _load_module_from_path(module_ref, base_dir=base_dir)
    return importlib.import_module(module_ref)


def _looks_like_file_reference(module_ref: str) -> bool:
    """Detect whether a module reference is a Python file path."""
    return module_ref.endswith(".py") or "/" in module_ref or "\\" in module_ref


def _load_module_from_path(module_ref: str, base_dir: str | None = None) -> ModuleType:
    """Import a Python file with a deterministic module name."""
    path = Path(module_ref)
    if not path.is_absolute():
        if base_dir is None:
            raise ValueError("Relative implementation paths require a material base_dir.")
        path = Path(base_dir) / path

    path = path.resolve()
    if not path.exists():
        raise FileNotFoundError(f"Tool implementation file not found: {path}")

    module_name = _module_name_for_path(path)
    if module_name in sys.modules:
        return sys.modules[module_name]

    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module from path: {path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def _module_name_for_path(path: Path) -> str:
    """Build a stable synthetic module name for a file-backed tool implementation."""
    digest = sha1(str(path).encode("utf-8")).hexdigest()[:12]
    return f"agentic_forge_tool_impl_{path.stem}_{digest}"
