from __future__ import annotations

from djangosdk.exceptions import ConfigurationError, ProviderError
from djangosdk.providers.base import AbstractProvider
from djangosdk.providers.litellm_provider import LiteLLMProvider
from djangosdk.providers.schemas import ProviderConfig


class ProviderRegistry:
    """Singleton registry of configured providers, built from AI_SDK settings."""

    def __init__(self) -> None:
        self._providers: dict[str, AbstractProvider] = {}
        self._configs: dict[str, ProviderConfig] = {}
        self._default: str = ""
        self._failover_chain: list[str] = []

    def configure(self, settings: dict) -> None:
        """Initialize registry from the AI_SDK settings dict."""
        self._providers.clear()
        self._configs.clear()

        self._default = settings.get("DEFAULT_PROVIDER", "openai")
        self._failover_chain = settings.get("FAILOVER", [])
        providers_cfg = settings.get("PROVIDERS", {})

        for name, cfg_dict in providers_cfg.items():
            config = ProviderConfig.from_dict(name, cfg_dict)
            self._configs[name] = config
            self._providers[name] = LiteLLMProvider(provider_config=config)

        # Always ensure a default LiteLLMProvider exists even without explicit config
        if self._default not in self._providers:
            self._providers[self._default] = LiteLLMProvider()

    def get(self, name: str | None = None) -> AbstractProvider:
        """Get a provider by name, falling back to the default."""
        name = name or self._default
        if name not in self._providers:
            raise ConfigurationError(
                f"Provider '{name}' is not configured. "
                f"Available providers: {list(self._providers.keys())}"
            )
        return self._providers[name]

    def complete_with_failover(self, request, agent=None):
        """
        Attempt ``provider.complete(request)``, falling back through the failover
        chain on ``ProviderError``. Emits ``agent_failed_over`` signal on each switch.
        """
        from djangosdk.signals import agent_failed_over

        chain = self._failover_chain or [request.provider or self._default]
        # Ensure the primary provider is first
        primary = request.provider or self._default
        ordered = [primary] + [p for p in chain if p != primary]

        last_exc: Exception | None = None
        for provider_name in ordered:
            if provider_name not in self._providers:
                continue
            try:
                import copy
                req = copy.copy(request)
                req.provider = provider_name
                return self._providers[provider_name].complete(req)
            except ProviderError as exc:
                last_exc = exc
                next_providers = [p for p in ordered if p != provider_name and p in self._providers]
                if next_providers:
                    agent_failed_over.send(
                        sender=agent.__class__ if agent else None,
                        agent=agent,
                        from_provider=provider_name,
                        to_provider=next_providers[0],
                        reason=str(exc),
                    )

        raise ProviderError(
            f"All providers in failover chain failed. Last error: {last_exc}"
        ) from last_exc

    def get_config(self, name: str | None = None) -> ProviderConfig | None:
        name = name or self._default
        return self._configs.get(name)

    def get_default_model(self, provider_name: str | None = None, fallback: str = "") -> str:
        config = self.get_config(provider_name)
        if config and config.default_model:
            return config.default_model
        return fallback

    def list_providers(self) -> list[str]:
        return list(self._providers.keys())

    @property
    def default_provider(self) -> str:
        return self._default


registry = ProviderRegistry()
