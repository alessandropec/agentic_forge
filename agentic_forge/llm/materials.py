"""Declarative materials for LLM providers, models, and managers."""

from enum import Enum
from typing import Any, Dict, Optional

from pydantic import Field

from agentic_forge.core.material import Material

# -------------------------
# ENUM CENTRALIZZATI
# -------------------------


class ProviderType(str, Enum):
    """Supported provider backends."""

    OPENAI = "openai"
    OLLAMA = "ollama"
    OPENROUTER = "openrouter"


class ModelType(str, Enum):
    """Supported model modalities."""

    CHAT = "chat"
    EMBEDDING = "embedding"


# -------------------------
# MATERIAL
# -------------------------


class LlmModelMaterial(Material):
    """Model configuration for a provider.

    Args:
        type: Model modality (chat or embedding).
        name: Provider-specific model name.
        max_tokens: Optional limit for chat responses.
        temperature: Optional sampling temperature.
        top_p: Optional nucleus sampling parameter.
        supports_vision: Whether this model can take image inputs. Informational
            metadata for callers (e.g. to decide whether to attach images to a
            prompt); not enforced by the forge itself.
        extra_options: Extra constructor kwargs forwarded to the underlying
            LangChain chat or embedding model (e.g. ``{"num_gpu": 0}`` to force CPU on
            Ollama, or ``{"reasoning": False}`` to disable a model's
            "thinking" mode). Caller-supplied kwargs to ``get_model`` take
            precedence over these on conflict.
    """

    type: ModelType
    name: str
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    supports_vision: bool = False
    extra_options: Dict[str, Any] = Field(default_factory=dict)


class LlmProviderMaterial(Material):
    """Provider configuration with its available models.

    Args:
        type: Provider backend type.
        base_url: Optional base URL (e.g., for Ollama/OpenRouter).
        api_key_file: Path to YAML file containing API keys.
        keep_alive: Optional keep-alive for Ollama.
        models: Mapping of model keys to model materials.
    """

    type: ProviderType
    base_url: Optional[str] = None
    api_key_file: Optional[str] = None
    keep_alive: Optional[str] = None
    models: Dict[str, LlmModelMaterial]


class LlmManagerMaterial(Material):
    """Manager configuration aggregating multiple providers.

    Args:
        providers: Mapping provider key -> provider configuration dict.
    """

    providers: Dict[str, dict]
