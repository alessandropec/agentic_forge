"""Runtime provider that builds chat or embedding models on demand."""

import os
from pathlib import Path
from typing import Any, Dict

import yaml

try:
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings
except ImportError:  # pragma: no cover - allow docs generation without heavy deps
    ChatOpenAI = OpenAIEmbeddings = None  # type: ignore

try:
    from langchain_ollama import ChatOllama, OllamaEmbeddings
except ImportError:  # pragma: no cover - allow docs generation without heavy deps
    ChatOllama = OllamaEmbeddings = None  # type: ignore

from agentic_forge.core.forged import Forged
from agentic_forge.llm.materials import LlmModelMaterial, LlmProviderMaterial, ModelType, ProviderType


class ForgedLlmProvider(Forged):
    """Runtime provider that builds chat or embedding models on demand."""

    def __init__(self, material: LlmProviderMaterial) -> None:
        """Store material and prepare environment variables."""
        self.material = material
        self.models: Dict[str, LlmModelMaterial] = material.models
        self._setup_env()

    # -------------------------
    # ENV HANDLING
    # -------------------------

    def _setup_env(self) -> None:
        """Load API keys/keep-alive settings into environment."""
        if self.material.api_key_file:
            key_path = Path(self.material.api_key_file).expanduser()
            if not key_path.is_absolute() and self.material.base_dir:
                key_path = Path(self.material.base_dir) / key_path
            key_path = key_path.resolve()

            with key_path.open("r", encoding="utf-8") as file:
                data = yaml.safe_load(file)

            if self.material.type == ProviderType.OPENAI:
                os.environ["OPENAI_API_KEY"] = data.get("openai_api_key", "")

            elif self.material.type == ProviderType.OPENROUTER:
                os.environ["OPENROUTER_API_KEY"] = data.get("openrouter_api_key", "")

        if self.material.keep_alive:
            os.environ["OLLAMA_KEEP_ALIVE"] = self.material.keep_alive

    # -------------------------
    # PUBLIC API
    # -------------------------

    def get_model(self, model_key: str, **kwargs: Any) -> Any:
        """Return a concrete LangChain model for the given key."""
        if model_key not in self.models:
            raise KeyError(f"Model `{model_key}` not found")
        model: LlmModelMaterial = self.models[model_key]

        if model.type == ModelType.CHAT:
            return self._build_chat_model(model, **kwargs)

        if model.type == ModelType.EMBEDDING:
            return self._build_embedding_model(model, **kwargs)

        raise ValueError(f"Unsupported model type: {model.type}")

    # -------------------------
    # INTERNAL BUILDERS
    # -------------------------

    def _build_chat_model(self, model: LlmModelMaterial, **kwargs: Any) -> Any:
        """Build a chat model for the configured provider."""
        if self.material.type == ProviderType.OPENAI:
            if ChatOpenAI is None:
                raise ImportError("langchain_openai is required for OpenAI chat models")
            return ChatOpenAI(
                model=model.name,
                max_tokens=model.max_tokens,
                temperature=model.temperature,
                top_p=model.top_p,
                openai_api_key=os.environ.get("OPENAI_API_KEY"),
                **kwargs,
            )

        if self.material.type == ProviderType.OLLAMA:
            if ChatOllama is None:
                raise ImportError("langchain_ollama is required for Ollama chat models")
            return ChatOllama(
                model=model.name,
                base_url=self.material.base_url,
                **kwargs,
            )

        if self.material.type == ProviderType.OPENROUTER:
            if ChatOpenAI is None:
                raise ImportError("langchain_openai is required for OpenRouter chat models")
            return ChatOpenAI(
                model=model.name,
                base_url=self.material.base_url,
                openai_api_key=os.environ.get("OPENROUTER_API_KEY"),
                **kwargs,
            )

        raise ValueError(f"Unsupported provider type for chat model: {self.material.type}")

    def _build_embedding_model(self, model: LlmModelMaterial, **kwargs: Any) -> Any:
        """Build an embedding model for the configured provider."""
        if self.material.type == ProviderType.OPENAI:
            if OpenAIEmbeddings is None:
                raise ImportError("langchain_openai is required for OpenAI embedding models")
            return OpenAIEmbeddings(
                model=model.name,
                openai_api_key=os.environ.get("OPENAI_API_KEY"),
                **kwargs,
            )

        if self.material.type == ProviderType.OLLAMA:
            if OllamaEmbeddings is None:
                raise ImportError("langchain_ollama is required for Ollama embedding models")
            return OllamaEmbeddings(
                model=model.name,
                base_url=self.material.base_url,
                **kwargs,
            )

        if self.material.type == ProviderType.OPENROUTER:
            if OpenAIEmbeddings is None:
                raise ImportError("langchain_openai is required for OpenRouter embedding models")
            return OpenAIEmbeddings(
                model=model.name,
                base_url=self.material.base_url,
                openai_api_key=os.environ.get("OPENROUTER_API_KEY"),
                **kwargs,
            )

        raise ValueError(f"Unsupported provider type for embedding model: {self.material.type}")
