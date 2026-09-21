"""Utilities to load YAML configs and resolve nested refs."""

from pathlib import Path
from typing import Any, Dict

import yaml


class Refiner:
    """Helper to load YAML and expand ``ref`` pointers recursively."""

    @staticmethod
    def from_yaml(path: str | Path) -> Dict[str, Any]:
        """Load a YAML file and resolve recursive ``ref`` entries.

        Args:
            path: Path to the YAML file.

        Returns:
            Fully expanded dictionary with all refs inlined.
        """
        path = Path(path).resolve()
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        resolved = Refiner._resolve_refs_and_merge(data, path.parent, (path,))
        if isinstance(resolved, dict) and "base_dir" not in resolved:
            resolved["base_dir"] = str(path.parent)
        return resolved

    @staticmethod
    def _resolve_refs_and_merge(node: Any, base: Path, stack: tuple[Path, ...] = ()) -> Any:
        """Resolve nested refs, overrides, and merges in a YAML structure.

        Rules:
        - If a dict contains ``ref``, load the referenced file, resolve it, then override with inline keys.
        - Lists and nested dicts are processed recursively.

        Args:
            node: Current YAML node (dict/list/primitive).
            base: Base directory for resolving relative refs.

        Returns:
            Node with refs fully resolved.
        """
        if isinstance(node, list):
            return [Refiner._resolve_refs_and_merge(i, base, stack) for i in node]

        if isinstance(node, dict):
            if "ref" in node:
                ref_path = (base / node["ref"]).resolve()
                if ref_path in stack:
                    chain = " -> ".join(str(path) for path in (*stack, ref_path))
                    raise ValueError(f"Cyclic YAML reference: {chain}")
                ref_data = yaml.safe_load(ref_path.read_text(encoding="utf-8"))
                ref_resolved = Refiner._resolve_refs_and_merge(ref_data, ref_path.parent, (*stack, ref_path))
                if isinstance(ref_resolved, dict) and "base_dir" not in ref_resolved:
                    ref_resolved["base_dir"] = str(ref_path.parent)
                inline_overrides = {k: v for k, v in node.items() if k != "ref"}
                resolved_overrides = Refiner._resolve_refs_and_merge(inline_overrides, base, stack)
                return {**ref_resolved, **resolved_overrides}

            return {k: Refiner._resolve_refs_and_merge(v, base, stack) for k, v in node.items()}

        return node
