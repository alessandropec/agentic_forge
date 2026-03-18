"""Runtime registry for a collection of declarative tools."""

from __future__ import annotations

from typing import Any, Dict

from agentic_forge.core.forged import Forged
from agentic_forge.tools.forged.tool import ForgedTool


class ForgedToolset(Forged):
    """Runtime collection of forged tools."""

    def __init__(self, tools: Dict[str, ForgedTool]) -> None:
        self.tools = dict(tools)

    def get_tool(self, name: str) -> ForgedTool:
        """Retrieve a tool by its runtime name."""
        if name not in self.tools:
            raise KeyError(f"Unknown tool '{name}'. Available tools: {list(self.tools.keys())}")
        return self.tools[name]

    def list_tools(self) -> list[str]:
        """List the runtime names of all available tools."""
        return list(self.tools.keys())

    def to_openai_tools(self) -> list[dict[str, Any]]:
        """Render the whole toolset as OpenAI-compatible tool definitions."""
        return [tool.to_openai_tool() for tool in self.tools.values()]

    def invoke(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
        /,
        *,
        state: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Invoke one of the registered tools by name."""
        return self.get_tool(name).invoke(arguments, state=state, **kwargs)

    async def ainvoke(
        self,
        name: str,
        arguments: dict[str, Any] | None = None,
        /,
        *,
        state: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        """Async variant of ``invoke``."""
        return await self.get_tool(name).ainvoke(arguments, state=state, **kwargs)
