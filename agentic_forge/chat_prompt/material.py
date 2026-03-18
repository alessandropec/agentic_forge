"""Declarative materials for chat prompts and messages."""

from typing import List, Optional, Literal

from pydantic import Field

from agentic_forge.core.material import Material

RoleType = Literal["system", "human", "ai", "placeholder"]


class ChatMessageMaterial(Material):
    """Single chat message template configuration.

    Args:
        role: Message role (system, human, ai, or placeholder).
        content: Template or literal content for the message.
        images: Optional list of image URLs for multimodal human messages.

    Example:
        >>> ChatMessageMaterial(role="human", content="Hello {name}")
    """

    role: RoleType
    content: Optional[str] = None
    images: List[str] = Field(default_factory=list)


class ChatPromptMaterial(Material):
    """Chat prompt assembled from ordered message materials.

    Args:
        name: Optional identifier for the prompt template.
        messages: Ordered list of ``ChatMessageMaterial`` entries.

    Example:
        >>> msg = ChatMessageMaterial(role="system", content="You are a bot.")
        >>> prompt = ChatPromptMaterial(name="bot", messages=[msg])
    """

    name: str
    messages: List[ChatMessageMaterial]
