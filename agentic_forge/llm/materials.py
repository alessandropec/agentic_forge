"""Declarative materials for LLM providers, models, and managers."""

from enum import Enum
from typing import Dict, Optional

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
    """

    type: ModelType
    name: str
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None


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
