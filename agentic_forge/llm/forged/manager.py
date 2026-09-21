"""Runtime manager exposing provider/model selection utilities."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

from agentic_forge.core.forged import Forged

if TYPE_CHECKING:
    from agentic_forge.llm.forged.provider import ForgedLlmProvider

ProviderMap = Dict[str, "ForgedLlmProvider"]


class ForgedLlmManager(Forged):
    """Runtime manager exposing provider/model selection utilities."""

    def __init__(self, providers: ProviderMap):
        """Store available providers keyed by name."""
        self.providers = providers

    def get_model(self, provider_key: str, model_key: Optional[str] = None, **kwargs: Any) -> Any:
        """Fetch a model via provider/model keys or selector ``provider:model``.

        Args:
            provider_key: Provider key or combined selector.
            model_key: Optional model key (ignored if selector is combined).
            **kwargs: Extra arguments forwarded to provider builders.

        Returns:
            Backend-specific model instance.

        Raises:
            KeyError: If the provider is missing.
            ValueError: If selector format is invalid.
        """
        if model_key is None:
            provider_key, model_key = self._split_selector(provider_key)

        provider = self.providers.get(provider_key)
        if provider is None:
            raise KeyError(f"Provider `{provider_key}` not found")
        return provider.get_model(model_key, **kwargs)

    def list_models(self) -> List[Dict[str, Any]]:
        """List available models with provider/model metadata."""
        catalog: List[Dict[str, Any]] = []
        for provider_key, provider in self.providers.items():
            models = getattr(provider, "models", {}) or {}
            provider_type = getattr(getattr(provider, "material", None), "type", None)
            for model_key, model in models.items():
                catalog.append(
                    {
                        "selector": f"{provider_key}:{model_key}",
                        "provider": provider_key,
                        "provider_type": provider_type,
                        "model": model_key,
                        "type": getattr(model, "type", None),
                        "name": getattr(model, "name", None),
                        "max_tokens": getattr(model, "max_tokens", None),
                        "temperature": getattr(model, "temperature", None),
                        "top_p": getattr(model, "top_p", None),
                        "supports_vision": getattr(model, "supports_vision", False),
                    }
                )
        return catalog

    def get_model_info(self, selector: str) -> Dict[str, Any]:
        """Return the catalog entry for one ``provider:model`` selector.

        Raises:
            KeyError: If no model matches the selector.
        """
        for entry in self.list_models():
            if entry["selector"] == selector:
                return entry
        raise KeyError(f"Model selector '{selector}' not found")

    def _split_selector(self, selector: str) -> Tuple[str, str]:
        """Split ``provider:model`` selector into components."""
        if ":" not in selector:
            raise ValueError("Model selector must be 'provider:model'")
        provider_key, model_key = selector.split(":", 1)
        return provider_key, model_key
