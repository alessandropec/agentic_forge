"""Forged structured model runtime utilities."""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, Iterable, Mapping, Optional

from agentic_forge.core.forged import Forged


class ForgedStructuredModel(Forged):
    """Hold a model and multiple prompt+schema chains, ready to invoke."""

    def __init__(
        self,
        model: Any,
        chains: Dict[str, Any],
        format_instructions: Optional[Dict[str, str]] = None,
    ) -> None:
        """Store model, chains and optional format instructions."""
        self.model = model
        self.chains = chains
        self._format_instructions = format_instructions or {}

    def list_chains(self) -> Iterable[str]:
        """Return available chain names.

        Example:
            >>> list(ForgedStructuredModel(model=None, chains={}, format_instructions={}).list_chains())
            []
        """
        return self.chains.keys()

    def invoke(self, chain_name: str, payload: dict, **kwargs) -> Any:
        """Invoke a single chain by name.

        Args:
            chain_name: Name of the chain to call.
            payload: Input data for the chain.
            **kwargs: Extra options forwarded to the underlying chain invocation.

        Returns:
            Result of the chain invocation.

        Example:
            >>> f = ForgedStructuredModel(model=None, chains={"c": lambda x: x}, format_instructions={})
            >>> f.chains["c"] = type("C", (), {"invoke": staticmethod(lambda p, **_: p)})()
            >>> f.invoke("c", {"a": 1})["a"]
            1
        """
        if chain_name not in self.chains:
            raise KeyError(f"Chain `{chain_name}` not found. Available: {list(self.chains.keys())}")
        return self.chains[chain_name].invoke(payload, **kwargs)

    def batch(
        self,
        payloads: Mapping[str, dict],
        concurrency: int | None = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Run multiple payloads routed to chains by name in parallel (threads).

        - payloads: mapping chain_name -> payload
        - concurrency: optional max workers; defaults to min(len(payloads), cpu_count or 4)

        Example:
            >>> f = ForgedStructuredModel(model=None, chains={}, format_instructions={})
            >>> f.chains["c"] = type("C", (), {"invoke": staticmethod(lambda p, **_: p)})()
            >>> f.batch({"c": {"v": 1}})["c"]["v"]
            1
        """
        if not payloads:
            return {}

        max_workers = concurrency or min(len(payloads), os.cpu_count() or 4)
        results: Dict[str, Any] = {}

        def _run(name: str, payload: dict):
            return name, self.invoke(name, payload, **kwargs)

        try:
            from tqdm import tqdm
        except Exception:  # pragma: no cover - fallback if tqdm not installed
            tqdm = None

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_name = {
                executor.submit(_run, name, payload): name for name, payload in payloads.items()
            }
            iterator = as_completed(future_to_name)
            if tqdm:
                iterator = tqdm(iterator, total=len(future_to_name), desc="Processing batch")
            for future in iterator:
                name, result = future.result()
                results[name] = result

        return results

    def get_format_instruction(self, chain_name: str) -> str:
        """Return the format instruction string for the given chain.

        Example:
            >>> f = ForgedStructuredModel(model=None, chains={}, format_instructions={"c": "fmt"})
            >>> f.get_format_instruction("c")
            'fmt'
        """
        if chain_name not in self._format_instructions:
            raise KeyError(f"Format instruction for chain `{chain_name}` not available")
        return self._format_instructions[chain_name]
