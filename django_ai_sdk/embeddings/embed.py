from __future__ import annotations

from typing import Any

# Default embedding models per provider
_EMBEDDING_MODELS = {
    "openai": "text-embedding-3-small",
    "anthropic": "voyage-3",
    "gemini": "text-embedding-004",
    "ollama": "nomic-embed-text",
    "cohere": "embed-english-v3.0",
}


def embed(
    text: str | list[str],
    *,
    provider: str = "openai",
    model: str | None = None,
    **kwargs: Any,
) -> list[float] | list[list[float]]:
    """
    Generate an embedding vector for the given text using litellm.

    Returns a single vector when ``text`` is a string, or a list of vectors
    when ``text`` is a list.

    Example::

        from django_ai_sdk.embeddings import embed

        vector = embed("Django ORM is great.", provider="openai")
        vectors = embed(["text one", "text two"], provider="openai")

    Requires: ``pip install litellm``
    """
    try:
        import litellm
    except ImportError as exc:
        raise ImportError("litellm is required. Run: pip install litellm") from exc

    from django_ai_sdk.providers.registry import registry

    provider_config = registry.get_config(provider)
    resolved_model = model or _EMBEDDING_MODELS.get(provider, "text-embedding-3-small")

    # Prefix model with provider for litellm routing
    if "/" not in resolved_model and provider not in ("openai",):
        resolved_model = f"{provider}/{resolved_model}"

    call_kwargs: dict[str, Any] = {
        "model": resolved_model,
        "input": text if isinstance(text, list) else [text],
    }

    if provider_config:
        if provider_config.api_key:
            call_kwargs["api_key"] = provider_config.api_key
        if provider_config.base_url:
            call_kwargs["api_base"] = provider_config.base_url

    call_kwargs.update(kwargs)

    try:
        response = litellm.embedding(**call_kwargs)
    except Exception as exc:
        from django_ai_sdk.exceptions import ProviderError
        raise ProviderError(str(exc), provider=provider) from exc

    vectors = [item["embedding"] for item in response.data]
    return vectors[0] if isinstance(text, str) else vectors


async def aembed(
    text: str | list[str],
    *,
    provider: str = "openai",
    model: str | None = None,
    **kwargs: Any,
) -> list[float] | list[list[float]]:
    """Async version of :func:`embed`."""
    try:
        import litellm
    except ImportError as exc:
        raise ImportError("litellm is required.") from exc

    from django_ai_sdk.providers.registry import registry

    provider_config = registry.get_config(provider)
    resolved_model = model or _EMBEDDING_MODELS.get(provider, "text-embedding-3-small")

    if "/" not in resolved_model and provider not in ("openai",):
        resolved_model = f"{provider}/{resolved_model}"

    call_kwargs: dict[str, Any] = {
        "model": resolved_model,
        "input": text if isinstance(text, list) else [text],
    }

    if provider_config:
        if provider_config.api_key:
            call_kwargs["api_key"] = provider_config.api_key
        if provider_config.base_url:
            call_kwargs["api_base"] = provider_config.base_url

    call_kwargs.update(kwargs)

    try:
        response = await litellm.aembedding(**call_kwargs)
    except Exception as exc:
        from django_ai_sdk.exceptions import ProviderError
        raise ProviderError(str(exc), provider=provider) from exc

    vectors = [item["embedding"] for item in response.data]
    return vectors[0] if isinstance(text, str) else vectors
