"""Forge implementations for chat prompts and messages."""

from pathlib import Path
from typing import Any, List, Union

from pydantic import Field

try:
    from langchain_core.prompts import (
        AIMessagePromptTemplate,
        ChatMessagePromptTemplate,
        ChatPromptTemplate,
        HumanMessagePromptTemplate,
        MessagesPlaceholder,
        SystemMessagePromptTemplate,
    )
except ImportError:  # pragma: no cover - allow docs generation without langchain
    AIMessagePromptTemplate = ChatMessagePromptTemplate = ChatPromptTemplate = None  # type: ignore
    HumanMessagePromptTemplate = MessagesPlaceholder = SystemMessagePromptTemplate = None  # type: ignore

from agentic_forge.chat_prompt.material import ChatMessageMaterial, ChatPromptMaterial
from agentic_forge.chat_prompt.forged import ForgedChatPrompt, _normalize_message_images
from agentic_forge.core.codex import register_forge
from agentic_forge.core.forge import Forge


# TODO: add schema-level validation to ensure message coherence beyond field checks.

if HumanMessagePromptTemplate is not None:
    class _LocalImageMessageTemplate(HumanMessagePromptTemplate):
        """Resolve images relative to the YAML that defines this message."""

        image_base_dir: str | None = None
        image_sources: dict[str, str] = Field(default_factory=dict)

        def format(self, **kwargs: Any) -> Any:
            message = super().format(**kwargs)
            base = Path(self.image_base_dir) if self.image_base_dir else None
            return _normalize_message_images([message], base, self.image_sources)[0]

        async def aformat(self, **kwargs: Any) -> Any:
            message = await super().aformat(**kwargs)
            base = Path(self.image_base_dir) if self.image_base_dir else None
            return _normalize_message_images([message], base, self.image_sources)[0]


@register_forge("chat_message")
class ChatMessageForge(Forge):
    """Build LangChain message prompt templates from ``ChatMessageMaterial``."""

    material_cls = ChatMessageMaterial

    def forge_from_material(
        self, material: ChatMessageMaterial
    ) -> Union[ChatMessagePromptTemplate, MessagesPlaceholder]:
        """Convert a message material into a LangChain prompt template.

        Args:
            material: Declarative chat message configuration.

        Returns:
            A LangChain ``ChatMessagePromptTemplate`` or ``MessagesPlaceholder``.

        Raises:
            ValueError: If the role is unsupported or placeholder content is invalid.

        Example:
            >>> material = ChatMessageMaterial(role="system", content="You are a bot.")
            >>> template = ChatMessageForge().forge_from_material(material)
        """
        if MessagesPlaceholder is None:
            raise ImportError("langchain_core is required to build chat prompts")
        if material.role == "placeholder":
            if material.content is None or " " in material.content:
                raise ValueError(
                    f"Unsupported content for placeholder i.e {material.content} space "
                    "  are not allowed for placeholder variable name"
                )
            return MessagesPlaceholder(variable_name=material.content)

        if material.role == "system":
            return SystemMessagePromptTemplate.from_template(material.content or "")

        if material.role == "human":
            blocks: List[dict[str, Any]] = []

            if material.content:
                blocks.append({"type": "text", "text": material.content})

            for img in material.images:
                blocks.append({"type": "image_url", "image_url": {"url": img}})

            return _LocalImageMessageTemplate.from_template(
                blocks, image_base_dir=material.base_dir
            )

        if material.role == "ai":
            return AIMessagePromptTemplate.from_template(material.content or "")

        raise ValueError(f"Unsupported role: {material.role}")


@register_forge("chat_prompt")
class ChatPromptForge(Forge):
    """Compose chat messages into a LangChain ``ChatPromptTemplate``."""

    material_cls = ChatPromptMaterial

    def forge_from_material(self, material: ChatPromptMaterial) -> ForgedChatPrompt:
        """Build a chat prompt from message materials.

        Args:
            material: Prompt configuration containing ordered messages.

        Returns:
            A ``ForgedChatPrompt`` wrapping a ``ChatPromptTemplate``.

        Example:
            >>> msg = ChatMessageMaterial(role="system", content="You are a bot.")
            >>> prompt = ChatPromptMaterial(name="bot", messages=[msg])
            >>> template = ChatPromptForge().forge_from_material(prompt)
        """
        if ChatPromptTemplate is None:
            raise ImportError("langchain_core is required to build chat prompts")
        msg_forge = ChatMessageForge()
        messages = [
            msg_forge.forge_from_material(
                m if m.base_dir else m.model_copy(update={"base_dir": material.base_dir})
            )
            for m in material.messages
        ]
        prompt = ChatPromptTemplate.from_messages(messages)
        return ForgedChatPrompt(prompt, base_dir=material.base_dir)
