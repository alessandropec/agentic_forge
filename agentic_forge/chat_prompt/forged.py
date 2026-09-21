"""Forged runtime wrapper for chat prompts."""

from __future__ import annotations

import base64
import copy
import mimetypes
import re
from pathlib import Path
from typing import Any

from agentic_forge.core.forged import Forged

try:
    from langchain_core.runnables import RunnableLambda
except ImportError:  # pragma: no cover - docs/runtime without langchain
    RunnableLambda = None  # type: ignore


def _to_data_url(path: Path) -> str:
    """Encode a local file into a data URL."""
    mime = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    payload = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{payload}"


def _normalize_image_ref(
    value: Any, base_dir: Path | None, source_map: dict[str, str] | None = None
) -> Any:
    """Convert local image paths to data URLs, leaving URLs/data URLs unchanged."""
    if not isinstance(value, str):
        return value
    if value.startswith("data:"):
        return value
    if value.startswith("http://") or value.startswith("https://"):
        return value
    # Keep unresolved placeholders untouched.
    if value.startswith("{") and value.endswith("}"):
        return value

    candidate = Path(value).expanduser()
    if not candidate.is_absolute() and base_dir is not None:
        candidate = (base_dir / candidate).resolve()
    if candidate.exists() and candidate.is_file():
        data_url = _to_data_url(candidate)
        if source_map is not None:
            source_map[data_url] = str(candidate)
        return data_url
    return value


def _normalize_message_images(
    messages: list[Any],
    base_dir: Path | None,
    source_map: dict[str, str] | None = None,
) -> list[Any]:
    """Normalize image_url blocks for all human messages."""
    for msg in messages:
        content = getattr(msg, "content", None)
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict) or block.get("type") != "image_url":
                continue
            image_url = block.get("image_url")
            if isinstance(image_url, dict) and "url" in image_url:
                image_url["url"] = _normalize_image_ref(
                    image_url.get("url"), base_dir, source_map=source_map
                )
            elif isinstance(image_url, str):
                block["image_url"] = _normalize_image_ref(
                    image_url, base_dir, source_map=source_map
                )
    return messages


def _normalize_prompt_value(
    value: Any, base_dir: Path | None, source_map: dict[str, str] | None = None
) -> Any:
    """Normalize images in prompt runtime payloads."""
    if hasattr(value, "to_messages"):
        messages = value.to_messages()
        return _normalize_message_images(messages, base_dir, source_map=source_map)
    if isinstance(value, list):
        return _normalize_message_images(value, base_dir, source_map=source_map)
    return value


_DATA_URL_RE = re.compile(r"^data:([^;]+);base64,", re.IGNORECASE)


def _compact_data_url(value: Any, source_map: dict[str, str]) -> Any:
    """Return a compact placeholder for long data URLs."""
    if not isinstance(value, str):
        return value
    m = _DATA_URL_RE.match(value)
    if not m:
        return value
    mime = m.group(1)
    source = source_map.get(value)
    if source:
        return f"<image:{mime} from_path='{source}'>"
    return f"<image:{mime} data_url_len={len(value)}>"


def _compact_for_display(value: Any, source_map: dict[str, str]) -> Any:
    """Recursively compact data URLs for safe printing."""
    if isinstance(value, dict):
        return {k: _compact_for_display(v, source_map) for k, v in value.items()}
    if isinstance(value, list):
        return [_compact_for_display(v, source_map) for v in value]
    if hasattr(value, "content"):
        content = getattr(value, "content", None)
        if isinstance(content, list):
            compacted = _compact_for_display(content, source_map)
            setattr(value, "content", compacted)
        return value
    return _compact_data_url(value, source_map)


class ForgedChatPrompt(Forged):
    """Runtime chat prompt with automatic local image path normalization."""

    def __init__(self, prompt: Any, base_dir: str | Path | None = None) -> None:
        self.prompt = prompt
        self.base_dir = Path(base_dir).resolve() if base_dir else None
        self._data_url_sources: dict[str, str] = {}

    @property
    def input_variables(self) -> Any:
        return getattr(self.prompt, "input_variables", [])

    def format_messages(self, *args: Any, **kwargs: Any) -> list[Any]:
        messages = self.prompt.format_messages(*args, **kwargs)
        return _normalize_message_images(messages, self.base_dir, source_map=self._data_url_sources)

    def partial(self, **kwargs: Any) -> "ForgedChatPrompt":
        return ForgedChatPrompt(self.prompt.partial(**kwargs), base_dir=self.base_dir)

    def invoke(self, input: Any, config: Any = None, **kwargs: Any) -> Any:
        value = self.prompt.invoke(input=input, config=config, **kwargs)
        _normalize_prompt_value(value, self.base_dir, source_map=self._data_url_sources)
        return value

    async def ainvoke(self, input: Any, config: Any = None, **kwargs: Any) -> Any:
        value = await self.prompt.ainvoke(input=input, config=config, **kwargs)
        _normalize_prompt_value(value, self.base_dir, source_map=self._data_url_sources)
        return value

    def compact_for_display(self, value: Any) -> Any:
        """Return a print-safe object with data URLs replaced by placeholders."""
        for template in getattr(self.prompt, "messages", []):
            self._data_url_sources.update(getattr(template, "image_sources", {}))
        return _compact_for_display(copy.deepcopy(value), self._data_url_sources)

    def __or__(self, other: Any) -> Any:
        if RunnableLambda is None:
            raise ImportError("langchain_core is required to compose chat prompts")
        return self.prompt | RunnableLambda(
            lambda value: _normalize_prompt_value(
                value, self.base_dir, source_map=self._data_url_sources
            )
        ) | other

    def __getattr__(self, item: str) -> Any:
        return getattr(self.prompt, item)
