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
        """Store material without reading files or changing the environment.

        API-key files are NOT read here: forging a provider (e.g. just to list
        the model catalog or select a session) must not require every
        provider's key file to exist. Keys are loaded lazily the first time a
        model is actually built for this provider -- see ``_ensure_keys``.
        """
        self.material = material
        self.models: Dict[str, LlmModelMaterial] = material.models
        self._keys_loaded = False
        self._api_key: str | None = None

    # -------------------------
    # CREDENTIAL HANDLING
    # -------------------------

    def _ensure_keys(self) -> None:
        """Lazily load this provider's API key into instance-local storage.

        Called only when a concrete model is built (i.e. an actual LLM call is
        imminent), so listing/forging never touches the filesystem. Idempotent
        and only relevant for key-file providers (OpenAI / OpenRouter); Ollama
        needs no key. Raises a clear error if the file is missing instead of
        surfacing an opaque failure deep in a graph node.
        """
        if self._keys_loaded:
            return
        if self.material.type not in (ProviderType.OPENAI, ProviderType.OPENROUTER):
            self._keys_loaded = True
            return
        if not self.material.api_key_file:
            self._keys_loaded = True
            return

        key_path = Path(self.material.api_key_file).expanduser()
        if not key_path.is_absolute() and self.material.base_dir:
            key_path = Path(self.material.base_dir) / key_path
        key_path = key_path.resolve()

        if not key_path.exists():
            raise FileNotFoundError(
                f"API key file not found for provider '{self.material.type}': {key_path}. "
                f"Copy the example and fill in your keys (e.g. providers_api_key.example.yaml "
                f"-> providers_api_key.yaml)."
            )

        with key_path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}

        if self.material.type == ProviderType.OPENAI:
            self._api_key = data.get("openai_api_key", "")
        elif self.material.type == ProviderType.OPENROUTER:
            self._api_key = data.get("openrouter_api_key", "")

        self._keys_loaded = True

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

    def _build_chat_model(self, model: LlmModelMaterial, /, **kwargs: Any) -> Any:
        """Build a chat model for the configured provider.

        Precedence (lowest to highest): the model's static fields
        (temperature/top_p/max_tokens), ``model.extra_options``, then
        explicit ``**kwargs`` passed to ``get_model``.
        """
        self._ensure_keys()

        options = {"model": model.name}
        if self.material.base_url is not None:
            options["base_url"] = self.material.base_url
        if model.temperature is not None:
            options["temperature"] = model.temperature
        if model.top_p is not None:
            options["top_p"] = model.top_p
        if model.max_tokens is not None:
            token_option = "num_predict" if self.material.type == ProviderType.OLLAMA else "max_tokens"
            options[token_option] = model.max_tokens
        if self.material.type == ProviderType.OPENAI:
            options["openai_api_key"] = self._api_key if self._api_key is not None else os.environ.get("OPENAI_API_KEY")
        elif self.material.type == ProviderType.OPENROUTER:
            options["openai_api_key"] = self._api_key if self._api_key is not None else os.environ.get("OPENROUTER_API_KEY")
        elif self.material.type == ProviderType.OLLAMA and self.material.keep_alive is not None:
            options["keep_alive"] = self.material.keep_alive
        options.update(model.extra_options)
        options.update(kwargs)

        if self.material.type == ProviderType.OPENAI:
            if ChatOpenAI is None:
                raise ImportError("langchain_openai is required for OpenAI chat models")
            return ChatOpenAI(**options)

        if self.material.type == ProviderType.OLLAMA:
            if ChatOllama is None:
                raise ImportError("langchain_ollama is required for Ollama chat models")
            return ChatOllama(**options)

        if self.material.type == ProviderType.OPENROUTER:
            if ChatOpenAI is None:
                raise ImportError("langchain_openai is required for OpenRouter chat models")
            return ChatOpenAI(**options)

        raise ValueError(f"Unsupported provider type for chat model: {self.material.type}")

    def _build_embedding_model(self, model: LlmModelMaterial, /, **kwargs: Any) -> Any:
        """Build an embedding model for the configured provider."""
        self._ensure_keys()
        options = {"model": model.name}
        if self.material.base_url is not None:
            options["base_url"] = self.material.base_url
        if self.material.type in (ProviderType.OPENAI, ProviderType.OPENROUTER):
            env_name = "OPENAI_API_KEY" if self.material.type == ProviderType.OPENAI else "OPENROUTER_API_KEY"
            options["openai_api_key"] = self._api_key if self._api_key is not None else os.environ.get(env_name)
            constructor = OpenAIEmbeddings
        elif self.material.type == ProviderType.OLLAMA:
            constructor = OllamaEmbeddings
            if self.material.keep_alive is not None:
                options["keep_alive"] = self.material.keep_alive
        else:
            raise ValueError(f"Unsupported provider type for embedding model: {self.material.type}")
        options.update(model.extra_options)
        options.update(kwargs)
        if constructor is None:
            raise ImportError(f"LangChain integration is required for {self.material.type} embedding models")
        return constructor(**options)
